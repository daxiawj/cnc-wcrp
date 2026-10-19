// 滚动到指定位置截图，用于检查吸顶导航
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const { spawn } = require("child_process");
const fs = require("fs");
const PORT = 9338;
const chrome = spawn(CHROME, ["--headless=new","--disable-gpu","--hide-scrollbars","--no-proxy-server",
  `--remote-debugging-port=${PORT}`,"--window-size=1440,900","about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  let t;
  for (let i = 0; i < 30; i++) {
    try { const r = await fetch(`http://127.0.0.1:${PORT}/json/list`); t = await r.json(); if (t.length) break; } catch (e) {}
    await sleep(250);
  }
  const pg = t.find((x) => x.type === "page");
  const ws = new WebSocket(pg.webSocketDebuggerUrl);
  let id = 0; const pend = new Map();
  const send = (m, p = {}) => new Promise((res) => { const i = ++id; pend.set(i, res); ws.send(JSON.stringify({ id: i, method: m, params: p })); });
  ws.addEventListener("message", (e) => { const m = JSON.parse(e.data); if (m.id && pend.has(m.id)) { pend.get(m.id)(m.result); pend.delete(m.id); } });
  await new Promise((r) => ws.addEventListener("open", r));
  await send("Page.enable");
  await send("Page.navigate", { url: "http://127.0.0.1:1314/" });
  await sleep(2200);
  await send("Runtime.evaluate", { expression: "window.scrollTo(0, 900)" });
  await sleep(900);
  const shot = await send("Page.captureScreenshot", { format: "png" });
  fs.writeFileSync(process.argv[2] || "_shots/sticky.png", Buffer.from(shot.data, "base64"));
  console.log("ok");
  ws.close(); chrome.kill();
})();
