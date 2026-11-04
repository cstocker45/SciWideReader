"""Generate 1280x800 Chrome Web Store screenshots from the synthetic test layouts."""
import pathlib
import sys
import tempfile

from PIL import Image
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "tests"))
from conftest import launch  # noqa: E402
from fixtures import LAYOUTS  # noqa: E402

URL = "https://www.nature.com/wr-test/grid-3col"

with sync_playwright() as p, tempfile.TemporaryDirectory() as d:
    ctx, sw = launch(p, d)
    page = ctx.new_page()
    page.set_viewport_size({"width": 1280, "height": 800})
    page.route(URL, lambda r: r.fulfill(status=200, content_type="text/html", body=LAYOUTS["grid-3col"]))

    sw.evaluate("chrome.storage.local.set({'wr:www.nature.com': false})")
    page.goto(URL); page.wait_for_timeout(800)
    page.screenshot(path=str(HERE / "screenshot-1-before.png"))

    sw.evaluate("chrome.storage.local.set({'wr:www.nature.com': true, 'wr:settings': {font: 'book', size: 18, line: 1.7}})")
    page.wait_for_selector("html.wr-on", state="attached"); page.wait_for_timeout(800)
    page.screenshot(path=str(HERE / "screenshot-2-after.png"))

    ext_id = sw.url.split("/")[2]
    tab_id = sw.evaluate("chrome.tabs.query({}).then(t => t[t.length - 1].id)")
    popup = ctx.new_page()
    # The menu normally reads the active tab; point it at the article tab instead.
    popup.add_init_script(f"chrome.tabs.query = async () => [{{id: {tab_id}, url: '{URL}'}}];")
    popup.set_viewport_size({"width": 290, "height": 560})
    popup.goto(f"chrome-extension://{ext_id}/popup.html"); popup.wait_for_timeout(500)
    popup.locator("body").screenshot(path=str(HERE / "_popup.png"))
    ctx.close()

base = Image.open(HERE / "screenshot-2-after.png").convert("RGB")
pop = Image.open(HERE / "_popup.png").convert("RGB")
shadow = Image.new("RGB", (pop.width + 2, pop.height + 2), (180, 180, 180))
base.paste(shadow, (1280 - pop.width - 41, 19))
base.paste(pop, (1280 - pop.width - 40, 20))
base.save(HERE / "screenshot-3-menu.png")
(HERE / "_popup.png").unlink()
print("ok")
