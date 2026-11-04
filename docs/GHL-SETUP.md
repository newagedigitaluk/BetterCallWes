# HighLevel on Better Call Wes: setup and trial log

Started 4 Nov 2026. Trial plan from 2 Nov: run BCW on HighLevel (GHL) for a month next to ServiceM8, tweak it, then price plumber tiers. ServiceM8 stays the live system the whole time. Nothing in this trial messages customers, moves the customer list, buys numbers, turns on billable AI, connects payments or changes ServiceM8 without Wes saying yes first.

Sub-account: Better Call Wes, location `7sUSfobemejSgrc2sd3v`, agency Automa AI, SaaS mode on, GBP, Europe/London.

## Where things stand (4 Nov)

- Field Services is still a private beta (HighLevel help articles updated 29 Oct 2026, no GA date). Not enabled on BCW yet. Register interest: https://api.gohighlevel.com/widget/form/hUqdKVCSNu82zc9TFY3x. Once on, a "Field Services" item with a Beta tag shows in the left menu.
- The pre-beta build is scripted but **not applied yet**. This session wasn't started by Wes directly, so writes to GHL were blocked pending his OK. Run the dry run, check it, then `--apply` (see "What's built").
- The BCW integration token can't see calendars, forms, tags, users, products, invoices or the AI agents. It needs more scopes before the calendars and AI pieces can be scripted (see "Token scopes").
- The workflow API is still 403 (`WORKFLOW_API_NOT_ENABLED_FOR_LOCATION`). It's a private beta for selected sub-accounts; ask HighLevel support to switch it on for BCW in the same ticket as Field Services.

## What's already on the BCW sub-account

This isn't a blank account. Found on 4 Nov:

- 994 contacts, 141 opportunities. 134 of them are in **Review Management** (41 since May). That was the GHL review sequence, switched off on 21 Oct when ServiceHQ Reviews took over.
- 7 pipelines: Boiler Installation/Replacement (13 stages, 6 opps), Boiler Service (1 stage), Boiler Service Reminders, Keep The Heat (Service Plan), Leads, QuickQuote, Review Management. None of them mirror the SM8 job flow.
- 23 workflows, 7 published: CTWA → CAPI Forward, Glow-Worm Winter Warmer Offer, Lead Site Enquiry, New Boiler Funnel Workflow, New Enquiry With AI Follow Up, New Lead Flow to Completed Survey, Summer Heating Services Ad, Voice Ai End Of Call.
- 24 contact custom fields, mostly from old boiler-install funnels. `SM8 Job Id` and `Date of Last Job` exist but nothing seems to fill them.
- **GHL is carrying live traffic.** In October it logged 76 inbound calls (127 minutes), 83 outbound SMS and 54 outbound emails (full table in the cost log). The "Voice Ai End Of Call" workflow is published, so a GHL voice agent may be answering some calls. ServiceM8 also has its own phone agent. **Wes: confirm which number customers ring and which agent answers it.** It changes the cost baseline.
- The SM8 "Add to HL" queue suggests jobs were once pushed across by hand. The GHL website tracking script is on every page of bettercallwes.co.uk (decision of 16 Jan 2026).

The new build leaves all of the above alone. New pieces get new names.

## ServiceM8 usage map

Counts are for jobs created 1 Nov 2025 to 4 Nov 2026, pulled read-only from the SM8 API. In that window there were 518 jobs (395 Completed, 88 Unsuccessful, 28 Work Order, 7 Quote) and £72.9k of completed work. That is about 40-45 jobs a month, rising to 71 in October. The median job is £100 and the mean £199. About 20% of jobs are subcontract work for SJM, YourRepair, Warmzilla and BeSure.

The usage column uses three levels: **a lot**, **now and then**, and **unused** (set up but unused).

The GHL column says one of: **today** (GHL does it today), **FS** (wait for Field Services), or **none** (no match).

