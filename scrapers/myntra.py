"""Myntra — uses SerpAPI Google Shopping filtered to Myntra.

Same approach as Flipkart — real Myntra listings via Google Shopping.
Alternates categories on opposite days to Flipkart to share quota.
"""
import logging
import os
from datetime import date

import requests

from .base import load_config, make_item, save_raw

log = logging.getLogger("myntra")


def search(query, api_key, limit):
    try:
        r = requests.get(
            "https://serpapi.com/search.json",
            params={
                "engine": "google_shopping",
                "q": f"{query} site:myntra.com",
                "gl": "in",
                "hl": "en",
                "api_key": api_key,
                "num": limit,
            },
            timeout=30,
        )
        if r.status_code != 200:
            log.warning("SerpAPI Myntra %s for %r", r.status_code, query)
            return []
        results = r.json().get("shopping_results", [])
    except Exception as e:
        log.warning("SerpAPI Myntra error for %r: %s", query, e)
        return []

    items = []
    for p in results[:limit]:
        try:
            items.append(make_item(
                title=p["title"],
                url=p.get("link") or p.get("product_link", ""),
                image=p.get("thumbnail"),
                source="Myntra",
                country="IN",
                price=p.get("price"),
                currency="INR",
                query=query,
            ))
        except (KeyError, TypeError):
            continue
    return items


def run():
    cfg = load_config()
    api_key = os.environ.get("SERPAPI_KEY", "")
    if not api_key:
        log.warning("SERPAPI_KEY not set — skipping Myntra")
        save_raw("myntra", [])
        return []

    limit = min(cfg["max_per_query"], 3)
    cats = list(cfg["categories"].items())
    day = date.today().toordinal()
    # opposite rotation to Flipkart
    todays = [c for i, c in enumerate(cats) if i % 3 == (day + 1) % 3]

    all_items = []
    for slug, cat in todays:
        got = search(cat["queries"][0], api_key, limit)
        for it in got:
            it["category"] = slug
        all_items += got

    save_raw("myntra", all_items)
    log.info("myntra: saved %d items", len(all_items))
    return all_items


if __name__ == "__main__":
    run()
