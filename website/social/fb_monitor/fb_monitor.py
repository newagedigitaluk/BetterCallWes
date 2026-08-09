"""
Facebook group lead monitor for Better Call Wes.

Runs on the VPS every 20-30 minutes via cron. Loads a Facebook session
exported from Wes's Chrome (storage_state.json), opens each configured
group's mobile page in headless Chromium, extracts recent posts, filters
for plumbing/heating leads, drafts a tailored reply, and pings Telegram.

Subcommands
-----------
  --login           Run a one-time visible browser on the Mac to log in and
                    save storage_state.json. (Run ONCE on your Mac.)
  --run             Headless poll across configured groups. Sends Telegram
                    alerts for new leads. (Run via cron on the VPS.)
  --dry-run         Like --run but only prints to stdout, no Telegram send.
  --test-telegram   Send a one-shot test alert to verify Telegram works.

Files
-----
  config.json                    polling config + groups + keywords
  storage_state.json             FB session — created by --login, kept gitignored
  state/seen_posts.json          dedup state — never re-alert on the same post
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import random
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).parent
PROJECT_ROOT = HERE.parent.parent.parent
CONFIG_PATH = HERE / "config.json"
STORAGE_STATE_PATH = HERE / "storage_state.json"
SEEN_PATH = HERE / "state" / "seen_posts.json"
LOG_PATH = HERE / "fb_monitor.log"

# Telegram creds — stored alongside the bcw channel state, NOT in this repo
TELEGRAM_ENV_PATH = Path.home() / ".claude" / "channels" / "telegram-bcw" / ".env"
ACCESS_PATH = Path.home() / ".claude" / "channels" / "telegram-bcw" / "access.json"

sys.path.insert(0, str(HERE))
from reply_drafter import draft_reply  # noqa: E402


# ----- logging ---------------------------------------------------------------

def log(message: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {message}"
    print(line, flush=True)
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


# ----- config + state --------------------------------------------------------

def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def load_seen() -> set:
    if SEEN_PATH.exists():
        try:
            data = json.loads(SEEN_PATH.read_text(encoding="utf-8"))
            return set(data.get("seen", []))
        except Exception:
            return set()
    return set()


def save_seen(seen: set):
    # Cap at last 5000 to prevent unbounded growth
    seen_list = list(seen)[-5000:]
    SEEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    SEEN_PATH.write_text(
        json.dumps({"seen": seen_list, "updated_at": datetime.now(timezone.utc).isoformat()},
                   indent=2),
        encoding="utf-8",
    )


def _extract_post_id(permalink: str) -> str | None:
    """Extract Facebook's stable post ID from a permalink URL.

    Handles all three common URL formats:
      /groups/{gid}/posts/{post_id}/
      /groups/{gid}/permalink/{post_id}/
      ?story_fbid={post_id}&...
    Returns None if no ID found (rare — most group posts have one).
    """
    if not permalink:
        return None
    # /posts/{id}/ or /permalink/{id}/
    m = re.search(r"/(?:posts|permalink)/(\d+)", permalink)
    if m:
        return m.group(1)
    # story_fbid={id}
    m = re.search(r"story_fbid=(\d+)", permalink)
    if m:
        return m.group(1)
    return None


# Volatile fragments that change between polls and MUST be stripped before
# hashing, or the same post produces a new hash each poll → duplicate alerts.
# (Confirmed in production: seen-state had pid:0 — permalink extraction has
# never worked on mobile FB, so the text hash is the real dedup key, and it
# was drifting on timestamps/counts every time someone commented.)
_PUA = re.compile(r"[-\U000f0000-\U000ffffd\U00100000-\U0010fffd]")  # FB icon glyphs
_TIMESTAMP = re.compile(
    r"\b\d+\s*(?:m|min|mins|minute|minutes|h|hr|hrs|hour|hours|"
    r"d|day|days|w|wk|wks|week|weeks|y|yr|yrs|year|years)\b", re.I)
_REL_TIME = re.compile(r"\b(?:just now|yesterday|today|an hour ago|a day ago|edited)\b", re.I)
_COUNTS = re.compile(
    r"\b\d[\d,\.]*\s*(?:comments?|shares?|likes?|reactions?|views?|"
    r"others?|people)\b", re.I)
_UI_WORDS = re.compile(
    r"\b(?:like|comment|share|reply|see more|see translation|follow|"
    r"all reactions|top fan|author|admin|moderator|comment as \w+|write something)\b", re.I)


def stable_fingerprint(post_text: str) -> str:
    """Reduce a post to its durable body words only.

    Strips FB icon glyphs, relative timestamps (7m/2h/1d — the main culprit),
    'just now'/'yesterday', engagement counts (N comments / N likes) and UI
    words, then keeps lowercase LETTERS ONLY (no digits — so ageing
    timestamps and rising counts physically cannot shift the hash).
    The words someone typed don't change between polls → same post, same key.
    """
    t = post_text or ""
    t = _PUA.sub(" ", t)
    t = _TIMESTAMP.sub(" ", t)
    t = _REL_TIME.sub(" ", t)
    t = _COUNTS.sub(" ", t)
    t = _UI_WORDS.sub(" ", t)
    return re.sub(r"[^a-z]", "", t.lower())[:160]


def post_dedup_keys(group_url: str, post_text: str, permalink: str) -> list[str]:
    """Return dedup keys (a hit on ANY key = already seen).

    pid:{id} when a permalink yields one (rare on mobile FB), plus
    fp:{stable_fingerprint_hash} which does the real work.

    Returns [] when the post has too little durable text to fingerprint
    (image-only posts, or parser mis-grabs like a bare timestamp) — the
    caller must SKIP those rather than alert on junk.
    """
    keys = []
    pid = _extract_post_id(permalink)
    if pid:
        keys.append(f"pid:{pid}")
    fp = stable_fingerprint(post_text)
    if len(fp) >= 25:  # enough real words to be a genuine post
        keys.append("fp:" + hashlib.sha256(fp.encode("utf-8")).hexdigest()[:20])
    return keys


# ----- filter ---------------------------------------------------------------

def _kw_present(text: str, kw: str) -> bool:
    """Whole-word(ish) match so 'tap' doesn't fire on 'tap the link' etc."""
    return re.search(r"(?<![a-z])" + re.escape(kw) + r"(?![a-z])", text) is not None


