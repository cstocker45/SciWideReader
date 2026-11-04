import os
import pathlib
import tempfile

import pytest
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXT = ROOT / "extension"
VIEWPORT = {"width": 1400, "height": 900}


def launch(p, user_data_dir):
    """Chromium with the unpacked extension loaded (works headless via the new headless mode)."""
    ctx = p.chromium.launch_persistent_context(
        user_data_dir,
        channel="chromium",
        headless=os.environ.get("HEADED") != "1",
        viewport=VIEWPORT,
        args=[f"--disable-extensions-except={EXT}", f"--load-extension={EXT}"],
    )
    sw = ctx.service_workers[0] if ctx.service_workers else ctx.wait_for_event("serviceworker")
    return ctx, sw


@pytest.fixture(scope="session")
def browser_ctx():
    with sync_playwright() as p, tempfile.TemporaryDirectory() as d:
        ctx, sw = launch(p, d)
        yield ctx, sw
        ctx.close()


@pytest.fixture
def ext(browser_ctx):
    ctx, sw = browser_ctx
    sw.evaluate("chrome.storage.local.clear()")
    yield ctx, sw
    for pg in ctx.pages[1:]:
        pg.close()
