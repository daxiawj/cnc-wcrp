# -*- coding: utf-8 -*-
"""把抓取到的页面整理成 Hugo 内容文件（正文保留原始 HTML，最大程度保真）"""
import os, re, json, base64, hashlib, io
from urllib.parse import urljoin, urlparse, unquote
from bs4 import BeautifulSoup, NavigableString, Tag
import requests

BASE = "https://www.cnc-wcrp.cn"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "_raw")
PAGES = os.path.join(RAW, "pages")
CONTENT = os.path.join(ROOT, "content")
THEME_STATIC = os.path.join(ROOT, "themes", "wcrp", "static")
IMG_UPLOADS = os.path.join(THEME_STATIC, "images", "uploads")
IMG_EXT = os.path.join(THEME_STATIC, "images", "ext")

for d in (CONTENT, IMG_UPLOADS, IMG_EXT):
    os.makedirs(d, exist_ok=True)

s = requests.Session()
s.headers.update({"User-Agent": "Mozilla/5.0", "Referer": BASE + "/"})

asset_cache = {}


def download(url, folder):
    """下载到主题 static，返回站内路径"""
    url = url.strip()
    if url in asset_cache:
        return asset_cache[url]
    p = urlparse(urljoin(BASE, url))
    name = unquote(os.path.basename(p.path)) or "img"
    name = re.sub(r"[^0-9A-Za-z._\-\u4e00-\u9fa5]", "_", name)
    if not os.path.splitext(name)[1]:
        name += ".png"
    stem, ext = os.path.splitext(name)
    # 用 URL 短哈希避免同名覆盖
    h = hashlib.md5(url.encode()).hexdigest()[:8]
    fname = f"{stem}-{h}{ext}".lower()
    dest = os.path.join(folder, fname)
    if not os.path.exists(dest) or os.path.getsize(dest) == 0:
        try:
            target = url if url.startswith("http") else urljoin(BASE, url)
            r = s.get(target, timeout=45, verify=False)
            # 源站部分图片写成了 cnc-wcrp.org，回落到主域同路径
            if r.status_code == 404 and "cnc-wcrp.org" in target:
                alt = target.replace("cnc-wcrp.org", "cnc-wcrp.cn")
                r = s.get(alt, timeout=45, verify=False)
            if r.status_code != 200 or not r.content:
                print("  !! img fail", url, r.status_code)
                return url
            with open(dest, "wb") as f:
                f.write(r.content)
            print("  img", fname, len(r.content))
        except Exception as e:
            print("  !! img err", url, e)
            return url
    rel = os.path.relpath(dest, THEME_STATIC).replace(os.sep, "/")
    path = "/" + rel
    asset_cache[url] = path
    return path


DROP_PROPS = {"font-family", "background", "mso-pagination", "mso-line-height-rule",
              "mso-margin-top-alt", "mso-margin-bottom-alt", "text-justify", "dir"}


def clean_style(style, keep_font_size=True):
    props = []
    for part in style.split(";"):
        if ":" not in part:
            continue
        k, v = part.split(":", 1)
        k = k.strip().lower()
        v = v.strip()
        if not k or not v:
            continue
        if k in DROP_PROPS or k.startswith("mso-") or k.startswith("--"):
            continue
        if k == "font-size" and not keep_font_size:
            continue
        if k == "background-color" and v.lower() in ("#ffffff", "#fff", "white"):
            continue
        props.append(f"{k}:{v}")
    return ";".join(props)


def clean_fragment(node, page_key, img_idx):
    """就地清理 HTML 片段：去 Word 垃圾、抽 base64 图、本地化图片"""
    # 去掉 Office 注释与 o:p
    for el in node.find_all(string=lambda t: isinstance(t, NavigableString) and t.strip().startswith("[if ")):
        el.extract()
    for tag in node.find_all(["o:p", "st1", "v:shape", "w:wrap"]):
        tag.decompose()
    # 清掉空的标题/段落残留（原页面 h1 常与标题重复）
    for tag in node.find_all(["h1", "h2", "h3"]):
        if not text_of(tag) and not tag.find("img"):
            tag.decompose()

    for tag in node.find_all(True):
        if not isinstance(tag, Tag):
            continue
        # 图片处理
        if tag.name == "img":
            src = tag.get("src", "")
            if src.startswith("data:image"):
                m = re.match(r"data:image/(\w+);base64,(.+)", src, re.S)
                if m:
                    ext = "jpg" if m.group(1) in ("jpeg", "jpg") else m.group(1)
                    idx = img_idx[0]; img_idx[0] += 1
                    fname = f"{page_key}-inline{idx}.{ext}"
                    dest = os.path.join(IMG_UPLOADS, fname)
                    with open(dest, "wb") as f:
                        f.write(base64.b64decode(m.group(2)))
                    tag["src"] = f"/images/uploads/{fname}"
            elif src and not src.startswith("data:"):
                is_ext = src.startswith("http") and "cnc-wcrp.cn" not in src
                tag["src"] = download(urljoin(BASE, src), IMG_EXT if is_ext else IMG_UPLOADS)
            tag["loading"] = "lazy"
            if not tag.get("alt"):
                tag["alt"] = tag.get("alt", "") or ""
            continue

        # 属性清理
        for attr in ("class", "id", "align", "lang", "dir", "face", "size", "color"):
            if attr in tag.attrs:
                del tag.attrs[attr]
        if tag.name in ("td", "th", "tr", "table", "col", "colgroup"):
            tag.attrs = {k: v for k, v in tag.attrs.items() if k in ("colspan", "rowspan", "style", "width")}
        if "style" in tag.attrs:
            st = clean_style(tag["style"])
            if st:
                tag["style"] = st
            else:
                del tag.attrs["style"]

    # 合并多余空白（只清纯 ASCII 空白，保留 &nbsp; —— 原站用它做缩进与名单对齐）
    for el in node.find_all(string=True):
        if isinstance(el, NavigableString) and not el.strip(" \t\r\n\f"):
            el.extract()
    return node