def matches_filters(text: str, config: dict) -> tuple[bool, list]:
    """Tightened two-tier match. Returns (is_lead, matched_terms).

    Tiers (from config['keywords']):
      strong  — specific plumbing/heating terms; match on their own.
      weak    — broad/ambiguous words (gas, tap, shower, pressure); only count
                if an INTENT phrase is also present, so 'gas bill' / 'baby
                shower' / 'tap the link' don't trigger.
      intent  — service-request signals (recommend, anyone know, looking for…).
      exclude — hard-reject phrases; if any is present the post is dropped even
                if a keyword matched (energy-bill chat, for-sale posts, etc.).

    Falls back to the legacy flat 'trade' list if strong/weak aren't configured.
    """
    t = text.lower()
    kw = config["keywords"]
    filters = config.get("filters", {})

    if len(text) < filters.get("min_post_length_chars", 25):
        return False, []

    # Hard exclusions first
    for ex in kw.get("exclude", []):
        if ex in t:
            return False, []

    # Legacy mode (flat list) — kept for safety if config not migrated
    if "strong" not in kw:
        trade = [k for k in kw.get("trade", []) if _kw_present(t, k)]
        return (bool(trade), trade)

    strong = [k for k in kw.get("strong", []) if _kw_present(t, k)]
    if strong:
        return True, strong

    weak = [k for k in kw.get("weak", []) if _kw_present(t, k)]
    if weak:
        has_intent = any(p in t for p in kw.get("intent", []))
        if has_intent:
            return True, weak + ["+intent"]
    return False, []


# ----- Telegram --------------------------------------------------------------

