---
title: "{{ replace .Name "-" " " }}"
date: {{ .Date }}
summary: ""
cover: ""
featured: false
draft: true
---

正文支持标准 Markdown。

## 插入本地图片

把图片放在本文件夹（与 index.md 同级），然后：

    ![图片说明](photo.jpg)

构建时会自动转成带宽高的绝对路径，不会出现布局跳动。

## 插入网络图片 / 附件

    ![图片说明](https://example.com/a.png)
    [会议通知（PDF）](notice.pdf)   ← PDF 也放本文件夹即可
