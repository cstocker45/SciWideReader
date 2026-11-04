"""Build dist/SciWideReader.zip (the store upload) and _site/ (GitHub Pages).

usage: python scripts/build.py [--status path/to/status.json] [--repo owner/name] [--cws-url URL]
"""
import argparse, json, pathlib, shutil, zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("--status"); ap.add_argument("--repo", default="cstocker45/SciWideReader")
ap.add_argument("--cws-url", default="")
a = ap.parse_args()

version = json.loads((ROOT / "extension/manifest.json").read_text())["version"]
dist, site = ROOT / "dist", ROOT / "_site"
shutil.rmtree(dist, ignore_errors=True); shutil.rmtree(site, ignore_errors=True)
dist.mkdir(); site.mkdir()

zpath = dist / "SciWideReader.zip"
with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted((ROOT / "extension").rglob("*")):
        if f.is_file() and not f.name.startswith("."):
            z.write(f, f.relative_to(ROOT / "extension"))
shutil.copy(zpath, dist / f"SciWideReader-v{version}.zip")

for f in (ROOT / "site").iterdir():
    text = f.read_text()
    for k, v in {"{{REPO}}": a.repo, "{{VERSION}}": version, "{{CWS_URL}}": a.cws_url or "{{CWS_URL}}"}.items():
        text = text.replace(k, v)
    (site / f.name).write_text(text)
for f in ["icon128.png", "screenshot-1-before.png", "screenshot-3-menu.png"]:
    shutil.copy(ROOT / "store" / f, site / f)
shutil.copy(zpath, site / "SciWideReader.zip")
if a.status and pathlib.Path(a.status).exists():
    shutil.copy(a.status, site / "status.json")
print(f"built v{version}: {zpath} and {site}/")
