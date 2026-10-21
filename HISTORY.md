# 项目历史

CNC-WCRP 官网从 Laravel 迁移到 Hugo 静态站的完整记录。按时间顺序排列，包含关键决策与踩过的坑，供以后维护参考。

---

## 缘起

原站 `www.cnc-wcrp.cn` 基于 Laravel + MySQL + PHP，跑在中国科学院大气物理研究所的服务器上。问题有三个：

1. **维护成本高**：PHP 版本、Laravel 依赖、数据库备份，每次升级都要动整套环境
2. **安全合规压力**：所内规定「未通过等保备案的网站不得部署在研究所服务器上」，而原站过不了等保
3. **访问受限**：`.org` 域名解析到所内 IP，中科院网络之外访问不了

目标：迁成纯静态站点，托管到境外（Netlify），恢复 `.org` 为主域名，彻底摆脱对院内服务器的依赖。

---

## 第一阶段：内容迁移（2026-10-19）

**导出原站**

用 Python + BeautifulSoup 抓取 `www.cnc-wcrp.cn` 全站：25 个内容页（16 篇新闻 + 7 篇公告 + 2 个栏目页）、6 个栏目页、4 张轮播图，资源全部本地化到 `_raw/` 存档。

**自建主题 `themes/wcrp`**

原站是 jQuery + SuperSlide 的老结构，套现成主题反而更难对齐，所以直接手写：

- 模板：`baseof.html`、`index.html`、`list.html`、`single.html`、`info.html`、`contact.html`、`search.html`、`404.html`
- 样式：单一 `style.css`，深青 `#009b90` + 亮黄 `#ffca00`
- 交互：原生 JS 重写轮播、移动菜单、站内搜索，去掉 jQuery 依赖

**内容形态**

新闻和公告存为 `.html` 内容文件（保留原站 Word 富文本的字号、缩进、名单对齐），front matter 里写死 `url`，保证 `/news/87/` 这类旧路径不变。

**遇到的坑**

| 问题 | 原因 | 解法 |
|---|---|---|
| 构建报「text/html 不在允许范围」 | Hugo 默认安全策略 | `hugo.toml` 加 `[security] allowContent` |
| about/committee 页被错误布局接管 | Hugo 0.146+ 起 `_default/page.html` 优先于 `single.html` | 这两个栏目改用自定义 `layout: info` |
| 原站 `notices/84` 图片 404 | 图片域名误写成 `.org` | 抓取时按路径回退到 `.cn` |
| `about/10` 页面 646KB | 原站内嵌 base64 图片 | 抽成独立文件 |

**图片优化**：超过 1600px 的缩到 1600 宽，图片总量 16.7MB → 9.4MB。

---

## 第二阶段：改版（2026-10-19）

第一版复刻完成后，在**独立目录** `WCRP-Hugo-v2` 里做现代化改版，v1 冻结另存（`WCRP-Hugo-v1-backup-20261019.zip`）。

保留的东西：品牌色、logo 在左站名在右、导航在下、黄线分隔。

改掉的东西：

- **头部**：加柔光渐变、搜索框改半透明胶囊、滚动后出现白色毛玻璃吸顶导航
- **首屏**：大圆角卡片，左侧文字区渐变，右下角胶囊指示器
- **列表**：四宫格改卡片，加分类 chip、日期、三行摘要、悬浮上浮
- **文章页**：加面包屑、窄栏阅读（16.5px/1.95）、上一篇/下一篇、回到顶部
- **动画**：轻微上浮进场，`prefers-reduced-motion` 下自动关闭

**摘要算法重写**

原站一律截 150 字符，英文必然断在词中间。改为按句切分，中文约 130 字、英文约 230 字符，保证停在句号上；`Published: 23 March 2023` 这类前缀自动剥离。

**内容 Markdown 化**