| ServiceM8 feature | What BCW does with it | Usage | Counts (12m) | GHL cover | How |
|---|---|---|---|---|---|
| Job statuses (Quote, Work Order, Completed, Unsuccessful) | Jobs start as Work Orders. Quote status is rarely used. Unsuccessful is mostly cancellations or no-shows. | a lot | 395 completed, 88 unsuccessful (6 had a quote) | today, then FS | Pipeline "Jobs (SM8 mirror)" now. Real jobs with visits come with FS. |
| Invoices | Invoice PDF sent from SM8 | a lot | 324 jobs invoiced, 396 PDFs | today | Payments > Invoices (GBP, UK VAT via automatic taxes). Needs HighLevel Payments/Stripe connected, which is a red item. FS ties invoices to jobs. |
| Payments | Mostly bank transfer. Card goes through SM8's Stripe. | a lot | 384 payments, £78.4k: EFT 262, Stripe 110, Xero 10 | today (card), none (Xero) | Text-to-pay and invoice links via Stripe. I found no confirmed Xero sync. |
| Quotes | Quote PDFs, mostly boiler work | now and then | 31 sent, 22 won | today | Payments > Estimates. FS turns estimates into jobs. |
| Job categories | Labels jobs by service, loosely | a lot | 23 categories. 34% of jobs have none. | today, then FS | "Job Category" contact field exists. FS service catalogue replaces it. |
| Job templates | Online bookings spawn from BCW templates. Subcontract work uses SJM, Warmzilla and BeSure price templates. | now and then | 15 active | FS | FS service catalogue with add-ons. Products in Payments are a stopgap. |
| Gas service record (asset) and gas safety certificate | Filled on site, tied to the boiler asset | a lot | 182 form responses: 109 service record, 43 GSC, 20 client-branded GSCs | none | GHL forms can't produce a CP12 tied to an appliance. FS checklists aren't certificates. **This keeps SM8 (or a cert app) in the loop.** |
| Appliance / asset history | Boiler make, model, GC, service history | a lot | 56 assets, 151 asset service reports | today (partial) | Appliance contact fields (below). A custom object "Appliance" fits better for landlords with several boilers. |
| Diary / scheduling | Wes's diary. The booking API reads availability from it. | a lot | 537 diary entries on 375 jobs, 1 engineer | today, then FS | Calendars now (one engineer is easy). FS adds dispatch, map and routes. |
| Allocation windows | Morning, Afternoon, Business Hours, Urgent | unused | 0 of 537 entries | FS | FS arrival windows if wanted |
| Queues | Holding pens, mainly "Parts on Order" | now and then | 7 active, 2 jobs queued now | today | "Parts on order" pipeline stage |
| Badges | Trigger SM8 automations | a lot (about 8 of 47) | Booking Reminder 179, Service 130, Leave A Review 110, Courtesy 93, Callback 83 | today | Tags that trigger workflows |
| SMS automations | On-my-way, invoice and payment chasers, reminders, reschedules | a lot | 1,014 out, 191 in. 12 active templates. | today (UI only), FS for on-my-way | Workflows. Built in the UI while the workflow API is 403. On-my-way needs the FS technician app status. |
| Email templates | Invoice, quote, overdue, service reminder, boiler docs | a lot | 14 active templates. Send count not available. | today | Email templates and workflows |
| Online booking | Custom booking API (`api.bettercallwes.co.uk`) and ServiceHQ Booking. The SM8 widget is retired. | a lot | 66 widget bookings to Sep, then 42 booking-API bookings since 12 May | today, then FS | Calendars and a booking widget now. FS booking page has postcode check, travel fee and pay online. Deposits work on calendars once Stripe is connected; FS docs don't mention deposits. |
| WhatsApp (ServiceHQ Chat) | Customer threads logged to jobs | a lot, growing | 989 notes on 376 jobs. 514 in October. | today (but red) | GHL WhatsApp channel, $10/month plus Meta fees. BCW's WhatsApp number is Wes's own mobile on ServiceHQ, so moving it is a red item. Leave it. |
| Reviews (ServiceHQ Reviews) | Review request SMS after completion | new (live 21 Oct) | 8 sent | today | Reputation > review requests. GHL did this until 21 Oct. Reviews AI replies are $0.01 each. |
| Phone answering | SM8 phone agent. ServiceHQ cron sends booking links after calls. | now and then | 9 phone-sourced jobs since Aug | today (billable) | Voice AI agent. See the receptionist draft below. |
| Paid-invoice follow-up (n8n) | Thank-you SMS and email plus a More Trees tree | a lot | 77 SMS | today | Workflow on "Invoice paid", once invoices live in GHL |
| Supplier invoice forwarding (n8n) | Daily forward to SM8 import and Jentry | a lot | n/a | none | Stays in n8n. Not an SM8 feature anyway. |
| Photos, videos, signatures on jobs | Site evidence | a lot | about 1,180 photos, 44 videos, 190 signatures | FS | FS technician app has notes and checklists. Signatures not confirmed. |
| Job notes | Notes, 60% of them WhatsApp logs | a lot | 1,587 | today | Contact and opportunity notes |
| Subcontract clients | Per-client templates, badges and branded certs | a lot | about 20% of jobs | none (branding) | Company records and a "Client" field cover the billing side. Client-branded certificates have no match. |
| SM8 feedback ratings | Native rating | unused | last used Mar 2021 | n/a | n/a |
| Job and company custom fields | Marketing source from the booking API | barely used | marketing_source on 30 of 518 jobs | today | Contact attribution is built in |
| Tax rates | 7 set | set | n/a | today | Payments tax settings |