BLOCK_TAGS = {"p", "div", "br", "li", "td", "th", "tr", "table", "ul", "ol",
              "h1", "h2", "h3", "h4", "h5", "h6", "section", "blockquote"}


def strip_title_heading(frag, title):
    """去掉正文开头与页面标题重复的 h1（原后台正文里重复渲染了一次）"""
    for h in frag.find_all(["h1", "h2", "h3"]):
        if text_of(h)[:24] == title[:24]:
            h.decompose()
            return True
    return False


def text_of(node):
    """取纯文本：只在块级元素处补空格，避免把 "(AR6)" 拆成 "( AR6 )" """
    parts = []
    for el in node.descendants:
        if isinstance(el, NavigableString):
            parts.append(str(el))
        elif isinstance(el, Tag) and el.name in BLOCK_TAGS:
            parts.append(" ")
    t = "".join(parts).replace("\xa0", " ")
    return re.sub(r"\s+", " ", t).strip()


def split_sentences(t):
    """按中英文句末标点切句，并把缩写/短碎片并回下一句"""
    parts = re.split(r"(?<=[。！？])|(?<=\.)\s+|(?<=[!?])\s+", t)
    merged = []
    for p in parts:
        p = (p or "").strip()
        if not p:
            continue
        # "Dr." "U.S." "March 2023." 这类短碎片并入下一句
        if merged and len(merged[-1]) < 35:
            merged[-1] = merged[-1] + " " + p
        else:
            merged.append(p)
    return merged


def excerpt(html, title, target_cjk=130, target_en=230):
    """生成摘要：中文约 130 字、英文约 230 字符，且尽量在句末收尾"""
    soup = BeautifulSoup(html, "lxml")
    for h in soup.find_all(["h1", "h2", "h3"]):
        if text_of(h)[:20] == title[:20]:
            h.decompose()
    t = text_of(soup)
    if t.startswith(title):
        t = t[len(title):].strip()
    t = re.sub(r"^[\s.。…、,，:：]+", "", t)
    t = strip_published(t)
    if not t:
        return ""

    cjk = len(re.findall(r"[\u4e00-\u9fff]", t))
    latin = len(re.findall(r"[A-Za-z]", t))
    is_cjk = cjk * 2 >= latin
    target = target_cjk if is_cjk else target_en
    hard = int(target * 1.9)          # 单句超长时的兜底上限

    out = ""
    for s in split_sentences(t):
        cand = (out + ("" if is_cjk or not out else " ") + s).strip()
        # 再加一句会明显超长时，宁可停在已有句子的句号上
        if len(cand) > hard and out:
            break
        out = cand
        if len(out) >= target:
            break

    truncated = len(out) < len(t) - 3
    if len(out) > hard:
        cut = out[:hard]
        if not is_cjk and " " in cut:
            cut = cut[:cut.rfind(" ")]
        out = cut.rstrip("，,；;、:：")
        truncated = True
    return out + ("…" if truncated else "")


def strip_published(t):
    """去掉摘要在开头带的 'Published: 23 March 2023' 前缀"""
    return re.sub(r"^Published:\s*[0-9]{1,2}\s+\w+\s+[0-9]{4}\s*", "", t or "")


def fit_text(t, n):
    """按词边界截断，避免出现半个单词"""
    t = t.rstrip(".。… ")
    if len(t) <= n:
        return t
    cut = t[:n]
    cut = cut[:cut.rfind(" ")] if " " in cut else cut
    return cut.rstrip(",;:") + "…"


def yaml_str(s):
    return json.dumps(s, ensure_ascii=False)


