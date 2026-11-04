import tempfile

import pytest
from playwright.sync_api import sync_playwright

from browser import EXT, launch  # noqa: F401  (EXT re-exported for tests)


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
