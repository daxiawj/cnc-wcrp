# 部署配置说明

记录当前的部署架构、DNS 配置与各环节的配置依据。日常操作步骤见 [MANUAL.md](MANUAL.md)。

---

## 架构

```
本地仓库  ──git push──▶  GitHub (daxiawj/cnc-wcrp)
                              │
                              │ 推送触发
                              ▼
                         Netlify 自动构建
                    (hugo --gc --minify → public/)
                              │
                              ▼
              www.cnc-wcrp.org  ──▶  全球 CDN
                    ▲
                    │ 301
        cnc-wcrp.org / www.cnc-wcrp.cn / cnc-wcrp.cn
```

院内服务器 `159.226.119.10` 已不再参与 CNC-WCRP 的访问链路，只服务竺南中心（`nzc.iap.ac.cn`）。

---

## DNS

| 主机记录 | 类型 | 值 | TTL |
|---|---|---|---|
| `www.cnc-wcrp.org` | CNAME | `cnc-wcrp.netlify.app` | 300 |
| `cnc-wcrp.org` | A | `75.2.60.5` | 300 |
| `www.cnc-wcrp.cn` | CNAME | `cnc-wcrp.netlify.app` | 300 |
| `cnc-wcrp.cn` | A | `75.2.60.5` | 300 |

`.org` 的 NS 由域名代理托管，`.cn` 在阿里云（`dns25/26.hichina.com`）。

> 裸域用 A 记录指向 Netlify 的负载均衡地址。如果 DNS 服务商支持 ALIAS/ANAME，指向 `apex-loadbalancer.netlify.com` 会更好（能跟随 Netlify 的 IP 变化）。

---

## Netlify 配置

`netlify.toml` 已声明全部构建参数，后台不需要手填：

```toml
[build]
  command = "hugo --gc --minify"
  publish = "public"

[build.environment]
  HUGO_VERSION = "0.168.0"
```

同时配置了响应头：

| 规则 | 缓存策略 | 原因 |
|---|---|---|
| `/*.html` | `max-age=0, must-revalidate` | 内容更新要立刻生效 |
| `/css/*`、`/js/*` | `max-age=31536000, immutable` | 文件名带内容哈希，可以永久缓存 |
| `/images/*` | `max-age=604800` | 正文配图文件名不带哈希，用 7 天 |
| `/index.json` | `max-age=0, must-revalidate` | 搜索索引必须最新 |

### 域名与证书

Netlify 后台 **Domain management** 里应该看到四个域名：

| 域名 | 角色 |
|---|---|
| `www.cnc-wcrp.org` | **Primary domain**（主域名） |
| `cnc-wcrp.org` | 301 → primary |
| `www.cnc-wcrp.cn` | 301 → primary |
| `cnc-wcrp.cn` | 301 → primary |

证书由 Netlify 自动向 Let's Encrypt 申请，90 天自动续期。如果显示签发失败，点 **Retry certificate provisioning** 即可——DNS 刚生效时第一次验证经常失败。

---

## 旧地址 301

`.cn` 老站是 Laravel，地址形如 `/news/87`、`/about/9`，在搜索引擎里已有收录。这些地址不能 404。

`static/_redirects` 由 `scripts/05_redirects.py` 生成，共 27 条映射 × 2（带/不带尾斜杠）= 54 条规则：

```
/news/87       /news/2023-04-ar6-synthesis-report-on-climate-change-from-the-ipcc/   301
/about/9       /about/introduction/                                                  301
/committee/7   /committee/members/                                                   301
```

内容增删后重新生成：

```bash
python scripts/05_redirects.py
```

> `_redirects` 是 Netlify 的语法，只在 Netlify 生效。GitHub Pages 不支持；迁到 Nginx 要改成 `rewrite` 规则（示例见 `deploy/nginx.conf.example`）。

---

## 院内 Apache（159.226.119.10）

这台机器现在只跑 NZC 站点。配置留档在 `deploy/apache/`：

| 文件 | 作用 | 状态 |
|---|---|---|
| `000-default.conf` | 发行版默认兜底站点 | 启用 |
| `001-nzc.conf` | NZC 站点，80 → 443 | 启用 |
| `001-nzc-le-ssl.conf` | NZC 站点 HTTPS | 启用 |
| `wcrp-org.conf` | 曾经的 `.org` → `.cn` 301 | **已弃用**，DNS 切走后 `a2dissite` |

### 两条必须遵守的规则

**1. VirtualHost 一律写 `*:80` / `*:443`，不要写域名**

```apache
<VirtualHost *:80>
```

写成 `<VirtualHost nzc.iap.ac.cn:80>` 时 Apache 会把它解析成 IP（`159.226.119.10:80`），单独形成一个 VirtualHost 组。而 Apache 匹配时**精确 IP 组优先于 `*:port` 组**，其他写 `*:80` 的站点会永远匹配不到——症状是 http 访问返回 404、证书续期验证返回 403。

**2. 有 301 跳转就必须放行 ACME 验证**

```apache
RewriteCond %{REQUEST_URI} !^/\.well-known/acme-challenge/
RewriteRule ^(.*)$ https://目标地址$1 [R=301,L]
```

否则 Let's Encrypt 的 HTTP-01 验证会被跳走，证书到期续不上。

### 改配置的流程

```bash
sudo apachectl configtest          # 必须 Syntax OK
sudo systemctl reload apache2      # 不要 restart，configtest 不过会停掉服务
```

回滚备份在 `/root/apache-backup-YYYYMMDD/`。

### 证书

```bash
sudo certbot certificates
```

`nzc.iap.ac.cn` 那张证书原本还覆盖 `www.cnc-wcrp.org`。`.org` 迁到 Netlify 后，续期时无法验证 `.org` 的 80 端口，需要把它从证书里摘掉：

```bash
sudo certbot certonly --apache -d nzc.iap.ac.cn --cert-name nzc.iap.ac.cn --force-renewal
sudo certbot renew --dry-run --cert-name nzc.iap.ac.cn
```

---

## 备用方案

### GitHub Pages

`.github/workflows/deploy.yml` 已就绪：checkout → 装 Hugo 0.168 → `actions/configure-pages` 自动注入 baseURL → 构建 → 发布。

启用方式：仓库 **Settings → Pages → Source** 选 **GitHub Actions**。

注意：内容里的 `url` 是绝对路径（`/news/...`），在项目子路径（`账号.github.io/仓库名/`）下内链会失效，必须绑定自定义域名。

### 自建 Nginx

`deploy/nginx.conf.example` 是完整示例，含：

- 主域名与裸域的 301
- 旧 ID 地址的 `rewrite` 规则（示例）
- 静态资源缓存策略（带哈希的资源长期缓存，配图 7 天）
- `try_files $uri $uri/` 自动补尾斜杠

---

## 账号与权限

| 项 | 说明 |
|---|---|
| GitHub 仓库 | `daxiawj/cnc-wcrp` |
| 推送方式 | HTTPS + Token，或 SSH（HTTPS 被代理挡住时用 SSH） |
| Netlify | 绑定同一 GitHub 账号，推送即触发构建 |
| 域名 | `.org` 在代理处托管，`.cn` 在阿里云 |