`scripts/03_to_markdown.py` 把「中委会简介」「历史沿革」「委员会名单」「顾问委员会名单」转成 Markdown。名单转成「姓名 / 单位」两列表格，79 + 21 行逐行校验，没有一行错位。

**地址语义化**

原站 `/news/87`、`/about/9` 这类 CMS 自增 ID 没有实际含义。改成 `/{栏目}/{YYYY-MM}-{英文 slug}/`：

| 旧 | 新 |
|---|---|
| `/news/87` | `/news/2023-04-ar6-synthesis-report-on-climate-change-from-the-ipcc/` |
| `/about/9` | `/about/introduction/` |
| `/committee/7` | `/committee/members/` |

**中文标题不转拼音**（专业站用拼音显得不专业），在 `scripts/04_slugs.py` 的 `EN_SLUGS` 里手工指定英文 slug。

**本地图片方案**

采用页包（page bundle）：`content/news/xxx/index.md` 与图片放在同一目录，正文里 `![说明](photo.jpg)`。新增 `layouts/_default/_markup/render-image.html` 自动解析资源、补宽高、加懒加载。

**这一阶段踩的坑**

| 问题 | 原因 | 解法 |
|---|---|---|
| 图标显示成白方块 | 原站 PNG 图标自带白底，`filter: invert()` 反而变白块 | 改成内联 SVG / CSS 折角 |
| 下拉菜单不弹出 | `.site-header` 加了 `overflow: hidden` 裁剪背景光效，把绝对定位的下拉面板一起裁掉 | 移除 `overflow`，下拉面板改 `top: calc(100% + 8px)`，加透明「桥」防悬停断档 |
| logo 背后有深色方块 | `logo.png` 不透明，底色烘焙成原站青色 | 用反预乘算法把底色抠成 alpha |
| 改完看不到变化 | 浏览器缓存了同 URL 的 CSS/logo | 改用 Hugo Pipes 内容哈希：`style.min.<hash>.css` |
| 菜单项占满整行显得散 | 用了 `space-between` 两端对齐 | 改回 `justify-content: center` |

---

## 第三阶段：上线（2026-10-19 ~ 10-20）

**部署链路**

GitHub 源码 → Netlify 自动构建（`netlify.toml` 里写死 `hugo --gc --minify`、Hugo 0.168.0、publish=public）。

首次部署是网页手动上传的源码（Git 认证问题，分两批上传，网页单次上限 100 文件），认证修好后改为 `git push`。

**域名迁移：.cn → .org → .cn → .org**

这个过程反复了一次，值得记下来：

1. 最早计划用 `.org`（原始主域名）
2. 因 `.org` 的 DNS 在代理手上改不了，先改用 `.cn`（在自己手上）
3. 站点先跑在 `.cn` 上，`.org` 由院内 Apache 做 301 到 `.cn`
4. 后来确认「`.org` 解析到院内 IP，中科院网络外根本访问不了」，`.org → .cn` 的 301 只在院内有效
5. 代理终于改好 `.org` 的 DNS，主域名切回 `.org`，`.cn` 反过来 301 到 `.org`

**现在的状态**：`www.cnc-wcrp.org` 是主域名，`.cn` 和裸域全部 301 过去。

**旧地址 301**

`.cn` 有历史收录和外链，`/news/87` 这类地址不能 404。用 `scripts/05_redirects.py` 生成 `static/_redirects`（Netlify 语法），27 条映射 × 2（带/不带尾斜杠）= 54 条规则，全部 301 到新地址。

**院内 Apache 的规范化**

`.org` 迁走后，院内那台 Apache（159.226.119.10）只剩 NZC 站点。顺手把配置规范化：

- 配置只放 `sites-available/`，`sites-enabled/` 只留 `a2ensite` 软链
- VirtualHost 一律 `*:80` / `*:443`，用 ServerName 区分

