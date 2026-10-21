# 操作手册

CNC-WCRP 官网（Hugo 静态站）的日常维护、发布与迁移指南。

**当前线上**：https://www.cnc-wcrp.org/
**代码仓库**：https://github.com/daxiawj/cnc-wcrp
**本地工作目录**：`D:/WorkSpace/2026/WCRP-Hugo-v2`

---

## 一、目录结构：哪些必需，哪些可以删

### 构建网站必需的（移植时只带这些就够）

| 路径 | 作用 | 能不能删 |
|---|---|---|
| `content/` | 所有文章和页面 | 不能 |
| `themes/wcrp/` | 主题：模板、样式、脚本、正文配图 | 不能 |
| `data/banner.json` | 首页轮播的 4 条数据 | 不能 |
| `static/CNAME` | 站点域名标识 | 不能 |
| `static/_redirects` | 旧地址 301 规则（54 条） | 不能 |
| `static/.nojekyll` | 告诉 GitHub Pages 不要用 Jekyll | 不能 |
| `archetypes/` | `hugo new` 的模板 | 建议保留 |
| `hugo.toml` | 站点配置（导航、联系方式、地图、版权） | 不能 |
| `netlify.toml` | Netlify 构建配置 | 用 Netlify 就必需 |

### 参考用，可留可删

| 路径 | 作用 |
|---|---|
| `scripts/` | 迁移与检查脚本（有历史价值，日常不用跑） |
| `deploy/` | Apache / Nginx 配置留档 |
| `.github/workflows/deploy.yml` | GitHub Pages 备用方案 |
| `README.md`、`DEPLOY.md`、`HISTORY.md`、本文件 | 文档 |

### 构建产物和临时文件，不要带走

| 路径 | 说明 |
|---|---|
| `public/` | 每次 `hugo` 都会重新生成，12MB |
| `resources/` | Hugo 构建缓存 |
| `_raw/` | 原站抓取存档，9.7MB，只用于迁移留痕 |
| `_shots/` | 开发过程中的截图，33MB |
| `_tools/` | 本地 `hugo.exe`，63MB，新电脑重新装即可 |
| `.workbuddy/` | AI 协作记录 |
| `.hugo_build.lock` | Hugo 运行时的锁文件 |
| `*.zip` | 历史打包文件 |

---

## 二、环境准备

### 安装 Hugo（扩展版）

需要 **Hugo 0.146 或更高**（0.168 验证过），必须是 **extended** 版本。

**Windows**

```powershell
winget install Hugo.Hugo.Extended
# 或者 scoop install hugo-extended
```

**macOS**

```bash
brew install hugo
```

**Linux**

```bash
sudo apt install hugo       # 注意：发行版仓库的版本可能太旧
# 推荐直接下载：https://github.com/gohugoio/hugo/releases
```

验证：

```bash
hugo version
# 应输出 hugo v0.1xx.x+extended ...
```

### 可选工具

- **Git**：推送代码用
- **Python 3**：只有重跑 `scripts/` 里的迁移脚本时才需要

---

## 三、本地预览

```bash
cd D:/WorkSpace/2026/WCRP-Hugo-v2
hugo server
```

浏览器打开 `http://localhost:1313/`。改文件会自动刷新，`Ctrl+C` 停止。

> 如果本地有 `_tools/hugo/hugo.exe`，也可以用 `./_tools/hugo/hugo.exe server`，效果一样。

**只构建不预览**：

```bash
hugo --gc --minify --cleanDestinationDir
```

产物在 `public/`。

---

## 四、日常内容更新

### 4.1 发一篇新闻

```bash
hugo new content news/2026-11-annual-meeting/index.md --kind news
```

会创建 `content/news/2026-11-annual-meeting/index.md`。图片直接丢进同一个文件夹，正文里这样引用：

```markdown
![会议现场](photo.jpg)
```

**关于地址**：新文章的 URL 默认按文件名生成（`/news/2026-11-annual-meeting/`）。如果想自定义，在 front matter 加一行：

```yaml
url: "/news/2026-11-china-climate-forum/"
```

**关于封面**：列表页缩略图用 `cover` 字段，写页包内的文件名即可：

```yaml
cover: "cover.jpg"
```

**图片建议**：宽度控制在 1600px 以内、单张不超过 400KB，否则页面加载会慢。

### 4.2 发一条通知公告

```bash
hugo new content notices/2026-11-meeting-notice/index.md --kind notices
```

其余同上。

### 4.3 修改栏目页（关于我们、委员会名单）

直接编辑 Markdown：

