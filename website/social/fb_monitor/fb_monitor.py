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
  --replay N        Re-run the keyword filter and the LLM gate over the last N
                    alerts recorded in fb_monitor.log. Sends nothing; prints a
                    markdown table of what would pass now.
  --gate-test TEXT  Run one post through the keyword filter and the gate.

Files
-----
  config.json                    polling config + groups + keywords + gate
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


# Seen-post state is a dict {key: first_seen_iso}. Until 2026-10-24 it was a
# set capped at 5,000 with `list(seen)[-5000:]`; a set has no order, so every
# save threw away 200-odd RANDOM keys, including posts seen minutes earlier.
# That is why one post alerted six times in ten hours. Now the OLDEST go first
# and the cap is high enough that nothing ages out for months (50k keys is a
# ~2 MB file).
SEEN_CAP = 50_000


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_seen() -> dict:
    """Load {key: first_seen}. A legacy list is migrated in place on the next
    save; every legacy key gets the file's updated_at as its first_seen so the
    whole old set ages out before anything written from now on."""
    if not SEEN_PATH.exists():
        return {}
    try:
        data = json.loads(SEEN_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}
    seen = data.get("seen", {})
    if isinstance(seen, dict):
        return seen
    stamp = data.get("updated_at") or _now_iso()
    return {k: stamp for k in seen}


def mark_seen(seen: dict, keys) -> None:
    for k in keys:
        seen.setdefault(k, _now_iso())


def save_seen(seen: dict):
    if len(seen) > SEEN_CAP:
        # Drop the oldest first_seen; ties keep insertion order (dicts are ordered)
        kept = sorted(seen.items(), key=lambda kv: kv[1])[-SEEN_CAP:]
        seen = dict(kept)
    SEEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = SEEN_PATH.with_suffix(".json.tmp")
    tmp.write_text(
        json.dumps({"seen": seen, "updated_at": _now_iso()}, indent=0),
        encoding="utf-8",
    )
    tmp.replace(SEEN_PATH)


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


# Letters of durable text that go into the fingerprint. The mobile feed cuts a
# long post at "…See more", and the cut lands a character or two apart from
# poll to poll because the timestamp in front of it changes width ("this
# week,  " one poll, "this week, p" the next). 160 letters reached past that
# cut on long posts, so the same post hashed differently; 90 stays well short
# of it while still being far more than 25 letters of real words.
FP_LETTERS = 90
_LEGACY_FP_LETTERS = 160  # keys written before 2026-10-24, looked up but no longer written


def stable_fingerprint(post_text: str, letters: int = FP_LETTERS) -> str:
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
    return re.sub(r"[^a-z]", "", t.lower())[:letters]


def _fp_key(fp: str) -> str:
    return "fp:" + hashlib.sha256(fp.encode("utf-8")).hexdigest()[:20]


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
        keys.append(_fp_key(fp))
    return keys


def legacy_dedup_keys(post_text: str) -> list[str]:
    """The 160-letter key the seen file was built on until 2026-10-24. Checked
    on lookup only, so posts seen before the change stay seen; never written."""
    fp = stable_fingerprint(post_text, _LEGACY_FP_LETTERS)
    return [_fp_key(fp)] if len(fp) >= 25 else []


# ----- filter ---------------------------------------------------------------

def _kw_present(text: str, kw: str) -> bool:
    """Whole-word(ish) match so 'tap' doesn't fire on 'tap the link' etc."""
    return re.search(r"(?<![a-z])" + re.escape(kw) + r"(?![a-z])", text) is not None


def _spans(text: str, term: str) -> list[tuple[int, int]]:
    """Whole-word spans of a term. A trailing '*' in the config means prefix
    match ('repair*' hits repairs/repaired), otherwise both ends must be word
    boundaries so 'need a' no longer fires on 'need any' and 'fit ' on 'benefit'."""
    term = term.strip()
    prefix = term.endswith("*")
    core = re.escape(term.rstrip("*").strip())
    pat = r"(?<![a-z])" + core + ("" if prefix else r"(?![a-z])")
    return [(m.start(), m.end()) for m in re.finditer(pat, text)]


