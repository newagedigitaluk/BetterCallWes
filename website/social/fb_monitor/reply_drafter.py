"""
Generate a tailored reply for a Facebook group lead post.

Six-point format (from research/content/local-trade-social-playbook.md):
  1. Name: first name from the post author
  2. Empathy: one phrase acknowledging the specific problem
  3. Credential: Gas Safe engineer / plumber, local to Southampton
  4. Action: what to WhatsApp and what Wes will do next
  5. Urgency: availability language calibrated to real urgency (weekday only)
  6. Sign-off: short URL for the relevant service + name + phone

V1: template-based with keyword routing. Fast, deterministic, no LLM cost.
V2 (later): swap _draft_reply for a Claude Haiku call for more nuanced replies
when the post is ambiguous.

The drafted reply ALWAYS:
- Sounds like a real person (Wes), not a bot
- Includes a Linke short URL for click attribution
- Includes Wes's WhatsApp number for direct contact
- Stays under ~300 chars (FB group replies that are too long get scrolled past)
- Never mentions VAT (per project rule) or the Gas Safe reg number
"""

import random


# Short links: match the generic_short_links created in content_bank.json
SHORT = {
    "boiler-repair":   "https://u.bettercallwes.co.uk/boiler-repair",
    "boiler-service":  "https://u.bettercallwes.co.uk/boiler-service",
    "boiler-install":  "https://u.bettercallwes.co.uk/boiler-install",
    "power-flush":     "https://u.bettercallwes.co.uk/power-flush",
    "gas-safety":      "https://u.bettercallwes.co.uk/gas-safety",
    "cp12":            "https://u.bettercallwes.co.uk/cp12",
    "plumbing":        "https://u.bettercallwes.co.uk/plumbing",
    "radiators":       "https://u.bettercallwes.co.uk/radiators",
    "tap-repair":      "https://u.bettercallwes.co.uk/tap-repair",
    "pipe-leak":       "https://u.bettercallwes.co.uk/pipe-leak",
    "shower-repair":   "https://u.bettercallwes.co.uk/shower-repair",
    "toilet-repair":   "https://u.bettercallwes.co.uk/toilet-repair",
    "smart-controls":  "https://u.bettercallwes.co.uk/smart-controls",
}

PHONE = "07700 155 655"
WA    = "wa.me/447700155655"

# Topic detection: ordered, first match wins (most specific first)
TOPIC_RULES = [
    # (keywords_to_match_any_of, service_slug)
    (["no hot water", "no heat", "no heating", "boiler not working", "boiler broken", "boiler stopped"], "boiler-repair"),
    (["boiler service", "annual service", "service my boiler"],   "boiler-service"),
    (["new boiler", "replace boiler", "boiler quote", "boiler install"], "boiler-install"),
    (["power flush", "powerflush", "magnacleanse", "sludge", "system flush"], "power-flush"),
    (["cp12", "landlord cert", "landlord certificate", "gas certificate"], "cp12"),
    (["gas safety", "gas safe", "gas check", "gas inspection"], "gas-safety"),
    (["radiator", "cold rad", "rads cold", "bleed"],            "radiators"),
    (["burst pipe", "pipe leak", "leaking pipe", "water leak"], "pipe-leak"),
    (["dripping tap", "leaking tap", "tap problem"],            "tap-repair"),
    (["shower", "thermostatic"],                                "shower-repair"),
    (["toilet", "loo", "cistern"],                              "toilet-repair"),
    (["smart thermostat", "hive", "nest", "tado"],              "smart-controls"),
    # fallback
    (["boiler", "heating"], "boiler-repair"),
    (["plumb", "plumber"],  "plumbing"),
]

# Point 1: Name openers (rotate to avoid sounding canned across many replies)
OPENERS = [
    "Hi {name},\n",
    "Hey {name},\n",
    "Hi {name},\n",
    "Hi {name},\n",
]

# Point 2: Empathy, topic-specific acknowledgement of the problem
EMPATHY = {
    "boiler-repair":   "Sorry to hear the boiler's out. No heating is rough.",
    "boiler-service":  "Happy to help sort your annual service.",
    "boiler-install":  "Happy to help with a new boiler. I'll give you an honest quote.",
    "power-flush":     "Sludge and cold radiators are frustrating. I can sort that.",
    "cp12":            "Happy to help with the certificate.",
    "gas-safety":      "Happy to help with the gas safety check.",
    "radiators":       "Cold or uneven radiators are usually a quick fix.",
    "pipe-leak":       "Sorry to hear about the leak. Turn off the stopcock if you haven't already.",
    "tap-repair":      "Dripping taps are annoying. Usually just a cartridge or washer.",
    "shower-repair":   "Sorry to hear the shower's playing up.",
    "toilet-repair":   "Sorry to hear the toilet is giving you trouble.",
    "smart-controls":  "Happy to help with the thermostat install.",
    "plumbing":        "Happy to help with this.",
}

