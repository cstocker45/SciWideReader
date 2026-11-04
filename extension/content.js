(() => {
  if (window.__wideReader) return;
  window.__wideReader = true;

  const KEY = "wr:" + location.hostname;          // per-site on/off
  const SETTINGS = "wr:settings";                  // global typography
  const HIDE = "wr-hidden", WIDE = "wr-wide", FLAT = "wr-flat", ART = "wr-article", PAD = "wr-pad";
  let on = false;

  const FONTS = {
    serif: 'Georgia, "Times New Roman", serif',
    book: '"Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif',
    sans: '-apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif',
    verdana: 'Verdana, Geneva, sans-serif',
  };

  const layoutStyle = document.createElement("style");
  layoutStyle.textContent = `
    .${HIDE} { display: none !important; }
    .${WIDE} { width: auto !important; max-width: none !important; flex: 1 1 auto !important;
               float: none !important; margin-left: 0 !important; margin-right: 0 !important;
               grid-area: auto !important; grid-column: 1 / -1 !important; }
    .${FLAT} { max-width: none !important; grid-template-columns: minmax(0, 1fr) !important;
               grid-template-areas: none !important; }
    .${PAD} { padding-left: max(2vw, 16px) !important; padding-right: max(2vw, 16px) !important;
              box-sizing: border-box !important; }
    html.wr-on figure img, html.wr-on .${WIDE} img { max-width: 100% !important; height: auto !important; }
  `;
  const typoStyle = document.createElement("style");

  function renderTypography(s = {}) {
    const text = `html.wr-on .${ART} :is(p, li, figcaption, blockquote, dd, dt, td, th)`;
    const all = `html.wr-on .${ART} :is(p, li, figcaption, blockquote, dd, dt, td, th, h1, h2, h3, h4, h5, h6)`;
    let css = "";
    if (s.font && FONTS[s.font]) css += `${all} { font-family: ${FONTS[s.font]} !important; }\n`;
    if (s.size) css += `${text} { font-size: ${s.size}px !important; }\n`;
    if (s.line) css += `${text} { line-height: ${s.line} !important; }\n`;
    if (s.para != null) css += `html.wr-on .${ART} p { margin-top: 0 !important; margin-bottom: ${s.para}em !important; }\n`;
    if (s.width && s.width < 100)
      css += `html.wr-on .${ART}.${WIDE} { max-width: ${s.width}% !important; margin-left: auto !important; margin-right: auto !important; }\n`;
    typoStyle.textContent = css;
  }

  // Element holding the most paragraph text = the article body.
  // A "paragraph" is a <p>, or a text-only <div> (ScienceDirect and some other
  // platforms mark up body paragraphs as <div class="u-margin-s-bottom">).
  const BLOCKS = "div, p, section, article, ul, ol, table, figure, li, h1, h2, h3, h4, h5, h6";
  function paragraphs() {
    const out = [];
    for (const el of document.querySelectorAll("p, div")) {
      if (el.tagName === "DIV" && el.querySelector(BLOCKS)) continue;
      const len = el.textContent.trim().length;
      if (len < (el.tagName === "P" ? 40 : 80) || !el.offsetParent) continue;
      if (el.closest("nav, header, footer, aside")) continue;
      out.push([el, len]);
    }
    return out;
  }

  // Element holding the most paragraph text = the article body; then climb to the
  // whole column it sits in (title, abstract, figures, references), stopping at
  // the first wrapper that is much wider, i.e. the one that also holds sidebars.
  function findArticleBody() {
    const score = new Map();
    for (const [el, len] of paragraphs())
      score.set(el.parentElement, (score.get(el.parentElement) || 0) + len);
    let best = null, bestScore = 0;
    for (const [el, s] of score) if (s > bestScore) { best = el; bestScore = s; }
    if (!best) return null;
    const w = best.getBoundingClientRect().width;
    let el = best;
    while (el.parentElement && el.parentElement !== document.body) {
      if (el.parentElement.getBoundingClientRect().width > w * 1.2 + 40) break;
      el = el.parentElement;
    }
    return el;
  }

  const overlapV = (a, b) => a.top < b.bottom - 5 && b.top < a.bottom - 5;
  const overlapH = (a, b) => a.left < b.right - 5 && b.left < a.right - 5;

  function apply() {
    const body = document.querySelector("." + ART) || findArticleBody();
    if (!body) return;
    // Walk up from the article; any sibling sitting *beside* (not above/below) the
    // branch we're on is a sidebar -> hide it, then widen the branch.
    const hide = [], widen = [], flatten = [];
    for (let el = body; el && el !== document.body; el = el.parentElement) {
      const r = el.getBoundingClientRect();
      if (r.width === 0) continue;
      for (const sib of el.parentElement.children) {
        if (sib === el || sib.tagName === "SCRIPT" || sib.tagName === "STYLE") continue;
        const s = sib.getBoundingClientRect();
        if (s.width === 0 || s.height === 0) continue;
        if (overlapV(r, s) && !overlapH(r, s)) hide.push(sib);
      }
      widen.push(el);
      flatten.push(el.parentElement);
    }
    document.documentElement.classList.add("wr-on");
    body.classList.add(ART);
    hide.forEach(e => e.classList.add(HIDE));
    widen.forEach(e => e.classList.add(WIDE));
    flatten.forEach(e => e.classList.add(FLAT));
    // Side padding once, on the outermost widened wrapper (not on every level).
    widen[widen.length - 1]?.classList.add(PAD);
    hideStragglers(body);
  }

  // Second pass, on the widened layout: narrow, tall panels outside the article that
  // still sit beside it or now float on top of it (sticky "PDF / Cite / Share" rails,
  // sidebars injected after the first pass).
  function hideStragglers(body) {
    const vw = document.documentElement.clientWidth, maxW = vw * 0.35;
    const a = body.getBoundingClientRect();
    const found = [];
    for (const el of document.body.querySelectorAll("aside, nav, div, section")) {
      if (el.classList.contains(HIDE) || el.contains(body) || body.contains(el)) continue;
      const s = el.getBoundingClientRect();
      if (s.width < 40 || s.width > maxW || s.height < 150) continue;
      if (s.right <= 0 || s.left >= vw) continue;                       // off-canvas menus
      if (Math.min(a.bottom, s.bottom) - Math.max(a.top, s.top) < 150) continue;
      const cs = getComputedStyle(el);
      if (cs.visibility === "hidden" || cs.opacity === "0") continue;
      if (el.closest("figure, table, header, footer") || el.querySelector("figure, table, video")) continue;
      let top = el;                                                       // hide the whole panel
      while (top.parentElement && top.parentElement !== document.body && !top.parentElement.contains(body)
             && top.parentElement.getBoundingClientRect().width <= maxW) top = top.parentElement;
      found.push(top);
    }
    found.forEach(e => e.classList.add(HIDE));
  }

  function clear() {
    document.documentElement.classList.remove("wr-on");
    for (const c of [HIDE, WIDE, FLAT, ART, PAD])
      document.querySelectorAll("." + c).forEach(e => e.classList.remove(c));
  }

  function set(state) {
    on = state;
    if (!layoutStyle.isConnected) document.head.append(layoutStyle, typoStyle);
    clear();
    if (on) {
      apply();
      // Late-loading sidebars (ads, "related articles") – re-check a couple of times.
      setTimeout(() => on && apply(), 1500);
      setTimeout(() => on && apply(), 4000);
    }
    chrome.runtime.sendMessage({ type: "wr-state", on }).catch(() => {});
  }

  chrome.runtime.onMessage.addListener((msg, _sender, reply) => {
    if (msg.type === "wr-ping") reply({ on });
  });

  // Popup / shortcut write to storage; react live.
  chrome.storage.onChanged.addListener((changes, area) => {
    if (area !== "local") return;
    if (KEY in changes) set(changes[KEY].newValue !== false);
    if (SETTINGS in changes) renderTypography(changes[SETTINGS].newValue || {});
  });

  // Default: ON (listed journal sites, or sites you switched on), remembered per site.
  chrome.storage.local.get([KEY, SETTINGS], (v) => {
    renderTypography(v[SETTINGS] || {});
    set(v[KEY] !== false);
  });
})();
