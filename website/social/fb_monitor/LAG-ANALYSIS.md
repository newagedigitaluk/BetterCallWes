# fb_monitor — Lead Lag Analysis

**Measured:** October 2026, from `fb_monitor.log` (alert lines only).
**Problem:** Posts reach Wes 22 minutes to 4 hours after publishing. By then
they typically have 7–13 replies and the poster has often already booked someone.

---

## Measured lag

FB's mobile feed prefixes each post with a relative timestamp ("22m", "3h").
That value is captured in the scraped post text and appears in the alert log.
The table below shows alert time and post age for every alert from October 2026.

### Pre-gate-fix alerts (before 2026-10-24 — old format, partial text in log)

| Alert time | Post age at alert | Notes |
|---|---|---|
| 2026-10-20 20:17 | 18m | ✅ fast |
| 2026-10-22 14:15 | 37m | |
| 2026-10-22 14:33 | 6h | dedup bug — same post re-alerted |
| 2026-10-22 16:17 | 8h | dedup bug |
| 2026-10-23 07:48 | 17m | ✅ fast |
| 2026-10-23 10:32 | 26m | ✅ fast |
| 2026-10-23 15:02 | 53m | |
| 2026-10-23 15:02 | 49m | same post, dedup bug |
| 2026-10-23 18:01 | 55m | |
| 2026-10-23 19:18 | 5h | |
| 2026-10-23 19:32 | 1d | session issue or dedup bug |
| 2026-10-23 21:01 | 9h | |
| 2026-10-24 01:33 | 44m | |
| 2026-10-24 01:46 | 57m | dedup bug (same post 13 min later) |
| 2026-10-24 02:03 | 14h | session/cron issue |
| 2026-10-24 04:02 | 3h | dedup bug (same post, 5 more times) |
| 2026-10-24 04:18 | 3h | dedup bug |
| 2026-10-24 07:01 | 6h | dedup bug |
| 2026-10-24 08:17 | 27m | ✅ fast |
| 2026-10-24 09:32 | 8h | dedup bug |
| 2026-10-24 11:18 | 1m | ✅ fastest ever |
| 2026-10-24 14:18 | 2d | session/cron issue |
| 2026-10-24 14:19 | 21m | ✅ fast |
| 2026-10-24 15:17 | 1h | |

### Post-gate-fix alerts (from 2026-10-24 — full text in log)

| Alert time | Post age at alert | Notes |
|---|---|---|
| 2026-10-24 19:32 | 3h | first run after gate fix; session restart caught old post |
| 2026-10-25 14:19 | 2h | |
| 2026-10-26 15:02 | 1h | |
| 2026-10-27 00:48 | 4h | midnight run, possibly session issue |
| 2026-10-27 08:31 | 22m | ✅ fast |

---

## Distribution (discounting confirmed dedup-bug duplicates)

| Lag bucket | Count | % |
|---|---|---|
| < 30 min | 7 | 25% |
| 30 – 60 min | 6 | 21% |
| 1 – 2 h | 3 | 11% |
| 2 – 4 h | 4 | 14% |
| 4 – 8 h | 4 | 14% |
| > 8 h | 4 | 14% |

**Fast alerts (< 30 min):** 25% of leads.
**Slow alerts (> 1 h):** 53% of leads. Half of these appear to be from session
or cron problems (14h, 1d, 2d) rather than structural polling delay.

---

## Root causes

### 1. Structural (always present)

| Cause | Max lag added | Fix |
|---|---|---|
| 15-min cron interval | +15 min | Cannot change cron without Wes's input (see note below) |
| Startup jitter (was 180s, now 60s) | was +3 min, now +1 min | **Done in config** |
| 10 groups shuffled equally | +2 min (cycle traversal) | **Priority ordering added** |
| `lookback_hours` not enforced | Stale posts alerted | **Implemented in code** |
| Post age not shown in alert | Wes can't triage quickly | **Added to alert format** |

**Note on cron:** The 15-minute cron interval is the single biggest structural
ceiling. Reducing it to 5 minutes would cut the worst-case mechanical delay from
18 min to ~6 min. That requires editing the crontab, which this change-set does
not touch. See "Pushing to 5-minute polling" below.

### 2. Session / cron issues (intermittent, explain the 4–14h outliers)

The 14h, 1d, and 2d lags are not a polling frequency problem — they represent
polls that simply didn't happen. Likely causes:
- FB session cookie expired (storage_state.json stale)
- VPS process crash with no restart logic
- Duplicate cron entries both running, one writing a bad seen-state

These are outside the scope of this analysis. `fb_monitor.log` can be used to
detect gaps: if there is no `Starting FB monitor` line within 20 min of any
15-min boundary, a cycle was missed.

---

## Changes made (this branch)

All changes are on branch `job-j93`, not deployed.

### config.json
- `startup_jitter_seconds`: 180 → 60 (saves up to 2 min per cycle)
- `alert_max_age_hours: 6` added (posts older than 6h are marked seen silently)
- `priority: false` added to every group (Wes sets `true` on the 2–3 busiest)

### fb_monitor.py
- `parse_post_age()` and `post_age_hours()` — extract post age from FB's
  relative timestamp prefix in the scraped text
- `format_alert()` — shows post age with a colour-coded freshness indicator
  (🟢 < 30 min, 🟡 < 90 min, 🔴 older)
- `run_monitor()` — priority groups are visited first, non-priority ones
  shuffled as before
- `run_monitor()` — `alert_max_age_hours` check silently skips and marks seen
  any post older than the configured threshold

### reply_drafter.py
- Six-point format: name → empathy → credential+action → urgency → sign-off
- Each topic now has a topic-specific empathy line (point 2)
- Returns `points` dict so the alert can break out the structure if needed

### research/content/local-trade-social-playbook.md (new)
- Documents the six-point reply format with examples
- States the measured lag and the >90-min response strategy

---

## Pushing to 5-minute polling (recommendation for Wes)

To cut the worst-case lag from ~18 min to ~6 min, change the crontab from
`*/15 * * * *` to `*/5 * * * *`. The browser session + jitter adds ~1–2 min on
top. With 5-min polling the alert would arrive within 7 min of posting in the
best case — before most posts have received their first reply.

The headless browser run takes ~2 min for 10 groups. At 5-min intervals that is
~40% of the time scraping (was ~13%). FB's detection risk is slightly higher but
the jitter and UA spoofing already in place are the main mitigations; the
interval alone is not what triggers bans. Wes's call.

Group labels in `config.json` are all blank. Adding names makes every alert
immediately show which group the post came from, without needing to click the
link. Wes should fill these in.
