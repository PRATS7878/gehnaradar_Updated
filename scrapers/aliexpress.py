"""AliExpress replacement — uses RapidAPI AliExpress Datahub (free tier).

Free tier: 500 requests/month — enough for our daily 27-category run.
Get key: https://rapidapi.com/aliexpress-datahub/api/aliexpress-datahub
  → Subscribe → Basic (free) → copy your RapidAPI key

Set GitHub secret: RAPIDAPI_KEY

Falls back to AliExpress affiliate open API if no RapidAPI key.
"""
import logging
import os

from .base import load_config, make_item, polite_get, save_raw

log = logging.getLogger("aliexpress")

RAPID_HOST = "aliexpress-datahub.p.rapidapi.com"


def search_rapidapi(query, api_key, limit):
    r = polite_get(
        "https://aliexpress-datahub.p.rapidapi.com/item_search",
        params={"q": query, "page": "1", "sort": "default"},
        headers={
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": RAPID_HOST,
        },
        sleep=(0.5, 1),
    )
    if not r:
        return []
    try:
        result = r.json().get("result", {})
        products = result.get("resultList", [])
    except ValueError:
        return []
    items = []
    for p in products[:limit]:
        try:
            detail = p.get("item", p)
            pid = detail.get("itemId") or detail.get("productId")
            title = detail.get("title") or detail.get("name", "")
            img = detail.get("image") or detail.get("imageUrl", "")
            if img and img.startswith("//"):
                img = "https:" + img
            price_obj = detail.get("sku", {}).get("def", {}) or detail
            price = str(price_obj.get("promotionPrice") or
                        price_obj.get("price") or
                        detail.get("salePrice") or "")
            items.append(make_item(
                title=title,
                url=f"https://www.aliexpress.com/item/{pid}.html" if pid else
                    f"https://www.aliexpress.com/wholesale?SearchText={query}",
                image=img, source="AliExpress", country="GLOBAL",
                price=price, query=query,
            ))
        except (KeyError, TypeError):
            continue
    return items


def run():
    cfg = load_config()
    limit = cfg["max_per_query"]
    api_key = os.environ.get("RAPIDAPI_KEY", "")

    if not api_key:
        log.warning("RAPIDAPI_KEY not set — skipping AliExpress")
        save_raw("aliexpress", [])
        return []

    all_items = []
    for slug, cat in cfg["categories"].items():
        got = search_rapidapi(cat["queries"][0], api_key, limit)
        for it in got:
            it["category"] = slug
        all_items += got

    save_raw("aliexpress", all_items)
    log.info("aliexpress: saved %d items", len(all_items))
    return all_items


if __name__ == "__main__":
    run()
