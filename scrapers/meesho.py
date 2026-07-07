"""Meesho/India shopping — Google Shopping via SerpAPI for India market.

Covers Indian marketplace trends broadly. SerpAPI quota is shared
across Flipkart, Myntra, Noon and Meesho — each rotates different
category groups on different days to stay within 100/month free limit.
"""
import logging
import os
from datetime import date

import requests

from .base import load_config, make_item, save_raw

log = logging.getLogger("meesho")


def search(query, api_key, limit):
    try:
        r = requests.get(
            "https://serpapi.com/search.json",
            params={
                "engine": "google_shopping",
                "q": query + " artificial jewellery",
                "gl": "in",
                "hl": "en",
                "api_key": api_key,
                "num": limit,
            },
            timeout=30,
        )
        if r.status_code != 200:
            log.warning("SerpAPI meesho %s for %r", r.status_code, query)
            return []
        results = r.json().get("shopping_results", [])
    except Exception as e:
        log.warning("SerpAPI meesho error: %s", e)
        return []

    items = []
    for p in results[:limit]:
        try:
            source = p.get("source", "India Shopping")
            items.append(make_item(
                title=p["title"],
                url=p.get("link") or p.get("product_link", ""),
                image=p.get("thumbnail"),
                source=source,
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
        log.warning("SERPAPI_KEY not set — skipping India Shopping")
        save_raw("meesho", [])
        return []

    limit = min(cfg["max_per_query"], 5)
    cats = list(cfg["categories"].items())
    day = date.today().toordinal()
    todays = [c for i, c in enumerate(cats) if i % 3 == day % 3]

    all_items = []
    for slug, cat in todays:
        got = search(cat["queries"][0], api_key, limit)
        for it in got:
            it["category"] = slug
        all_items += got

    save_raw("meesho", all_items)
    log.info("india_shopping: saved %d items", len(all_items))
    return all_items


if __name__ == "__main__":
    run()