What GHL can't take over, even with Field Services: gas certificates tied to appliances, client-branded certs for subcontract work, and Xero sync. The booking API and ServiceHQ also read SM8's diary and jobs directly. Any switch has to replace that plumbing, not just the screens.

## What's built

Two scripts in `website/scripts/ghl/`, run from the project root:

| Script | What it does | Writes? |
|---|---|---|
| `ghl_usage.py` | Counts messages in and out per month per channel (SMS, Email, Call, WhatsApp). Includes SMS segments and call minutes. Feeds the cost log. | No |
| `bcw_ghl_setup.py` | Creates the trial pieces if missing. Dry run unless `--apply`. Skips anything with the same name, so it's safe to re-run once more scopes are added. | Only with `--apply` |

```bash
with-secret .env -- python3 website/scripts/ghl/bcw_ghl_setup.py
```

```bash
with-secret .env -- python3 website/scripts/ghl/bcw_ghl_setup.py --apply
```

What `bcw_ghl_setup.py` creates (dry run checked on 4 Nov; **not applied yet**):

- **Pipeline "Jobs (SM8 mirror)"**: Enquiry, Visit booked, Quote sent, Quote accepted, Parts on order, Work booked, Completed, Invoiced, Paid, Review requested. SM8's Unsuccessful becomes the opportunity's Lost status. If HighLevel's public API refuses to create pipelines, the script says so; build it in Opportunities > Pipelines with those stage names instead.
- **Contact fields**: Appliance Make, Appliance Model, Appliance GC Number, Appliance Type (Combi / System / Regular (heat only) / Back boiler / Gas fire / Other), Appliance Location, Last Service Date, Next Service Due, Gas Safety Record Expiry.
- **Opportunity fields**: SM8 Job UUID, SM8 Job Number. These link each card back to the live SM8 job.
- **Calendars** (needs the calendars scope first), all created **switched off**: Boiler Service (60 min), Gas Safety Check (CP12) (60), Boiler Repair / Diagnostic (60), General Plumbing (60), Power Flush (480, whole day). Hours match the booking API: Mon to Fri, 9-12 and 1-5, earliest slot 2 hours ahead. No payment or deposit is attached.

Status: the pipeline and fields are waiting on Wes's go-ahead to run `--apply`. The calendars are waiting on token scopes.

### Token scopes

The BCW Private Integration token reads pipelines, custom fields, workflows, contacts, opportunities and conversations. Everything else returns 401.

Suggested fix, matching the Mindset pattern: create a second Private Integration on BCW named "Claude builder". Store it in `~/.config/secrets/bcw-ghl-builder.env` (GHL_PIT_TOKEN, GHL_LOCATION_ID) and add a row to REGISTRY.md and API-ACCESS.md. Give it these scopes:

