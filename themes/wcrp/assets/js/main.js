/* CNC-WCRP · 2026 版交互
   首页轮播 / 滚动导航 / 回到顶部 / 进场动画 / 移动端菜单 / 站内搜索
   无第三方依赖 */
(function () {
  "use strict";

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------------- 首页轮播 ---------------- */
  function initSlider() {
    var box = document.querySelector("[data-slider]");
    if (!box) return;

    var slides = Array.prototype.slice.call(box.querySelectorAll(".hero-slide"));
    if (!slides.length) return;

    var dotsBox = box.querySelector(".hero-dots");
    var prev = box.querySelector(".hero-arrow.prev");
    var next = box.querySelector(".hero-arrow.next");
    var index = 0;
    var timer = null;
    var DURATION = 6500;

    var dots = [];
    if (dotsBox) {
      dots = slides.map(function (_, i) {
        var b = document.createElement("button");
        b.type = "button";
        b.setAttribute("aria-label", "第 " + (i + 1) + " 张焦点图");
        b.addEventListener("click", function () {
          go(i);
          restart();
        });
        dotsBox.appendChild(b);
        return b;
      });
    }

    function go(i) {
      index = (i + slides.length) % slides.length;
      slides.forEach(function (s, k) {
        var on = k === index;
        s.classList.toggle("is-active", on);
        s.setAttribute("aria-hidden", on ? "false" : "true");
      });
      dots.forEach(function (d, k) {
        d.classList.toggle("is-active", k === index);
        d.setAttribute("aria-current", k === index ? "true" : "false");
      });
    }

    function restart() {
      if (timer) window.clearInterval(timer);
      if (slides.length > 1 && !reduceMotion) {
        timer = window.setInterval(function () {
          go(index + 1);
        }, DURATION);
      }
    }

    if (prev) {
      prev.addEventListener("click", function () {
        go(index - 1);
        restart();
      });
    }
    if (next) {
      next.addEventListener("click", function () {
        go(index + 1);
        restart();
      });
    }

    box.addEventListener("mouseenter", function () {
      if (timer) window.clearInterval(timer);
    });
    box.addEventListener("mouseleave", restart);

    box.addEventListener("keydown", function (e) {
      if (e.key === "ArrowLeft") {
        go(index - 1);
        restart();
      } else if (e.key === "ArrowRight") {
        go(index + 1);
        restart();
      }
    });

    // 触摸滑动
    var startX = null;
    box.addEventListener("touchstart", function (e) {
      startX = e.touches[0].clientX;
    }, { passive: true });
    box.addEventListener("touchend", function (e) {
      if (startX === null) return;
      var dx = e.changedTouches[0].clientX - startX;
      startX = null;
      if (Math.abs(dx) < 40) return;
      go(index + (dx < 0 ? 1 : -1));
      restart();
    }, { passive: true });

    go(0);
    restart();
  }

  /* ---------------- 滚动相关：紧凑导航 + 回到顶部 ---------------- */
  function initScrollUI() {
    var bar = document.getElementById("stickybar");
    var top = document.querySelector(".to-top");
    var header = document.querySelector(".site-header");
    var threshold = header ? header.offsetHeight - 40 : 160;

    var ticking = false;

    function onScroll() {
      if (ticking) return;
      ticking = true;
      window.requestAnimationFrame(function () {
        var y = window.scrollY || window.pageYOffset;
        if (bar) bar.classList.toggle("is-shown", y > threshold);
        if (top) {
          var shown = y > 640;
          top.classList.toggle("is-shown", shown);
          top.setAttribute("aria-hidden", shown ? "false" : "true");
        }
        ticking = false;
      });
    }

    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();

    if (top) {
      top.addEventListener("click", function () {
        window.scrollTo({ top: 0, behavior: reduceMotion ? "auto" : "smooth" });
      });
    }
  }

  /* ---------------- 进场动画 ---------------- */
  function initReveal() {
    var items = document.querySelectorAll(".reveal");
    if (!items.length) return;

    if (reduceMotion || !("IntersectionObserver" in window)) {
      Array.prototype.forEach.call(items, function (el) {
        el.classList.add("is-visible");
      });
      return;
    }

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-visible");
        io.unobserve(entry.target);
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.05 });

    Array.prototype.forEach.call(items, function (el, i) {
      el.style.transitionDelay = Math.min(i % 4, 3) * 60 + "ms";
      io.observe(el);
    });
  }

  /* ---------------- 移动端导航 ---------------- */
  function initNav() {
    var toggle = document.querySelector(".nav-toggle");
    var nav = document.getElementById("site-nav");
    if (!toggle || !nav) return;

    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      toggle.setAttribute("aria-label", open ? "关闭菜单" : "打开菜单");
    });

    // 窄屏下二级菜单点击展开
    Array.prototype.forEach.call(
      nav.querySelectorAll(".nLi[data-arrow='1'] > h3 > a"),
      function (a) {
        a.addEventListener("click", function (e) {
          if (!window.matchMedia("(max-width: 900px)").matches) return;
          e.preventDefault();
          var li = a.parentElement.parentElement;
          li.classList.toggle("is-expanded");
        });
      }
    );
  }

  /* ---------------- 站内搜索 ---------------- */
  function initSearch() {
    var list = document.getElementById("search-results");
    if (!list) return;

    var hint = document.getElementById("search-hint");
    var input = document.getElementById("search-input");
    var params = new URLSearchParams(window.location.search);
    // 兼容旧站的 ?title= 参数
    var q = (params.get("q") || params.get("title") || "").trim();

    if (input) input.value = q;

    if (!q) {
      hint.textContent = "输入关键词后回车，可检索新闻、公告与栏目内容。";
      return;
    }

    var indexUrl = list.getAttribute("data-index") || "/index.json";
    hint.textContent = "检索中……";

    fetch(indexUrl)
      .then(function (r) {
        return r.json();
      })
      .then(function (data) {
        var kw = q.toLowerCase();
        var hits = data.filter(function (p) {
          return (p.title + " " + p.text).toLowerCase().indexOf(kw) !== -1;
        });

        hint.textContent = hits.length
          ? "共找到 " + hits.length + " 条与“" + q + "”相关的内容"
          : "没有找到与“" + q + "”相关的内容，换个关键词试试。";

        list.innerHTML = "";
        hits.forEach(function (p) {
          var li = document.createElement("li");
          var h = document.createElement("h2");
          var a = document.createElement("a");
          a.href = p.url;
          a.textContent = p.title;
          h.appendChild(a);
          li.appendChild(h);

          var meta = document.createElement("div");
          meta.className = "meta";
          var LABELS = {
            news: "新闻资讯",
            notices: "通知公告",
            about: "关于我们",
            committee: "委员会名单"
          };
          meta.textContent = (LABELS[p.section] || "栏目") + (p.date ? " · " + p.date : "");
          li.appendChild(meta);

          var desc = document.createElement("p");
          desc.innerHTML = highlight(snippet(p.text, q), q);
          li.appendChild(desc);
          list.appendChild(li);
        });
      })
      .catch(function () {
        hint.textContent = "搜索索引加载失败，请刷新页面重试。";
      });
  }

  function snippet(text, q) {
    var i = text.toLowerCase().indexOf(q.toLowerCase());
    if (i < 0) return text.slice(0, 120);
    var start = Math.max(0, i - 40);
    return (start > 0 ? "…" : "") + text.slice(start, start + 140) + "…";
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  function highlight(text, q) {
    var esc = escapeHtml(text);
    var eq = escapeHtml(q);
    var i = esc.toLowerCase().indexOf(eq.toLowerCase());
    if (i < 0) return esc;
    return esc.slice(0, i) + "<mark>" + esc.slice(i, i + eq.length) + "</mark>" + esc.slice(i + eq.length);
  }

  document.addEventListener("DOMContentLoaded", function () {
    initSlider();
    initScrollUI();
    initReveal();
    initNav();
    initSearch();
  });
})();
