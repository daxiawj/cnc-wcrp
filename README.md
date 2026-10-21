# CNC-WCRP 官网（Hugo 静态站）

世界气候研究计划中国委员会（CNC-WCRP）官方网站，2026 年由 Laravel 迁移为纯静态站点。

- **线上地址**：https://www.cnc-wcrp.org/
- **代码仓库**：https://github.com/daxiawj/cnc-wcrp
- **本地目录**：`D:/WorkSpace/2026/WCRP-Hugo-v2`

## 文档索引

| 文件 | 内容 |
|---|---|
| **[MANUAL.md](MANUAL.md)** | **操作手册**：目录说明、环境准备、发布流程、日常更新、常见问题 |
| [HISTORY.md](HISTORY.md) | 项目历史：迁移过程、关键决策、踩过的坑 |
| [DEPLOY.md](DEPLOY.md) | 部署细节：Netlify / GitHub Pages、DNS、证书、旧地址 301 |
| [deploy/](deploy/) | Apache / Nginx 配置留档 |

## 技术栈

| 项 | 说明 |
|---|---|
| 生成器 | Hugo 0.168（扩展版） |
| 主题 | `themes/wcrp`（自建，无第三方依赖） |
| 样式 | 原生 CSS，单一文件，品牌色 `#009b90` + `#ffca00` |
| 交互 | 原生 JS（轮播、吸顶导航、抽屉菜单、站内搜索），无 jQuery |
| 托管 | Netlify（Git 推送自动构建） |
| 域名 | `www.cnc-wcrp.org`，其余三个域名 301 过来 |

## 快速开始

```bash
# 本地预览
hugo server

# 构建
hugo --gc --minify --cleanDestinationDir

# 发布（Netlify 自动构建，约 1 分钟）
git add . && git commit -m "更新说明" && git push
```

需要 Hugo **0.146+ 扩展版**。安装与详细操作见 [MANUAL.md](MANUAL.md)。

## 内容规模

| 栏目 | 数量 | 位置 |
|---|---|---|
| 新闻资讯 | 17 篇 | `content/news/` |
| 通知公告 | 7 篇 | `content/notices/` |
| 栏目页 | 4 个 | `content/about/`、`content/committee/` |
| 联系我们 | 1 个 | `content/contact.md` |
| 首页轮播 | 4 条 | `data/banner.json` |

新闻和公告的历史内容存为 `.html`（保留原站富文本排版），新建内容用 `.md`，两者可以混排。

## URL 规则

原站是 `/news/87`、`/about/9` 这类 CMS 自增 ID，已全部改为语义化地址：

| 栏目 | 示例 |
|---|---|
| 新闻 | `/news/2026-03-top-10-china-climate-research-advances/` |
| 公告 | `/notices/2023-04-tipping-points-discussion-series/` |
| 关于我们 | `/about/introduction/`、`/about/history/` |
| 委员会 | `/committee/members/`、`/committee/advisors/` |

命名规则 `/{栏目}/{YYYY-MM}-{英文 slug}/`。中文标题在 `scripts/04_slugs.py` 的 `EN_SLUGS` 里手工指定英文 slug，不用拼音。

旧地址通过 `static/_redirects`（54 条 301 规则）跳到新地址，由 `scripts/05_redirects.py` 生成。

## 目录速查

```
content/          内容（新闻、公告、栏目页）
themes/wcrp/      主题（模板 layouts / 样式 assets / 正文配图 static/images）
data/             首页轮播数据
static/           CNAME、_redirects、.nojekyll
archetypes/       新建内容的模板
scripts/          迁移与检查脚本（日常不用跑）
deploy/           Apache / Nginx 配置留档
hugo.toml         站点配置（导航、联系方式、地图、版权）
netlify.toml      Netlify 构建配置
```

`public/`、`resources/`、`_tools/`、`_raw/`、`_shots/` 都是可再生成的，不进版本库。

## 迁移来源

原站 `www.cnc-wcrp.cn` 基于 Laravel + MySQL，已全量导出为静态内容。导出脚本在 `scripts/`，原站抓取存档在 `_raw/`（不进版本库）。完整过程见 [HISTORY.md](HISTORY.md)。
