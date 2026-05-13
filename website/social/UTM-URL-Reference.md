# Marketing UTM Reference — Better Call Wes

Quick reference for tagging links in social posts, ads, GMB posts, emails, and
QR codes so every online booking lands in ServiceM8 with the right marketing
attribution. **Last updated: 2026-05-13.**

Booking-api auto-fills four SM8 custom fields on every online booking based
on the UTM parameters in the booking URL (commit `838fb87`):

- `customfield_contact_method` → always `"Website"`
- `customfield_lead_quality` → always `"Good"`
- `customfield_marketing_source` → mapped from `utm_source` / `utm_medium`
- `customfield_campaign_ref` → `utm_campaign` / `utm_content` / `utm_term` joined

---

## Copy-paste URLs by channel

The base URL is always `https://bettercallwes.co.uk/booking.html`. Add the
relevant query string for your channel. Mix in `?service=<slug>` (see below)
to also pre-select a service.

### Google

| Channel | URL |
|---|---|
| Google Ads (paid search) | `https://bettercallwes.co.uk/booking.html?utm_source=google&utm_medium=cpc&utm_campaign=<campaign_name>` |
| Google Local Services Ads | `https://bettercallwes.co.uk/booking.html?utm_source=google&utm_medium=local_services` |
| Google My Business post | `https://bettercallwes.co.uk/booking.html?utm_source=gmb&utm_campaign=<post_topic>` |
| Google My Business profile button | `https://bettercallwes.co.uk/booking.html?utm_source=gmb&utm_medium=profile_button` |

### Meta (Facebook + Instagram)

| Channel | URL |
|---|---|
| Facebook ad | `https://bettercallwes.co.uk/booking.html?utm_source=facebook&utm_medium=cpc&utm_campaign=<campaign_name>` |
| Facebook organic post | `https://bettercallwes.co.uk/booking.html?utm_source=facebook&utm_medium=organic&utm_campaign=<post_topic>` |
| Instagram ad | `https://bettercallwes.co.uk/booking.html?utm_source=instagram&utm_medium=cpc&utm_campaign=<campaign_name>` |
| Instagram bio link | `https://bettercallwes.co.uk/booking.html?utm_source=instagram&utm_medium=bio` |
| Instagram organic post / story | `https://bettercallwes.co.uk/booking.html?utm_source=instagram&utm_medium=organic&utm_campaign=<post_topic>` |

### Third-party directories

| Channel | URL |
|---|---|
| Checkatrade profile | `https://bettercallwes.co.uk/booking.html?utm_source=checkatrade` |
| Bark profile | `https://bettercallwes.co.uk/booking.html?utm_source=bark` |
| Gas Safe Register | `https://bettercallwes.co.uk/booking.html?utm_source=gas_safe` |

### Direct outreach

| Channel | URL |
|---|---|
| Email newsletter | `https://bettercallwes.co.uk/booking.html?utm_source=email&utm_medium=newsletter&utm_campaign=<topic>` |
| Service-reminder email | `https://bettercallwes.co.uk/booking.html?utm_source=email&utm_medium=service_reminder` |
| Customer referral | `https://bettercallwes.co.uk/booking.html?utm_source=referral` |
| QR code on van / flyer | `https://bettercallwes.co.uk/booking.html?utm_source=qr&utm_medium=<van\|flyer\|business_card>` |
| WhatsApp template | `https://bettercallwes.co.uk/booking.html?utm_source=whatsapp&utm_medium=outbound` |

---

## Deep-linking to a specific service

Add `service=<slug>` and the booking form auto-selects that service and jumps
to step 2. Stack it alongside UTM params for maximum convenience.

Valid `service` slugs:

| Slug | Service |
|---|---|
| `boiler-service` | Boiler Service |
| `gas-safety-check` | Gas Safety Check (CP12) |
| `boiler-repair` | Boiler Repair / Diagnostic |
| `power-flush` | Power Flush |
| `plumbing` | General Plumbing |

**Example — boiler-repair Facebook ad campaign:**
```
https://bettercallwes.co.uk/booking.html?service=boiler-repair&utm_source=facebook&utm_medium=cpc&utm_campaign=winter_breakdowns_2026
```

Customer clicks → boiler-repair pre-selected → on step 2 questions → books → SM8 job tagged "Facebook / cpc / winter_breakdowns_2026".

---

## How URLs map to SM8 `customfield_marketing_source`

Source values come from your existing taxonomy (verified against 200 recent
jobs). Mapping rules in `booking-api/main.py` → `map_utm_to_marketing_source()`:

| URL params | SM8 value |
|---|---|
| `utm_source=google&utm_medium=cpc` | `PPC` |
| `utm_source=google&utm_medium=organic` (or just `google`) | `Google Organic` |
| `utm_source=google&utm_medium=local_services` (or `utm_medium=lsa`) | `Google Local Services` |
| `utm_source=gmb` / `google_business` / `google_my_business` | `Google My Business` |
| `utm_source=google_local_ads` | `Google Local Ads` |
| `utm_source=facebook` / `fb` / `meta` | `Facebook` |
| `utm_source=instagram` / `ig` | `Facebook` (same bucket — Meta ads) |
| `utm_source=checkatrade` | `Checkatrade` |
| `utm_source=bark` | `Bark` |
| `utm_source=referral` / `referred` / `wom` | `Referred` |
| `utm_source=gas_safe` / `gassafe` | `Gas Safe Register` |
| `utm_source=existing` / `existing_customer` | `Existing` |
| (none, or unmapped) | `Other` |

**Need a new bucket?** Add a value in SM8 admin (Settings → Custom Fields →
Marketing Source) AND add a case to `map_utm_to_marketing_source()` in
`website/booking-api/main.py`. Or just keep using `utm_source=<new_thing>`
and the booking will land as `Other` — Wes can recategorise manually in SM8
once you decide it's a permanent bucket.

---

## How to view this in SM8

1. Open SM8 → Reports
2. Filter by date range
3. Group / segment by **Marketing Source**
4. Drill into each source to see lead quality, conversion to invoice, value, etc.
5. Use **Campaign Ref** for granular drill-down — e.g., compare `winter_breakdown_2026` vs `summer_offer_2026` performance.

---

## First-touch attribution

The booking-api respects **first-touch**: the very first UTM-tagged URL a
customer hits in their browsing session "owns" the booking, even if they
later navigate around the site without UTMs. Attribution is stored in
`sessionStorage` so it survives across pages but resets between sessions.

This is the correct model for plumbing — customers often click an ad,
browse around, then come back hours later to book. We want to credit the
ad, not the "Direct" return visit.

---

## Tools

- [Google Campaign URL Builder](https://ga-dev-tools.google/campaign-url-builder/)
  — paste the BCW base URL plus your tags, get a clean URL.
- For QR codes: any free QR generator → tag URL with `?utm_source=qr&utm_medium=<medium>`.

---

## Cheatsheet for naming campaigns

Convention to keep reporting tidy:

- **`utm_campaign`**: short, lowercase, underscores. E.g., `winter_breakdowns_2026`, `annual_service_reminder`, `spring_boiler_offer`.
- **`utm_content`**: the specific creative or post. E.g., `video_30s`, `static_carousel`, `post_001`.
- **`utm_term`**: only used for paid search; the keyword that triggered it.

Avoid spaces (URL-encoded as `%20`, ugly), capitals (inconsistent across team), and emoji.
