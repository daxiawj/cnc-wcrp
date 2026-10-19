# CNC-WCRP 静态站（Hugo · 2026 改版）

把原来基于 Laravel 的官网迁移成纯静态站点：内容全量导出、界面在保留原视觉识别的基础上重做、无需数据库与 PHP。

- 主域名：**https://www.cnc-wcrp.cn/**（`.org` 目前仍指向 NZC，待 DNS 可改后 301 过来）
- 生成器：Hugo 0.168（扩展版）
- 主题：`themes/wcrp`（自建，无第三方依赖）
- 内容：16 篇新闻 + 7 篇公告 + 4 个栏目页 + 联系我们 + 搜索页
- 前端：原生 JS，无 jQuery；响应式，移动端单列 + 抽屉菜单

## 目录结构

```
.
├── hugo.toml                 # 站点配置：域名、导航、分页、SEO、联系方式、百度地图
├── content/
│   ├── _index.md
│   ├── about/                # 9 → introduction.md，10 → history.md（Markdown）
│   ├── committee/            # 7 → members.md，6 → advisors.md（Markdown 表格）
│   ├── news/                 # *.html（历史正文，保留原始排版）
│   ├── notices/
│   ├── contact.md
│   └── search.html
├── data/banner.json          # 首页焦点图（4 条）
├── themes/wcrp/
│   ├── layouts/
│   │   ├── _default/_markup/render-image.html   # Markdown 图片渲染（本地图片自动解析）
│   │   ├── partials/hero.html                   # 首屏轮播
│   │   └── ...
│   └── static/{css,js,images}
├── scripts/                  # 迁移脚本（幂等，可重跑）
├── deploy/nginx.conf.example
└── public/                   # 构建产物，整体上传即可
```

## 本地预览 / 构建

```bash
# Windows（仓库自带 hugo.exe）
_tools/hugo/hugo.exe server        # http://localhost:1313
_tools/hugo/hugo.exe --gc --minify # 产物在 public/

# macOS / Linux
hugo server
hugo --gc --minify
```

## 内容维护

### 发一条新闻（支持本地图片）

```bash
hugo new content news/2026-11-annual-meeting/index.md --kind news
```

生成的是一个**页包（page bundle）**：

```
content/news/2026-11-annual-meeting/
├── index.md
└── photo.jpg        ← 图片直接放这里
```

正文里这样引用即可：

```markdown
![研讨会现场](photo.jpg)
[会议通知（PDF）](notice.pdf)
```

渲染时 `render-image.html` 会把本地图片解析成真实地址并补上宽高（避免布局跳动），
PDF 之类的附件放在同一目录、用普通链接引用即可。**网络图片照旧写完整 URL**。

> 历史上的 25 篇文章是 `.html` 内容文件（Word 富文本原样保留）。
> 新文章用 `.md` 完全没问题，两者可以共存于同一栏目。

### 改「关于我们 / 委员会名单」

这几个页面已经是干净的 Markdown：

- `content/about/introduction.md`（中委会简介）
- `content/about/history.md`（历史沿革，4 张扫描图）
- `content/committee/members.md` / `advisors.md`（姓名 / 单位两列表格，直接加行）

### 改联系方式

统一在 `hugo.toml` 的 `[params]` 里：`contact_phone`、`contact_email`、`contact_address`，
页脚和「联系我们」页会同步更新。

### 换首页焦点图

`data/banner.json`，每条含 `title / url / image / text`。图片放 `themes/wcrp/static/images/uploads/`。

## URL 规则

原站是 `/news/68`、`/about/9` 这种 CMS 自增 ID，本次全部改成语义化地址：

| 栏目 | 地址示例 |
| --- | --- |
| 新闻 | `/news/2023-04-ar6-synthesis-report-on-climate-change-from-the-ipcc/` |
| 通知公告 | `/notices/2023-04-tipping-points-discussion-series/` |
| 关于我们 | `/about/introduction/`、`/about/history/` |
| 委员会名单 | `/committee/members/`、`/committee/advisors/` |

