# -*- coding: utf-8 -*-
"""把“关于我们 / 委员会名单 / 联系我们”的 HTML 正文转成 Markdown，
   便于后续直接编辑。新闻、公告保持 HTML 不动。

用法：python scripts/03_to_markdown.py
"""
import os
import re
from bs4 import BeautifulSoup, NavigableString, Tag

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, "content")

# 需要转换的栏目页：路径 -> (标题, weight)
PAGES = {
    "about/9": ("中委会简介", 1),
    "about/10": ("历史沿革", 2),
    "committee/7": ("委员会委员", 1),
    "committee/6": ("顾问委员会委员", 2),
}


def inline(node):
    """把行内标签转成 Markdown 片段"""
    out = []
    for c in node.children:
        if isinstance(c, NavigableString):
            out.append(str(c))
        elif isinstance(c, Tag):
            if c.name in ("strong", "b"):
                out.append("**" + inline(c).strip() + "**")
            elif c.name in ("em", "i"):
                out.append("*" + inline(c).strip() + "*")
            elif c.name == "br":
                out.append("  \n")
            elif c.name == "a":
                href = c.get("href", "")
                text = inline(c).strip()
                out.append(f"[{text}]({href})" if href else text)
            elif c.name == "img":
                out.append(f"![{c.get('alt', '')}]({c.get('src', '')})")
            else:
                out.append(inline(c))
    return "".join(out).replace("\xa0", " ")


def norm(t):
    return re.sub(r"[ \t]+", " ", t).strip()


def is_committee(paras):
    """判断是不是“姓名 + 单位”的名单页"""
    hits = 0
    for p in paras:
        t = p.get_text().replace("\xa0", " ")
        if re.search(r"\s{3,}\S", t):
            hits += 1
    return hits >= max(5, len(paras) * 0.5)


def split_name_unit(text):
    """按 3 个以上空格切开姓名与单位（2 字姓名内部的单空格不会误切）"""
    t = text.replace("\xa0", " ").strip()
    t = re.sub(r"^[\s]+", "", t)
    parts = re.split(r"\s{3,}", t, maxsplit=1)
    if len(parts) == 2 and parts[0] and parts[1]:
        return norm(parts[0]), norm(parts[1])
    return None


def convert_committee(soup):
    lines = []
    rows = []
    title = None
    for p in soup.find_all("p"):
        raw = inline(p)
        t = norm(raw)
        if not t:
            continue
        # 标题行取纯文本，避免 Word 里层层嵌套的 <b>/<strong> 变成一串星号
        if "名单" in t and len(t) < 40 and not re.search(r"\s{3,}", raw):
            title = norm(p.get_text().replace("\xa0", " ")).replace("*", "")
            continue
        pair = split_name_unit(raw)
        if pair:
            rows.append(pair)
        else:
            lines.append(t)

    md = []
    if title:
        md.append(f"## {title}\n")
    if lines:
        md.append("\n\n".join(lines) + "\n")
    if rows:
        md.append("| 姓名 | 单位 |\n| --- | --- |")
        for name, unit in rows:
            md.append(f"| {name.replace(' ', '')} | {unit} |")
    return "\n".join(md) + "\n"


def convert_generic(soup):
    """段落 / 列表 / 图片的通用转换"""
    blocks = []
    for el in soup.children:
        if not isinstance(el, Tag):
            continue
        name = el.name
        if name == "p":
            t = inline(el)
            if t.strip():
                blocks.append(norm(t))
        elif name in ("h1", "h2", "h3", "h4"):
            blocks.append("#" * int(name[1]) + " " + norm(inline(el)))
        elif name in ("ul", "ol"):
            items = []
            for li in el.find_all("li", recursive=False):
                items.append("- " + norm(inline(li)))
            blocks.append("\n".join(items))
        elif name == "img":
            blocks.append(f"![{el.get('alt', '')}]({el.get('src', '')})")
        elif name == "div":
            blocks.extend(convert_generic(el).split("\n\n"))
        else:
            t = norm(inline(el))
            if t:
                blocks.append(t)

    # 把“（1）…（7）”这类手工编号合并成有序列表
    out, buf = [], []
    def flush():
        nonlocal buf
        if len(buf) >= 3:
            out.append("\n".join(f"{i+1}. {re.sub(r'^（[0-9]+）', '', s)}" for i, s in enumerate(buf)))
        else:
            out.extend(buf)
        buf = []

    for b in blocks:
        if re.match(r"^（[0-9]+）", b):
            buf.append(b)
        else:
            flush()
            out.append(b)
    flush()

    # 单独成行的图片并成一段
    md, imgs = [], []
    def flush_img():
        nonlocal imgs
        if imgs:
            md.append("\n\n".join(imgs))
            imgs = []
    for b in out:
        if b.startswith("!["):
            imgs.append(b)
        else:
            flush_img()
            md.append(b)
    flush_img()

    return "\n\n".join(x for x in md if x.strip()) + "\n"


def main():
    for key, (title, weight) in PAGES.items():
        src = os.path.join(CONTENT, key + ".html")
        if not os.path.exists(src):
            print("跳过（不存在）", src)
            continue
        raw = open(src, encoding="utf-8").read()
        parts = raw.split("---", 2)
        front, body = parts[1], parts[2]
        soup = BeautifulSoup(body, "html.parser")
        paras = soup.find_all("p")

        md_body = convert_committee(soup) if is_committee(paras) else convert_generic(soup)
        # 清掉 Word 加粗留下的纯星号行（会被 Markdown 当成分割线）
        md_body = "\n".join(l for l in md_body.split("\n") if not re.fullmatch(r"\s*\*+\s*", l))
        md_body = re.sub(r"\n{3,}", "\n\n", md_body)

        # 重整 front matter：去掉 source_url（.org 域名下无意义），保留 layout/url/weight
        fm = []
        for line in front.strip().splitlines():
            if line.startswith("source_url:"):
                continue
            fm.append(line)

        dst = os.path.join(CONTENT, key + ".md")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "w", encoding="utf-8") as f:
            f.write("---\n" + "\n".join(fm) + "\n---\n\n" + md_body)
        os.remove(src)
        print("转换完成", key, "->", os.path.relpath(dst, ROOT), len(md_body), "字符")


if __name__ == "__main__":
    main()
