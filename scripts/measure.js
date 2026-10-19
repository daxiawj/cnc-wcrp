// 量一下头部/导航的实际尺寸，避免凭截图缩放猜
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const { spawn } = require("child_process");
const PORT = 9336;
const chrome = spawn(CHROME, [
  "--headless=new", "--disable-gpu", "--no-proxy-server",
  `--remote-debugging-port=${PORT}`, "--window-size=1440,900", "about:blank",
], { stdio: "ignore" });
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
  await sleep(2000);
  const expr = [
    "(() => {",
    "  const h = document.querySelector('.site-header').getBoundingClientRect();",
    "  const n = document.querySelector('.nav').getBoundingClientRect();",
    "  const l = document.querySelector('.logo').getBoundingClientRect();",
    "  const a = document.querySelectorAll('.nav .nLi h3 a')[1].getBoundingClientRect();",
    "  return JSON.stringify({header: Math.round(h.height), navTop: Math.round(n.top),",
    "    navH: Math.round(n.height), logoTop: Math.round(l.top), logoH: Math.round(l.height),",
    "    menuItem: [Math.round(a.left), Math.round(a.top), Math.round(a.width), Math.round(a.height)],",
    "    vw: innerWidth});",
    "})()",
  ].join("\n");
  const r = await send("Runtime.evaluate", { expression: expr, returnByValue: true });
  console.log(r.result.value);
  ws.close(); chrome.kill();
})();