def get_telegram_creds() -> tuple[str, str] | None:
    """Read bot token + chat_id from the BCW channel state, not from this repo."""
    if not TELEGRAM_ENV_PATH.exists() or not ACCESS_PATH.exists():
        return None
    token = None
    for line in TELEGRAM_ENV_PATH.read_text().splitlines():
        if line.startswith("TELEGRAM_BOT_TOKEN="):
            token = line.split("=", 1)[1].strip()
            break
    if not token:
        return None
    access = json.loads(ACCESS_PATH.read_text(encoding="utf-8"))
    allow = access.get("allowFrom", [])
    if not allow:
        return None
    chat_id = allow[0]
    return token, chat_id


# Generic services banner — attached to every lead alert so Wes can reply
# with text + image in one go. Generated via Higgsfield GPT Image 2.
BANNER_PATH = HERE.parent / "reply_banners" / "generic-services-v1.png"


def send_telegram(text: str) -> bool:
    """Send a plain text message via Telegram Bot API."""
    creds = get_telegram_creds()
    if not creds:
        log("  ⚠️  Telegram creds not available — skipping send")
        return False
    token, chat_id = creds
    import requests
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "disable_web_page_preview": True,
                "parse_mode": "HTML",
            },
            timeout=15,
        )
        ok = resp.status_code == 200 and resp.json().get("ok") is True
        if not ok:
            log(f"  ❌ Telegram send failed: {resp.status_code} {resp.text[:200]}")
        return ok
    except Exception as e:
        log(f"  ❌ Telegram error: {e}")
        return False


def send_telegram_photo(photo_path, caption: str = "") -> bool:
    """Send the services banner as a photo so Wes can forward/save it straight
    onto his Facebook reply. Best-effort — a failed photo never blocks the
    text alert (which already went out first)."""
    creds = get_telegram_creds()
    if not creds or not Path(photo_path).exists():
        return False
    token, chat_id = creds
    import requests
    try:
        with open(photo_path, "rb") as f:
            resp = requests.post(
                f"https://api.telegram.org/bot{token}/sendPhoto",
                data={"chat_id": chat_id, "caption": caption[:1020], "parse_mode": "HTML"},
                files={"photo": f},
                timeout=30,
            )
        return resp.status_code == 200 and resp.json().get("ok") is True
    except Exception as e:
        log(f"  ⚠️  Telegram photo send failed: {e}")
        return False


def _esc(s: str) -> str:
    """Escape HTML special chars so post text can't break Telegram parsing."""
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def format_alert(post: dict, drafted: dict) -> str:
    """HTML-formatted Telegram alert, built for a 15-second reply:
    lead → tap-to-copy reply → link. Reply is the hero, at the top."""
    urgent_tag = "🚨 <b>URGENT LEAD</b>\n" if drafted["urgent"] else "🔧 <b>New lead</b>\n"
    group_label = _esc(post.get("group_label") or "a group")
    post_excerpt = _esc((post.get("text") or "")[:400])
    permalink = post.get("permalink", "")

    return (
        f"{urgent_tag}"
        f"📍 {group_label}\n"
        f"💬 <i>{post_excerpt}</i>\n\n"
        f"👇 <b>Tap to copy your reply</b>\n"
        f"<pre>{_esc(drafted['reply'])}</pre>\n"
        f"🖼 Banner to attach is in the next message\n"
        f"🔗 <a href=\"{permalink}\">Open the post on Facebook</a>"
    )


# ----- scraper --------------------------------------------------------------

