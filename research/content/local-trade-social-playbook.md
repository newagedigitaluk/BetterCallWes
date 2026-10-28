# Local Trade — Facebook Group Social Playbook

Research and conventions for responding to local Facebook group leads.
Applies to Better Call Wes (plumbing and heating, Southampton SO14–SO51).

---

## Why Facebook groups matter

Southampton's local community groups (Freegle, neighbourhoods, buy/sell) are
where residents first shout for tradespeople. Most posts get 7–13 replies within
two hours; in that window the poster usually picks someone. Leads that arrive
more than an hour after posting are mostly wasted — the slot is gone.

**Measured lag (fb_monitor, Oct 2026):** posts reach Wes 22 minutes to 4 hours
after they are published, with roughly half arriving over 60 minutes late.
Posts that show up at >2 hours old should still be responded to but with lower
urgency — at that age the poster likely already has 5+ replies and may have
already booked someone.

---

## The six-point reply format

Every reply Wes posts in a Facebook group should follow these six points in
order. Together they take under 300 characters. The monitor drafts the full text
automatically; Wes edits before posting.

| # | Point | Purpose |
|---|-------|---------|
| 1 | **Name** | Personalise — use their first name from the post |
| 2 | **Empathy** | One phrase acknowledging the specific problem |
| 3 | **Credential** | Gas Safe engineer, local to Southampton |
| 4 | **Action** | What to WhatsApp, what Wes will do with it |
| 5 | **Urgency close** | Availability language calibrated to urgency |
| 6 | **Sign-off** | Short URL for the relevant service + name + phone |

### Example (boiler repair, urgent, weekday)

```
Hi Sarah,
Sorry to hear the boiler's out — no heating is rough.
Gas Safe engineer in Southampton here — done this many times.
WhatsApp me a quick video of the boiler (wa.me/447700155655) and I'll diagnose before I come out.
This sounds urgent — I can come today. Message me now and I'll confirm.
More info: u.bettercallwes.co.uk/boiler-repair | Wes — 07700 155 655
```

### Example (radiator, non-urgent)

```
Hi Pete,
Cold or uneven radiators are usually a quick fix.
Gas Safe engineer in Southampton here.
WhatsApp me a photo of the radiator (wa.me/447700155655) and I'll tell you what's involved.
No pressure — happy to help whenever suits you.
More info: u.bettercallwes.co.uk/radiators | Wes — 07700 155 655
```

---

## Rules

- **Always use the first name** visible on the post. "Hi" alone is fine if no name.
- **Empathy line must be specific** — match the language of the problem, not generic.
- **Credential is always "Gas Safe engineer in Southampton"** (or "plumber in Southampton" for non-gas work). Never print the Gas Safe registration number in posts.
- **CTA is always WhatsApp** — not phone call, not email. The number is 07700 155 655 (wa.me/447700155655 for links).
- **No VAT mention** anywhere in any post.
- **Urgency language only on genuine emergencies** (no heating, flooding, gas leak) and only on weekdays — do not promise same-day on weekends.
- **Stay under ~300 characters** so the post is not collapsed by FB on mobile.

---

## Responding to an aged post

If the alert shows the post is >90 minutes old:

1. Still reply — it shows you're active and the poster may not have booked anyone yet.
2. Do NOT use "I can come today" language unless it is genuinely still the same day and urgent.
3. Consider a shorter reply: empathy + credential + WhatsApp + sign-off (skip the urgency close).

---

## Group selection and monitoring

See `website/social/fb_monitor/config.json` for the monitored groups.
The monitor runs every 15 minutes via cron on the VPS.

Mark the busiest groups `"priority": true` in config — the monitor visits those
first on every cycle rather than shuffling all groups randomly. This shaves
2–5 minutes off the alert time for posts from high-activity groups.
