"""Amazon Best Sellers (jewellery) — one page per market, once per day.

NOTE: Scraping Amazon is against their ToS even at this low volume.
It's a single bestseller page per market per day (3 requests total),
which is about as gentle as it gets, but if you'd rather not carry the
risk as a future Amazon seller, set sources.amazon: false in config.yaml.
"""
import logging

from bs4 import BeautifulSoup

from .base import load_config, make_item, polite_get, save_raw

log = logging.getLogger("amazon")

BESTSELLER_PATHS = {
    "IN": "https://www.amazon.in/gp/bestsellers/jewelry",
    "US": "https://www.amazon.com/Best-Sellers-Fashion-Jewelry/zgbs/fashion/7454939011",
    "AE": "https://www.amazon.ae/gp/bestsellers/fashion/12149480031",
    "SA": "https://www.amazon.sa/gp/bestsellers/fashion",
    "GB": "https://www.amazon.co.uk/Best-Sellers-Jewellery/zgbs/jewelry",
}


def scrape_market(country, url, limit):
    r = polite_get(url, sleep=(3, 6))
    if not r:
        return []
    soup = BeautifulSoup(r.text, "html.parser")
    items = []
    cards = soup.select("div[id^='gridItemRoot'], div.zg-grid-general-faceout")
    for rank, card in enumerate(cards[:limit], start=1):
        a = card.select_one("a.a-link-normal[href*='/dp/']")
        img = card.select_one("img")
        price = card.select_one("span._cDEzb_p13n-sc-price_3mJ9Z, span.p13n-sc-price")
        if not a or not img:
            continue
        href = a["href"].split("?")[0]
        base = url.split("/gp/")[0].split("/Best-Sellers")[0]
        items.append(make_item(
            title=img.get("alt", "").strip(),
            url=href if href.startswith("http") else base + href,
            image=img.get("src"), source="Amazon", country=country,
            price=price.text.strip() if price else None, query="bestsellers",
            trend_score=max(0, 100 - (rank - 1) * 3),  # rank 1 → 100
        ))
    return items


def run():
    cfg = load_config()
    limit = min(cfg["max_per_query"] * 4, 30)  # bestseller list is richer
    all_items = []
    for country, url in BESTSELLER_PATHS.items():
        all_items += scrape_market(country, url, limit)
    save_raw("amazon", all_items)
    return all_items


if __name__ == "__main__":
    run()
