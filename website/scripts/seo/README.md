# SEO automation — Better Call Wes

DataForSEO + VebAPI scripts for continuous SEO/AIO monitoring. All scripts are
pure Python stdlib. Credentials live in the project `.env`:
- `DATAFORSEO_LOGIN`, `DATAFORSEO_PASSWORD` — DataForSEO (SERPs, volumes, onpage, competitor keywords).
- `VEBAPI_KEY` — VebAPI (backlinks). Scout tier $9/mo, 10,000 credits.

## Scripts

| Script | What it does | API spend per run | Cadence |
|---|---|---|---|
| `dataforseo_client.py` | REST wrapper. Run directly to check account balance. | free | as needed |
| `serp_tracker.py` | Organic + local pack + PAA + related-searches per query. Diffs against previous snapshot. Supports `--merge`. | ~$0.005 per query | weekly (tier 1) |
| `weekly_report.py` | Distils the latest SERP snapshot into a markdown report. | free | weekly |
| `paa_harvester.py` | Aggregates PAA + related searches + featured snippets across all snapshots → content-gap report. | free | weekly |
| `keyword_volumes.py` | UK Google Ads search volumes + CPC + competition. Bulk endpoint, flat fee per call. | ~$0.075 per call | monthly |
| `onpage_audit.py` | Technical SEO audit per page (title, meta, h1, links, broken, 4xx). | ~$0.0001 per page | monthly |
| `competitor_intel.py` | Pulls every keyword competitors rank for in top 20 (DataForSEO Labs `ranked_keywords`). Surfaces content gaps. | ~$0.01–0.025 per domain | monthly |
| `backlinks.py` | **(VebAPI)** Backlink summary + referring-domain comparison vs competitors. Filters spam TLDs. Highlights citation gaps. | ~3 credits per domain | monthly |
| `backlinks_dfs.py` | DataForSEO backlinks alternative — kept for forensic deep dives or if VebAPI is offline. Requires the $100/mo DataForSEO Backlinks commitment. | ~$0.04 per domain | as needed |
| `backlinks_compare.py` | Side-by-side comparison of the two backlink providers. Run quarterly to sanity-check VebAPI coverage. | ~$0.20 + ~15 credits | quarterly |
| `vebapi_client.py` | VebAPI REST wrapper. Run directly to smoke-test the key. | free | as needed |
| `seo_dashboard.py` | One-page executive summary combining all of the above. | free | weekly |

## Config

`queries.json` holds the tiered query lists:

- `tier_1_weekly` — 20 highest-value head + neighbourhood terms (weekly SERP track).
- `tier_2_monthly_services` × `tier_2_monthly_locations` — Cartesian product (~120 queries) for broad monthly coverage.
- `tier_3_quarterly_long_tail` — long-tail commercial terms for quarterly checks.
- `brand_terms` — defensive brand monitoring.

Edit this file to add or remove queries; every script reads from it.

## Outputs

Everything lands in the obsidian vault:

```
~/obsidian-vault/Better-Call-Wes/
├── SEO-Data/
│   ├── serp/YYYY-MM-DD.json
│   ├── volumes/YYYY-MM-DD-<tier>.json
│   ├── onpage/YYYY-MM-DD/<slug>.json
│   ├── competitors/YYYY-MM-DD/<domain>.json
│   └── backlinks/YYYY-MM-DD/{summary,refdomains}-<domain>.json
└── SEO-Reports/
    ├── YYYY-MM-DD.md                       ← weekly SERP report
    ├── dashboard-YYYY-MM-DD.md             ← consolidated dashboard (read this first)
    ├── content-gaps-YYYY-MM-DD.md          ← PAA + related searches
    ├── volumes-YYYY-MM-DD-<tier>.md        ← keyword volumes
    ├── onpage-YYYY-MM-DD.md                ← technical audit
    ├── competitor-intel-YYYY-MM-DD.md      ← competitor ranked keywords + gaps
    └── backlinks-YYYY-MM-DD.md             ← (when subscription enabled)
```

## Standard cadences

**Weekly (~$0.10):**
```sh
cd "$(dirname "$0")"
python3 serp_tracker.py
python3 paa_harvester.py
python3 weekly_report.py
python3 seo_dashboard.py
```

**Monthly (~$1.00):**
```sh
python3 serp_tracker.py --tier tier_2_monthly --merge
python3 keyword_volumes.py --tier tier_1_weekly
python3 keyword_volumes.py --tier tier_3_quarterly_long_tail
python3 onpage_audit.py --preset all
python3 competitor_intel.py
python3 backlinks.py            # if subscribed
python3 seo_dashboard.py
```

**Quarterly:**
```sh
python3 serp_tracker.py --tier tier_3_quarterly_long_tail --merge
python3 competitor_intel.py --limit 1000     # deeper crawl
```

**Always available:**
```sh
python3 dataforseo_client.py             # check account balance
python3 serp_tracker.py --dry-run        # preview query set + cost
python3 keyword_volumes.py --dry-run
python3 onpage_audit.py --preset all --dry-run
python3 competitor_intel.py --dry-run
python3 backlinks.py --dry-run
```

## Cost guardrails

Per-call rough costs (verified live):

- `serp/google/organic/live/advanced`: **$0.005** per query
- `keywords_data/google_ads/search_volume/live`: **$0.075** flat per call (any keyword count up to 1,000)
- `on_page/instant_pages`: **$0.0001** per page
- `dataforseo_labs/google/ranked_keywords/live`: **$0.01–0.025** per domain (scales with limit)
- `backlinks/summary/live`: **~$0.02** per domain — requires subscription
- `backlinks/referring_domains/live`: **~$0.02** per domain — requires subscription

Always `--dry-run` before expanding query/URL sets. Run `python3 dataforseo_client.py` to see remaining balance.

## Backlinks providers

We use **VebAPI** as the primary backlinks data source (Scout tier $9/mo, 10,000 credits — vastly more than we use). The 2026-05-11 side-by-side comparison (`backlinks-compare-2026-05-11.md`) showed only 31% overlap with DataForSEO's index — neither tool is "complete," but VebAPI gives equivalent signal volume at 10% of the cost.

`backlinks_dfs.py` is kept as a fallback for forensic deep dives. It requires the $100/mo DataForSEO Backlinks subscription. Run `backlinks_compare.py` quarterly to confirm VebAPI's coverage hasn't degraded.

## Roadmap (not built yet)

- Automated execution via `scheduled-tasks` MCP or systemd timer.
- Telegram alert for >5 position drops, broken-page regressions, or competitor rank surges.
- Propose-and-approve FAQ generation loop: top PAA questions → Wes-voice answers → PR against the site (with `FAQPage` schema).
- Local pack tracker that also pulls Google Business Profile metrics (reviews count, photo count) for us + the local-pack winners.
- Google Search Console + GA4 export pipeline so CTR / impressions / conversions can be joined with the rank data.
