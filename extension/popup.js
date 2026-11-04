const SETTINGS = "wr:settings";
// Bar length fills its track: measure one mono cell once.
let CELLS = 22;
function measureCells() {
  const track = document.querySelector(".track"), bar = track.querySelector(".bar");
  const probe = document.createElement("span");
  probe.textContent = "━".repeat(10); probe.style.cssText = "position:absolute;visibility:hidden;white-space:pre";
  bar.appendChild(probe);
  const cell = probe.getBoundingClientRect().width / 10;
  probe.remove();
  if (cell > 0) CELLS = Math.max(8, Math.floor((track.clientWidth - 12) / cell));
}
const fmt = {
  size: v => v + "px",
  line: v => (+v).toFixed(2),
  para: v => (+v).toFixed(1) + "em",
  width: v => (v >= 100 ? "full" : v + "%"),
};
let settings = {};

const save = () => chrome.storage.local.set({ [SETTINGS]: settings });
const decimals = step => (String(step).split(".")[1] || "").length;

// ━━━━━━━━━━●──────────
function drawBar(bar, input) {
  const min = +input.min, max = +input.max;
  const frac = (+input.value - min) / (max - min);
  const pos = Math.round(frac * (CELLS - 1));
  bar.innerHTML = `${"━".repeat(pos)}<span class="thumb">●</span><span class="rest">${"─".repeat(CELLS - 1 - pos)}</span>`;
}

function render() {
  document.querySelectorAll("#fonts button").forEach(b =>
    b.classList.toggle("sel", (settings.font || "") === b.dataset.font));
  document.querySelectorAll(".row[data-key]").forEach(row => {
    const k = row.dataset.key, input = row.querySelector("input"), val = row.querySelector(".val");
    const v = settings[k];
    const isDefault = v == null || (k === "width" && v >= 100);
    row.classList.toggle("default", isDefault);
    input.value = v ?? input.dataset.default;
    drawBar(row.querySelector(".bar"), input);
    val.innerHTML = isDefault ? (k === "width" ? "full" : "default") : fmt[k](v) + ' <button title="Back to site default">↺</button>';
    const r = val.querySelector("button");
    if (r) r.onclick = () => { delete settings[k]; save(); render(); };
  });
}

document.querySelectorAll("#fonts button").forEach(b => b.onclick = () => {
  settings.font = b.dataset.font || undefined; save(); render();
});
document.querySelectorAll(".row[data-key] input").forEach(input => input.oninput = () => {
  settings[input.closest(".row").dataset.key] = +input.value; save(); render();
});
document.querySelectorAll(".row[data-key] .step").forEach(btn => btn.onclick = () => {
  const row = btn.closest(".row"), input = row.querySelector("input");
  const step = +input.step, d = decimals(input.step);
  const next = Math.min(+input.max, Math.max(+input.min, +input.value + step * +btn.dataset.dir));
  settings[row.dataset.key] = +next.toFixed(d); save(); render();
});
document.getElementById("reset").onclick = () => { settings = {}; save(); render(); };

// Status dot: filled when wide view is on for this site
function setPulse(on) {
  const el = document.getElementById("pulse");
  el.toggleAttribute("data-on", on);
  el.textContent = on ? "●" : "○";
}

(async () => {
  settings = (await chrome.storage.local.get(SETTINGS))[SETTINGS] || {};
  measureCells();
  render();

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const site = document.getElementById("site");
  if (!tab || !/^https?:/.test(tab.url || "")) {
    site.disabled = true;
    document.getElementById("note").style.display = "block";
    return;
  }
  document.getElementById("host").textContent = new URL(tab.url).hostname;
  try { site.checked = (await chrome.tabs.sendMessage(tab.id, { type: "wr-ping" })).on; }
  catch { site.checked = false; }
  setPulse(site.checked);

  site.onchange = async () => {
    setPulse(site.checked);
    const key = "wr:" + new URL(tab.url).hostname;
    await chrome.storage.local.set({ [key]: site.checked });
    try { await chrome.tabs.sendMessage(tab.id, { type: "wr-ping" }); }
    catch { if (site.checked) await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ["content.js"] }); }
  };
})();
