"""eBay Browse API — official, free, no scraping.

Uses eBay's production Browse API which is free with a developer account.
Get key: https://developer.ebay.com → Create Application → Production keys
Set GitHub secret: EBAY_CLIENT_ID (the App ID / Client ID)

Falls back to a simpler RSS feed if no key is set.
"""
import base64
import logging
import os
import xml.etree.ElementTree as ET

import requests

from .base import load_config, make_item, polite_get, save_raw

log = logging.getLogger("ebay")


def get_token(client_id, client_secret):
    creds = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    r = requests.post(
        "https://api.ebay.com/identity/v1/oauth2/token",
        headers={"Authorization": f"Basic {creds}",
                 "Content-Type": "application/x-www-form-urlencoded"},
        data="grant_type=client_credentials&scope=https%3A%2F%2Fapi.ebay.com%2Foauth%2Fapi_scope",
        timeout=15,
    )
    if r.status_code == 200:
        return r.json().get("access_token")
    log.warning("eBay token error %s", r.status_code)
    return None


def search_api(query, token, limit):
    r = polite_get("https://api.ebay.com/buy/browse/v1/item_summary/search",
                   params={"q": query, "category_ids": "281",  # Jewellery & Watches
                           "sort": "newlyListed", "limit": limit},
                   headers={"Authorization": f"Bearer {token}",
                            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"},
                   sleep=(0.3, 0.8))
    if not r:
        return []
    try:
        items_data = r.json().get("itemSummaries", [])
    except ValueError:
        return []
    items = []
    for it in items_data:
        try:
            items.append(make_item(
                title=it["title"],
                url=it["itemWebUrl"],
                image=(it.get("thumbnailImages") or it.get("image") and [it["image"]] or [{}])[0].get("imageUrl"),
                source="eBay",
                country="US",
                price=it.get("price", {}).get("value"),
                currency=it.get("price", {}).get("currency", "USD"),
                query=query,
            ))
        except (KeyError, TypeError, IndexError):
            continue
    return items


def search_rss_fallback(query, limit):
    """No-key fallback: eBay RSS feed for new listings."""
    r = polite_get("https://www.ebay.com/sch/i.html",
                   params={"_nkw": query, "_sop": 10, "_rss": 1},
                   sleep=(1, 2))
    if not r:
        return []
    try:
        root = ET.fromstring(r.content)
        ns = {"media": "http://search.yahoo.com/mrss/"}
        items = []
        for item in root.findall(".//item")[:limit]:
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            thumb = item.find("media:thumbnail", ns)
            img = thumb.get("url") if thumb is not None else None
            if title and link:
                items.append(make_item(
                    title=title, url=link, image=img,
                    source="eBay", country="GLOBAL", query=query,
                ))
        return items
    except ET.ParseError:
        return []


def run():
    cfg = load_config()
    limit = cfg["max_per_query"]
    client_id = os.environ.get("EBAY_CLIENT_ID", "")
    client_secret = os.environ.get("EBAY_CLIENT_SECRET", "")

    token = None
    if client_id and client_secret:
        token = get_token(client_id, client_secret)

    all_items = []
    for slug, cat in cfg["categories"].items():
        q = cat["queries"][0]
        got = search_api(q, token, limit) if token else search_rss_fallback(q, limit)
        for it in got:
            it["category"] = slug
        all_items += got

    save_raw("ebay", all_items)
    log.info("ebay: saved %d items (token=%s)", len(all_items), bool(token))
    return all_items


if __name__ == "__main__":
    run()
