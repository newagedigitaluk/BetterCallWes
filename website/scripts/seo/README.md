# SEO automation — Better Call Wes

DataForSEO + VebAPI + Google Search Console scripts for continuous SEO/AIO
monitoring. Credentials live in:
- `.env` — `DATAFORSEO_LOGIN`, `DATAFORSEO_PASSWORD`, `VEBAPI_KEY`
- `.credentials/` (gitignored) — Google Search Console OAuth client + token:
  - `gsc-oauth-client.json` — OAuth 2.0 Desktop client (project `bcw-seo`)
  - `gsc-token.json` — saved refresh token (auto-refreshes via the client)
  - `gsc-service-account.json` — fallback service-account key (currently unused;
    GSC's "Add user" UI rejects service accounts for personal Google accounts)

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
| `gsc_client.py` | Google Search Console wrapper (OAuth user credentials, auto-refresh). Run directly to list properties. | **free** | as needed |
| `gsc_oauth_setup.py` | One-time interactive OAuth flow to seed `gsc-token.json` (GSC scope only). Superseded by `gbp_reauth.py` for re-seeding all 3 scopes. | free | one-off |
| `gbp_reauth.py` | Two-step re-auth (`--start` prints URL, `--finish "<redirect>"` exchanges) that re-seeds `gsc-token.json` with **all 3 scopes** (GSC + GA4 + GBP). Run with `OAUTHLIB_INSECURE_TRANSPORT=1` on the `--finish` step (localhost redirect). Use whenever the token shows `invalid_grant`. | free | as needed |
| `gbp_probe.py` | Tests whether the Google Business Profile API quota is approved (calls Account Management `accounts.list`). `quota_limit_value: 0` + HTTP 429 = still throttled. | free | as needed |
| `ga4_pull.py` | GA4 Data API read (reuses the OAuth token's analytics scope; property from `.env`). Totals, by device, by channel, top landing pages w/ engagement+bounce, key events. Default 28d+90d. | **free** | weekly/monthly |
| `clarity_insights.py` | Microsoft Clarity Data Export API (token in `.env` as `CLARITY_API_TOKEN`). Behavioural metrics — dead/rage/quickback clicks, scroll depth, script errors — by Device/URL/Source. **Limit: 10 calls/project/day, last 1–3 days only.** Net out bots. | free | as needed |
| `gsc_pull.py` | Pull pages + queries + queries×pages from GSC, snapshot to `~/obsidian-vault/Better-Call-Wes/SEO-Data/gsc/YYYY-MM-DD/`. | **free** | weekly |
| `gsc_report.py` | Read the latest GSC snapshot, write a markdown analysis to `SEO-Reports/gsc-YYYY-MM-DD.md` (pages, queries, near-page-1 wins, snippet problems, cannibalisation). | **free** | weekly |
| `seo_dashboard.py` | One-page executive summary combining all of the above. | free | weekly |
| `blog_opportunities.py` | Mines GSC near-page-1 queries + PAA + competitor gaps → ranked blog topic ideas. | free | monthly |
| `blog_post_template.html` | Reusable starter for new blog posts at `/site/blog/<slug>.html`. Includes Article + FAQPage + Breadcrumb JSON-LD, author byline + bio, answer capsule, mid-page CTA, related-links section. Replace every `{{PLACEHOLDER}}`. | n/a | per post |

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
python3 gsc_pull.py            # free — Google Search Console snapshot
python3 gsc_report.py          # free — markdown analysis
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
python3 dataforseo_client.py             # check DataForSEO account balance
python3 vebapi_client.py                 # smoke-test VebAPI key
python3 gsc_client.py                    # list GSC properties (free)
python3 serp_tracker.py --dry-run        # preview query set + cost
python3 keyword_volumes.py --dry-run
python3 onpage_audit.py --preset all --dry-run
python3 competitor_intel.py --dry-run
python3 backlinks.py --dry-run
```

**GSC ad-hoc queries (free, no rate-limit concern):**
```sh
# Pull a per-page query report for the boiler-repair page (last 90 days)
python3 gsc_pull.py --page /services/boiler-repair.html

# Shorter window
python3 gsc_pull.py --days 28

# Generate the markdown analysis from the latest snapshot
python3 gsc_report.py
```

**GSC outputs:**
- Data: `~/obsidian-vault/Better-Call-Wes/SEO-Data/gsc/YYYY-MM-DD/`
  - `pages.json` — page-level metrics
  - `queries.json` — query-level metrics
  - `queries-by-page.json` — query × page pairs (used to detect cannibalisation)
  - `queries-for-<slug>.json` — created when `--page` is passed
- Reports: `~/obsidian-vault/Better-Call-Wes/SEO-Reports/gsc-YYYY-MM-DD.md`
  - Top pages + queries
  - Near-page-1 wins (positions 11–20)
  - Snippet problems (top-10 ranking, sub-2% CTR)
  - Cannibalisation (multiple pages competing for same query)

## Cost guardrails

Per-call rough costs (verified live):

- `serp/google/organic/live/advanced`: **$0.005** per query
- `keywords_data/google_ads/search_volume/live`: **$0.075** flat per call (any keyword count up to 1,000)
- `on_page/instant_pages`: **$0.0001** per page
- `dataforseo_labs/google/ranked_keywords/live`: **$0.01–0.025** per domain (scales with limit)
- `backlinks/summary/live`: **~$0.02** per domain — requires subscription
- `backlinks/referring_domains/live`: **~$0.02** per domain — requires subscription

Always `--dry-run` before expanding query/URL sets. Run `python3 dataforseo_client.py` to see remaining balance.

## Google Search Console — quick reference

The OAuth token at `.credentials/gsc-token.json` auto-refreshes when expired (as long as the `refresh_token` is present in the file). If a session ever sees `RefreshError` or `invalid_grant`, the refresh token was revoked. Re-seed it:

```sh
python3 website/scripts/seo/gsc_oauth_setup.py
```

This prints an auth URL — open it on any device with the GSC-owning Google account, approve, paste the `http://localhost?code=...` URL back, done. The refresh token lasts ~6 months of regular use; daily use keeps it indefinite.

The GSC property is configured in `gsc_client.py` as `DEFAULT_PROPERTY = "sc-domain:bettercallwes.co.uk"`. Override per-call with the `site_url` argument.

## Backlinks providers

We use **VebAPI** as the primary backlinks data source (Scout tier $9/mo, 10,000 credits — vastly more than we use). The 2026-05-11 side-by-side comparison (`backlinks-compare-2026-05-11.md`) showed only 31% overlap with DataForSEO's index — neither tool is "complete," but VebAPI gives equivalent signal volume at 10% of the cost.

`backlinks_dfs.py` is kept as a fallback for forensic deep dives. It requires the $100/mo DataForSEO Backlinks subscription. Run `backlinks_compare.py` quarterly to confirm VebAPI's coverage hasn't degraded.

## Roadmap (not built yet)

- Automated execution via `scheduled-tasks` MCP or systemd timer.
- Telegram alert for >5 position drops, broken-page regressions, or competitor rank surges.
- Propose-and-approve FAQ generation loop: top PAA questions → Wes-voice answers → PR against the site (with `FAQPage` schema).
- Local pack tracker that also pulls Google Business Profile metrics (reviews count, photo count) for us + the local-pack winners.
- Google Search Console + GA4 export pipeline so CTR / impressions / conversions can be joined with the rank data.