def _words_between(text: str, a: tuple[int, int], b: tuple[int, int]) -> int:
    lo, hi = (a, b) if a[0] <= b[0] else (b, a)
    if lo[1] >= hi[0]:
        return 0
    return len(text[lo[1]:hi[0]].split())


def filter_detail(text: str, config: dict) -> dict:
    """Everything the keyword tiers see in a post, with no verdict attached.

    Returns {excluded, strong, weak, intent, near} where `near` is the list of
    (weak, intent) pairs that sit within filters.weak_intent_max_words of each
    other. --replay prints this so a false positive shows WHICH pair fired.
    """
    t = text.lower()
    kw = config["keywords"]
    filters = config.get("filters", {})
    window = filters.get("weak_intent_max_words", 6)

    excluded = [ex for ex in kw.get("exclude", []) if ex in t]
    strong = [k for k in kw.get("strong", []) if _spans(t, k)]
    weak_spans = {k: _spans(t, k) for k in kw.get("weak", [])}
    weak_spans = {k: v for k, v in weak_spans.items() if v}
    intent_spans = {p: _spans(t, p) for p in kw.get("intent", [])}
    intent_spans = {p: v for p, v in intent_spans.items() if v}

    near = []
    for w, ws in weak_spans.items():
        for p, ps in intent_spans.items():
            if any(_words_between(t, a, b) <= window for a in ws for b in ps):
                near.append((w, p.rstrip("*")))
    return {
        "excluded": excluded,
        "strong": strong,
        "weak": list(weak_spans),
        "intent": [p.rstrip("*") for p in intent_spans],
        "near": near,
    }


def matches_filters(text: str, config: dict) -> tuple[bool, list]:
    """Keyword tiers. Returns (is_lead, matched_terms).

    Tiers (from config['keywords']):
      strong  — specific plumbing/heating terms; match on their own.
      weak    — broad/ambiguous words (gas, tap, shower, pressure). Count only
                when an INTENT phrase sits within a few words of the weak term
                ("recommend someone to replace a gas hob"), or when two
                different weak terms AND an intent phrase appear anywhere.
                A weak term and an intent phrase at opposite ends of a long
                post is how a cat-sitter request got through.
      intent  — service-request signals (recommend, anyone know, looking for…).
                Whole-word; a trailing '*' allows a prefix match.
      exclude — hard-reject phrases; if any is present the post is dropped even
                if a keyword matched (energy-bill chat, for-sale posts, etc.).

    Every match then goes through llm_gate() before an alert is sent.
    Falls back to the legacy flat 'trade' list if strong/weak aren't configured.
    """
    kw = config["keywords"]
    filters = config.get("filters", {})
    if len(text) < filters.get("min_post_length_chars", 25):
        return False, []

    # Legacy mode (flat list) — kept for safety if config not migrated
    if "strong" not in kw:
        t = text.lower()
        if any(ex in t for ex in kw.get("exclude", [])):
            return False, []
        trade = [k for k in kw.get("trade", []) if _kw_present(t, k)]
        return (bool(trade), trade)

    d = filter_detail(text, config)
    if d["excluded"]:
        return False, []
    if d["strong"]:
        return True, d["strong"]
    if d["near"]:
        w, p = d["near"][0]
        return True, [w, f"+intent:{p}"]
    min_weak = filters.get("min_weak_terms_without_proximity", 2)
    if len(d["weak"]) >= min_weak and d["intent"]:
        return True, d["weak"] + [f"+intent:{d['intent'][0]}"]
    return False, []


# ----- LLM gate ---------------------------------------------------------------
# The keyword tiers are cheap but blunt: "shower" + "looking for" is also an
# electrician's job, and "plumbing" is also a Level 2 student saying hello.
# One Haiku call per keyword match (a handful a day) answers the only question
# that matters before Wes's phone buzzes.