async def extract_posts_from_group(page, group_url: str, max_posts: int = 20) -> list[dict]:
    """
    Navigate to a group's mobile page and extract recent posts.

    Returns list of {author, text, permalink}.

    Modern m.facebook.com strips all semantic DOM attributes — no <article>,
    no role="article", no data-pagelet. So we parse the visible TEXT instead,
    which is much more stable. Each post ends with "Comment as Wesley"
    (literal "Comment as {first name}" — we use it as a delimiter).
    """
    # Convert group URL to mobile equivalent
    parsed = urlparse(group_url)
    mobile_url = group_url.replace("www.facebook.com", "m.facebook.com")
    if "m.facebook.com" not in mobile_url:
        mobile_url = "https://m.facebook.com" + parsed.path

    log(f"  🌐 Navigating: {mobile_url}")
    try:
        await page.goto(mobile_url, wait_until="domcontentloaded", timeout=30000)
    except Exception as e:
        log(f"  ❌ Navigation failed: {e}")
        return []

    # Scroll a couple of times to trigger lazy-loaded content + look more human
    for scroll_y in (800, 1800, 3000):
        await page.evaluate(f"window.scrollTo(0, {scroll_y})")
        await asyncio.sleep(random.uniform(1.5, 3.0))

    # Collect data needed for parsing: full body text + all permalinks in order
    page_data = await page.evaluate(
        """
        () => {
          const body_text = document.body.innerText || '';
          // Find anchors that look like post permalinks — order matters,
          // we use index-correspondence to match permalinks to posts.
          const anchors = Array.from(document.querySelectorAll('a[href]'));
          const post_links = [];
          anchors.forEach(a => {
            const href = a.href || '';
            if (/\\/groups\\/\\d+\\/(permalink|posts)\\//.test(href)
                || /story_fbid/.test(href)
                || /\\/permalink\\.php/.test(href)) {
              if (!post_links.includes(href)) post_links.push(href);
            }
          });
          return { body_text, post_links };
        }
        """
    )

    body_text: str = page_data["body_text"]
    permalinks: list = page_data["post_links"]

    # Parse posts from the body text. Each post ends with "Comment as <firstname>".
    posts = _parse_posts_from_body(body_text, permalinks, group_url)
    return posts[:max_posts]


# Lines that are pure FB icon characters or status decorations.
# These are private-use-area Unicode codepoints FB uses to render icons.
ICON_LINE_RE = re.compile(r"^[\s︀-️​‍‪-‮]*[0-f0-f☀-➿\U0001f300-\U0001fa9f]+[\s︀-️​‍‪-‮]*$")

# Common UI strings that aren't part of a post body
UI_NOISE_PREFIXES = (
    "comment as ", "sort", "recent activity", "your group suggestions",
    "popular in southampton", "anthony stark", "members ·",
    "invite", "videos", "announcements", "events", "write something...",
    "photo", "feeling", "join", "remove", "all-star contributor", "see more",
)


def _is_ui_noise(line: str) -> bool:
    s = line.strip().lower()
    if not s:
        return True
    if any(s.startswith(p) for p in UI_NOISE_PREFIXES):
        return True
    # Pure number (engagement counts)
    if s.isdigit() and len(s) <= 5:
        return True
    # "N comments" / "N comment" / "N like" / "N shares"
    if re.match(r"^\d+\s+(comments?|likes?|shares?)$", s):
        return True
    # Pure icon line
    if ICON_LINE_RE.match(line):
        return True
    return False


