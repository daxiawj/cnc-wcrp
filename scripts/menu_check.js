// 验证菜单点击行为：主菜单父项、吸顶导航父项是否真的导航到目标页
// 用法: node scripts/menu_check.js
const { spawn } = require("child_process");

const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const PORT = 9351;
const BASE = "http://127.0.0.1:1314";

const chrome = spawn(
  CHROME,
  ["--headless=new", "--disable-gpu", "--no-proxy-server",
   `--remote-debugging-port=${PORT}`, "--window-size=1440,900", "about:blank"],
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
  const send = (m, p = {}) =>
    new Promise((res) => {
      const i = ++id;
      pending.set(i, res);
      ws.send(JSON.stringify({ id: i, method: m, params: p }));
    });

  ws.addEventListener("message", (e) => {
    const m = JSON.parse(e.data);
    if (m.id && pending.has(m.id)) {
      pending.get(m.id)(m.result);
      pending.delete(m.id);
    }
  });

  await new Promise((r) => ws.addEventListener("open", r));
  await send("Page.enable");

  const evalJs = async (expr) => {
    try {
      const r = await send("Runtime.evaluate", { expression: expr, returnByValue: true });
      return r.result ? r.result.value : null;
    } catch (e) {
      return "ERR";
    }
  };

  // --- 场景 1：主菜单父项点击 ---
  await send("Page.navigate", { url: BASE + "/" });
  await sleep(2000);
  const before = await evalJs(
    `(() => { const a = document.querySelector('.nav .nLi[data-arrow="1"] h3 a');
       return JSON.stringify({ text: a.textContent.trim(), href: a.getAttribute('href'), url: location.href }); })()`
  );
  console.log("主菜单父项:", before);

  await evalJs(`document.querySelector('.nav .nLi[data-arrow="1"] h3 a').click()`);
  await sleep(2500);
  const afterNav = await evalJs(`JSON.stringify({ url: location.href, scrollY: Math.round(scrollY) })`);
  console.log("点击后:", afterNav);

  // --- 场景 2：滚动后点吸顶导航 ---
  await send("Page.navigate", { url: BASE + "/" });
  await sleep(2000);
  await evalJs(`window.scrollTo(0, 1600)`);
  await sleep(1200);
  const stickyState = await evalJs(
    `(() => { const bar = document.getElementById('stickybar');
       const a = bar.querySelectorAll('.sticky-nav a')[1];
       const r = bar.getBoundingClientRect();
       return JSON.stringify({ visible: r.top > -5, scrollY: Math.round(scrollY),
                               text: a.textContent.trim(), href: a.getAttribute('href') }); })()`
  );
  console.log("吸顶栏:", stickyState);

  await evalJs(`document.querySelectorAll('#stickybar .sticky-nav a')[1].click()`);
  await sleep(2500);
  const afterSticky = await evalJs(`JSON.stringify({ url: location.href, scrollY: Math.round(scrollY) })`);
  console.log("吸顶点击后:", afterSticky);

  ws.close();
  chrome.kill();
})();