- `calendars.readonly`, `calendars.write`, `calendars/groups.readonly`, `calendars/groups.write`
- `forms.readonly`, `surveys.readonly`
- `locations/tags.readonly`, `locations/tags.write`, `locations/customValues.readonly`, `locations/customValues.write`
- `locations/customFields.readonly`, `locations/customFields.write`, `opportunities.readonly`, `opportunities.write`
- `conversation-ai.readonly`, `conversation-ai.write`, `voice-ai-agents.readonly`, `voice-ai-agents.write`
- `products.readonly`, `invoices.readonly`, `invoices/estimate.readonly`, `users.readonly`
- `objects/schema.readonly`, `objects/schema.write`, `objects/record.readonly` (for an Appliance custom object later)
- the workflow scopes (`workflows.readonly`, plus write/publish if HighLevel turns the API on)

Then run the setup script against that file instead of `.env`.

### UI steps for Wes (no API route today)

1. **HighLevel support ticket**: ask for Field Services private beta and the workflow API on location `7sUSfobemejSgrc2sd3v`. Also use the interest form above.
2. **Booking form** (Sites > Forms; forms can't be created by API): name, mobile, email, address and postcode, service (the five calendar names), boiler make/model/GC number mapped to the new Appliance fields, and "what's the problem". Attach it to the calendars. Leave the calendars switched off until the trial starts.
3. **Review requests** (Reputation > Settings): don't switch the old GHL review workflows back on. ServiceHQ Reviews is live and both would text the same customer. For the trial, set up the GHL request template only and keep it manual.
4. **Workflows to sketch, all left in draft:** "Job completed → review request" (manual only, see above), "Next Service Due → reminder 4 weeks before" (Wait action, yearly on date), "Invoice paid → thank-you". Don't publish any of them during the trial without a yes from Wes.
5. **AI receptionist**: paste the draft below into a new Conversation AI agent in **Suggestive** mode, so it drafts replies and Wes sends them. Don't connect it to a number and don't use Auto-pilot; both bill. Check what the existing "Voice Ai End Of Call" setup is answering before adding a voice agent.

### AI receptionist draft (Conversation AI, Suggestive mode)

```
You answer messages for Better Call Wes, a one-man plumbing and heating
business in Southampton run by Wes, a Gas Safe registered engineer.
Area: SO14 to SO19, SO30, SO31, SO40, SO45, SO50, SO51, SO53. Outside that,
say Wes will let them know if he can help.

Work Wes does: boiler servicing, gas safety checks (CP12), boiler repairs and
fault finding, power flushes, general plumbing. Wes does mostly servicing
and repairs, not big installs.

Prices you may quote:
- Boiler repair / diagnostic: £100 for the first hour. Any repair after
  that is quoted separately, sometimes on another day.
- General plumbing: from £100 for the first hour, parts quoted on the day.
For anything else, say Wes will confirm the price. Never guess a price.

Your job: find out what's wrong or what they need, their postcode, the
boiler make and model if it's a boiler job, and when suits them. Then offer
the booking link or say Wes will confirm a time.

Rules:
- Short, plain, friendly UK English. No emoji.
- Don't say Wes answers every call or is always available. Say he'll get
  back to them quickly.
- Never say the diagnostic fee comes off the repair price.
- Don't mention VAT.
- Don't give the Gas Safe registration number unless asked.
- If someone smells gas: tell them to turn off the gas at the meter, open
  windows, don't use switches, and ring the National Gas Emergency number,
  0800 111 999, now. Don't book anything.
- Carbon monoxide alarm going off: get everyone out, fresh air, ring
  0800 111 999.
- Never promise a same-day visit. Say Wes will confirm.
```

Fill the knowledge base from `website/site/data/services.json` and the FAQ on bettercallwes.co.uk.

## Waiting for Field Services

When the beta lands on BCW, set these up in this order, and log each against SM8 in the trial diary below:

1. **Service catalogue**: the five services from `services.json`, plus add-ons (extra radiators on a power flush, extra appliances on a CP12). Import from Calendars > Services or CSV.
2. **Service area**: SO14 to SO53 by postcode. Decide on a travel fee for edge postcodes.
3. **Booking page with deposits**: deposits aren't confirmed in the FS docs. Calendars can take one once Stripe is connected, which is a red item for Wes.
4. **Dispatch and routes**: one engineer, so mainly the map view and drive-time-aware availability.
5. **Jobs and visits**, with checklists that copy the gas service record fields. The certificate itself stays in SM8.
6. **Estimates → jobs → invoices.**
7. **Technician app** on Wes's phone.
8. **AI receptionist (chat) and Google Business Profile booking.**

FS beta gaps, per HighLevel: no reporting yet, no workflow triggers or actions, no Opportunities link, no client portal, no voice AI. UK and GBP aren't mentioned anywhere.

## Cost log

Prices are in USD from HighLevel's pricing guide and AI pricing pages (both updated late Oct 2026). LC Phone says "matches Twilio" but HighLevel publishes no UK figure, so the phone rows use Twilio UK list prices as a stand-in. The agency rebills: carrier and A2P fees carry a fixed 5% markup when rebilling is on, and AI usage can be rebilled at a fixed per-unit price on the $497 plan.

### Rate card

| Item | Rate | Source |
|---|---|---|
| SMS out, UK | $0.056 per segment (Twilio proxy) | twilio.com/en-us/sms/pricing/gb |
| SMS in, UK | $0.0075 per segment (Twilio proxy) | same |
| Call in | $0.0100/min | twilio.com/en-us/voice/pricing/gb |
| Call out, UK landline / mobile | $0.0158 / $0.0305 per min | same |
| Call recording / transcription | $0.0025 / $0.024 per min | HighLevel LC Phone guide |
| UK number rent | $1.15 to $3.50 a month for a local number (Twilio's two pages disagree), $2.50 for a mobile number | Twilio |
| LC Email | $0.675 per 1,000; validation $2.50 per 1,000 | HighLevel pricing guide |
| Conversation AI | token-based (e.g. GPT-4.1 $2 in / $8 out per million tokens) | HighLevel AI pricing |
| Voice AI | $0.045/min engine, plus $0.015 to $0.17/min voice, plus tokens and phone. Speech-to-speech models $0.10 to $0.20/min all-in. | same |
| AI Employee plan | Growth $50/month (1,000 conversation replies, 100 voice minutes); Unlimited $97 | same |
| Reviews AI | $0.01 per reply sent | same |
| Workflow premium AI action | $0.01 per run | HighLevel pricing guide |
| WhatsApp | $10/month per sub-account, plus Meta fees: UK marketing $0.0635, utility $0.0231 | HighLevel WhatsApp billing guide |

### Baseline: GHL traffic before the trial

From `ghl_usage.py`, run 4 Nov 2026:

| Month | Channel | In | Out | SMS segments out | Call mins in |
|---|---|---|---|---|---|
| 2026-08 | Call | 39 | 0 | | 44 |
| 2026-08 | Email | 4 | 58 | | |
| 2026-08 | SMS | 18 | 23 | 52 | |
| 2026-09 | Call | 63 | 0 | | 75 |
| 2026-09 | Email | 12 | 58 | | |
| 2026-09 | SMS | 25 | 48 | 116 | |
| 2026-10 | Call | 76 | 0 | | 127 |
| 2026-10 | Email | 5 | 54 | | |
| 2026-10 | SMS | 55 | 83 | 208 | |
| 2026-11 (to 4th) | Call | 14 | 0 | | 24 |
| 2026-11 (to 4th) | Email | 1 | 10 | | |
| 2026-11 (to 4th) | SMS | 5 | 4 | 8 | |

No WhatsApp traffic goes through GHL.

October at proxy rates comes to about **$13 a month** before AI and number rent:

- SMS: 208 segments out × $0.056 = $11.65, plus 55 in = $0.41
- Calls: 127 inbound minutes = $1.27
- Email: 54 emails, under $0.05

If a GHL voice agent answered those 127 minutes, add roughly $13 to $25 at $0.10 to $0.20/min. That's why the question about which agent answers the phone matters.

For scale: SM8 itself sent about 1,014 SMS in 12 months (about 85 a month). Moving all job texts to GHL would add about $5 to $12 a month in SMS at 1 to 2.5 segments each.

### Trial diary

One row per billable action type as it's switched on, and a usage pull at each month end. Paste the `ghl_usage.py` output under a dated heading.

| Date | What changed | Billable? | Est. monthly cost | Note |
|---|---|---|---|---|
| 2026-11-04 | Setup scripts written, dry run only | No | $0 | Nothing applied, nothing messaged |
