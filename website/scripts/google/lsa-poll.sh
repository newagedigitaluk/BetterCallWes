#!/usr/bin/env bash
# Poll Google Local Services for new leads and respond.
#
# Every two minutes, 07:00-22:00 UK. Not round the clock on purpose: a
# WhatsApp landing at 3am reads worse than one landing at 8am, and a lead
# that arrives overnight still gets answered first thing because the script
# keeps retrying until it has actually sent (see RETRY_HOURS).
#
# Quota: ~450 runs a day at 2 API calls each is ~900 operations, against the
# 2,880 a day Explorer access allows. Room to double the frequency if needed.
set -euo pipefail

PROJECT="/home/wes/Coding/Projects/Better Call Wes"
cd "$PROJECT"

if [ -r "$PROJECT/.env" ]; then
  set -a; . "$PROJECT/.env"; set +a
fi

for var in GOOGLE_ADS_CLIENT_ID GOOGLE_ADS_CLIENT_SECRET GOOGLE_ADS_REFRESH_TOKEN; do
  if [ -z "${!var:-}" ]; then
    echo "$var missing; refusing to run" >&2
    exit 78
  fi
done

exec python3 "$PROJECT/website/scripts/google/lsa_leads.py" --send
