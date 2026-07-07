"""Build the static catalog site into dist/.

Injects data/catalog.json into templates/index.html at the
__CATALOG_JSON__ marker and copies the latest Excel for download.
"""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"


def run():
    DIST.mkdir(exist_ok=True)
    (DIST / "downloads").mkdir(exist_ok=True)

    catalog = (ROOT / "data" / "catalog.json").read_text()
    template = (ROOT / "site_builder" / "templates" / "index.html").read_text()
    html = template.replace("__CATALOG_JSON__", catalog)
    (DIST / "index.html").write_text(html)

    xlsx = ROOT / "output" / "latest.xlsx"
    if xlsx.exists():
        shutil.copy(xlsx, DIST / "downloads" / "GehnaRadar_latest.xlsx")
    print(f"Site built at {DIST}/index.html")


if __name__ == "__main__":
    run()
