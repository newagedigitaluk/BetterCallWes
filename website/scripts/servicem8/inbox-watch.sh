#!/usr/bin/env bash
# Flag silent ServiceM8 Inbox items (calls, online enquiries) with an @mention.
set -euo pipefail
exec python3 "/home/wes/Coding/Projects/Better Call Wes/website/scripts/servicem8/inbox_watch.py" --run
