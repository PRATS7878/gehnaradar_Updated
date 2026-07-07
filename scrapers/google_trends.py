"""Google Trends via pytrends — fixed for urllib3 v2 compatibility.

Produces:
1. Rising related queries per category per market
2. Interest scores per category per market
"""
import json
import logging
import time

from .base import DATA, load_config, save_raw

log = logging.getLogger("google_trends")


def run():
    # Import here so a missing/broken install degrades gracefully
    try:
        from pytrends.request import TrendReq
    except ImportError:
        log.error("pytrends not installed")
        save_raw("google_trends", [])
        return [], []

    try:
        py = TrendReq(hl="en-US", tz=330, retries=2, backoff_factor=2,
                      requests_args={"verify": True})
    except TypeError:
        # Older pytrends signature without requests_args
        py = TrendReq(hl="en-US", tz=330)

    cfg = load_config()
    rising, interest = [], []
    cats = list(cfg["categories"].items())

    for geo_key, market in cfg["markets"].items():
        geo = market["trends_geo"]
        for i in range(0, len(cats), 5):
            batch = cats[i:i + 5]
            kw = [c[1]["queries"][0] for c in batch]
            try:
                py.build_payload(kw, geo=geo, timeframe="now 7-d")
                iot = py.interest_over_time()
                if not iot.empty:
                    means = iot[kw].mean()
                    for (slug, c), term in zip(batch, kw):
                        score = float(means.get(term, 0))
                        if score > 0:
                            interest.append({
                                "market": geo_key, "category": slug,
                                "term": term, "score": round(score, 1),
                            })
                rq = py.related_queries()
                for (slug, c), term in zip(batch, kw):
                    r = (rq.get(term) or {}).get("rising")
                    if r is not None and not r.empty:
                        for _, row in r.head(5).iterrows():
                            rising.append({
                                "market": geo_key, "category": slug,
                                "query": str(row["query"]),
                                "growth": str(row["value"]),
                            })
            except Exception as e:
                log.warning("Trends batch failed (geo=%s): %s", geo or "GLOBAL", e)
            time.sleep(10)

    (DATA / "trends_rising.json").write_text(
        json.dumps(rising, ensure_ascii=False, indent=1))
    (DATA / "trends_interest.json").write_text(
        json.dumps(interest, ensure_ascii=False, indent=1))
    log.info("rising=%d interest=%d", len(rising), len(interest))
    save_raw("google_trends", [])
    return rising, interest


if __name__ == "__main__":
    run()
