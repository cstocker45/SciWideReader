"""Load the real extension in Chromium and check it on synthetic journal layouts.

Fixture pages are served at https://www.nature.com/wr-test/<layout> via request
interception, so Chrome injects the content script exactly as on a real journal site.
"""
import json

import pytest

from conftest import EXT
from fixtures import LAYOUTS, SIDEBAR_LAYOUTS

BASE = "https://www.nature.com/wr-test/"

MEASURE = """() => {
  const vw = document.documentElement.clientWidth;
  const art = document.getElementById('article');
  const vis = el => !!el && el.getClientRects().length > 0 && getComputedStyle(el).visibility !== 'hidden';
  const r = art.getBoundingClientRect();
  const img = document.querySelector('#fig1 img').getBoundingClientRect();
  return {
    on: document.documentElement.classList.contains('wr-on'),
    widthRatio: r.width / vw,
    articleVisible: vis(art),
    headerVisible: vis(document.getElementById('header')),
    footerVisible: vis(document.getElementById('footer')),
    figureVisible: vis(document.getElementById('fig1')),
    imgFits: img.right <= vw + 1 && img.width > 0,
    sidebarsVisible: [...document.querySelectorAll('[data-sidebar]')].filter(vis).map(e => e.id),
  };
}"""


def open_layout(ctx, name, wait_ms=0):
    page = ctx.new_page()
    page.route(BASE + "**", lambda route: route.fulfill(
        status=200, content_type="text/html", body=LAYOUTS[route.request.url.rsplit("/", 1)[1]]))
    page.goto(BASE + name)
    page.wait_for_selector("html.wr-on", state="attached", timeout=5000)
    if wait_ms:
        page.wait_for_timeout(wait_ms)
    return page


@pytest.mark.parametrize("layout", SIDEBAR_LAYOUTS)
def test_sidebars_hidden_and_article_full_width(ext, layout):
    ctx, _ = ext
    page = open_layout(ctx, layout, wait_ms={"late-sidebar": 2000, "late-floating-rail": 4600}.get(layout, 0))
    m = page.evaluate(MEASURE)
    assert m["sidebarsVisible"] == [], f"sidebars still visible: {m}"
    assert m["widthRatio"] > 0.85, f"article only {m['widthRatio']:.0%} of viewport"
    assert m["articleVisible"] and m["figureVisible"] and m["imgFits"], m
    assert m["headerVisible"] and m["footerVisible"], "header/footer must not be hidden"


def test_single_column_page_untouched_except_width(ext):
    ctx, _ = ext
    m = open_layout(ctx, "no-sidebar").evaluate(MEASURE)
    assert m["articleVisible"] and m["headerVisible"] and m["footerVisible"] and m["figureVisible"]
    assert m["widthRatio"] > 0.85


def test_typography_settings(ext):
    ctx, sw = ext
    sw.evaluate("""chrome.storage.local.set({'wr:settings':
        {font: 'serif', size: 21, line: 2, para: 1.5, width: 70}})""")
    page = open_layout(ctx, "flex-right")
    p = page.evaluate("""() => { const s = getComputedStyle(document.querySelector('#article p'));
        return {size: s.fontSize, line: s.lineHeight, font: s.fontFamily, mb: s.marginBottom}; }""")
    assert p == {"size": "21px", "line": "42px", "font": p["font"], "mb": "31.5px"}
    assert "Georgia" in p["font"]
    m = page.evaluate(MEASURE)
    assert 0.6 < m["widthRatio"] < 0.75, m


def test_settings_apply_live_without_reload(ext):
    ctx, sw = ext
    page = open_layout(ctx, "flex-right")
    size = lambda: page.evaluate("getComputedStyle(document.querySelector('#article p')).fontSize")
    before = size()
    sw.evaluate("chrome.storage.local.set({'wr:settings': {size: 24}})")
    page.wait_for_function("getComputedStyle(document.querySelector('#article p')).fontSize === '24px'",
                           timeout=3000)
    assert before != "24px"


def test_switching_site_off_restores_layout(ext):
    ctx, sw = ext
    page = open_layout(ctx, "flex-right")
    sw.evaluate("chrome.storage.local.set({'wr:www.nature.com': false})")
    page.wait_for_function("!document.documentElement.classList.contains('wr-on')", timeout=3000)
    m = page.evaluate(MEASURE)
    assert m["sidebarsVisible"] == ["side"]
    assert m["widthRatio"] < 0.75
    # ...and stays off after reload
    page.reload()
    page.wait_for_timeout(1000)
    assert page.evaluate(MEASURE)["sidebarsVisible"] == ["side"]


def test_popup_controls_write_settings(ext):
    ctx, sw = ext
    ext_id = sw.url.split("/")[2]
    popup = ctx.new_page()
    popup.goto(f"chrome-extension://{ext_id}/popup.html")
    popup.click("#fonts button[data-font=book]")
    popup.fill('.row[data-key=line] input', "1.9")
    popup.click("#fonts button[data-font=book]")  # flush
    stored = sw.evaluate("chrome.storage.local.get('wr:settings').then(v => v['wr:settings'])")
    assert stored["font"] == "book" and stored["line"] == 1.9
    assert "1.90" in popup.inner_text('.row[data-key=line] .val')
    popup.click("#reset")
    assert sw.evaluate("chrome.storage.local.get('wr:settings').then(v => v['wr:settings'])") == {}


def test_manifest_is_valid():
    m = json.loads((EXT / "manifest.json").read_text())
    assert m["manifest_version"] == 3
    for f in ["background.js", "content.js", "popup.html", "popup.js"]:
        assert (EXT / f).exists(), f
    assert m["content_scripts"][0]["js"] == ["content.js"]