GATE_SYSTEM = (
    "You screen Facebook group posts for Wes, a sole-trader Gas Safe registered "
    "plumber and heating engineer in Southampton. He does boiler repairs and "
    "servicing, gas work (hobs, cookers, gas safety certificates), plumbing "
    "repairs (taps, toilets, leaks, showers, pipework, bathrooms), radiators and "
    "heating, and blocked drains. He is not an electrician, roofer, builder, "
    "tiler, handyman or gutter cleaner.\n\n"
    "Answer yes only if the post is a request for plumbing, heating, gas or "
    "drainage work that a Gas Safe plumber could quote for, posted by a customer "
    "or someone acting for one. A post that asks for a plumber alongside another "
    "trade is still a yes. Answer no for: tradespeople advertising their own "
    "services; people looking for work, apprenticeships or training; students "
    "introducing themselves; items for sale or wanted; complaints or chat about "
    "companies, deliveries or bills; requests for other trades where no plumbing, "
    "heating, gas or drainage work is involved; posts too short or vague to tell.\n\n"
    "Reply with one word: yes or no."
)
_GATE_MAX_CHARS = 1500


def _read_env_value(path: Path, name: str) -> str | None:
    """Read one NAME=value line from an env file without sourcing it."""
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith(name + "="):
                return line.split("=", 1)[1].strip().strip('"').strip("'") or None
    except Exception:
        return None
    return None


