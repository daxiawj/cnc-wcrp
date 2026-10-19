# -*- coding: utf-8 -*-
"""抓取 cnc-wcrp.cn 全站页面与静态资源（只读，不改动源站）"""
import os, re, json, time, posixpath
from urllib.parse import urljoin, urlparse, unquote
import requests
from bs4 import BeautifulSoup

BASE = "https://www.cnc-wcrp.cn"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "_raw")
PAGES = os.path.join(RAW, "pages")
ASSETS = os.path.join(RAW, "assets")
for d in (PAGES, ASSETS):
    os.makedirs(d, exist_ok=True)

HDRS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Accept-Language": "zh-CN,zh;q=0.9"}

s = requests.Session()
s.headers.update(HDRS)

fetched = {}
asset_seen = set()


def keysafe(u):
    """URL -> 本地文件名"""
    p = urlparse(u)
    name = (p.path or "/").strip("/") or "index"
    if p.query:
        name += "?" + p.query
    name = unquote(name)
    name = name.replace("/", "_")
    name = re.sub(r'[\\:*?"<>|]', "_", name)
    return name + ".html"


def get(url, referer=None):
    if url in fetched:
        return fetched[url]
    h = {}
    if referer:
        h["Referer"] = referer
    try:
        r = s.get(url, headers=h, timeout=30, verify=False)
        r.encoding = r.apparent_encoding or "utf-8"
        fetched[url] = r
        print(f"[{r.status_code}] {url}  {len(r.content)}B")
        return r
    except Exception as e:
        print("[ERR]", url, e)
        fetched[url] = None
        return None


def save_page(url, html):
    with open(os.path.join(PAGES, keysafe(url)), "w", encoding="utf-8") as f:
        f.write(html)


def download_asset(u, referer):
    u = urljoin(BASE, u)
    if not u.startswith(BASE):
        p = urlparse(u)
        if p.netloc and "cnc-wcrp" not in p.netloc:
            return None  # 跳过外链
    if u.split("?")[0] in asset_seen:
        return u.split("?")[0]
    asset_seen.add(u.split("?")[0])
    p = urlparse(u)
    rel = unquote(p.path).lstrip("/")
    dest = os.path.join(ASSETS, rel.replace("/", os.sep))
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return u.split("?")[0]
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    try:
        r = s.get(u, headers={"Referer": referer}, timeout=30, verify=False)
        if r.status_code == 200:
            with open(dest, "wb") as f:
                f.write(r.content)
            print("   asset", rel, len(r.content))
            return u.split("?")[0]
    except Exception as e:
        print("   asset ERR", u, e)
    return None


def collect_assets(soup, page_url):
    urls = []
    for tag, attr in (("link", "href"), ("script", "src"), ("img", "src")):
        for el in soup.find_all(tag):
            v = el.get(attr)
            if v:
                urls.append(v)
    # 内联 style 中的 url(...)
    for el in soup.find_all(style=True):
        urls += re.findall(r'url\(([\'"]?)(.*?)\1\)', el["style"])
    for u in urls:
        if isinstance(u, tuple):
            u = u[1]
        if not u or u.startswith("data:") or u.startswith("javascript:"):
            continue
        download_asset(u, page_url)


def crawl_section(prefix, url):
    """遍历分页列表，返回详情页链接"""
    detail = []
    page = 1
    while page < 30:
        u = url if page == 1 else f"{url}?page={page}"
        r = get(u, referer=url)
        if not r or r.status_code != 200:
            break
        save_page(u, r.text)
        soup = BeautifulSoup(r.text, "lxml")
        collect_assets(soup, u)
        links = []
        for a in soup.select(f'a[href*="/{prefix}/"]'):
            href = urljoin(BASE, a["href"])
            if re.search(rf"/{prefix}/\d+$", urlparse(href).path):
                if href not in links:
                    links.append(href)
        if not links:
            break
        for l in links:
            if l not in detail:
                detail.append(l)
        pager = [a.get("href", "") for a in soup.select(".pagination a")]
        nxt = any(f"page={page+1}" in p for p in pager)
        if not nxt:
            break
        page += 1
    return detail


def main():
    requests.packages.urllib3.disable_warnings()
    seeds = ["/", "/about/9", "/about/10", "/committee/7", "/committee/6",
             "/contact", "/about", "/committee"]
    for path in seeds:
        r = get(BASE + path, referer=BASE)
        if r and r.status_code == 200:
            save_page(BASE + path, r.text)
            collect_assets(BeautifulSoup(r.text, "lxml"), BASE + path)

    news = crawl_section("news", BASE + "/news")
    notices = crawl_section("notices", BASE + "/notices")
    # 首页轮播里也有 news/<id>，合并
    home = fetched.get(BASE)
    extra = []
    if home:
        for a in BeautifulSoup(home.text, "lxml").select('a[href*="/news/"]'):
            u = urljoin(BASE, a["href"])
            if u not in extra:
                extra.append(u)
    for u in extra:
        if u not in news:
            news.append(u)

    all_detail = news + notices
    for u in all_detail:
        r = get(u, referer=BASE + "/news")
        if r and r.status_code == 200:
            save_page(u, r.text)
            collect_assets(BeautifulSoup(r.text, "lxml"), u)

    manifest = {
        "news": news,
        "notices": notices,
        "pages": sorted(fetched.keys()),
        "asset_count": len(asset_seen),
    }
    with open(os.path.join(RAW, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print("\nDONE news=%d notices=%d assets=%d" % (len(news), len(notices), len(asset_seen)))


if __name__ == "__main__":
    main()