**这里有个很隐蔽的坑**：原来 `001-nzc.conf` 写的是 `<VirtualHost nzc.iap.ac.cn:80>`，Apache 把它解析成 `159.226.119.10:80`，单独组成一个 VirtualHost 组。而 Apache 匹配时**精确 IP 组优先于 `*:port` 组**，导致另一个写 `*:80` 的站点永远匹配不到——表现为 http 访问返回 404、ACME 验证返回 403。

**证书**

统一在 Apache 上时，`www.cnc-wcrp.org` 和 `nzc.iap.ac.cn` 两张证书都覆盖 `.org`，续期要验证 80 端口。跳转配置里必须放行：

```apache
RewriteCond %{REQUEST_URI} !^/\.well-known/acme-challenge/
```

否则证书到期续不上，且会连累 NZC 那张。

---

## 第四阶段：日常维护（2026-10-20 至今）

**新增首篇 Markdown 新闻**

「2025 年度中国气候研究十大进展在南京发布」，来源现代快报/现代+。原页面是 Vue SPA，正文靠 JS 渲染，用 CDP 拦截 `getArticleContent` 接口拿到内容与图片。

顺手修了两个模板问题：

- 列表页封面链接原本写 `href="{{ $.RelPermalink }}"`，在 `range` 循环里 `$` 指向栏目页，导致所有封面缩略图都跳到 `/news/` 列表页
- `cover` 字段现在支持页包内的文件名

**菜单点击修复**

`hugo.toml` 里两个父菜单写成 `url = "#"`，点击会：地址变成 `.../members/#`、空锚点触发滚动到页面顶部、链接获得焦点后 `:focus-within` 让下拉面板保持展开。

改成真实地址：关于我们 → `/about/introduction/`，委员会名单 → `/committee/members/`。

**联系地址更新**

改为「北京市朝阳区北辰西路81号中国科学院大气物理研究所」。经百度地图 POI 核对，新旧地址是同一个园区，坐标只差 60 米。

---

## 关键决策记录

| 决策 | 选择 | 原因 |
|---|---|---|
| 生成器 | Hugo | 单二进制、构建快、无需 Node/PHP 运行时 |
| 主题 | 自建 `themes/wcrp` | 原站结构与现成主题差异大，改主题不如直接写 |
| 内容格式 | 新闻/公告用 `.html`，栏目页用 `.md` | 前者保留原站富文本排版，后者便于日常编辑 |
| 地址规则 | `/{栏目}/{YYYY-MM}-{英文 slug}/` | 语义化、对搜索引擎友好；中文标题手工配英文 slug |
| 旧地址 | 全部 301（`_redirects`） | `.cn` 有历史收录，直接 404 会丢权重 |
| 托管 | Netlify | 免费额度够用、Git 推送自动构建、自动 HTTPS |
| 主域名 | `www.cnc-wcrp.org` | 原始域名；`.cn` 域名受备案约束，不适合长期做主站 |
| 服务器上的 `.org` | 最终撤掉 301 | `.org` 已直接解析到 Netlify，Apache 只需要服务 NZC |

---

## 当前规模

| 项 | 数量 |
|---|---|
| 新闻 | 17 篇（16 篇历史 + 1 篇新增） |
| 通知公告 | 7 篇 |
| 栏目页 | 4 个（中委会简介、历史沿革、委员会委员、顾问委员会委员） |
| 其他页面 | 联系我们、站内搜索、404 |
| 轮播图 | 4 张 |
| 构建产物 | 约 83 个文件，12MB |
| 源码（不含配图） | 约 200KB |

---

## 里程碑

| 日期 | 事件 |
|---|---|
| 2026-10-19 | 完成全站抓取与内容导出；自建主题复刻上线；v2 改版完成 |
| 2026-10-19 | 部署到 Netlify，`.cn` 域名切换成功 |
| 2026-10-20 | 新增首篇 Markdown 新闻；菜单与地址修复；主域名切回 `.org` |
| 2026-10-21 | 整理最终版，补齐操作手册与历史记录 |