命名规则：`/{栏目}/{YYYY-MM}-{英文标题短横线}/`。
中文标题的文章在 `scripts/04_slugs.py` 的 `EN_SLUGS` 里指定英文 slug（不用拼音）。
所有页面都能从顶部菜单、首页卡片、页脚进入，不依赖旧地址。

> **旧 ID 地址做 301**：`/news/87`、`/about/9` 这些在 `.cn` 上已有搜索收录和外部引用，
> 用 `static/_redirects`（Netlify 语法）逐个永久跳转到新地址，共 54 条。
> 由 `scripts/05_redirects.py` 生成，内容增删后重跑一次即可。

## 部署

- **Netlify / GitHub Pages**：见 [DEPLOY.md](DEPLOY.md)，仓库里已放好 `netlify.toml`、`.github/workflows/deploy.yml`、`static/CNAME`
- **自建服务器**：把 `public/` 传到站点根目录，Nginx 参考 `deploy/nginx.conf.example`：

- 裸域 301 到 `https://www.cnc-wcrp.cn`
- `try_files $uri $uri/` 负责补结尾斜杠（`/news/87` → `/news/87/`）

也可直接部署到 Cloudflare Pages / Netlify / Vercel（构建 `hugo --gc --minify`，输出 `public`）。

## 迁移脚本

| 脚本 | 作用 |
| --- | --- |
| `01_crawl.py` | 抓取原站页面与静态资源到 `_raw/` |
| `02_export.py` | 生成新闻/公告内容、下载并本地化图片、生成摘要与首页轮播 |
| `03_to_markdown.py` | 把栏目页 HTML 转成 Markdown（已执行，原文件已替换） |
| `04_slugs.py` | 生成语义化地址 + 旧地址 alias（已执行） |

> `02_export.py` 会覆盖 `content/news`、`content/notices`；`03/04` 对栏目页是幂等的。
> 一旦在站内手工改过内容，就不要再重跑 02。

## 与原站的差异

| 项 | 原站 | 本站 |
| --- | --- | --- |
| 技术栈 | Laravel + MySQL + PHP | 纯静态，零运行时 |
| 部署 | 国内服务器 + Laravel + MySQL | Netlify（Git 推送自动构建） |
| 文章地址 | 自增 ID | 日期 + 英文语义 slug（旧 ID 由 `_redirects` 301 过来） |
| 列表摘要 | 一律截断 150 字符，英文常断在半句 | 按中英文分别取整句（中文 ~130 字 / 英文 ~230 字符） |
| 首页 | 轮播 + 四宫格 | 轮播 + 最新动态 + 通知公告 |
| 移动端 | 固定 1200px | 响应式，抽屉菜单 |
| 交互 | jQuery + SuperSlide | 原生 JS（轮播、滚动吸顶、进场动画、回到顶部） |
| 检索 | 服务端 like | 前端检索 `/index.json`，兼容旧 `?title=` 参数 |

## 待确认

1. **ICP 备案号**：`.cn` 域名页脚必须展示备案号。拿到号码后填 `hugo.toml` 的 `[params] icp_number`，页脚自动出现一行。
2. **百度地图 ak**：沿用原站密钥，多数 ak 绑定域名白名单，需在百度地图开放平台确认 `www.cnc-wcrp.cn` 可用；不可用时页面会降级显示地址。
3. **`.org` 域名**：目前仍指向竺可桢-南森国际研究中心（NZC），DNS 在代理手上。等能改之后建议 301 到 `.cn`，把老外链权重带过来；切之前先跟 NZC 确认不冲突。
4. **图片版权**：正文配图来自原站与 wcrp-climate.org，已本地化，版权归原权利人。
5. 原 Laravel 后台不再需要；要可视化编辑可接 Decap CMS（基于 Git）或直接用编辑器改 Markdown。
