# GehnaRadar

Autonomous trend radar for artificial jewellery. Every day it scrapes trending
designs across India, USA, Gulf and global sources, updates a luxury catalog
website, and emails you an Excel report. Rolling 14-day trend window.

**Running cost: ₹0/month.** Only fixed cost is your domain (~₹700/year, optional —
the site works on the free `username.github.io` URL too).

---

## How it works

```
GitHub Actions (daily, 8:00 AM IST, free)
 ├─ scrapers/          Google Trends · Etsy · Pinterest · AliExpress · Meesho · Amazon · eBay · Noon · Flipkart · Myntra
 ├─ pipeline/aggregate  merge + dedupe + auto-categorise + 14-day history
 ├─ pipeline/make_excel Summary | All Items | Rising Searches | Category Interest | Source Status
 ├─ pipeline/send_email Gmail → your inbox with the .xlsx attached
 └─ site_builder/build  static catalog site → deployed to GitHub Pages
```

## One-time setup (~20 minutes)

1. **Create a GitHub repo** (private is fine) and push this folder:
   ```bash
   git init && git add . && git commit -m "GehnaRadar v1"
   git remote add origin https://github.com/YOURNAME/gehnaradar.git
   git push -u origin main
   ```

2. **Enable GitHub Pages**: repo → Settings → Pages → Source: **GitHub Actions**.

3. **Add email secrets** (repo → Settings → Secrets and variables → Actions):
   - `GMAIL_USER` — your Gmail address
   - `GMAIL_APP_PASSWORD` — Google Account → Security → 2-Step Verification →
     App passwords → create one for "Mail" (16 characters)
   - `EMAIL_TO` — where the report goes (can be same address)

4. **First run**: repo → Actions → "GehnaRadar daily run" → **Run workflow**.
   After ~5–10 minutes: site is live, Excel is in your inbox.

5. **(Optional) Custom domain**: buy `gehnaradar.in` / `.com` (~₹700/yr),
   point a CNAME at `YOURNAME.github.io`, add the domain in Pages settings.
   Verify availability before buying — the name was checked against major
   registries in mid-2026 but re-verify yourself.

## Local test

```bash
pip install -r requirements.txt
python run_all.py
open dist/index.html   # or double-click it
```

## Source reliability — honest notes

| Source | Reliability | Notes |
|---|---|---|
| Google Trends | **High** | Official-ish library (pytrends). Rate-limited; the code sleeps between batches. |
| Etsy | Medium | HTML scrape of public search pages; selectors may need a fix every few months. |
| Amazon bestsellers | Medium | 3 requests/day total. **ToS grey-zone** — as a future Amazon seller, you can disable it in `config.yaml` (`sources.amazon: false`). |
| Meesho | Medium | Internal search API; may change without notice. |
| Pinterest | Low-medium | Public resource endpoint, no login. Most fragile source. |
| AliExpress | Low-medium | Parses embedded page JSON; markup rotates often. |
| eBay | Medium-high | `.s-item` markup stable for years; sorted by newest. |
| Noon | Medium | Parses embedded `__NEXT_DATA__`; covers UAE + Saudi storefronts. |
| Flipkart | Low | Heavily bot-protected; works when unblocked. **ToS grey-zone** — future-seller risk, disable anytime. |
| Myntra | Low | Internal gateway API, often gated. **ToS grey-zone** — disable anytime. |

Markets covered: **India, USA, UK, UAE/Gulf, Saudi Arabia, Global.**
Shein and Temu are deliberately excluded — their bot protection can't be
beaten on a free tier (paid Apify actors ~₹1,500/mo when you want them).

**The pipeline never fails because one source fails.** Each source is wrapped;
the "Source Status" sheet in the daily Excel tells you which returned 0 items
so you know when something needs a fix. Instagram is deliberately excluded —
Meta blocks scrapers hard, and Pinterest captures the same visual trends.

## Tuning

Everything lives in `config.yaml`:
- add/remove **categories** and their search queries
- switch **sources** on/off
- change `max_per_query` (bigger = more items, slower run)
- change `retention_days` for catalog history

## Legal + fair-use posture

- Every card links to and names its original source; images are hotlinked, not copied.
- Fine as a private research tool. Before making the site fully public/commercial,
  consider replacing hotlinked images with your own product shots per category —
  displaying competitors' photos commercially is a copyright grey zone.
- Robots-respectful volumes: single-digit requests per source per day with delays.

## Roadmap ideas (when revenue justifies it)

- Play Store app (₹2,100 one-time): wrap the site as a TWA — 1 day of work.
- Paid Apify/SerpAPI actors (~₹1,500/mo) for bulletproof Pinterest + Amazon data.
- WhatsApp daily digest instead of email (free via Meta Cloud API tier).
