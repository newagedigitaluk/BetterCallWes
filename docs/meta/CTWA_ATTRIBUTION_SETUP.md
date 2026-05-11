# CTWA Attribution Setup — GHL Workflow Build Guide

## Context

Previous Meta campaign (v2) reported zero WhatsApp conversations despite real messages arriving, because attribution wasn't being sent from GHL back to Meta. This guide builds the missing attribution pipeline.

**Confirmed state:**
- GHL WhatsApp integration is Meta WhatsApp Business Platform (Cloud API) — correct type
- Messages arrive in GHL Conversations with referral data prepended to the body (`Headline: ...` / `Source URL: ...`)
- No existing workflows, pipelines, or CAPI actions set up
- Diagnostic workflow already built and published

**Goal:** wire up the two-hop workflow pattern so every CTWA message automatically fires a Meta CAPI `Lead` event, making Ads Manager attribution work.

---

## Architecture — why two workflows

GHL's "Click to WhatsApp Ads" trigger doesn't natively offer the Meta CAPI action. Its allowed actions are limited to: Tag, Pipeline Move, WhatsApp Message, Webhook.

But the **Pipeline Stage Change** trigger *does* support Meta CAPI. So we chain:

1. **Workflow A**: CTWA message arrives → contact gets moved into a pipeline stage.
2. **Workflow B**: pipeline stage change fires → Meta CAPI `Lead` event sent.

By the time Workflow B runs, the contact has all the attribution fields GHL populated from the webhook (ctwa_clid, ad_id, etc.), and CAPI picks them up automatically.

---

## Step 1 — Create the pipeline

1. GHL sidebar → **Opportunities** → **Pipelines** (or **Settings → Opportunities & Pipelines**)
2. **+ Create Pipeline**
3. Name: `Ad Leads`
4. Create these stages in order:
   - `New CTWA Lead`
   - `Engaged`
   - `Quoted`
   - `Booked`
   - `Lost`
5. Save

---

## Step 2 — Convert the diagnostic workflow into Workflow A

Rename and extend the existing `Diagnostic — CTWA Inbound` workflow.

1. Automation → open `Diagnostic — CTWA Inbound`
2. Rename to: **`CTWA Capture → Pipeline`**
3. Keep the existing **Click to WhatsApp Ads** trigger (no filters — must fire for every CTWA message)
4. Keep the existing **Add Tag `ctwa-inbound`** action
5. **+ Add new action** after the tag:
   - Action type: **Create / Update Opportunity**
   - Pipeline: `Ad Leads`
   - Stage: `New CTWA Lead`
   - Opportunity name: `{{contact.first_name}} — WhatsApp`
   - Status: `Open`
   - Monetary value: leave blank
6. Save + Publish
7. Settings tab → confirm:
   - **Allow Re-Entry** = ON
   - **Allow Multiple** = ON

**Screenshot** the completed workflow.

---

## Step 3 — Build Workflow B (fires CAPI Lead event)

1. Automation → **+ Create Workflow** → **Start from Scratch**
2. Name: **`CAPI Lead — from CTWA Stage`**
3. **+ Add Trigger** → search **Pipeline Stage Change** (may also appear as "Opportunity Status Changed")
4. Configure trigger filter:
   - Pipeline: `Ad Leads`
   - Moved to Stage: `New CTWA Lead`
5. Save trigger
6. **+ Add Action** → search **Facebook Conversions API** (may be labelled "Meta Conversions API" or "Facebook Conversion API")
7. Configure action:
   - Connection: select connected Meta ad account (Better Call Wes / `act_1157261541704017`)
   - Pixel: `1612104182479593`
   - Event: **Lead**
   - Event ID: leave default (GHL generates)
   - User data fields — enable if shown:
     - Phone
     - Client IP
     - Client user agent
     - External ID (contact ID)
     - FBC (click ID cookie)
     - FBP (browser ID cookie)
     - CTWA CLID (the key one for WhatsApp attribution)
   - Custom data: leave blank for now
8. Save action
9. Publish the workflow
10. Settings tab → confirm:
    - **Allow Re-Entry** = ON
    - **Allow Multiple** = ON

**Screenshot** the completed workflow — especially the CAPI action's user-data field list.

---

## Step 4 — Test end-to-end (no ad spend needed)

Verify the chain works by manually creating an opportunity on an existing contact.

1. Find the Cee Jay contact (2 April — the one with the real CTWA message)
2. Open the contact → **Opportunities** tab → **+ Add Opportunity**:
   - Pipeline: `Ad Leads`
   - Stage: `New CTWA Lead`
3. Save
4. Wait ~30 seconds, then check:
   - `CAPI Lead — from CTWA Stage` → **Execution Logs** tab → should show 1 run
   - Meta Events Manager → **Test Events** tab → should show a `Lead` event arrived

**Screenshot** both:
- Workflow B execution log (the run entry)
- Meta Events Manager Test Events showing the Lead event

---

## What to send back

Four screenshots:

1. The `Ad Leads` pipeline with stages
2. Workflow A (`CTWA Capture → Pipeline`) — full trigger + actions view
3. Workflow B (`CAPI Lead — from CTWA Stage`) — full trigger + action view, including CAPI field config
4. Test results — Workflow B execution log + Meta Test Events Lead event

---

## Pass criteria

- Workflow A executes when Workflow B's manual opportunity is created in Step 4
- Workflow B executes within 30 seconds of the opportunity being created
- Meta Events Manager Test Events shows a `Lead` event in real time
- The Lead event's "Match quality" shows which fields matched (phone at minimum, ideally ctwa_clid)

If all four pass → attribution is wired, we can move to the ad rework + v3 campaign build.

If any fail → we inspect the execution log payload and troubleshoot from there.
