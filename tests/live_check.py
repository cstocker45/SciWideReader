"""Open real open-access articles with the extension loaded and report what happens.

Statuses:
  pass     - article found, nothing beside it, article spans the page
  fail     - page loaded normally but the extension didn't do its job  -> exit code 1
  blocked  - publisher served a bot check / error page (common from CI datacenter IPs);
             reported but not counted as a failure. We do NOT try to get around these.

Usage: python live_check.py [--out DIR] [--only NAME]
"""
import argparse
import datetime as dt
import json
import pathlib
import sys
import tempfile

from playwright.sync_api import sync_playwright

from browser import launch

HERE = pathlib.Path(__file__).parent
BLOCK_MARKERS = ["just a moment", "attention required", "access denied", "are you a robot",
                 "captcha", "verify you are human", "unusual traffic", "forbidden",
                 "request rejected", "too many requests", "security check", "pardon our interruption"]

MEASURE = """() => {
  const vw = document.documentElement.clientWidth;
  const art = document.querySelector('.wr-article');
  const vis = el => el.getClientRects().length > 0 && getComputedStyle(el).visibility !== 'hidden';
  const bodyText = document.body ? document.body.innerText.length : 0;
  if (!art) return {on: document.documentElement.classList.contains('wr-on'), found: false, bodyText};
  const r = art.getBoundingClientRect();
  // Anything still visible and sitting beside the article (vertical overlap, no horizontal overlap)?
  const beside = [];
  for (const el of document.body.querySelectorAll('aside, nav, div, section')) {
    if (art.contains(el) || el.contains(art) || !vis(el)) continue;
    const s = el.getBoundingClientRect();
    if (s.width < 150 || s.height < 150 || getComputedStyle(el).position === 'fixed') continue;
    if (s.left >= vw || s.right <= 0) continue;  // pushed off-screen: not visible to the reader
    const vOverlap = Math.min(r.bottom, s.bottom) - Math.max(r.top, s.top);
    if (vOverlap > 150 && (s.left >= r.right - 5 || s.right <= r.left + 5)) beside.push(
      el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + (el.className && typeof el.className === 'string' ? '.' + el.className.trim().split(/\\s+/)[0] : ''));
  }
  return {
    on: document.documentElement.classList.contains('wr-on'), found: true, bodyText,
    widthRatio: +(r.width / vw).toFixed(3),
    articleText: art.innerText.length,
    hidden: document.querySelectorAll('.wr-hidden').length,
    sideScroll: document.scrollingElement.scrollWidth - document.documentElement.clientWidth,
    beside: beside.slice(0, 5),
  };
}"""


def check(ctx, pub, shots):
    page = ctx.new_page()
    res = {"name": pub["name"], "url": pub["url"]}
    try:
        resp = page.goto(pub["url"], wait_until="commit", timeout=45000)
        try:  # some publishers keep long-polling connections open; don't wait forever for "loaded"
            page.wait_for_load_state("domcontentloaded", timeout=30000)
        except Exception:
            pass
        page.wait_for_timeout(6000)  # let late widgets load + the extension's re-checks run
        res["http"] = resp.status if resp else None
        title = (page.title() or "").lower()
        text = page.evaluate("document.body ? document.body.innerText.slice(0, 3000).toLowerCase() : ''")
        m = page.evaluate(MEASURE)
        res.update(m)
        blocked_marker = next((b for b in BLOCK_MARKERS if b in title or b in text[:600]), None)
        if (res["http"] or 0) >= 400 or (blocked_marker and m.get("bodyText", 0) < 5000) or m.get("bodyText", 0) < 1500:
            res["status"] = "blocked"
            res["reason"] = f"HTTP {res['http']}" + (f", '{blocked_marker}'" if blocked_marker else "") + \
                            f", {m.get('bodyText', 0)} chars of page text"
        elif not m["found"] or not m["on"]:
            res["status"], res["reason"] = "fail", "extension did not find/activate on the article"
        elif m["articleText"] < 3000:
            res["status"], res["reason"] = "fail", f"picked a too-small block as the article ({m['articleText']} chars)"
        elif m["beside"]:
            res["status"], res["reason"] = "fail", "still visible beside article: " + ", ".join(m["beside"])
        elif m["sideScroll"] > 5:
            res["status"], res["reason"] = "fail", f"page now scrolls sideways by {m['sideScroll']}px"
        elif m["widthRatio"] < 0.8:
            res["status"], res["reason"] = "fail", f"article only {m['widthRatio']:.0%} of window width"
        else:
            res["status"], res["reason"] = "pass", f"article {m['widthRatio']:.0%} wide, {m['hidden']} sidebar element(s) hidden"
        if shots:
            page.screenshot(path=str(shots / (pub["name"].replace(" ", "_").replace("/", "-") + ".png")))
    except Exception as e:  # timeouts, DNS, etc. are infrastructure problems, not extension bugs
        res["status"], res["reason"] = "blocked", f"could not load: {type(e).__name__}: {str(e).splitlines()[0][:120]}"
    finally:
        page.close()
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(HERE / "live-results"))
    ap.add_argument("--only")
    args = ap.parse_args()
    out = pathlib.Path(args.out)
    shots = out / "screenshots"
    shots.mkdir(parents=True, exist_ok=True)
    pubs = json.loads((HERE / "publishers.json").read_text())
    if args.only:
        pubs = [p for p in pubs if args.only.lower() in p["name"].lower()]

    results = []
    with sync_playwright() as p, tempfile.TemporaryDirectory() as d:
        ctx, _ = launch(p, d)
        for pub in pubs:
            r = check(ctx, pub, shots)
            print(f"{r['status'].upper():8} {r['name']:24} {r['reason']}", flush=True)
            results.append(r)
        ctx.close()

    summary = {s: sum(r["status"] == s for r in results) for s in ("pass", "fail", "blocked")}
    (out / "status.json").write_text(json.dumps({
        "checked_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "summary": summary, "results": results}, indent=2))
    print(f"\n{summary}")
    sys.exit(1 if summary["fail"] else 0)


if __name__ == "__main__":
    main()
