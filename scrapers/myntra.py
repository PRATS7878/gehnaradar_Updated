"""Myntra — uses RapidAPI Myntra endpoint (free tier).

Myntra's API blocks all cloud IPs. Uses same RAPIDAPI_KEY.
"""
import logging
import os
from datetime import date

from .base import load_config, make_item, polite_get, save_raw

log = logging.getLogger("myntra")

RAPID_HOST = "myntra-unofficial.p.rapidapi.com"


def search_rapidapi(query, api_key, limit):
    r = polite_get(
        "https://myntra-unofficial.p.rapidapi.com/search",
        params={"query": query, "rows": limit},
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
            pid = p.get("id") or p.get("productId", "")
            items.append(make_item(
                title=f'{p.get("brand", "")} {p.get("productName", "")}'.strip(),
                url=f"https://www.myntra.com/{pid}" if pid else
                    f"https://www.myntra.com/{query.replace(' ', '-')}",
                image=p.get("searchImage") or p.get("image"),
                source="Myntra", country="IN",
                price=str(p.get("price") or p.get("discountedPrice") or ""),
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
        log.warning("RAPIDAPI_KEY not set — skipping Myntra")
        save_raw("myntra", [])
        return []

    cats = list(cfg["categories"].items())
    day_index = date.today().toordinal()
    todays_cats = [c for i, c in enumerate(cats) if i % 2 != day_index % 2]

    all_items = []
    for slug, cat in todays_cats:
        got = search_rapidapi(cat["queries"][0], api_key, limit)
        for it in got:
            it["category"] = slug
        all_items += got

    save_raw("myntra", all_items)
    log.info("myntra: saved %d items", len(all_items))
    return all_items


if __name__ == "__main__":
    run()
