// 用 CDP 渲染 SPA 页面并导出正文与 DOM
// 用法: node scripts/fetch_article.js <url> <输出前缀>
const { spawn } = require("child_process");
const fs = require("fs");

const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const PORT = 9347;
const URL_ = process.argv[2];
const PREFIX = process.argv[3] || "_shots/article";

const chrome = spawn(
  CHROME,
  [
    "--headless=new",
    "--disable-gpu",
    "--no-proxy-server",
    `--remote-debugging-port=${PORT}`,
    "--window-size=1200,1600",
    "about:blank",
  ],
  { stdio: "ignore" }
);

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  let targets;
  for (let i = 0; i < 40; i++) {
    try {
      const r = await fetch(`http://127.0.0.1:${PORT}/json/list`);
      targets = await r.json();
      if (targets.length) break;
    } catch (e) {}
    await sleep(300);
  }
  const page = targets.find((x) => x.type === "page");
  const ws = new WebSocket(page.webSocketDebuggerUrl);

  let id = 0;
  const pending = new Map();
  const xhr = [];

  const send = (method, params = {}) =>
    new Promise((res) => {
      const i = ++id;
      pending.set(i, res);
      ws.send(JSON.stringify({ id: i, method, params }));
    });

  ws.addEventListener("message", (e) => {
    const m = JSON.parse(e.data);
    if (m.id && pending.has(m.id)) {
      pending.get(m.id)(m.result);
      pending.delete(m.id);
      return;
    }
    if (m.method === "Network.responseReceived") {
      const u = m.params.response.url;
      if (/api|news|detail|content/i.test(u) && !/\.(js|css|png|jpg|ico)/i.test(u)) {
        xhr.push(u);
      }
    }
  });

  await new Promise((r) => ws.addEventListener("open", r));
  await send("Page.enable");
  await send("Network.enable");
  await send("Page.navigate", { url: URL_ });
  await sleep(9000);

  const text = await send("Runtime.evaluate", {
    expression: "document.body.innerText",
    returnByValue: true,
  });
  const html = await send("Runtime.evaluate", {
    expression: "document.documentElement.outerHTML",
    returnByValue: true,
  });

  fs.writeFileSync(`${PREFIX}.txt`, text.result.value || "", "utf8");
  fs.writeFileSync(`${PREFIX}.html`, html.result.value || "", "utf8");

  console.log("正文长度:", (text.result.value || "").length);
  console.log("接口候选:", [...new Set(xhr)].slice(0, 8).join("\n  "));

  ws.close();
  chrome.kill();
})();
