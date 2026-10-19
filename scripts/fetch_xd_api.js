// 拦截 xdplus 的 getArticleContent 接口响应，拿到含真实图片地址的正文 JSON
// 用法: node scripts/fetch_xd_api.js <页面URL> <输出文件>
const { spawn } = require("child_process");
const fs = require("fs");

const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const PORT = 9349;
const URL_ = process.argv[2];
const OUT = process.argv[3] || "_shots/xd_api.json";

const chrome = spawn(
  CHROME,
  ["--headless=new", "--disable-gpu", "--no-proxy-server",
   `--remote-debugging-port=${PORT}`, "--window-size=1200,1600", "about:blank"],
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
  let targetId = null;

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
      if (u.includes("getArticleContent")) targetId = m.params.requestId;
    }
  });

  await new Promise((r) => ws.addEventListener("open", r));
  await send("Page.enable");
  await send("Network.enable");
  await send("Page.navigate", { url: URL_ });
  await sleep(10000);

  if (!targetId) {
    console.log("没有捕获到 getArticleContent 响应");
  } else {
    const r = await send("Network.getResponseBody", { requestId: targetId });
    let body = r.body || "";
    if (r.base64Encoded) body = Buffer.from(body, "base64").toString("utf8");
    fs.writeFileSync(OUT, body, "utf8");
    console.log("已保存:", OUT, body.length, "字符");
  }

  ws.close();
  chrome.kill();
})();
