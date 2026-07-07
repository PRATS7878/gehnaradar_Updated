"""Meesho replacement — uses Google Shopping via SerpAPI free tier.

SerpAPI free tier: 100 searches/month. We run every other day per category
to stay within the limit and cover all 27 categories in ~2 weeks.

Get key: https://serpapi.com → Register → free plan (100/month)
Set GitHub secret: SERPAPI_KEY

Without key: skips gracefully, shows 0 items in Source Status.
"""
import logging
import os
from datetime import date

from .base import load_config, make_item, polite_get, save_raw

log = logging.getLogger("meesho")

SERPAPI = "https://serpapi.com/search.json"


def search_google_shopping(query, api_key, country, limit):
    r = polite_get(SERPAPI, params={
        "engine": "google_shopping",
        "q": query,
        "gl": country.lower(),
        "hl": "en",
        "api_key": api_key,
        "num": limit,
    }, sleep=(0.5, 1.0))
    if not r:
        return []
    try:
        results = r.json().get("shopping_results", [])
    except ValueError:
        return []
    items = []
    for p in results[:limit]:
        try:
            items.append(make_item(
                title=p["title"],
                url=p.get("link") or p.get("product_link", ""),
                image=p.get("thumbnail"),
                source=p.get("source", "Google Shopping"),
                country=country,
                price=p.get("price"),
                query=query,
            ))
        except (KeyError, TypeError):
            continue
    return items


def run():
    cfg = load_config()
    limit = min(cfg["max_per_query"], 5)   # stay within 100/month free tier
    api_key = os.environ.get("SERPAPI_KEY", "")

    if not api_key:
        log.warning("SERPAPI_KEY not set — skipping Google Shopping")
        save_raw("meesho", [])
        return []

    # Rotate through categories: run a different third each day to save quota
    cats = list(cfg["categories"].items())
    day_index = date.today().toordinal()
    # split into 3 groups, rotate daily
    group = day_index % 3
    todays_cats = [c for i, c in enumerate(cats) if i % 3 == group]

    all_items = []
    for slug, cat in todays_cats:
        # India queries
        got = search_google_shopping(cat["queries"][0], api_key, "IN", limit)
        for it in got:
            it["category"] = slug
        all_items += got

    save_raw("meesho", all_items)
    log.info("google_shopping: saved %d items (group %d)", len(all_items), group)
    return all_items


if __name__ == "__main__":
    run()
