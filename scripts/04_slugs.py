# -*- coding: utf-8 -*-
"""把 /news/68、/about/9 这类 CMS 自增 ID 地址改成可读的语义化路径。
   不做旧地址跳转：站内所有入口（菜单、首页、列表、页脚）都指向新地址。

用法：python scripts/04_slugs.py
"""
import os
import re
import json
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, "content")

STOP = {"a", "an", "the", "of", "on", "in", "to", "for", "and", "at", "by", "from", "with"}

# 中文标题的文章：手工给一个英文 slug（专业站点不用拼音）
EN_SLUGS = {
    "news/65": "4th-national-climate-system-research-symposium-harbin",
}

# 栏目页：固定语义化地址
FIXED = {
    "about/9": "introduction",
    "about/10": "history",
    "committee/7": "members",
    "committee/6": "advisors",
}


def slugify(title, max_len=62):
    """英文标题转 a-b-c 形式；中文标题必须走 EN_SLUGS 手工映射"""
    if re.search(r"[\u4e00-\u9fff]", title):
        raise ValueError("中文标题需要先在 EN_SLUGS 里指定英文 slug：" + title)
    words = re.findall(r"[A-Za-z0-9]+", title.lower())

    out = []
    length = 0
    for w in words:
        add = len(w) + (1 if out else 0)
        if length + add > max_len:
            break
        out.append(w)
        length += add
    # 结尾是虚词就去掉，避免“…-from”“…-the”这种尾巴
    while out and out[-1] in STOP:
        out.pop()
    return "-".join(out) or "post"


def read_fm(path):
    raw = open(path, encoding="utf-8").read()
    return raw.split("---", 2)


def rewrite(path, new_url, alias=None, layout=None):
    raw = open(path, encoding="utf-8").read()
    parts = raw.split("---", 2)
    fm = [l for l in parts[1].strip("\n").split("\n")]
    body = parts[2]

    fm = [l for l in fm if not l.startswith(("url:", "aliases:", "  - \"/news/", "  - \"/notices/",
                                             "  - \"/about/", "  - \"/committee/"))]
    fm.append(f'url: "{new_url}"')
    open(path, "w", encoding="utf-8").write("---\n" + "\n".join(fm) + "\n---" + body)


def main():
    changed = {}
    # 1) 新闻 / 公告
    for section in ("news", "notices"):
        for path in sorted(glob.glob(os.path.join(CONTENT, section, "*.html"))):
            parts = read_fm(path)
            fm = parts[1]
            title = re.search(r'^title: "(.*)"$', fm, re.M).group(1)
            date = re.search(r'^date: "(.*)"$', fm, re.M).group(1)
            old_id = os.path.splitext(os.path.basename(path))[0]
            ym = date[:7]
            slug = EN_SLUGS.get(f"{section}/{old_id}") or slugify(title)
            new_url = f"/{section}/{ym}-{slug}/"
            rewrite(path, new_url)
            changed[f"/{section}/{old_id}/"] = new_url
            print(f"{section}/{old_id}  ->  {new_url}")

    # 2) 栏目页（已转 Markdown）
    for key, slug in FIXED.items():
        path = os.path.join(CONTENT, key.split("/")[0], key.split("/")[1] + ".md")
        if not os.path.exists(path):
            print("跳过", path)
            continue
        section, old_id = key.split("/")
        new_url = f"/{section}/{slug}/"
        rewrite(path, new_url)
        changed[f"/{section}/{old_id}/"] = new_url
        print(f"{key}  ->  {new_url}")

    # 3) 首页轮播数据
    banner = os.path.join(ROOT, "data", "banner.json")
    if os.path.exists(banner):
        data = json.load(open(banner, encoding="utf-8"))
        for item in data:
            item["url"] = changed.get(item["url"], item["url"])
        json.dump(data, open(banner, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # 4) 配置文件里的导航地址
    cfg = os.path.join(ROOT, "hugo.toml")
    s = open(cfg, encoding="utf-8").read()
    for old, new in changed.items():
        s = s.replace(f'url = "{old}"', f'url = "{new}"')
    open(cfg, "w", encoding="utf-8").write(s)

    # 5) 页脚等模板里的硬编码链接
    for path in glob.glob(os.path.join(ROOT, "themes", "**", "*.html"), recursive=True):
        s = open(path, encoding="utf-8").read()
        o = s
        for old, new in changed.items():
            s = s.replace(f'"{old}"', f'"{new}"')
        if s != o:
            open(path, "w", encoding="utf-8").write(s)
            print("更新模板链接", os.path.relpath(path, ROOT))

    print("\n共调整", len(changed), "条地址")


if __name__ == "__main__":
    main()
