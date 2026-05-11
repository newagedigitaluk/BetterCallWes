# ServiceM8 Email & SMS Template Snapshots

Raw JSON snapshots of every email and SMS template currently in the ServiceM8 account. Used as the source of truth when drafting new templates so we can copy shared blocks (brand header, bank details, sign-off) verbatim.

- `emailtemplate.snapshot.json` — `GET /api_1.0/emailtemplate.json`
- `smstemplate.snapshot.json` — `GET /api_1.0/smstemplate.json`

These are point-in-time snapshots, not live state. If templates have been edited inside ServiceM8 since the snapshot date, re-pull before drafting.

## Refresh

```bash
cd "$(git rev-parse --show-toplevel)"
set -a && . ./.env && set +a
curl -sS -H "X-Api-Key: $SERVICEM8_API_KEY" \
  https://api.servicem8.com/api_1.0/emailtemplate.json \
  | jq '.' > website/ServiceM8/email-templates/emailtemplate.snapshot.json
curl -sS -H "X-Api-Key: $SERVICEM8_API_KEY" \
  https://api.servicem8.com/api_1.0/smstemplate.json \
  | jq '.' > website/ServiceM8/email-templates/smstemplate.snapshot.json
```

## Schema

**Email:** `{uuid, name, subject, message (HTML), active, edit_date}`
**SMS:** same minus `subject`.

`active = 1` is shown to staff in the SM8 send dialog; `active = 0` is hidden but kept on the account.

## Human-readable summary

A grouped, annotated view (with merge-field inventory and shared building blocks) lives in the vault: `~/obsidian-vault/Better-Call-Wes/ServiceM8-Email-Templates.md`. Read that first when drafting; come here for the literal HTML.
