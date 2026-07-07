"""Etsy Official API v3 scraper — requires free API key.

Set GitHub secret: ETSY_API_KEY
Get key: https://www.etsy.com/developers/register
Free tier: 10,000 requests/day — more than enough.
"""
import logging
import os

from .base import load_config, make_item, polite_get, save_raw

log = logging.getLogger("etsy")

API_BASE = "https://openapi.etsy.com/v3/application"


def search(query, api_key, limit=10):
    r = polite_get(f"{API_BASE}/listings/active",
                   params={
                       "keywords": query,
                       "limit": limit,
                       "sort_on": "score",
                       "includes": "Images",
                       "taxonomy_id": 68887686,  # Jewellery & Accessories
                   },
                   headers={"x-api-key": api_key},
                   sleep=(0.3, 0.8))
    if not r:
        return []
    try:
        results = r.json().get("results", [])
    except ValueError:
        return []
    items = []
    for listing in results:
        try:
            img = None
            images = listing.get("images") or []
            if images:
                img = images[0].get("url_570xN") or images[0].get("url_fullxfull")
            items.append(make_item(
                title=listing["title"],
                url=listing["url"],
                image=img,
                source="Etsy",
                country="GLOBAL",
                price=str(listing.get("price", {}).get("amount", "") or ""),
                currency=listing.get("price", {}).get("currency_code", "USD"),
                query=query,
                trend_score=min(100, int(listing.get("num_favorers", 0) / 10)),
            ))
        except (KeyError, TypeError):
            continue
    return items


def run():
    api_key = os.environ.get("ETSY_API_KEY", "")
    if not api_key:
        log.warning("ETSY_API_KEY not set — skipping Etsy")
        save_raw("etsy", [])
        return []

    cfg = load_config()
    limit = cfg["max_per_query"]
    all_items = []
    for slug, cat in cfg["categories"].items():
        for q in cat["queries"][:1]:
            got = search(q, api_key, limit)
            for it in got:
                it["category"] = slug
            all_items += got

    save_raw("etsy", all_items)
    log.info("etsy: saved %d items", len(all_items))
    return all_items


if __name__ == "__main__":
    run()
