// 用 CDP 模拟手机尺寸并点开菜单，验证抽屉导航
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const { spawn } = require("child_process");
const fs = require("fs");

const PORT = 9334;
const URL = "http://127.0.0.1:1314/";
const OUT = process.argv[2] || "_shots/mobile_nav.png";

const chrome = spawn(CHROME, [
  "--headless=new",
  "--disable-gpu",
  "--hide-scrollbars",
  "--no-proxy-server",
  `--remote-debugging-port=${PORT}`,
  "--window-size=800,900",
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
    } catch (e) {}
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
  await send("Emulation.setDeviceMetricsOverride", {
    width: 390, height: 844, deviceScaleFactor: 2, mobile: true,
  });
  await send("Page.navigate", { url: URL });
  await sleep(2200);

  // 展开二级菜单再点开抽屉，一并验证
  await send("Runtime.evaluate", {
    expression: `document.querySelector('.nav-toggle').click();`,
  });
  await sleep(400);

  // 再点开“关于我们”，验证二级菜单展开
  await send("Runtime.evaluate", {
    expression: `document.querySelectorAll('.nav .nLi h3 a')[1].click();`,
  });
  await sleep(350);

  const state = await send("Runtime.evaluate", {
    expression: `(() => {
      const nav = document.getElementById('site-nav');
      const cs = getComputedStyle(nav);
      return JSON.stringify({ display: cs.display, height: Math.round(nav.getBoundingClientRect().height) });
    })()`,
    returnByValue: true,
  });
  console.log("抽屉状态:", state.result.value);

  const shot = await send("Page.captureScreenshot", { format: "png" });
  fs.writeFileSync(OUT, Buffer.from(shot.data, "base64"));
  console.log("截图:", OUT);

  ws.close();
  chrome.kill();
}

main().catch((e) => { console.error(e); chrome.kill(); process.exit(1); });