def _anthropic_api_key(config: dict) -> str | None:
    """ANTHROPIC_API_KEY from the environment, else from the env file named in
    config.gate.api_key_file. The key stays where the registry says it lives;
    this reads it in-process, the same way mail-notify reads its Emailit key."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key
    path = (config.get("gate") or {}).get("api_key_file")
    if not path:
        return None
    return _read_env_value(Path(os.path.expanduser(path)), "ANTHROPIC_API_KEY")


def gate_input(text: str) -> str:
    """The post as the model should see it: glyphs out, whitespace folded."""
    t = _PUA.sub(" ", text or "")
    t = re.sub(r"[​-‏‪-‮]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:_GATE_MAX_CHARS]


_gate_client = None


def llm_gate(text: str, config: dict) -> tuple[str, str]:
    """Ask the model whether the post is quotable plumbing/heating/gas/drainage
    work. Returns (verdict, detail) with verdict one of 'yes', 'no', 'error',
    'off'. The caller decides what 'error' means (config.gate.on_error)."""
    global _gate_client
    gate = config.get("gate") or {}
    if not gate.get("enabled", True):
        return "off", "gate disabled in config"
    try:
        import anthropic
    except ImportError:
        return "error", "anthropic SDK not installed"
    key = _anthropic_api_key(config)
    if not key:
        return "error", "no ANTHROPIC_API_KEY (env or config.gate.api_key_file)"
    try:
        if _gate_client is None:
            _gate_client = anthropic.Anthropic(api_key=key, timeout=20.0, max_retries=2)
        resp = _gate_client.messages.create(
            model=gate.get("model", "claude-haiku-5-5"),
            max_tokens=8,
            thinking={"type": "disabled"},
            output_config={"effort": "low"},
            system=GATE_SYSTEM,
            messages=[{"role": "user", "content": "Post:\n" + gate_input(text)}],
        )
        answer = "".join(b.text for b in resp.content if b.type == "text").strip().lower()
        if answer.startswith("yes"):
            return "yes", answer
        if answer.startswith("no"):
            return "no", answer
        return "error", f"unparseable answer: {answer[:40]!r} (stop={resp.stop_reason})"
    except Exception as e:  # auth, network, 4xx/5xx after retries
        return "error", f"{type(e).__name__}: {str(e)[:160]}"


def gate_allows(verdict: str, config: dict) -> bool:
    """'yes' alerts, 'no' doesn't. On 'error' the default is to alert anyway
    (config.gate.on_error = "alert") so an expired key degrades to the old
    behaviour loudly rather than dropping real leads silently; set it to
    "drop" to prefer silence."""
    if verdict in ("yes", "off"):
        return True
    if verdict == "no":
        return False
    return (config.get("gate") or {}).get("on_error", "alert") == "alert"


def one_line(text: str, limit: int = 700) -> str:
    """Post text for the log: one line, glyphs stripped, so --replay can read
    it back in full instead of the 80 characters the old log line kept."""
    return gate_input(text)[:limit]


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
    """Lead alert to Wes. Telegram was retired 2026-10-24; this now emails the
    alert through ~/.local/bin/mail-notify (plain text, so the Telegram HTML
    tags are stripped first). Function name kept so callers are unchanged."""
    import html as _html
    import re as _re
    import subprocess
    plain = _html.unescape(_re.sub(r"<[^>]+>", "", text))
    try:
        r = subprocess.run([str(Path.home() / ".local" / "bin" / "mail-notify"), f"BCW lead: {plain}"],
                           capture_output=True, text=True, timeout=45)
        if r.returncode != 0:
            log(f"  ❌ alert send failed: {r.stderr.strip()[:200]}")
        return r.returncode == 0
    except Exception as e:
        log(f"  ❌ alert error: {e}")
        return False


def send_telegram_photo(photo_path, caption: str = "") -> bool:
    """The services banner used to follow each alert as a Telegram photo. The
    email channel has no photo send, so this is a deliberate no-op; the banner
    stays at reply_banners/ for Wes to attach by hand."""
    return False


def _esc(s: str) -> str:
    """Escape HTML special chars so post text can't break Telegram parsing."""
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def format_alert(post: dict, drafted: dict) -> str:
    """HTML-formatted Telegram alert, built for a 15-second reply:
    lead → tap-to-copy reply → link. Reply is the hero, at the top."""
    urgent_tag = "🚨 <b>URGENT LEAD</b>\n" if drafted["urgent"] else "🔧 <b>New lead</b>\n"
    if post.get("gate") == "error":
        urgent_tag = urgent_tag.rstrip("\n") + " (unchecked: lead gate unavailable)\n"
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
    gated_out = 0

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
                    if any(k in seen for k in keys + legacy_dedup_keys(text)):
                        skipped_seen += 1
                        continue

                    if reseed:
                        # Baseline pass: record every visible post as seen
                        # WITHOUT alerting, so switching dedup schemes doesn't
                        # produce one final wave of duplicate alerts.
                        mark_seen(seen, keys)
                        skipped_seen += 1
                        continue

                    ok, trade = matches_filters(text, config)
                    if not ok:
                        # Mark all keys so we don't re-evaluate this post next poll
                        mark_seen(seen, keys)
                        skipped_filter += 1
                        continue

                    # Keyword match. Ask the model before anyone's phone buzzes.
                    verdict, detail = llm_gate(text, config)
                    tags = f"[terms: {', '.join(trade)}] [gate: {verdict}]"
                    if verdict == "error":
                        log(f"  ⚠️  lead gate error: {detail}")
                    if not gate_allows(verdict, config):
                        log(f"  🚫 Gate said no {tags} :: {one_line(text)}")
                        mark_seen(seen, keys)
                        gated_out += 1
                        continue

                    # It's a lead. Draft and send.
                    drafted = draft_reply(text, author_name=raw.get("author", ""))
                    post = {
                        "group_url": group_url,
                        "group_label": label,
                        "author": raw.get("author", ""),
                        "text": text,
                        "permalink": raw.get("permalink", group_url),
                        "gate": verdict,
                    }
                    msg = format_alert(post, drafted)

                    if dry_run:
                        log(f"  🔔 [DRY] Would alert {tags} :: {one_line(text)}")
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
                            log(f"  ✅ Alert sent {tags} :: {one_line(text)}")
                            sent += 1

                    # Always add BOTH keys after alerting — so future polls
                    # dedup whether they match via permalink or text-hash
                    mark_seen(seen, keys)

            except Exception as e:
                log(f"  ❌ Error processing {label}: {e}")

            # Per-group jitter to look less robotic
            await asyncio.sleep(random.uniform(3.0, 8.0))

        await browser.close()

    save_seen(seen)
    log(f"\n📊 Done. Alerts sent: {sent}  |  Skipped (seen): {skipped_seen}  "
        f"|  Skipped (no match): {skipped_filter}  |  Gate said no: {gated_out}")


# ----- replay ----------------------------------------------------------------

_ALERT_LINE = re.compile(
    r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]\s+\S*\s*(?:Alert sent|\[DRY\] Would alert)"
    r"(?P<tags>(?: \[[^\]]*\])*)\s*(?::: |: )(?P<text>.*)$"
)