# Point 3 + 4: Credential + Action
BODIES = {
    "boiler-repair":   "Gas Safe engineer in Southampton. WhatsApp me a quick video of the boiler ({wa}) and I'll diagnose before I come out so I bring the right parts.",
    "boiler-service":  "Gas Safe engineer in Southampton. Annual service covers full combustion + safety checks. WhatsApp me ({wa}) for a slot.",
    "boiler-install":  "Gas Safe engineer in Southampton. WhatsApp ({wa}) a photo of your current boiler + space and I'll send a price.",
    "power-flush":     "Gas Safe engineer in Southampton. I do power flushes with proper kit. WhatsApp me ({wa}) and I'll talk you through it.",
    "cp12":            "Gas Safe engineer in Southampton. Full inspection, certificate issued same day. WhatsApp the property address ({wa}) and I'll fit you in.",
    "gas-safety":      "Gas Safe engineer in Southampton. Full check and certificate same day. WhatsApp ({wa}) to book.",
    "radiators":       "Gas Safe engineer in Southampton. WhatsApp me a photo ({wa}) and I'll tell you what's involved.",
    "pipe-leak":       "Plumber in Southampton. WhatsApp me a video ({wa}) and I'll tell you what's needed.",
    "tap-repair":      "Plumber in Southampton. WhatsApp me ({wa}) and I can pop round.",
    "shower-repair":   "Plumber in Southampton. WhatsApp me ({wa}) with what's happening and I'll sort it.",
    "toilet-repair":   "Plumber in Southampton. WhatsApp me ({wa}) and I'll get back to you with a price.",
    "smart-controls":  "Heating engineer in Southampton, install Hive/Nest/Tado regularly. WhatsApp me ({wa}) and I'll quote you.",
    "plumbing":        "Local plumber in Southampton. WhatsApp me ({wa}) with a photo and I'll get back to you fast.",
}

# Urgency detection: GENUINE emergencies only. This gates the "I can come
# today" language, so it must not fire on soft words. The old list included
# "help", "kids", "baby", "winter", "today", which flagged most posts urgent
# and put same-day promises in replies Wes couldn't always honour.
URGENT = [
    "urgent", "emergency", "asap", "no heating", "no hot water", "no heat",
    "burst", "flooding", "water everywhere", "pouring", "gushing",
    "gas leak", "smell gas", "smell of gas",
]


def detect_topic(text: str) -> str:
    """Return the service slug that best matches the post text."""
    t = text.lower()
    for keywords, slug in TOPIC_RULES:
        if any(k in t for k in keywords):
            return slug
    return "plumbing"  # safe default


def detect_urgency(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in URGENT)


def detect_name(text: str, fallback: str = "") -> str:
    """Heuristic: try to grab the poster's first name from common openers."""
    # If we get the author name from the scraper, use it; otherwise generic.
    return fallback.split()[0] if fallback else ""


def draft_reply(
    post_text: str,
    author_name: str = "",
    location_hint: str = "",
) -> dict:
    """
    Generate a tailored reply using the six-point format.

    Six points: name → empathy → credential → action → urgency → sign-off.

    Returns:
        {
          "topic":     detected service slug,
          "urgent":    bool,
          "short_url": Linke short URL chosen for this reply,
          "reply":     the full reply text ready to copy/paste,
          "points":    dict of the six individual point strings (for display)
        }
    """
    topic = detect_topic(post_text)
    urgent = detect_urgency(post_text)
    short_url = SHORT.get(topic, SHORT["plumbing"])

    first_name = detect_name(post_text, author_name)

    # Point 1: Name
    if first_name:
        p1_name = random.choice(OPENERS).format(name=first_name)
    else:
        p1_name = "Hi,\n"

    # Point 2: Empathy
    p2_empathy = EMPATHY[topic]

    # Point 3 + 4: Credential + Action (combined, naturally reads as one sentence)
    p34_body = BODIES[topic].format(wa=WA)

    # Point 5: Urgency close
    from datetime import datetime
    is_weekend = datetime.now().weekday() >= 5  # Sat/Sun
    if urgent and not is_weekend:
        p5_urgency = "This sounds urgent. I can come today if needed. Message me now and I'll confirm."
    elif urgent and is_weekend:
        p5_urgency = "Message me now. I'll see what I can do, worst case book you in first thing next week."
    else:
        p5_urgency = "No pressure, happy to help whenever suits you."

    # Point 6: Sign-off
    p6_signoff = f"More info: {short_url} | Wes, {PHONE}"

    reply = (
        f"{p1_name}{p2_empathy}\n"
        f"{p34_body}\n\n"
        f"{p5_urgency}\n\n"
        f"{p6_signoff}"
    )

    return {
        "topic": topic,
        "urgent": urgent,
        "short_url": short_url,
        "reply": reply,
        "points": {
            "1_name":       p1_name.strip(),
            "2_empathy":    p2_empathy,
            "3_credential": p34_body,
            "5_urgency":    p5_urgency,
            "6_signoff":    p6_signoff,
        },
    }


if __name__ == "__main__":
    # Smoke test
    samples = [
        ("Sarah Jones", "My boiler stopped working last night and we have no heating, anyone recommend a plumber?"),
        ("Mike Smith", "Looking for a Gas Safe engineer for a CP12 certificate on my rental in Eastleigh, urgent please"),
        ("Anna Brown", "Hi everyone, my radiator is cold at the top but warm at the bottom, anyone know what's wrong?"),
        ("Tom Lee", "Burst pipe under sink HELP, water everywhere"),
    ]
    for author, post in samples:
        r = draft_reply(post, author_name=author)
        print(f"\n--- {author}: {post[:60]}... ---")
        print(f"Topic: {r['topic']}  |  Urgent: {r['urgent']}  |  Link: {r['short_url']}")
        print(r['reply'])
