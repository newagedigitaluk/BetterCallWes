# Meta Ads V3 — Build Spec

Full copy, images, and decisions for the v3 campaign. Review here, tell me what to change.

---

## Campaign structure

**Campaign:** `BCW — WhatsApp Leads — v3`
- Objective: `OUTCOME_MESSAGES`
- Bid: `LOWEST_COST_WITHOUT_CAP`
- Spending limit: **None** (per your call)
- A/B test: Off
- CBO: Off (single ad set)

**Ad set:** `Southampton Homeowners — WhatsApp`
- Performance goal: `LINK_CLICKS` (EU restriction — CONVERSATIONS blocked)
- Attribution window: 1-day click
- Daily budget: **£20**
- Destination: WhatsApp → `447700155655`
- Location: Southampton, 17km radius, **"people living in" only** (not "recent")
- Age: 30–65
- Gender: All
- Advantage+ audience: **Off**
- Manual interests: Home improvement, Home ownership, Boiler, Central heating, Worcester Bosch, Property maintenance
- Detailed targeting expansion: Off
- Placements: **Manual** — Facebook Feed/Stories/Reels/Marketplace/Video Feeds, Instagram Feed/Stories/Reels/Explore, Messenger Inbox. **Audience Network OFF.**
- Past customer exclusion: **Skip for now** (you said you'd get list if needed — we can add later)

---

## Ad 1 — Wes Portrait (Direct Response)

**Image:** v2 creative reuse (the 9.5% CTR winner)

**Headline:** Boiler or Plumbing Issue? Send Me a Photo

**Primary text:**
> I'm Wes, Southampton's Gas Safe plumber and heating engineer. Send me a photo of your boiler, radiator or leak on WhatsApp — I'll tell you honestly what's going on, usually within 2 hours.
>
> No call centres. No sales pitch. Just a straight answer from a local engineer.
>
> Gas Safe registered · Southampton SO14–SO51 · Transparent pricing

**Description:** Honest diagnosis within 2 hours from a local Gas Safe engineer

**CTA button:** Send WhatsApp Message

**Pre-filled message:**
```
Hi Wes [WP] — photo attached of my [boiler / leak / radiator]. Can you tell me what's going on?
```

---

## Ad 2 — Magnetic Filter (Urgency)

**Image:** v2 sludge creative reuse

**Headline:** £165 Could Save You a £600 Boiler Repair

**Primary text:**
> This black sludge was circulating through a Southampton boiler last week. The owner had no idea until it caused a £600 breakdown.
>
> A magnetic filter costs £165 fitted, catches this stuff before it kills the pump or heat exchanger, and is often paid back by one avoided callout.
>
> Send me a photo of your boiler pipework — I'll confirm on WhatsApp whether yours needs one.

**Description:** Magnetic filter fitted with full system flush.

**CTA button:** Send WhatsApp Message

**Pre-filled message:**
```
Hi Wes [MF] — photo attached of my boiler. Does mine need a magnetic filter?
```

---

## Ad 3 — Worcester Bosch Range (Fixed Price)

**Image:** TBC — see "Image question" section below

**Headline:** Worcester Bosch Boiler Fitted From £1,800

**Primary text:**
> Thinking about replacing your boiler? I install the full Worcester Bosch range in Southampton — from the 1000 entry-level at £1,800 right up to the Worcester 4000 with a 10-year manufacturer guarantee.
>
> Gas Safe engineer. No surveyor visit, no sales pressure — send me a photo of your current boiler and pipework on WhatsApp and I'll come back with a fixed written quote within 24 hours.

**Description:** Worcester guarantee up to 10 years on flagship models.

**CTA button:** Send WhatsApp Message

**Pre-filled message:**
```
Hi Wes [NB] — photo attached of my current boiler and pipework. Can you send me a fixed quote?
```

---

## Image question for Ad 3

You asked me to use **nanobanana2** (Gemini 2.5 Flash Image) to create a creative image with a badge.

**I don't have direct access to nanobanana2 from this environment.** There's no image-generation tool wired in. Three options:

### Option A — Add a Google AI API key to the .env and I generate it via curl
- You get a free-tier key from: https://aistudio.google.com/app/apikey
- Add `GOOGLE_AI_API_KEY=...` to `.env`
- Tell me and I'll call Gemini 2.5 Flash Image directly with a prompt like:
  > "Modern product photograph of a Worcester Bosch 4000 combi boiler, white casing, two dial controls, centred on a clean light-grey gradient background. In the top-right corner, a circular orange badge reading '10-YEAR GUARANTEE' in bold white sans-serif. Soft studio lighting, sharp focus, commercial photography style, square 1:1 aspect ratio."
- The generated image gets saved to `Brand Images/Boiler Images/Worcester/`

### Option B — You generate it in Gemini, send me the file
- Use the same prompt in Gemini / nanobanana2 UI
- Download the result, drop into the project folder
- Tell me the filename

### Option C — Use the Worcester-supplied image that already has a badge
- `4000_Lft_10years_2500x2700_copy-400x_.png` is in your folder
- It's the 4000 with the 10-year guarantee badge baked in by Worcester
- Free, official, on-brand — but not custom

My recommendation: **Option A** if you've got 60 seconds to make the API key. **Option C** if you want to ship today.

---

## Pre-launch decisions needed

| # | Decision | Status / your answer |
|---|---|---|
| 1 | Ad 1 copy approved? |  |
| 2 | Ad 2 copy approved? |  |
| 3 | Ad 3 copy approved? |  |
| 4 | Ad 3 image — A (Gemini gen), B (you gen), or C (use C)? |  |
| 5 | Lifetime spend cap | **No cap** (your call) |
| 6 | Past customer exclusion | **Skip for now** (your call) |

---

## Attribution stack (already live)

Just a reminder of what's wired behind the ads:

1. **CTWA click** → WhatsApp opens with pre-fill
2. **User sends message** → WhatsApp Business Platform webhook → GHL
3. **GHL "Click to WhatsApp Ads" trigger fires** → workflow `CTWA → CAPI Forward`
4. **Workflow POSTs** to `https://n8n.newagedigital.uk/webhook/bcw-whatsapp-lead`
5. **n8n extracts** ctwa_clid, ad_id, headline, source_url + contact PII
6. **n8n fires** Meta CAPI `LeadSubmitted` event → Meta Ads Manager attributes the conversation

Any real ad traffic from v3 onwards will be measurable in Ads Manager.

---

## Urgent security reminder

Your `META_ACCESS_TOKEN` and `META_APP_SECRET` were confirmed in the **public** GitHub repo's git history (commits `34bfe53` and `8977b6e`). **Rotate both before launching v3.** If you don't, any actor who's scraped the repo has admin-level access to your ad account.

- `META_ACCESS_TOKEN`: Business Settings → System Users → regenerate
- `META_APP_SECRET`: App Dashboard → Settings → Basic → Reset

After rotation: paste the new values into `.env`, tell me, and I'll re-deploy the n8n workflow with the new token.