def _parse_posts_from_body(body_text: str, permalinks: list[str], group_url: str) -> list[dict]:
    """
    Split body text into post blocks using 'Comment as <name>' as delimiter.
    Then for each block, extract author + body text.
    """
    # Cut off the sidebar/footer content — these markers indicate end of the
    # real feed and start of group suggestions / popular in area / etc.
    END_MARKERS = (
        "Your group suggestions",
        "Popular in Southampton",
        "Recent listings",
        "Suggested for you",
        "More from this group",
    )
    for marker in END_MARKERS:
        idx = body_text.find(marker)
        if idx > 0:
            body_text = body_text[:idx]

    # Split on the "Comment as <FirstName>" sentinel
    blocks = re.split(r"Comment as \w+", body_text)

    posts = []
    perm_idx = 0

    # Find the start of the real feed — usually after "Recent activity" or "SORT"
    if "Recent activity" in body_text:
        offset = body_text.find("Recent activity")
        # Trim everything before this offset from the first block
        head_block_text = body_text[offset:].split("Comment as ")[0]
        blocks[0] = head_block_text

    for raw_block in blocks:
        lines = [ln.rstrip() for ln in raw_block.split("\n")]
        clean = [ln for ln in lines if not _is_ui_noise(ln)]
        if len(clean) < 2:
            continue

        # First non-noise line is the author. Filter out "Recent activity" and "SORT".
        if clean[0].lower() in ("recent activity", "sort"):
            clean = clean[1:]
        if not clean:
            continue
        author = clean[0]
        # Author must look like a person's name:
        #   - 2-60 chars
        #   - not ending in punctuation like "," "&" "..."
        #   - doesn't contain digits or common group/place markers
        if len(author) > 60 or len(author) < 2:
            continue
        if author[-1] in ",&.;:-/":
            continue
        if re.search(r"\d", author):
            continue
        if any(kw in author.lower() for kw in ("community", "members", "group", "page", "watch", "forum", "facebay", "sell", "buy")):
            continue
        # Names usually contain a space (first + surname). Single tokens often
        # leak from FB UI ("Photo", "Feeling", "Invite"). Allow single-word
        # only if it looks human (starts capital, all letters).
        if " " not in author and not (author[0].isupper() and author.isalpha()):
            continue

        # Skip lines that look like time markers right after author
        body_lines = []
        for ln in clean[1:]:
            # Drop lines that are just "Xh" / "Xd" / etc. (timestamps)
            if re.match(r"^[\d]+[hdwmy]$", ln.strip()):
                continue
            body_lines.append(ln)

        body = "\n".join(body_lines).strip()
        if len(body) < 15:
            continue

        permalink = permalinks[perm_idx] if perm_idx < len(permalinks) else group_url
        perm_idx += 1

        posts.append({"author": author, "text": body, "permalink": permalink})

    return posts


async def run_monitor(dry_run: bool = False, reseed: bool = False):
    from playwright.async_api import async_playwright

    config = load_config()
    seen = load_seen()
    sent = 0
    skipped_seen = 0
    skipped_filter = 0

    if not STORAGE_STATE_PATH.exists():
        log(f"❌ No storage_state.json at {STORAGE_STATE_PATH}")
        log("   Run --login on your Mac first to create it.")
        return

    # Randomised startup delay so cron-fired runs don't line up perfectly
    # with their schedule — breaks easy pattern detection by FB.
    if not dry_run:
        jitter_max = config.get("polling", {}).get("startup_jitter_seconds", 180)
        delay = random.randint(0, jitter_max)
        if delay > 0:
            log(f"⏳ Startup jitter: sleeping {delay}s before polling")
            await asyncio.sleep(delay)

    log(f"🔍 Starting FB monitor (dry_run={dry_run})")
    log(f"   Groups: {len(config['groups'])}  |  Seen-post cache: {len(seen)}")

    async with async_playwright() as p:
        # Use Firefox-ish UA to look less like default headless Chromium
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            storage_state=str(STORAGE_STATE_PATH),
            viewport={"width": 412, "height": 869},
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) "
                       "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 "
                       "Mobile/15E148 Safari/604.1",
            locale="en-GB",
        )
        page = await context.new_page()

        # Jitter the group order — looks less robotic
        groups = list(config["groups"])
        random.shuffle(groups)

        for g in groups:
            group_url = g["url"]
            label = g.get("label") or group_url.split("/groups/")[-1].rstrip("/")
            log(f"📂 {label}")

            try:
                posts = await extract_posts_from_group(
                    page,
                    group_url,
                    max_posts=config["polling"]["max_posts_per_group"],
                )
                log(f"  📜 Found {len(posts)} candidate posts")

                for raw in posts:
                    text = raw.get("text", "")
                    if not text:
                        continue

                    keys = post_dedup_keys(group_url, text, raw.get("permalink", ""))
                    if not keys:
                        # Too little durable text to fingerprint (image-only
                        # post or a parser mis-grab like a bare timestamp).
                        # Alerting would mean unstoppable repeats — skip.
                        skipped_filter += 1
                        continue
                    if any(k in seen for k in keys):
                        skipped_seen += 1
                        continue

                    if reseed:
                        # Baseline pass: record every visible post as seen
                        # WITHOUT alerting, so switching dedup schemes doesn't
                        # produce one final wave of duplicate alerts.
                        seen.update(keys)
                        skipped_seen += 1
                        continue

                    ok, trade = matches_filters(text, config)
                    if not ok:
                        # Mark all keys so we don't re-evaluate this post next poll
                        seen.update(keys)
                        skipped_filter += 1
                        continue

                    # It's a lead. Draft and send.
                    drafted = draft_reply(text, author_name=raw.get("author", ""))
                    post = {
                        "group_url": group_url,
                        "group_label": label,
                        "author": raw.get("author", ""),
                        "text": text,
                        "permalink": raw.get("permalink", group_url),
                    }
                    msg = format_alert(post, drafted)

                    if dry_run:
                        log(f"  🔔 [DRY] Would alert: {text[:80]}")
                        print("\n" + "=" * 60)
                        print(msg)
                        print("=" * 60 + "\n")
                    else:
                        if send_telegram(msg):
                            # Follow up with the services banner so Wes can
                            # reply with text + image in one move.
                            send_telegram_photo(
                                BANNER_PATH,
                                caption="🖼 Attach this to your Facebook reply",
                            )
                            log(f"  ✅ Alert sent: {text[:80]}")
                            sent += 1

                    # Always add BOTH keys after alerting — so future polls
                    # dedup whether they match via permalink or text-hash
                    seen.update(keys)

            except Exception as e:
                log(f"  ❌ Error processing {label}: {e}")

            # Per-group jitter to look less robotic
            await asyncio.sleep(random.uniform(3.0, 8.0))

        await browser.close()

    save_seen(seen)
    log(f"\n📊 Done. Alerts sent: {sent}  |  Skipped (seen): {skipped_seen}  "
        f"|  Skipped (no match): {skipped_filter}")


