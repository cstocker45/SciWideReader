"""Launch Chromium with the unpacked extension (shared by tests, live check and screenshot scripts)."""
import os
import pathlib

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
