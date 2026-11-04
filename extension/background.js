// Shared helper: switch SciWideReader on/off for a tab's site, injecting the script if needed.
async function setSite(tab, on) {
  const key = "wr:" + new URL(tab.url).hostname;
  await chrome.storage.local.set({ [key]: on });
  try {
    await chrome.tabs.sendMessage(tab.id, { type: "wr-ping" }); // already running: storage change applies it
  } catch {
    if (on) await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ["content.js"] });
  }
}

// Alt+W keyboard shortcut
chrome.commands.onCommand.addListener(async (cmd, tab) => {
  if (cmd !== "toggle-wide" || !tab?.id || !/^https?:/.test(tab.url || "")) return;
  let on = false;
  try { on = (await chrome.tabs.sendMessage(tab.id, { type: "wr-ping" })).on; } catch {}
  await setSite(tab, !on);
});

chrome.runtime.onMessage.addListener((msg, sender) => {
  if (msg.type === "wr-state" && sender.tab) {
    chrome.action.setBadgeText({ tabId: sender.tab.id, text: msg.on ? "W" : "" });
    chrome.action.setBadgeBackgroundColor({ tabId: sender.tab.id, color: "#2a7" });
  }
});
