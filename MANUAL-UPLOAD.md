# 手动上传（临时方案）

压缩包：**`github-source.zip`** —— 完整源码，102 个文件。

## 1. 建仓库

GitHub 新建 public 仓库，名字随意（如 `cnc-wcrp`）。

## 2. 上传（分两批）

网页一次最多 100 个文件，所以分两次：

- **第一批**：拖 `themes/` 进去 → Commit
- **第二批**：拖剩下的全部（`content/`、`hugo.toml`、`netlify.toml`、`static/`、`data/`、`scripts/`、`.github/` 等）→ Commit

## 3. 接 Netlify

Add new site → Import from GitHub → 选仓库 → **Deploy**（构建配置已在 `netlify.toml`，不用改）。

## 4. 绑域名

Domain management → Add a domain → `www.cnc-wcrp.org`，加两条解析：

| 主机记录 | 类型 | 值 |
| --- | --- | --- |
| `www` | CNAME | `<站点名>.netlify.app` |
| `@` | A | `75.2.60.5` |

证书自动签发后再打开 Force HTTPS。

## 5. 以后更新

修好 Git 认证（Personal access token，Contents: Read and write）后：

```bash
git remote set-url origin https://github.com/<用户名>/<仓库名>.git
git push -u origin main
```

之后 `git push` 就会自动触发 Netlify 构建。
