"""
Generate a tailored reply for a Facebook group lead post.

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


# Short links — match the generic_short_links created in content_bank.json
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

# Topic detection: ordered — first match wins (most specific first)
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

# Reply openers — rotate to avoid sounding canned across many replies
OPENERS = [
    "Hi {name}, ",
    "Hey {name}, ",
    "{name} — ",
    "Hi {name}, sorry to hear that. ",
    "Hi {name}, ",
]

# Urgency detection — GENUINE emergencies only. This gates the "I can come
# today" language, so it must not fire on soft words. The old list included
# "help", "kids", "baby", "winter", "today" — which flagged most posts urgent
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
    Generate a tailored reply.

    Returns:
        {
          "topic":   detected service slug,
          "urgent":  bool,
          "short_url": Linke short URL chosen for this reply,
          "reply":   the full reply text ready to copy/paste
        }
    """
    topic = detect_topic(post_text)
    urgent = detect_urgency(post_text)
    short_url = SHORT.get(topic, SHORT["boiler-repair"])

    first_name = detect_name(post_text, author_name)
    if first_name:
        opener = random.choice(OPENERS).format(name=first_name).replace("  ", " ")
        # Ensure single trailing space
        opener = opener.rstrip() + " "
    else:
        opener = "Hi, "

    # Topic-specific body, kept SHORT (FB group replies that are long get scrolled past)
    BODIES = {
        "boiler-repair":   "Gas Safe engineer here in Southampton — happy to take a look. WhatsApp me a quick video of the boiler ({wa}) and I'll diagnose before the visit so I bring the right parts.",
        "boiler-service":  "Local Gas Safe engineer in Southampton — happy to sort that. Annual service covers full combustion + safety checks. Drop me a WhatsApp ({wa}) for a slot.",
        "boiler-install":  "Local Gas Safe engineer in Southampton — happy to give you an honest quote. WhatsApp ({wa}) a photo of your current boiler + spot and I'll send a price.",
        "power-flush":     "Sounds like sludge. I'm a Gas Safe engineer in Southampton — do power flushes with proper kit. WhatsApp ({wa}) and I'll talk you through it.",
        "cp12":            "I do CP12s across Southampton — full inspection, certificate issued same day. WhatsApp the property address ({wa}) and I'll fit you in.",
        "gas-safety":      "Gas Safe engineer in Southampton — full check and certificate same day. WhatsApp ({wa}) to book.",
        "radiators":       "Sounds like trapped air or sludge. Happy to take a look — Gas Safe engineer in Southampton. WhatsApp ({wa}) and I'll sort it.",
        "pipe-leak":       "Plumber in Southampton — turn off the stopcock if you haven't already. WhatsApp me a video ({wa}) and I'll tell you what's involved.",
        "tap-repair":      "Plumber in Southampton — usually a cartridge or washer, quick fix. WhatsApp ({wa}) and I can pop round.",
        "shower-repair":   "Plumber in Southampton — happy to take a look. WhatsApp ({wa}) and I'll sort it.",
        "toilet-repair":   "Plumber in Southampton — happy to take a look. WhatsApp ({wa}) and I'll get back to you with a price.",
        "smart-controls":  "Heating engineer in Southampton — install Hive/Nest/Tado regularly. WhatsApp ({wa}) and I'll quote you.",
        "plumbing":        "Local plumber in Southampton — happy to help. WhatsApp ({wa}) with a photo and I'll get back to you fast.",
    }

    body = BODIES[topic].format(wa=WA)

    # Availability language — Wes's rules:
    #   Urgent + weekday  → "can come out today" is fine (shows real interest,
    #                       and he'll prioritise a genuine emergency).
    #   Urgent + weekend  → he doesn't really work weekends; be honest but
    #                       keep the door ajar rather than promising.
    #   Not urgent        → NO availability claim at all — interest only.
    from datetime import datetime
    is_weekend = datetime.now().weekday() >= 5  # Sat/Sun
    if urgent and not is_weekend:
        urgency_note = ("\n\nThis sounds urgent — I can come out today if needed. "
                        "WhatsApp me now and I'll confirm.")
    elif urgent and is_weekend:
        urgency_note = ("\n\nMessage me now — I'll see what I can do, and worst "
                        "case get you booked in first thing next week.")
    else:
        urgency_note = "\n\nNo pressure — happy to help whenever suits you."

    reply = (
        f"{opener}{body}{urgency_note}\n\n"
        f"More info: {short_url}\n"
        f"Wes — {PHONE}"
    )

    return {
        "topic": topic,
        "urgent": urgent,
        "short_url": short_url,
        "reply": reply,
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
