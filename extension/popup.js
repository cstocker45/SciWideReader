const SETTINGS = "wr:settings";
const fmt = {
  size: v => v + " px",
  line: v => (+v).toFixed(2),
  para: v => (+v).toFixed(1) + " em",
  width: v => (v >= 100 ? "Full" : v + "%"),
};
let settings = {};

const save = () => chrome.storage.local.set({ [SETTINGS]: settings });

function render() {
  document.querySelectorAll("#fonts button").forEach(b =>
    b.classList.toggle("sel", (settings.font || "") === b.dataset.font));
  document.querySelectorAll(".row[data-key]").forEach(row => {
    const k = row.dataset.key, input = row.querySelector("input"), val = row.querySelector(".val");
    const v = settings[k];
    const isDefault = v == null || (k === "width" && v >= 100);
    row.classList.toggle("default", isDefault);
    input.value = v ?? input.dataset.default;
    val.innerHTML = isDefault ? (k === "width" ? "Full" : "Site default") : fmt[k](v) + ' <button title="Back to site default">↺</button>';
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
document.getElementById("reset").onclick = () => { settings = {}; save(); render(); };

(async () => {
  settings = (await chrome.storage.local.get(SETTINGS))[SETTINGS] || {};
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

  site.onchange = async () => {
    const key = "wr:" + new URL(tab.url).hostname;
    await chrome.storage.local.set({ [key]: site.checked });
    try { await chrome.tabs.sendMessage(tab.id, { type: "wr-ping" }); }
    catch { if (site.checked) await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ["content.js"] }); }
  };
})();
