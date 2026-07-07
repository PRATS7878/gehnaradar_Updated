"""Etsy Official API v3 — fixed auth header and endpoint."""
import logging
import os
import time

import requests

from .base import load_config, make_item, save_raw

log = logging.getLogger("etsy")


def run():
    api_key = os.environ.get("ETSY_API_KEY", "").strip()
    if not api_key:
        log.warning("ETSY_API_KEY not set — skipping")
        save_raw("etsy", [])
        return []

    cfg = load_config()
    limit = cfg["max_per_query"]
    all_items = []

    for slug, cat in cfg["categories"].items():
        query = cat["queries"][0]
        try:
            r = requests.get(
                "https://openapi.etsy.com/v3/application/listings/active",
                headers={
                    "x-api-key": api_key,
                    "Accept": "application/json",
                },
                params={
                    "keywords": query,
                    "limit": limit,
                    "sort_on": "score",
                    "includes": ["Images", "MainImage"],
                },
                timeout=20,
            )
            if r.status_code == 403:
                log.warning("Etsy 403 — check API key is correct and app is approved")
                break
            if r.status_code == 429:
                log.warning("Etsy rate limit — sleeping 30s")
                time.sleep(30)
                continue
            if r.status_code != 200:
                log.warning("Etsy %s for %r", r.status_code, query)
                continue

            for listing in r.json().get("results", []):
                try:
                    # get image from MainImage or Images array
                    img = None
                    main = listing.get("MainImage")
                    if main:
                        img = main.get("url_570xN") or main.get("url_fullxfull")
                    if not img:
                        images = listing.get("Images") or listing.get("images") or []
                        if images:
                            img = images[0].get("url_570xN") or images[0].get("url_fullxfull")

                    price_data = listing.get("price", {})
                    price = str(price_data.get("amount", ""))
                    if price and price_data.get("divisor"):
                        price = str(int(price) / int(price_data["divisor"]))

                    all_items.append(make_item(
                        title=listing["title"],
                        url=listing["url"],
                        image=img,
                        source="Etsy",
                        country="GLOBAL",
                        price=price,
                        currency=price_data.get("currency_code", "USD"),
                        query=query,
                        trend_score=min(100, int(listing.get("num_favorers", 0) / 10)),
                        category=slug,
                    ))
                except (KeyError, TypeError, ZeroDivisionError):
                    continue
            time.sleep(0.5)

        except requests.RequestException as e:
            log.warning("Etsy request failed for %r: %s", query, e)

    save_raw("etsy", all_items)
    log.info("etsy: saved %d items", len(all_items))
    return all_items


if __name__ == "__main__":
    run()