def write(path, front, body, ext="html"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("---\n")
        for k, v in front.items():
            if isinstance(v, bool):
                f.write(f"{k}: {'true' if v else 'false'}\n")
            elif isinstance(v, (int, float)):
                f.write(f"{k}: {v}\n")
            elif isinstance(v, list):
                f.write(f"{k}:\n")
                for i in v:
                    f.write(f"  - {yaml_str(i)}\n")
            else:
                f.write(f"{k}: {yaml_str(v)}\n")
        f.write("---\n\n")
        f.write(body.strip() + "\n")


def load(name):
    with open(os.path.join(PAGES, name), encoding="utf-8", errors="ignore") as f:
        return BeautifulSoup(f.read(), "lxml")


def parse_date(txt):
    m = re.search(r"(\d{4})年(\d{2})月(\d{2})日", txt)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return "2020-12-05"


def article_page(fname, section, featured=()):
    soup = load(fname)
    box = soup.select_one(".news-info")
    title = text_of(box.find("h4"))
    date = parse_date(text_of(box.select_one(".date") or box))
    content = box.select_one(".content")
    body = content.decode_contents() if content else ""
    key = os.path.splitext(fname)[0].replace("_", "-")
    frag = BeautifulSoup(body, "html.parser")
    frag = clean_fragment(frag, key, [0])
    strip_title_heading(frag, title)
    out = frag.decode()
    slug = os.path.splitext(fname)[0].split("_")[1]
    page_key = f"{section}/{slug}"
    front = {
        "title": title,
        "date": date + "T00:00:00+08:00",
        "summary": excerpt(out, title),
        "source_url": f"{BASE}/{section}/{slug}",
        "url": f"/{section}/{slug}/",
    }
    first_img = re.search(r'<img[^>]+src="([^"]+)"', out)
    if first_img:
        front["cover"] = first_img.group(1)
    if slug in featured:
        front["featured"] = True
    write(os.path.join(CONTENT, section, slug + ".html"), front, out)
    print("  ->", page_key, len(out), "|", title[:30])
    return {"title": title, "slug": slug, "date": date, "summary": front["summary"],
            "body": out}


def single_page(fname, section, slug, title_override=None, weight=0):
    # 已经转成 Markdown 的栏目页不再覆盖（转换脚本 scripts/03_to_markdown.py）
    if os.path.exists(os.path.join(CONTENT, section, slug + ".md")):
        print("  跳过（已是 Markdown）", section, slug)
        return
    soup = load(fname)
    box = soup.select_one(".about-container .left")
    title = title_override or text_of(box.find("h4"))
    text = box.select_one(".text")
    body = text.decode_contents() if text else ""
    key = f"{section}-{slug}"
    frag = BeautifulSoup(body, "html.parser")
    frag = clean_fragment(frag, key, [0])
    out = frag.decode()
    write(os.path.join(CONTENT, section, slug + ".html"),
          {"title": title, "layout": "info", "weight": weight,
           "url": f"/{section}/{slug}/",
           "source_url": f"{BASE}/{section}/{slug}"}, out)
    print("  ->", section, slug, len(out), "|", title)


def main():
    requests.packages.urllib3.disable_warnings()
    print("== news ==")
    news = {}
    for i in range(65, 89):
        f = f"news_{i}.html"
        if os.path.exists(os.path.join(PAGES, f)):
            news[str(i)] = article_page(f, "news", featured={"87", "81", "77", "74"})
    print("== notices ==")
    for i in range(66, 87):
        f = f"notices_{i}.html"
        if os.path.exists(os.path.join(PAGES, f)):
            article_page(f, "notices")

    print("== about ==")
    single_page("about_9.html", "about", "9", weight=1)
    single_page("about_10.html", "about", "10", weight=2)
    print("== committee ==")
    single_page("committee_7.html", "committee", "7", weight=1)
    single_page("committee_6.html", "committee", "6", weight=2)

    print("== contact ==")
    soup = load("contact.html")
    info = soup.select_one(".us-info")
    body = info.decode_contents() if info else ""
    frag = BeautifulSoup(body, "html.parser")
    frag = clean_fragment(frag, "contact", [0])
    write(os.path.join(CONTENT, "contact.html"),
          {"title": "联系我们", "layout": "contact", "url": "/contact/"}, frag.decode())

    # 首页轮播
    home = load("index.html")
    banner = []
    for li in home.select(".slideBox .bd li"):
        a = li.find("a"); img = li.find("img")
        href = a["href"] if a else ""
        slug = re.search(r"/news/(\d+)", href)
        if not slug:
            continue
        sid = slug.group(1)
        item = news.get(sid, {})
        banner.append({
            "title": item.get("title", ""),
            "url": f"/news/{sid}/",
            "image": download(img["src"], IMG_UPLOADS) if img else "",
            "text": fit_text(strip_published(item.get("summary") or ""), 130),
        })
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    with open(os.path.join(ROOT, "data", "banner.json"), "w", encoding="utf-8") as f:
        json.dump(banner, f, ensure_ascii=False, indent=2)
    print("banner:", len(banner))


if __name__ == "__main__":
    main()
