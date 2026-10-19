// 用 CDP 模拟鼠标悬浮，验证下拉菜单真的能弹出
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const { spawn } = require("child_process");
const fs = require("fs");

const PORT = 9333;
const URL = "http://127.0.0.1:1314/";
const OUT = process.argv[2] || "_shots/hover_check.png";

const chrome = spawn(CHROME, [
  "--headless=new",
  "--disable-gpu",
  "--hide-scrollbars",
  "--no-proxy-server",
  `--remote-debugging-port=${PORT}`,
  "--window-size=1440,900",
  "about:blank",
], { stdio: "ignore" });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function main() {
  let targets = null;
  for (let i = 0; i < 40; i++) {
    try {
      const r = await fetch(`http://127.0.0.1:${PORT}/json/list`);
      targets = await r.json();
      if (targets.length) break;
    } catch (e) { /* 等 Chrome 起来 */ }
    await sleep(250);
  }
  const page = targets.find((t) => t.type === "page");
  const ws = new WebSocket(page.webSocketDebuggerUrl);

  let id = 0;
  const pending = new Map();
  const send = (method, params = {}) =>
    new Promise((resolve) => {
      const msgId = ++id;
      pending.set(msgId, resolve);
      ws.send(JSON.stringify({ id: msgId, method, params }));
    });

  ws.addEventListener("message", (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.id && pending.has(msg.id)) {
      pending.get(msg.id)(msg.result);
      pending.delete(msg.id);
    }
  });

  await new Promise((r) => ws.addEventListener("open", r));
  await send("Page.enable");
  await send("Page.navigate", { url: URL });
  await sleep(2500);

  // 找到“关于我们”这一项的中心坐标
  const loc = await send("Runtime.evaluate", {
    expression: `(() => {
      const a = document.querySelectorAll('.nav .nLi h3 a')[1];
      const r = a.getBoundingClientRect();
      return JSON.stringify({x: r.x + r.width / 2, y: r.y + r.height / 2});
    })()`,
    returnByValue: true,
  });
  const { x, y } = JSON.parse(loc.result.value);

  // 先移入再停留，触发 :hover
  await send("Input.dispatchMouseEvent", { type: "mouseMoved", x: x - 60, y: y });
  await sleep(120);
  await send("Input.dispatchMouseEvent", { type: "mouseMoved", x, y });
  await sleep(500);

  const state = await send("Runtime.evaluate", {
    expression: `(() => {
      const sub = document.querySelectorAll('.nav .nLi')[1].querySelector('.sub');
      const cs = getComputedStyle(sub);
      const r = sub.getBoundingClientRect();
      return JSON.stringify({ visibility: cs.visibility, opacity: cs.opacity,
                               width: Math.round(r.width), height: Math.round(r.height),
                               top: Math.round(r.top) });
    })()`,
    returnByValue: true,
  });
  console.log("下拉面板状态:", state.result.value);

  const shot = await send("Page.captureScreenshot", { format: "png" });
  fs.writeFileSync(OUT, Buffer.from(shot.data, "base64"));
  console.log("截图:", OUT);

  ws.close();
  chrome.kill();
}

main().catch((e) => { console.error(e); chrome.kill(); process.exit(1); });
