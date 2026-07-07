"""Flipkart — uses RapidAPI Flipkart endpoint (free tier).

Flipkart's website blocks all cloud IPs. RapidAPI has a stable
unofficial Flipkart search API on the free tier.

Uses same RAPIDAPI_KEY — one key covers AliExpress + Noon + Flipkart.
RapidAPI free: 500 req/month shared across all APIs you use.

Get key: https://rapidapi.com → search "flipkart" → subscribe free
"""
import logging
import os
from datetime import date

from .base import load_config, make_item, polite_get, save_raw

log = logging.getLogger("flipkart")

RAPID_HOST = "real-time-flipkart-api.p.rapidapi.com"


def search_rapidapi(query, api_key, limit):
    r = polite_get(
        "https://real-time-flipkart-api.p.rapidapi.com/product-search",
        params={"q": query, "page": "1"},
        headers={"X-RapidAPI-Key": api_key, "X-RapidAPI-Host": RAPID_HOST},
        sleep=(0.5, 1),
    )
    if not r:
        return []
    try:
        products = r.json().get("products", [])
    except ValueError:
        return []
    items = []
    for p in products[:limit]:
        try:
            items.append(make_item(
                title=p["title"] or p.get("name", ""),
                url=p.get("url") or f"https://www.flipkart.com/search?q={query}",
                image=p.get("thumbnail") or p.get("image"),
                source="Flipkart", country="IN",
                price=str(p.get("price") or p.get("selling_price") or ""),
                currency="INR", query=query,
            ))
        except (KeyError, TypeError):
            continue
    return items


def run():
    cfg = load_config()
    limit = cfg["max_per_query"]
    api_key = os.environ.get("RAPIDAPI_KEY", "")

    if not api_key:
        log.warning("RAPIDAPI_KEY not set — skipping Flipkart")
        save_raw("flipkart", [])
        return []

    # Every other category per day to save quota
    cats = list(cfg["categories"].items())
    day_index = date.today().toordinal()
    todays_cats = [c for i, c in enumerate(cats) if i % 2 == day_index % 2]

    all_items = []
    for slug, cat in todays_cats:
        got = search_rapidapi(cat["queries"][0], api_key, limit)
        for it in got:
            it["category"] = slug
        all_items += got

    save_raw("flipkart", all_items)
    log.info("flipkart: saved %d items", len(all_items))
    return all_items


if __name__ == "__main__":
    run()
