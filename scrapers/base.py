"""Shared utilities for all GehnaRadar scrapers."""
import hashlib
import json
import logging
import random
import time
from datetime import date
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:127.0) Gecko/20100101 Firefox/127.0",
]


def load_config():
    with open(ROOT / "config.yaml") as f:
        return yaml.safe_load(f)


def polite_get(url, *, headers=None, params=None, timeout=20, retries=2, sleep=(1.5, 3.5)):
    """GET with rotating UA, small random delay, and retries. Returns Response or None."""
    h = {"User-Agent": random.choice(USER_AGENTS),
         "Accept-Language": "en-US,en;q=0.9",
         "Accept": "text/html,application/json;q=0.9,*/*;q=0.8"}
    if headers:
        h.update(headers)
    for attempt in range(retries + 1):
        try:
            time.sleep(random.uniform(*sleep))
            r = requests.get(url, headers=h, params=params, timeout=timeout)
            if r.status_code == 200:
                return r
            logging.warning("GET %s -> %s (attempt %s)", url, r.status_code, attempt + 1)
        except requests.RequestException as e:
            logging.warning("GET %s failed: %s (attempt %s)", url, e, attempt + 1)
    return None


def make_item(*, title, url, image, source, country, price=None, currency=None,
              query=None, trend_score=None, extra=None):
    """Normalised item schema used across all sources."""
    return {
        "id": hashlib.md5((url or title).encode()).hexdigest()[:16],
        "title": (title or "").strip()[:200],
        "url": url,
        "image": image,
        "source": source,
        "country": country,          # IN / US / AE / GLOBAL
        "price": price,
        "currency": currency,
        "query": query,
        "trend_score": trend_score,  # 0-100 where available
        "first_seen": date.today().isoformat(),
        "scraped_at": date.today().isoformat(),
    }


def save_raw(source_name, items):
    """Each scraper dumps its raw results; aggregate.py merges them."""
    out = DATA / "raw"
    out.mkdir(exist_ok=True)
    path = out / f"{source_name}.json"
    path.write_text(json.dumps(items, ensure_ascii=False, indent=1))
    logging.info("%s: saved %d items", source_name, len(items))
    return path