def read_logged_alerts(n: int) -> list[dict]:
    """The last n alerts in fb_monitor.log, oldest first.

    Two formats live in the log. Before 2026-10-24 the line was
    `✅ Alert sent: <first 80 chars>` and the post's own newlines spilled onto
    the following lines, so those rows carry an 80-character excerpt and are
    marked partial. From 2026-10-24 it is
    `✅ Alert sent [terms: …] [gate: …] :: <whole post on one line>`.
    """
    if not LOG_PATH.exists():
        return []
    lines = LOG_PATH.read_text(encoding="utf-8", errors="replace").split("\n")
    out = []
    i = 0
    while i < len(lines):
        m = _ALERT_LINE.match(lines[i])
        if not m:
            i += 1
            continue
        text = m.group("text")
        partial = " :: " not in lines[i]
        j = i + 1
        if partial:
            # legacy: gather spilled continuation lines until the next log line
            while j < len(lines) and not re.match(r"^\[\d{4}-\d{2}-\d{2} ", lines[j]):
                text += "\n" + lines[j]
                j += 1
        out.append({"ts": m.group(1), "text": text, "partial": partial,
                    "tags": m.group("tags").strip()})
        i = j
    return out[-n:]


def replay(n: int, config: dict | None = None, use_gate: bool = True) -> list[dict]:
    """Re-run the keyword filter and the gate over the last n logged alerts.
    Sends nothing, writes nothing. Returns rows and prints a markdown table."""
    config = config or load_config()
    rows = read_logged_alerts(n)
    cache: dict[str, tuple[str, str]] = {}
    for r in rows:
        text = gate_input(r["text"])
        # the old log line started with the post's relative timestamp ("44m")
        text = _TIMESTAMP.sub("", text, count=1).strip()
        d = filter_detail(text, config)
        ok, trade = matches_filters(text, config)
        if ok and use_gate:
            if text not in cache:
                cache[text] = llm_gate(text, config)
            verdict, _ = cache[text]
        else:
            verdict = "-"
        r.update({
            "excerpt": text,
            # Legacy rows hold 80 characters of the post, so the weak term that
            # fired may lie beyond the excerpt: shown as "?" then.
            "fired_on": (", ".join(d["strong"]) if d["strong"]
                         else ", ".join(f"{w} + {p}" for w, p in d["near"][:2])
                         or ((", ".join(d["weak"]) or "?") + " + " + d["intent"][0] if d["intent"] else "")),
            "excluded": ", ".join(d["excluded"]),
            "keywords_now": "pass" if ok else "drop",
            "gate": verdict,
            "final": "alert" if ok and gate_allows(verdict, config) else "drop",
        })

    print("| When | Post (as logged) | Old rule fired on | Keywords now | Gate | Result |")
    print("|---|---|---|---|---|---|")
    for r in rows:
        ex = r["excerpt"][:90].replace("|", "/") + ("…" if r["partial"] or len(r["excerpt"]) > 90 else "")
        why = r["fired_on"] or "-"
        if r["excluded"]:
            why += f" (now excluded: {r['excluded']})"
        print(f"| {r['ts'][5:16]} | {ex} | {why} | {r['keywords_now']} | {r['gate']} | {r['final']} |")
    kept = sum(1 for r in rows if r["final"] == "alert")
    print(f"\n{len(rows)} alerts replayed; {kept} would alert now, {len(rows) - kept} would not.")
    return rows


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
    parser.add_argument("--replay",        type=int, metavar="N", help="Re-run filter + gate over the last N logged alerts, send nothing")
    parser.add_argument("--no-gate",       action="store_true", help="With --replay: keyword filter only, no model calls")
    parser.add_argument("--gate-test",     metavar="TEXT", help="Run one post through the filter and the gate")
    args = parser.parse_args()

    if args.replay:
        replay(args.replay, use_gate=not args.no_gate)
    elif args.gate_test:
        config = load_config()
        ok, trade = matches_filters(args.gate_test, config)
        print(f"keywords: {'pass' if ok else 'drop'} {trade}  detail={filter_detail(args.gate_test, config)}")
        print("gate:", llm_gate(args.gate_test, config))
    elif args.test_telegram:
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
