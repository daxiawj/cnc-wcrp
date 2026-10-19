#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成 Netlify `_redirects`：把旧站 /news/87 这类自增 ID 地址 301 到新的语义化地址。

旧站（Laravel）跑在 cnc-wcrp.cn 上，那些地址已有搜索引擎收录和外部引用，
换到新站后如果直接 404 会丢掉权重，所以逐个做永久跳转。

用法：python scripts/05_redirects.py
"""
import glob
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

URL_RE = re.compile(r'^url:\s*"([^"]+)"', re.M)


def main():
    files = sorted(
        glob.glob("content/**/*.html", recursive=True)
        + glob.glob("content/**/*.md", recursive=True)
    )
    rows = []
    for path in files:
        raw = open(path, encoding="utf-8").read()
        m = URL_RE.search(raw)
        if not m:
            continue
        new_url = m.group(1)
        rel = os.path.relpath(path, "content").replace(os.sep, "/")
        if "/" not in rel:
            continue                      # 根目录单页（contact.md），地址没变
        section, fname = rel.split("/", 1)
        if fname.startswith("_"):
            continue                      # 栏目索引
        old_url = "/%s/%s" % (section, os.path.splitext(fname)[0])
        if old_url.rstrip("/") == new_url.rstrip("/"):
            continue                      # 地址本来就一样
        rows.append((old_url, new_url))

    lines = [
        "# 旧站（Laravel）地址 -> 新站语义化地址，永久跳转（301）",
        "# cnc-wcrp.cn 上这些地址有搜索引擎收录和外部引用，用 301 保住权重",
        "# 由 scripts/05_redirects.py 生成，请勿手工编辑",
        "",
    ]
    for old, new in rows:
        lines.append("%-16s %-78s 301" % (old, new))
        lines.append("%-16s %-78s 301" % (old + "/", new))

    out = os.path.join("static", "_redirects")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")

    print("映射条数: %d，规则行数: %d -> %s" % (len(rows), len(rows) * 2, out))
    for old, new in rows[:3]:
        print("  %s -> %s" % (old, new))


if __name__ == "__main__":
    main()