# ----- one-time login on the Mac --------------------------------------------

async def run_login():
    """Open a visible Chromium window. Wes logs in to Facebook normally.
    When done, presses Enter in the terminal and we save the session state."""
    from playwright.async_api import async_playwright

    log("🔐 Opening Chromium for Facebook login...")
    log("   1. Log in to Facebook in the browser window that just opened")
    log("   2. Once you see your normal Facebook feed, come back here")
    log("   3. Press Enter to save the session\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 412, "height": 869},
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) "
                       "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 "
                       "Mobile/15E148 Safari/604.1",
            locale="en-GB",
        )
        page = await context.new_page()
        await page.goto("https://m.facebook.com/login")

        # Block until Wes confirms
        input("\n   Press Enter once you're logged in and see your feed... ")

        await context.storage_state(path=str(STORAGE_STATE_PATH))
        log(f"✅ Session saved to {STORAGE_STATE_PATH}")
        log("   Upload this file to the VPS at the same path, then run --dry-run.")
        await browser.close()


def test_telegram():
    msg = (
        "🧪 <b>Test alert from BCW lead monitor</b>\n\n"
        "If you see this, Telegram delivery is working.\n"
        f"Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    ok = send_telegram(msg)
    print("✅ Telegram test sent" if ok else "❌ Telegram test failed — check creds")


# ----- main -----------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Better Call Wes FB group lead monitor")
    parser.add_argument("--login",         action="store_true", help="One-time visible-browser login (run on Mac)")
    parser.add_argument("--run",           action="store_true", help="Headless poll + Telegram alerts (run via cron on VPS)")
    parser.add_argument("--dry-run",       action="store_true", help="Headless poll, print to stdout only")
    parser.add_argument("--reseed",        action="store_true", help="Record all visible posts as seen WITHOUT alerting (run once after dedup changes)")
    parser.add_argument("--test-telegram", action="store_true", help="Send a one-shot test alert")
    args = parser.parse_args()

    if args.test_telegram:
        test_telegram()
    elif args.login:
        asyncio.run(run_login())
    elif args.reseed:
        asyncio.run(run_monitor(dry_run=False, reseed=True))
    elif args.run:
        asyncio.run(run_monitor(dry_run=False))
    elif args.dry_run:
        asyncio.run(run_monitor(dry_run=True))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
