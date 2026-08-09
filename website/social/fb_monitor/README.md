# Facebook Group Lead Monitor

Monitors specified Facebook groups every 20-30 mins on the VPS, filters for plumbing/heating leads, and pings Telegram with a drafted reply ready to copy-paste.

## What it does

1. **Headless Chromium** on the VPS logs into Facebook using a session you exported from your Mac
2. Visits each configured group's mobile page, reads the top ~20 recent posts
3. Filters for plumbing/heating keywords (configurable in `config.json`)
4. For each new lead, drafts a tailored, professional reply with your Linke short link + WhatsApp
5. Sends it to your Telegram so you get the buzz on your phone within minutes

## Setup — three steps

### 1. One-time login on your Mac

The VPS has no screen, so you do the login on your Mac and copy the session file across.

On your Mac (in the project dir, which is mounted via SSHFS at `~/VPS/Projects/Better Call Wes/`):

```bash
cd ~/VPS/Projects/Better\ Call\ Wes
python3 -m pip install playwright
python3 -m playwright install chromium
python3 website/social/fb_monitor/fb_monitor.py --login
```

This opens a Chromium window. Log into Facebook normally. Once you see your feed, switch back to the terminal and press Enter. It saves `storage_state.json` next to the script — that's your portable FB session.

### 2. Verify Telegram works (no FB needed)

```bash
python3 website/social/fb_monitor/fb_monitor.py --test-telegram
```

You should get a test message on your phone. If not, the bot creds at `~/.claude/channels/telegram-bcw/.env` need checking.

### 3. First dry-run

Once `storage_state.json` is in place on the VPS:

```bash
python3 website/social/fb_monitor/fb_monitor.py --dry-run
```

This polls every configured group, prints what it would alert on, but **doesn't send Telegram messages yet**. You'll see the drafted replies in the terminal. If the output looks right, run live:

```bash
python3 website/social/fb_monitor/fb_monitor.py --run
```

### 4. Schedule via cron

Once happy, add to crontab:

```cron
*/25 * * * * cd "/home/wes/Coding/Projects/Better Call Wes" && python3 website/social/fb_monitor/fb_monitor.py --run >> website/social/fb_monitor/fb_monitor.log 2>&1
```

That polls every 25 minutes. The script itself adds random per-group jitter (3-8s between groups) to look less robotic.

## Files

| File | Purpose | Committed? |
|------|---------|------------|
| `config.json` | Groups, keywords, polling settings | ✅ yes |
| `fb_monitor.py` | Main script | ✅ yes |
| `reply_drafter.py` | Reply templates by topic | ✅ yes |
| `storage_state.json` | Your FB session — **NEVER commit** | ❌ gitignored |
| `state/seen_posts.json` | Dedup state | ❌ gitignored |
| `fb_monitor.log` | Runtime log | ❌ gitignored |

## Tuning the filter

Edit `config.json`:

- **`keywords.trade`** — add/remove plumbing keywords
- **`keywords.geo`** — restrict to specific areas
- **`filters.require_geo_match`** — set to `true` to only alert on posts that mention a Southampton location. Currently `false` so you also see e.g. someone in the Eastleigh group posting a generic plumber question.
- **`polling.interval_minutes`** — match your cron schedule

## Reply quality

The drafter (`reply_drafter.py`) uses keyword-routed templates today. Topic detection is anatomical (CP12, power flush, burst pipe, boiler repair, etc.) and the reply includes the matching Linke short link for click attribution.

If you want it smarter (more context-aware, less templated), we can swap the `draft_reply` function to call Claude Haiku — costs ~1p per draft, ~£3/month at typical lead volumes.

## Account safety reminders

- **Don't run the cron more often than every 20 mins.** Faster polling raises flag risk on your main FB account.
- **The script is read-only** — never likes, comments, or interacts. That keeps it well below most automation triggers.
- **Re-login if you start getting empty results consistently** — your FB session cookie will expire eventually (usually months, but not predictable). Just re-run `--login` on your Mac and overwrite `storage_state.json`.
- **If FB shows you a security challenge** in your normal browser, that's a sign they've noticed something. Stop the cron, address it, then resume more conservatively.

## Troubleshooting

- **"No storage_state.json"** → run `--login` on your Mac and upload the file
- **"Telegram creds not available"** → check `~/.claude/channels/telegram-bcw/.env` exists
- **Polls return 0 posts when there should be some** → Facebook may have changed the mobile DOM. Check the `extract_posts_from_group` selectors in `fb_monitor.py`. Or your session may have expired — re-do `--login`.
- **You get the same alerts twice** → the dedup hash is based on normalised text + group URL. If a post is heavily edited it could re-trigger; that's by design (rare).
