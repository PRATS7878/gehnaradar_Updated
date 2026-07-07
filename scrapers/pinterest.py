"""Pinterest replacement — uses Pinterest RSS feeds + Unsplash API.

Pinterest aggressively blocks server IPs. This module uses two
reliable free alternatives:

1. Pinterest RSS feeds (no auth, always works for public boards/searches)
2. Unsplash API (free 50 req/hr, beautiful jewellery images with tags)

Set GitHub secret: UNSPLASH_ACCESS_KEY
Get key: https://unsplash.com/developers → New Application (free, instant)
"""
import logging
import os
import xml.etree.ElementTree as ET

from .base import load_config, make_item, polite_get, save_raw

log = logging.getLogger("pinterest")


def search_unsplash(query, access_key, limit):
    r = polite_get("https://api.unsplash.com/search/photos",
                   params={"query": query, "per_page": limit,
                           "orientation": "portrait", "order_by": "relevant"},
                   headers={"Authorization": f"Client-ID {access_key}"},
                   sleep=(0.2, 0.5))
    if not r:
        return []
    try:
        results = r.json().get("results", [])
    except ValueError:
        return []
    items = []
    for p in results:
        try:
            items.append(make_item(
                title=p.get("alt_description") or query,
                url=p["links"]["html"],
                image=p["urls"]["regular"],
                source="Unsplash",
                country="GLOBAL",
                query=query,
                trend_score=min(100, p.get("likes", 0) // 5),
            ))
        except (KeyError, TypeError):
            continue
    return items


def search_pinterest_rss(query, limit):
    """Pinterest search RSS — public, no login, reliable."""
    slug = query.replace(" ", "%20")
    r = polite_get(f"https://www.pinterest.com/search/pins/?q={slug}&rs=typed",
                   headers={"Accept": "application/json"},
                   sleep=(1.5, 3))
    # Pinterest RSS for specific boards that are public jewellery trend boards
    rss_feeds = [
        "https://www.pinterest.com/trending/jewellery/feed.rss",
        f"https://in.pinterest.com/search/pins/?q={slug}.rss",
    ]
    items = []
    for feed_url in rss_feeds:
        r = polite_get(feed_url, sleep=(1, 2))
        if not r:
            continue
        try:
            root = ET.fromstring(r.content)
            for item in root.findall(".//item")[:limit]:
                title = item.findtext("title", "").strip()
                link = item.findtext("link", "").strip()
                desc = item.findtext("description", "")
                # Extract image from description HTML
                img = None
                if 'src="' in desc:
                    img = desc.split('src="')[1].split('"')[0]
                if title and link:
                    items.append(make_item(
                        title=title, url=link, image=img,
                        source="Pinterest", country="GLOBAL", query=query,
                    ))
        except ET.ParseError:
            continue
        if items:
            break
    return items[:limit]


def run():
    cfg = load_config()
    limit = cfg["max_per_query"]
    access_key = os.environ.get("UNSPLASH_ACCESS_KEY", "")
    all_items = []

    for slug, cat in cfg["categories"].items():
        q = cat["queries"][0]
        # Try Unsplash first (reliable), then Pinterest RSS
        if access_key:
            got = search_unsplash(q, access_key, limit)
        else:
            got = search_pinterest_rss(q, limit)
            if not got and access_key:
                got = search_unsplash(q, access_key, limit)

        for it in got:
            it["category"] = slug
        all_items += got

    save_raw("pinterest", all_items)
    log.info("pinterest/unsplash: saved %d items", len(all_items))
    return all_items


if __name__ == "__main__":
    run()
