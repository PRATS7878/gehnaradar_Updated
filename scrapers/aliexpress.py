"""AliExpress — uses AliExpress affiliate open platform API.

This is AliExpress's official free API for affiliates. No RapidAPI needed.
Falls back to their public product feed RSS if API key not set.

To get an affiliate API key (free):
https://portals.aliexpress.com → sign up → get App Key + Secret
Set secrets: ALIEXPRESS_APP_KEY and ALIEXPRESS_APP_SECRET

Without keys: uses their public trending feed RSS (limited but free).
"""
import hashlib
import hmac
import logging
import os
import time
import xml.etree.ElementTree as ET
from datetime import datetime

import requests

from .base import load_config, make_item, polite_get, save_raw

log = logging.getLogger("aliexpress")


def search_affiliate_api(query, app_key, app_secret, limit):
    """AliExpress Affiliate API — official, free."""
    params = {
        "method": "aliexpress.affiliate.product.query",
        "app_key": app_key,
        "sign_method": "hmac-sha256",
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "format": "json",
        "v": "2.0",
        "keywords": query,
        "page_size": limit,
        "sort": "SALE_PRICE_ASC",
        "target_currency": "USD",
        "target_language": "EN",
        "tracking_id": "gehnaradar",
    }
    # build signature
    sorted_params = sorted(params.items())
    base = "".join(f"{k}{v}" for k, v in sorted_params)
    sign = hmac.new(
        app_secret.encode(), base.encode(), hashlib.sha256
    ).hexdigest().upper()
    params["sign"] = sign

    try:
        r = requests.get("https://api-sg.aliexpress.com/sync", params=params, timeout=20)
        data = r.json()
        products = (
            data.get("aliexpress_affiliate_product_query_response", {})
                .get("resp_result", {})
                .get("result", {})
                .get("products", {})
                .get("product", [])
        )
    except Exception as e:
        log.warning("AliExpress API error: %s", e)
        return []

    items = []
    for p in products[:limit]:
        try:
            items.append(make_item(
                title=p["product_title"],
                url=p["product_detail_url"],
                image=p.get("product_main_image_url"),
                source="AliExpress",
                country="GLOBAL",
                price=str(p.get("target_sale_price") or p.get("sale_price", "")),
                currency=p.get("target_sale_price_currency", "USD"),
                query=query,
            ))
        except (KeyError, TypeError):
            continue
    return items


def search_rss_fallback(query, limit):
    """AliExpress public search RSS — no key needed."""
    slug = query.replace(" ", "+")
    r = polite_get(
        f"https://www.aliexpress.com/wholesale",
        params={"SearchText": query, "initiative_id": "SB_20240101"},
        sleep=(2, 4),
    )
    if not r:
        return []

    # Try to extract JSON from page
    import re, json
    m = re.search(r'"mods":\{"itemList":\{"content":(\[.*?\])', r.text, re.S)
    if not m:
        return []
    try:
        products = json.loads(m.group(1) + "]")[:limit]
    except Exception:
        return []

    items = []
    for p in products:
        try:
            pid = p["productId"]
            img = p["image"]["imgUrl"]
            if img.startswith("//"):
                img = "https:" + img
            items.append(make_item(
                title=p["title"]["displayTitle"],
                url=f"https://www.aliexpress.com/item/{pid}.html",
                image=img,
                source="AliExpress",
                country="GLOBAL",
                price=p.get("prices", {}).get("salePrice", {}).get("formattedPrice"),
                query=query,
            ))
        except (KeyError, TypeError):
            continue
    return items


def run():
    cfg = load_config()
    limit = cfg["max_per_query"]
    app_key = os.environ.get("ALIEXPRESS_APP_KEY", "")
    app_secret = os.environ.get("ALIEXPRESS_APP_SECRET", "")
    all_items = []

    for slug, cat in cfg["categories"].items():
        q = cat["queries"][0]
        if app_key and app_secret:
            got = search_affiliate_api(q, app_key, app_secret, limit)
        else:
            got = search_rss_fallback(q, limit)
        for it in got:
            it["category"] = slug
        all_items += got
        time.sleep(0.5)

    save_raw("aliexpress", all_items)
    log.info("aliexpress: saved %d items", len(all_items))
    return all_items


if __name__ == "__main__":
    run()