| 页面 | 文件 |
|---|---|
| 中委会简介 | `content/about/9.md` |
| 历史沿革 | `content/about/10.md` |
| 委员会委员名单 | `content/committee/7.md` |
| 顾问委员会名单 | `content/committee/6.md` |
| 联系我们 | `content/contact.md` |

委员会名单是 Markdown 表格，加人直接加一行：

```markdown
| 姓名 | 单位 |
| --- | --- |
| 曹龙 | 浙江大学 |
| 新委员 | 某某大学 |
```

### 4.4 改联系方式、轮播图、版权

全部在 `hugo.toml` 的 `[params]` 里，改一处全站生效：

```toml
[params]
  copyright      = "Copyright © 1996 - 2026 All Rights Reserved ..."
  contact_phone  = "010-82994983"
  contact_email  = "cnc_wcrp@mail.iap.ac.cn"
  contact_address = "北京市朝阳区北辰西路81号中国科学院大气物理研究所"
  baidu_map_ak   = "..."
  baidu_map_lng  = "116.393487"
  baidu_map_lat  = "39.984405"
```

**首页轮播**在 `data/banner.json`，4 条数据，每条包含标题、摘要、图片、跳转地址：

```json
{
  "title": "...",
  "text": "...",
  "image": "/images/uploads/xxx.jpg",
  "url": "/news/2023-04-.../",
  "fit": "cover"
}
```

`fit` 可选：`contain`（默认，完整显示不裁切，适合图上有字的）或 `cover`（铺满，适合纯照片）。

### 4.5 改导航菜单

在 `hugo.toml` 的 `[[menu.main]]` 段落。二级菜单靠 `parent` 关联：

```toml
[[menu.main]]
  name = "关于我们"
  url = "/about/introduction/"    # 点父项会去这里
  weight = 2
  identifier = "about"

[[menu.main]]
  name = "中委会简介"
  url = "/about/introduction/"
  weight = 1
  parent = "about"
```

> **注意**：父菜单的 `url` 一定要写真实地址，不要写 `#`。写 `#` 会导致点击后页面滚回顶部、下拉菜单卡住不收起。

### 4.6 改样式

| 要改什么 | 文件 |
|---|---|
| 颜色、字号、间距 | `themes/wcrp/assets/css/style.css` |
| 页面结构 | `themes/wcrp/layouts/` |
| 交互（轮播、菜单、搜索） | `themes/wcrp/assets/js/main.js` |

样式和脚本经过 Hugo Pipes 处理，文件名带内容哈希（`style.min.<hash>.css`），改完自动换地址，不会出现浏览器缓存旧样式的问题。

---

## 五、发布上线

### 正常流程

```bash
cd D:/WorkSpace/2026/WCRP-Hugo-v2

# 1. 本地先看一眼（可选但强烈建议）
hugo server

# 2. 提交
git add .
git commit -m "新增：11 月学术研讨会通知"

# 3. 推送
git push
```

Netlify 收到推送后 1 分钟左右自动构建并发布。构建状态在 Netlify 后台 **Deploys** 页面看，绿勾表示成功。

### 如果 `git push` 报 502

公司/园区网络的代理有时会挡住 GitHub 的 HTTPS。改用 SSH：

```bash
git push git@github.com:daxiawj/cnc-wcrp.git main
```

### 回滚到上一个版本

Netlify 后台 → **Deploys** → 找到上一个正常版本 → **Publish deploy**，秒级生效。

### 构建失败怎么办

Netlify 不会主动通知，站点只是不更新。去 **Deploys** 点那次失败的构建看日志。最常见原因：

- Markdown 表格列数不对
- front matter 的 YAML 缩进错误
- 图片路径写错（不影响构建，但页面上会 404）

本地先 `hugo --gc --minify` 跑一遍，能提前发现大部分问题。

---

## 六、域名、证书与服务器

### 当前域名关系

| 域名 | 指向 | 行为 |
|---|---|---|
| `www.cnc-wcrp.org` | Netlify | 主站，200 |
| `cnc-wcrp.org` | Netlify | 301 → `www.cnc-wcrp.org` |
| `www.cnc-wcrp.cn` | Netlify | 301 → `www.cnc-wcrp.org` |
| `cnc-wcrp.cn` | Netlify | 301 → `www.cnc-wcrp.org` |

DN​S 记录：

| 主机记录 | 类型 | 值 |
|---|---|---|
| `www` | CNAME | `cnc-wcrp.netlify.app` |
| `@` | A | `75.2.60.5` |

### 证书

Netlify 自动为 `www.cnc-wcrp.org` 和 `cnc-wcrp.org` 签发 Let's Encrypt 证书，90 天自动续期，不需要人工干预。

如果浏览器提示「不是私密连接」，去 Netlify 后台 **Domain management → HTTPS**：

