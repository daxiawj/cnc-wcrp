// 依次切换四张焦点图截图，检查不同比例图片的显示效果
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const { spawn } = require("child_process");
const fs = require("fs");
const PORT = 9337;
const chrome = spawn(CHROME, [
  "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-proxy-server",
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
  await sleep(2200);

  for (let i = 0; i < 4; i++) {
    await send("Runtime.evaluate", {
      expression: `document.querySelectorAll('.hero-dots button')[${i}].click()`,
    });
    await sleep(1100);
    const shot = await send("Page.captureScreenshot", { format: "png", clip: { x: 0, y: 150, width: 1440, height: 640, scale: 1 } });
    fs.writeFileSync(`_shots/slide${i + 1}.png`, Buffer.from(shot.data, "base64"));
    console.log("slide", i + 1, "ok");
  }
  ws.close(); chrome.kill();
})();
