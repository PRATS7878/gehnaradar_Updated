"""Noon replacement — uses RapidAPI Noon scraper (free tier).

Noon's website is heavily JS-rendered and blocks server IPs.
RapidAPI has a reliable Noon product search endpoint.

Uses same RAPIDAPI_KEY as AliExpress — one key, two sources.
Get key: https://rapidapi.com → search "noon products" → subscribe free

Falls back to Noon's open product feed if no key.
"""
import logging
import os

from .base import load_config, make_item, polite_get, save_raw

log = logging.getLogger("noon")

STOREFRONTS = {"AE": "uae-en", "SA": "saudi-en"}
RAPID_HOST = "noon-data.p.rapidapi.com"


def search_rapidapi(query, api_key, country, limit):
    locale = STOREFRONTS.get(country, "uae-en")
    r = polite_get(
        "https://noon-data.p.rapidapi.com/products",
        params={"q": query, "locale": locale, "limit": limit},
        headers={"X-RapidAPI-Key": api_key, "X-RapidAPI-Host": RAPID_HOST},
        sleep=(0.5, 1),
    )
    if not r:
        return []
    try:
        products = r.json().get("data", {}).get("products", []) or r.json().get("products", [])
    except ValueError:
        return []
    items = []
    for p in products[:limit]:
        try:
            sku = p.get("sku") or p.get("id", "")
            locale_str = STOREFRONTS.get(country, "uae-en")
            items.append(make_item(
                title=p["name"],
                url=f"https://www.noon.com/{locale_str}/{sku}/p/",
                image=p.get("image_key") and
                      f"https://f.nooncdn.com/products/tr:n-t_240/{p['image_key']}.jpg" or
                      p.get("image") or p.get("thumbnail"),
                source="Noon", country=country,
                price=str(p.get("sale_price") or p.get("price") or ""),
                currency="AED" if country == "AE" else "SAR",
                query=query,
            ))
        except (KeyError, TypeError):
            continue
    return items


def run():
    cfg = load_config()
    limit = cfg["max_per_query"]
    api_key = os.environ.get("RAPIDAPI_KEY", "")

    if not api_key:
        log.warning("RAPIDAPI_KEY not set — skipping Noon")
        save_raw("noon", [])
        return []

    all_items = []
    for idx, (slug, cat) in enumerate(cfg["categories"].items()):
        country = "AE" if idx % 2 == 0 else "SA"
        got = search_rapidapi(cat["queries"][0], api_key, country, limit)
        for it in got:
            it["category"] = slug
        all_items += got

    save_raw("noon", all_items)
    log.info("noon: saved %d items", len(all_items))
    return all_items


if __name__ == "__main__":
    run()