- 显示 **Verify DNS configuration** → 点它
- 显示 **Certificate provisioning in progress** → 等 5–15 分钟
- 显示失败 → 点 **Retry certificate provisioning**

### 院内的 Apache 服务器（159.226.119.10）

这台机器现在**只服务 NZC 站点**（`nzc.iap.ac.cn`），CNC-WCRP 的 `.org` 已经直接解析到 Netlify，不再经过它。

配置留档在 `deploy/apache/`，包含：

- `001-nzc.conf` / `001-nzc-le-ssl.conf`：NZC 站点
- `wcrp-org.conf`：**已弃用**（原 `.org` → `.cn` 的 301），DNS 切走后已 `a2dissite`

**规范要点**（改这台机器时务必遵守）：

1. 配置只放 `sites-available/`，`sites-enabled/` 只留 `a2ensite` 生成的软链
2. VirtualHost 一律写 `<VirtualHost *:80>` / `<VirtualHost *:443>`，用 `ServerName` 区分。**不要写 `<VirtualHost 域名:80>`** —— Apache 会把它解析成 IP 单独成组，精确 IP 组优先于通配符组，其他站点会永远匹配不到
3. 有任何 301 跳转，都要放行证书续期路径：

   ```apache
   RewriteCond %{REQUEST_URI} !^/\.well-known/acme-challenge/
   ```

改完务必：

```bash
sudo apachectl configtest      # 必须 Syntax OK
sudo systemctl reload apache2  # 不用 restart，失败会停服务
```

---

## 七、移植到新电脑

### 方式一：从 GitHub 克隆（推荐）

```bash
git clone git@github.com:daxiawj/cnc-wcrp.git cnc-wcrp
cd cnc-wcrp
hugo server
```

仓库里已经是完整源码（含所有配图），克隆下来直接能构建。

### 方式二：拷贝文件夹

从旧电脑的 `D:/WorkSpace/2026/WCRP-Hugo-v2` 复制以下内容（其余都不用带）：

```
content/
themes/
data/
static/
archetypes/
scripts/        （可选）
deploy/         （可选）
hugo.toml
netlify.toml
README.md
HISTORY.md
MANUAL.md
DEPLOY.md
```

**不要复制**：`public/`、`resources/`、`_tools/`、`_raw/`、`_shots/`、`.workbuddy/`、`*.zip`。

到新电脑后装好 Hugo，`cd` 进去执行 `hugo server` 即可。

### 换电脑后要改的地方

如果新电脑的目录路径变了，`git` 不需要改（它是相对仓库的）。只有一处需要注意：

`netlify.toml`、`.github/workflows/deploy.yml` 里都是相对路径，不用改。

---

## 八、常见问题

### 页面 404

- 新文章还没构建：本地 `hugo server` 看一眼，确认文件在 `content/news/` 下
- URL 写错：检查 front matter 里的 `url` 字段，注意**首尾都要有斜杠**

### 图片不显示

- 页面包内的图片名要和正文里的引用完全一致（区分大小写）
- 用 HTML `<figure>` 写图片时，`src` 要写**绝对路径**（`/news/xxx/photo.jpg`），写相对路径在无尾斜杠访问时会失图
- 用 Markdown `![](...)` 写图片时，框架会自动处理，不用管

### 改了样式但页面没变

正常情况下不会发生（文件名带哈希）。如果真遇到：

- 确认 `hugo server` 已重启（新增 `assets/` 目录后必须重启才能识别）
- 浏览器 `Ctrl + F5` 强制刷新

### 构建成功但线上没更新

- 确认推送成功：`git log --oneline -1 origin/main`
- Netlify 可能还在构建，等 1–2 分钟
- 看 Netlify 的 Deploys 页面有没有红色失败标记

### 站内搜索搜不到新文章

搜索索引在构建时生成（`/index.json`），新文章构建后自动收录。如果搜不到，检查文章的 `draft` 是否为 `true`（草稿不会构建）。

---

## 九、需要长期留意的三件事

| 事项 | 说明 |
|---|---|
| **域名续费** | `cnc-wcrp.org` 和 `cnc-wcrp.cn` 都要按时续费，`.org` 过期后没有宽限期保护 |
| **Netlify 免费额度** | 每月 100GB 流量、300 构建分钟，正常使用绰绰有余；超了会在后台提示 |
| **百度地图 ak** | `hugo.toml` 里的 `baidu_map_ak` 是原站的，若哪天「联系我们」地图空白，去[百度地图开放平台](https://lbsyun.baidu.com/)确认 ak 是否仍有效、`www.cnc-wcrp.org` 是否在白名单 |
