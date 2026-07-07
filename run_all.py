"""GehnaRadar daily run: scrape all enabled sources -> aggregate -> Excel -> site.

Every source is wrapped so one failure never kills the run.
Email is sent as a separate step in the GitHub Actions workflow.
"""
import importlib
import logging
import traceback

from scrapers.base import load_config

log = logging.getLogger("run_all")

SOURCE_MODULES = {
    "google_trends": "scrapers.google_trends",
    "etsy": "scrapers.etsy",
    "pinterest": "scrapers.pinterest",
    "aliexpress": "scrapers.aliexpress",
    "meesho": "scrapers.meesho",
    "amazon": "scrapers.amazon_bestsellers",
    "ebay": "scrapers.ebay",
    "noon": "scrapers.noon",
    "flipkart": "scrapers.flipkart",
    "myntra": "scrapers.myntra",
}


def main():
    cfg = load_config()
    for name, module in SOURCE_MODULES.items():
        if not cfg["sources"].get(name, False):
            log.info("Source %s disabled in config — skipping", name)
            continue
        try:
            importlib.import_module(module).run()
        except Exception:
            log.error("Source %s crashed:\n%s", name, traceback.format_exc())

    from pipeline import aggregate, make_excel
    aggregate.run()
    make_excel.run()

    from site_builder import build
    build.run()
    log.info("Daily run complete.")


if __name__ == "__main__":
    main()
