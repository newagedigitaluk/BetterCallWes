# Invoice & Receipt Forwarder — Setup Guide

Fully autonomous daily process: scans `wes@bettercallwes.co.uk` for supplier invoices and receipts, forwards each one to Dext (bookkeeping) and ServiceM8 (job management), then emails Wes a one-line summary. Runs every day at 19:00 with no human in the loop.

## What it does

Every day at 19:00 the workflow:

1. Pulls new messages from the Inbox received in the last 25 hours that haven't already been processed
2. Sends each one to an LLM that decides whether it's a **cost to the business** (supplier invoice / receipt / subscription bill) versus revenue, marketing, or noise
3. For matches with confidence ≥ 0.7, forwards the original email — attachments and all — to:
   - **Dext:** `akwetey.bortier.akwetey.bortier@dext.cc`
   - **ServiceM8:** `invoice_a4b25ba2@import.servicem8.com`
4. Tags the original message with the Outlook category `Invoices-Forwarded` so it can never be processed twice
5. Emails Wes a summary if anything was forwarded (silent if nothing matched)

## One-time setup

### 1. Create the Outlook category

In Outlook on the web → **Settings → General → Categories → Add category**.

- Name: **`Invoices-Forwarded`** (exact spelling, case-sensitive — the workflow filter depends on it)
- Colour: any

### 2. Connect the Microsoft Outlook credential in n8n

In n8n: **Credentials → New → Microsoft Outlook OAuth2 API**.

- Name it **`Outlook — wes@bettercallwes.co.uk`** (matches the placeholder in the workflow JSON)
- Click **Connect my account** → sign in with `wes@bettercallwes.co.uk` → consent
- Save

The Microsoft Outlook node uses Microsoft Graph under the hood. It can read, forward, update categories, and send mail — all through one credential. No app password required.

### 3. (If not already present) Connect the Straico/OpenAI credential

The classifier uses the same `openAiApi` credential pattern as `n8n_email_trap.json`. If `Straico API` already exists from that workflow, reuse it. Otherwise:

- **Credentials → New → OpenAI API**
- Name: **`Straico API`**
- API key: your Straico key
- Base URL: `https://api.straico.com/v0/openai` (or whatever the email-trap workflow uses)

### 4. Import the workflow

- n8n → **Workflows → Import from File** → select `invoice-forwarder.json`
- Open each Microsoft Outlook node and re-pick the credential (the placeholder ID won't auto-link)
- Open the **Classify (Straico)** node and re-pick the credential
- Save

### 5. Set the n8n instance timezone

n8n → **Settings → Instance** → set timezone to **Europe/London**. The schedule trigger uses the instance timezone, so this is what makes "0 0 19 * * *" mean 7pm UK.

### 6. Activate

Toggle the workflow to **Active**. That's it — it'll fire at 19:00 every night.

## First-run smoke test

Before trusting it overnight:

1. Send a fake invoice email to `wes@bettercallwes.co.uk` from a personal address. Body: `Invoice #TEST-001 — total £42.50`. Attach any PDF.
2. In n8n, open the workflow and click **Execute Workflow**.
3. Check:
   - Dext inbox shows the forwarded email within ~5 min
   - ServiceM8 → Inbox shows it
   - The original email in Outlook now has the **Invoices-Forwarded** category
   - A summary email arrived in Wes's inbox listing 1 forwarded item
4. Click **Execute Workflow** a second time → confirm the same email is **not** forwarded again (the category filter excludes it).
5. Send a customer-style email (`Quote for boiler service — £450, can you book it in?`) → run again → confirm it is **not** forwarded.

## Tuning

If supplier invoices are being missed (false negatives) or customer emails leak through (false positives), edit the prompt in the **Classify (Straico)** node. Lower/raise the `0.7` confidence gate in **Parse Classification** if needed.

To add suppliers, just add their names to the "Forward = TRUE" list in the prompt — no code change.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Nothing happens at 19:00 | Workflow not Active, or n8n timezone wrong | Toggle Active; set Europe/London |
| All emails being forwarded | Category not created or wrong name | Confirm exact category name `Invoices-Forwarded` exists |
| Forwards fail with 403 | Outlook credential lacks `Mail.ReadWrite` / `Mail.Send` scope | Reconnect the credential and accept all scopes |
| Summary email never arrives | `Anything Forwarded?` IF false because nothing matched (correct), or send node failing | Check execution log |
| Same email forwarded twice | Tag-as-Forwarded step failed | Check execution log; the category may not exist |

## Cost

- Microsoft Graph: free, included with O365 Business
- Straico classification: ~$0.0002 per email × ~10–30 emails/day = pennies/month
- Dext / ServiceM8: existing subscriptions, no per-message cost

## Files

- `invoice-forwarder.json` — the workflow itself
- This file — setup & troubleshooting
