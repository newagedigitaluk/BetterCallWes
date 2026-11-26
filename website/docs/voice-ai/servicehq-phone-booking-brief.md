# Brief for ServiceHQ Booking: book from a phone call

From the Better Call Wes session, 26 Nov 2026. Account 84fea8b1-7f3c-4454-af9c-f37e298001db, page slug `better-call-wes`.

## What's happening

Wes is moving his phone receptionist from ServiceM8 Phone to a GoHighLevel Voice AI agent (number +44 7700 155655 is already hosted in GHL). The agent must book jobs on the call, through ServiceHQ Booking, so phone, website and WhatsApp follow one set of rules (services, prices, durations, area, lead time, the after-booking extras flow).

GHL Voice AI reaches outside systems two ways: Custom Actions (webhooks, **POST only**, auth headers, parameters collected in the conversation) and MCP servers. It already uses the ServiceM8 MCP on this account.

## Wes's rules for phone bookings

- Collect **name and address (with postcode)** only. **No email**: older callers can't spell it out and it comes out wrong. Wes gets it on the day.
- **Phone number comes from caller ID**, confirmed with the caller. **Landlines must be accepted**: a lot of these callers are older and ring from one.
- If the caller is on a mobile, offer the alternative of being sent the booking link by **WhatsApp or SMS** instead of booking on the call.
- Everything else exactly as the website and Chat: same services, pre-booking questions, prices, durations, area check, lead time, extras after booking with the slot extended (see the separate rework brief from 20 Oct).

## What the booking API needs for that

The public routes don't fit a phone agent as they stand:

1. `POST /api/p/[slug]/book` requires `customer.email` and rejects non-mobiles (`looksLikeMobile`). Needs a phone-booking path where email is optional and landlines are fine. Probably a separate authenticated endpoint rather than loosening the public one, so the website form keeps its checks and bots can't book without email.
2. `GET /api/p/[slug]/availability` is GET; GHL Custom Actions are POST only. Needs a POST equivalent (service id + answers in, a handful of slots out, phrased so a voice agent can read them out: "Tuesday 2nd December, morning").
3. Auth: a shared secret header, so only Wes's agent can book without email. Key to live in Coolify and in the BCW project `.env`.
4. Mark the job's source as phone (contact method "Phone", marketing source from the agent), so these are distinguishable in ServiceM8.
5. Return something short for the agent to confirm back: date, time window, price.

An MCP server for ServiceHQ Booking would also work instead of 1-2 (GHL supports MCP on Voice AI), if that is cleaner than webhooks.

## Not in scope here

The call recording/transcript logging into ServiceM8 is being built on the BCW side (polls GHL's Voice AI call logs). Don't create ServiceM8 jobs for anything that isn't a booking: ServiceM8 bills per job.
