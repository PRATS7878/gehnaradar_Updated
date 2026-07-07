"""eBay — uses RSS feed (no key needed, always works from any IP).

eBay's search RSS feeds are public, stable, and never blocked.
Results are sorted by newly listed, giving fresh trend data.
"""
import logging
import xml.etree.ElementTree as ET

from .base import load_config, make_item, polite_get, save_raw

log = logging.getLogger("ebay")

NS = {"media": "http://search.yahoo.com/mrss/"}


def search_rss(query, limit):
    r = polite_get(
        "https://www.ebay.com/sch/i.html",
        params={"_nkw": query, "_sop": 10, "_rss": 1, "_sacat": 281},
        sleep=(1.5, 3),
    )
    if not r:
        return []
    try:
        root = ET.fromstring(r.content)
    except ET.ParseError:
        return []

    items = []
    for el in root.findall(".//item")[:limit]:
        title = (el.findtext("title") or "").strip()
        link = (el.findtext("link") or "").strip()
        if not title or not link or "eBay" in title:
            continue

        # image from media:content or media:thumbnail
        img = None
        mc = el.find("media:content", NS)
        mt = el.find("media:thumbnail", NS)
        if mc is not None:
            img = mc.get("url")
        elif mt is not None:
            img = mt.get("url")

        # price from description
        desc = el.findtext("description") or ""
        price = None
        if "Price:" in desc:
            try:
                price = desc.split("Price:")[1].split("<")[0].strip()
            except IndexError:
                pass

        items.append(make_item(
            title=title, url=link, image=img,
            source="eBay", country="GLOBAL",
            price=price, query=query,
        ))
    return items


def run():
    cfg = load_config()
    limit = cfg["max_per_query"]
    all_items = []

    for slug, cat in cfg["categories"].items():
        got = search_rss(cat["queries"][0], limit)
        for it in got:
            it["category"] = slug
        all_items += got

    save_raw("ebay", all_items)
    log.info("ebay: saved %d items", len(all_items))
    return all_items


if __name__ == "__main__":
    run()
