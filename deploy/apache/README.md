# Apache 配置留档（159.226.119.10）

这台机器同时承载两个站点，出问题或重装时按本目录恢复。

| 文件 | 作用 | 对应域名 |
|---|---|---|
| `000-default.conf` | 发行版默认兜底站点，不用改 | — |
| `001-nzc.conf` | NZC 站点，80 → 443 跳转 | `nzc.iap.ac.cn` |
| `001-nzc-le-ssl.conf` | NZC 站点 HTTPS | `nzc.iap.ac.cn`（证书含 `www.cnc-wcrp.org`） |
| `wcrp-org.conf` | 老域名 301 到新站 | `www.cnc-wcrp.org` → `www.cnc-wcrp.cn` |

## 部署

```bash
sudo cp 000-default.conf 001-nzc.conf 001-nzc-le-ssl.conf wcrp-org.conf /etc/apache2/sites-available/
sudo a2ensite 000-default 001-nzc 001-nzc-le-ssl wcrp-org
sudo apachectl configtest          # 必须 Syntax OK
sudo systemctl reload apache2
```

## 规范要点

1. **配置只放 `sites-available/`**，`sites-enabled/` 里只留 `a2ensite` 生成的软链。
   直接往 `enabled` 放实体文件会导致 `a2dissite` 失效、备份遗漏。
2. **VirtualHost 一律写 `*:80` / `*:443`**，靠 `ServerName` 区分。
   写成 `<VirtualHost nzc.iap.ac.cn:80>` 会被 Apache 解析成 `159.226.119.10:80`，
   单独形成一个组；由于精确 IP 组优先于 `*:port` 组，其他写 `*:80` 的站点永远匹配不到
   （典型症状：http 访问返回 404、ACME 验证返回 403）。
3. **跳转必须放行 ACME 路径**：

   ```apache
   RewriteCond %{REQUEST_URI} !^/\.well-known/acme-challenge/
   ```

   否则证书到期续不上。本机三张证书中有两张覆盖 `www.cnc-wcrp.org`
   （`nzc.iap.ac.cn` 和 `www.cnc-wcrp.org`），都会受影响。

## 证书

```bash
sudo certbot certificates
```

| 证书名 | 覆盖域名 | 用途 |
|---|---|---|
| `nzc.iap.ac.cn` | nzc.iap.ac.cn + www.cnc-wcrp.org | NZC 站 443 |
| `www.cnc-wcrp.org` | www.cnc-wcrp.org | 老域名 443（只需能完成 301） |
| `www.cnc-wcrp.cn-0001` | www.cnc-wcrp.cn | **已无用**，.cn 由 Netlify 签证书，可删除 |

续期演练（改完配置后必须跑一次）：

```bash
sudo certbot renew --dry-run --cert-name www.cnc-wcrp.org
sudo certbot renew --dry-run --cert-name nzc.iap.ac.cn
```

## 清理项

```bash
# 损坏的续期配置，每次 certbot renew 都会报错
sudo rm /etc/letsencrypt/renewal/www.cnc-wcrp.cn.conf

# .cn 已托管 Netlify，本机证书续期必然失败，建议删除
sudo certbot delete --cert-name www.cnc-wcrp.cn-0001
```
