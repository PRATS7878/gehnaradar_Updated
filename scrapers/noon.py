"""Noon — uses SerpAPI Google Shopping filtered to Noon UAE and KSA.

Noon blocks cloud IPs entirely. Google Shopping via SerpAPI
reliably returns Noon listings for Gulf markets.
"""
import logging
import os
from datetime import date

import requests

from .base import load_config, make_item, save_raw

log = logging.getLogger("noon")


def search(query, api_key, country, limit):
    gl = "ae" if country == "AE" else "sa"
    try:
        r = requests.get(
            "https://serpapi.com/search.json",
            params={
                "engine": "google_shopping",
                "q": f"{query} site:noon.com",
                "gl": gl,
                "hl": "en",
                "api_key": api_key,
                "num": limit,
            },
            timeout=30,
        )
        if r.status_code != 200:
            log.warning("SerpAPI Noon %s for %r", r.status_code, query)
            return []
        results = r.json().get("shopping_results", [])
    except Exception as e:
        log.warning("SerpAPI Noon error: %s", e)
        return []

    items = []
    for p in results[:limit]:
        try:
            items.append(make_item(
                title=p["title"],
                url=p.get("link") or p.get("product_link", ""),
                image=p.get("thumbnail"),
                source="Noon",
                country=country,
                price=p.get("price"),
                currency="AED" if country == "AE" else "SAR",
                query=query,
            ))
        except (KeyError, TypeError):
            continue
    return items


def run():
    cfg = load_config()
    api_key = os.environ.get("SERPAPI_KEY", "")
    if not api_key:
        log.warning("SERPAPI_KEY not set — skipping Noon")
        save_raw("noon", [])
        return []

    limit = min(cfg["max_per_query"], 3)
    cats = list(cfg["categories"].items())
    day = date.today().toordinal()
    # third rotation group
    todays = [c for i, c in enumerate(cats) if i % 3 == (day + 2) % 3]

    all_items = []
    for slug, cat in todays:
        country = "AE" if len(all_items) % 2 == 0 else "SA"
        got = search(cat["queries"][0], api_key, country, limit)
        for it in got:
            it["category"] = slug
        all_items += got

    save_raw("noon", all_items)
    log.info("noon: saved %d items", len(all_items))
    return all_items


if __name__ == "__main__":
    run()
