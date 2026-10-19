# 不装 Git，直接用网页上传（临时方案）

> 网页版上传的是**构建好的网页**（`public/` 里的内容），不是源码。
> 好处是不用装 Hugo、不用配密钥；代价是以后每改一次内容都要重传一次。
> 等 Git 认证修好了，建议切回 `git push`（文末有一步到位的办法）。

压缩包：**`github-upload.zip`**（75 个文件，9.4MB，已含 `.nojekyll`，暂未含 `CNAME`）

---

## 第 1 步：建仓库（名字很关键）

新建一个 **public** 仓库，名字必须写成：

```
<你的GitHub用户名>.github.io
```

比如用户名是 `zhangsan`，仓库就叫 `zhangsan.github.io`。

**为什么必须这样**：站内链接是绝对路径（`/news/2026-.../`、`/css/style...css`）。
只有用「用户名.github.io」这种仓库，站点才挂在根路径 `https://zhangsan.github.io/`，链接才对得上。
如果建成 `cnc-wcrp` 这种普通仓库，地址会变成 `https://zhangsan.github.io/cnc-wcrp/`，
在你绑好自定义域名之前，页面会**没有样式、文章点进去 404**——不是坏了，是路径对不上。

---

## 第 2 步：上传文件

1. 解压 `github-upload.zip`
2. 打开仓库首页 → **Add file → Upload files**
3. 把解压出来的**里面的内容**全选拖进去（不是拖那个文件夹本身）

应该看到这些一起被选中：

```
.nojekyll   404.html   about/   committee/   contact/   css/
images/     index.html index.json  js/  news/  notices/  robots.txt  search/  sitemap.xml
```

4. 下面填一句提交说明，点 **Commit changes**

> **文件数超限怎么办**：GitHub 网页一次最多 100 个文件，这里是 75 个，正常一次就够。
> 如果浏览器提示过多，分两批：先拖 `images/` 提交，再拖其余部分提交。

---

## 第 3 步：开启 Pages

仓库 → **Settings → Pages**

- **Source**：选 `Deploy from a branch`
- **Branch**：`main`，目录选 `/ (root)`
- 点 **Save**

等 1–2 分钟，访问：

```
https://<你的用户名>.github.io/
```

能看到完整首页（有样式、轮播、菜单）就说明成功了。

---

## 第 4 步：绑自定义域名（确认页面正常后再做）

1. **Settings → Pages → Custom domain** 填 `www.cnc-wcrp.org` → Save
   （仓库里会自动多出一个 `CNAME` 文件，不用管）
2. 去域名商加解析：

| 主机记录 | 类型 | 值 |
| --- | --- | --- |
| `www` | CNAME | `<你的用户名>.github.io` |
| `@` | A | `185.199.108.153` |
| `@` | A | `185.199.109.153` |
| `@` | A | `185.199.110.153` |
| `@` | A | `185.199.111.153` |

3. 等 DNS 生效（几分钟到几小时），回到 Pages 设置，DNS check 通过后勾上 **Enforce HTTPS**
4. 证书签发可能要等十几分钟到一小时

> 用 Cloudflare 管 DNS 的，`www` 那条先设成**灰云（DNS only）**，证书签好后再考虑开代理。

---

## 每次改内容后怎么更新

手工重传很麻烦。改完内容后：

```bash
cd D:/WorkSpace/2026/WCRP-Hugo-v2
_tools/hugo/hugo.exe --gc --minify --cleanDestinationDir
```

然后重新打包 `public/`，把变动的文件拖上去覆盖。**但更省事的是一次性修好 Git 认证**：

### 用 Personal Access Token 代替密钥（5 分钟）

1. GitHub → 右上头像 → **Settings → Developer settings**
   → **Personal access tokens → Fine-grained tokens → Generate new token**
2. Repository access 选 **Only select repositories** → 选这个仓库
3. Permissions → **Contents: Read and write**
4. 生成后复制那串 `github_pat_...`（只显示一次）
5. 本地执行：

```bash
cd D:/WorkSpace/2026/WCRP-Hugo-v2
git remote set-url origin https://github.com/<用户名>/<仓库名>.git
git push -u origin main
# 用户名填 GitHub 用户名，密码处粘贴 token
```

之后就能正常 `git add . && git commit -m "更新" && git push` 了，Windows 凭据管理器会记住它。

---

## 常见问题

| 现象 | 原因 |
| --- | --- |
| 打开是文件列表 / 404 | Pages 还没构建完，或 Branch 选错 |
| 页面没样式、图片不显示 | 仓库名不是 `<用户名>.github.io`，且还没绑域名（见第 1 步） |
| 显示的是 README 而不是网页 | 缺少 `index.html`，或把文件夹整体套了一层（上传时应是内容本身，不是 `github-upload.zip` 解压出的外层文件夹） |
| 中文文件名 404 | 这个包里没有中文路径，正常不会遇到 |
| 想删掉重来 | Settings → Pages 先关掉，或直接改文件重新提交 |
