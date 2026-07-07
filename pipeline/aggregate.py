"""Merge raw scraper outputs into the master catalog.

- Dedupes by item id (hash of URL)
- Auto-categorises uncategorised items from title keywords
- Preserves first_seen across days, drops items older than retention_days
- Writes data/catalog.json (site + Excel both read this)
- Writes data/source_status.json so you can see which sources delivered
"""
import json
import logging
from datetime import date, timedelta
from pathlib import Path

from scrapers.base import DATA, load_config

log = logging.getLogger("aggregate")


def categorise(title, cfg):
    t = (title or "").lower()
    for slug, cat in cfg["categories"].items():
        if any(kw.strip() in t for kw in cat["match"]):
            return slug
    return "jewellery_set"  # sensible default bucket


def run():
    cfg = load_config()
    raw_dir = DATA / "raw"
    catalog_path = DATA / "catalog.json"

    old = {}
    if catalog_path.exists():
        for it in json.loads(catalog_path.read_text()).get("items", []):
            old[it["id"]] = it

    status, merged = {}, {}
    for f in sorted(raw_dir.glob("*.json")) if raw_dir.exists() else []:
        items = json.loads(f.read_text())
        status[f.stem] = len(items)
        for it in items:
            if not it.get("category"):
                it["category"] = categorise(it["title"], cfg)
            prev = old.get(it["id"])
            if prev:  # keep original first_seen; refresh everything else
                it["first_seen"] = prev["first_seen"]
            merged[it["id"]] = it

    # carry forward recent old items not seen today (retention window)
    cutoff = (date.today() - timedelta(days=cfg["retention_days"])).isoformat()
    for iid, it in old.items():
        if iid not in merged and it["scraped_at"] >= cutoff:
            merged[iid] = it

    items = sorted(merged.values(),
                   key=lambda x: (x["scraped_at"], x.get("trend_score") or 0),
                   reverse=True)

    trends_rising = json.loads((DATA / "trends_rising.json").read_text()) \
        if (DATA / "trends_rising.json").exists() else []
    trends_interest = json.loads((DATA / "trends_interest.json").read_text()) \
        if (DATA / "trends_interest.json").exists() else []

    out = {
        "generated": date.today().isoformat(),
        "items": items,
        "rising_queries": trends_rising,
        "category_interest": trends_interest,
        "categories": {k: v["label"] for k, v in cfg["categories"].items()},
        "markets": {k: v["name"] for k, v in cfg["markets"].items()},
    }
    catalog_path.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    (DATA / "source_status.json").write_text(json.dumps(status, indent=1))
    log.info("catalog: %d items | sources: %s", len(items), status)
    return out


if __name__ == "__main__":
    run()
