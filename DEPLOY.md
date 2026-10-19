# 部署到 Netlify / GitHub Pages

仓库里已经把两个平台的配置都放好了，**不需要在网页后台手填构建命令**：

| 文件 | 作用 |
| --- | --- |
| `netlify.toml` | Netlify 构建命令（`hugo --gc --minify`）、Hugo 版本、缓存与安全响应头 |
| `.github/workflows/deploy.yml` | GitHub Actions：装 Hugo → 构建 → 发布到 Pages |
| `static/CNAME` | 构建后自动带上 `www.cnc-wcrp.org`，GitHub Pages 认它 |

两个平台都要求代码先在一个 Git 仓库里（GitHub / GitLab / Gitee 都行，下面以 GitHub 为例）。

---

## 0. 先把代码推到 GitHub

```bash
cd D:/WorkSpace/2026/WCRP-Hugo-v2

git init
git add .
git commit -m "CNC-WCRP 静态站"

# 在 GitHub 上新建一个空仓库（不要勾选 README/.gitignore），然后：
git remote add origin git@github.com:<你的账号>/cnc-wcrp.git
git branch -M main
git push -u origin main
```

> `.gitignore` 已经排除了 `public/`、`resources/`、`_tools/`（本地 hugo.exe）、`_raw/`（原站抓取存档）、`_shots/`。
> 仓库实际大小约 10MB，主要是正文配图。

---

## 方案一：Netlify（推荐，最省事）

### 1. 建站

1. 登录 [netlify.com](https://app.netlify.com) → **Add new site → Import an existing project**
2. 选 GitHub，授权后选中刚推的仓库
3. 构建设置**不用改**（`netlify.toml` 已声明）：
   - Build command：`hugo --gc --minify`
   - Publish directory：`public`
4. 点 **Deploy site**，一两分钟出结果，先给一个 `xxx-yyy.netlify.app` 的临时域名

### 2. 绑自定义域名

**Domain management → Add a domain** → 填 `www.cnc-wcrp.org`。

然后去域名商（阿里云/腾讯云/Cloudflare 都行）加解析：

| 主机记录 | 类型 | 值 | 说明 |
| --- | --- | --- | --- |
| `www` | CNAME | `<你的站点名>.netlify.app` | 主站入口 |
| `@`（裸域） | A | `75.2.60.5` | Netlify 负载均衡地址，让 `cnc-wcrp.org` 也能开 |

> 如果域名的 NS 直接托管给 Netlify（Netlify DNS），它会自动配好，不用手动加上面两条。

### 3. HTTPS

Netlify 会自动签发 Let's Encrypt 证书（几分钟内）。证书生效后在 **Domain management → HTTPS** 里打开 **Force HTTPS**。

### 4. 完成后的检查

```bash
curl -I https://www.cnc-wcrp.org/            # 200，且 server: Netlify
curl -I https://cnc-wcrp.org/                # 301 到 www
curl -s https://www.cnc-wcrp.org/index.json | head -c 120   # 搜索索引
```

---

## 方案二：GitHub Pages

### 1. 开启 Pages

仓库 → **Settings → Pages → Build and deployment**
- Source 选 **GitHub Actions**（不要选 Deploy from a branch）

推一次代码（或手动跑一次 workflow）就会开始构建：

`.github/workflows/deploy.yml` 会依次执行：装 Hugo 0.168 扩展版 → `hugo --gc --minify` → 上传 `public/` → 发布。

### 2. 先验证临时地址

第一次部署完成会给出 `https://<账号>.github.io/<仓库名>/`。
这一步的 `baseURL` 由 `actions/configure-pages` 自动注入，**不用改 hugo.toml**，临时地址里 CSS 和图片也能正常加载。

### 3. 绑自定义域名

**Settings → Pages → Custom domain** 填 `www.cnc-wcrp.org` → Save。
（仓库里已有 `static/CNAME`，构建产物自带这个文件，填完等 DNS 检查通过即可。）

DNS 解析：

| 主机记录 | 类型 | 值 |
| --- | --- | --- |
| `www` | CNAME | `<账号>.github.io` |
| `@`（裸域） | A | `185.199.108.153` |
| `@` | A | `185.199.109.153` |
| `@` | A | `185.199.110.153` |
| `@` | A | `185.199.111.153` |

解析生效后回到 Pages 设置，勾上 **Enforce HTTPS**（证书签发可能要等十几分钟到一小时）。

> **用 Cloudflare 托管 DNS 的话**：`www` 那条先设成 **DNS only（灰云）**，等 GitHub 签好证书再决定要不要开代理，否则容易出现「重定向次数过多 / 证书不匹配」。

---

## 两个平台怎么选

| | Netlify | GitHub Pages |
| --- | --- | --- |
| 上手 | 连仓库即可，配置已写好 | 需要开 Actions，多一步 |
| 构建速度 | 约 1 分钟 | 约 1–2 分钟（含装 Hugo） |
| 自定义域名 / HTTPS | 自动，几分钟 | 自动，证书可能慢一些 |
| 缓存与响应头 | 可在 `netlify.toml` 精细控制 | 只能用平台默认 |
| 回滚 | 后台点一下历史部署 | 重跑旧 commit 的 workflow |
| 流量限制 | 100GB/月（免费额度） | 软限制 100GB/月、仓库 1GB |
| 国内访问 | 一般 | 一般（两者都建议套 CDN） |

**建议**：先用 Netlify 上线（最快），GitHub 仓库照常维护；以后想换平台，`public/` 是纯静态文件，搬到任何地方都能跑。

---

## 上线检查清单

- [ ] 首页、六个菜单项、随便点开一篇文章
- [ ] 站内搜索（`/search/?q=WCRP`）
- [ ] 手机打开，抽屉菜单能展开二级项
- [ ] `https://www.cnc-wcrp.org/sitemap.xml`、`/robots.txt`、`/index.json` 均可访问
- [ ] 随便访问一个不存在的地址，出现 404 页
- [ ] 百度地图：**联系我们的地图是否正常显示**（见下）

### 百度地图 ak 必看

`hugo.toml` 里的 `baidu_map_ak` 沿用原站密钥 `Pl2onSZWMags4yK4leGulSX5GXhktcjV`，这类 ak 通常**绑定了域名白名单**。
上线后如果「联系我们」的地图空白、页面显示「地图暂时无法显示」，去[百度地图开放平台](https://lbsyun.baidu.com/)控制台，把这个 ak 的白名单改成 `www.cnc-wcrp.org`（或新建一个浏览器端 ak 填进去）。

---

## 回滚

- **Netlify**：Deploys → 找到上一个正常版本 → **Publish deploy**（秒级回滚）
- **GitHub Pages**：Actions → 选历史运行 → **Re-run all jobs**；或者本地 `git revert` 后重新 push

---

## 原来的 `.cn` 域名怎么办

`.cn` 是当初为了备案临时用的，现在主域名回到 `.org`，建议这样处理：

1. **保留并 301 到 .org**（推荐）——已经发出去的旧链接、搜索引擎收录都还能用
2. 做法三选一：
   - 在域名商后台用「URL 转发」把 `www.cnc-wcrp.cn` 转到 `https://www.cnc-wcrp.org`
   - 或另建一个 Netlify 站点，只放一个 `_redirects` 文件：`/* https://www.cnc-wcrp.org/:splat 301!`
   - 或在自建 Nginx 上按 `deploy/nginx.conf.example` 的写法做 301
3. 如果决定彻底停用，记得先在百度/Google 站长平台提交域名变更，否则原来的收录会掉。
