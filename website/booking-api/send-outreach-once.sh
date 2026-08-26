#!/usr/bin/env bash
# One-shot: send touch 1 of the booking outreach, then remove its own cron line.
#
# One-shot rather than recurring because this sends real SMS to real
# customers. A dated cron entry ("15 9 26 8 *") would fire again next
# August, so it deletes itself once it has run. outreach.py's state file
# is the second line of defence: a job already messaged is skipped.
#
# Wes approved this send on 2026-08-25 for the eleven YourRepair/Hometree
# jobs, ten of which have a mobile.
set -euo pipefail

PROJECT="/home/wes/Coding/Projects/Better Call Wes"
MARKER="send-outreach-once.sh"

cd "$PROJECT"

# cron inherits no shell environment, so the API key and the link-signing
# secret have to be pulled in explicitly.
if [ -r "$PROJECT/.env" ]; then
  set -a; . "$PROJECT/.env"; set +a
fi

for var in SERVICEM8_API_KEY MAGIC_LINK_SECRET; do
  if [ -z "${!var:-}" ]; then
    echo "$var missing; refusing to run" >&2
    exit 78   # EX_CONFIG
  fi
done

# Take the cron line out FIRST. If the send crashes half way we want a
# human looking at it, not an automatic retry firing more texts.
( crontab -l 2>/dev/null | grep -v "$MARKER" || true ) | crontab -
echo "cron entry removed; this run is the only one"

# auto: WhatsApp if Meta has approved the template by now, SMS if not.
# Both are tested end to end; the only thing in doubt at scheduling time
# was Meta's review queue.
exec python3 "$PROJECT/website/booking-api/outreach.py" \
  --send --channel auto --notify
