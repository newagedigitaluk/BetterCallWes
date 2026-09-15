#!/usr/bin/env python3
"""One-off OAuth dance for the Google Ads API, from a machine with no browser.

The VPS is headless and Google killed the out-of-band flow in 2022, so the
loopback redirect is the only option left. It does work here, just not the
way it looks: Wes opens the URL on his Mac, approves, and Google redirects
to http://localhost:8080/?code=... which fails to load because nothing is
listening on the Mac. That failure is fine. The code is in the address bar.

    python lsa_oauth.py url                 # print the consent URL
    python lsa_oauth.py exchange '<url>'    # swap the code for a refresh token

Writes GOOGLE_ADS_REFRESH_TOKEN into .env. Never prints it: a refresh token
does not expire, so it belongs in a file rather than in scrollback.
"""
import os
import sys
import json
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path

ENV = Path("/home/wes/Coding/Projects/Better Call Wes/.env")
REDIRECT = "http://localhost:8080"
SCOPE = "https://www.googleapis.com/auth/adwords"


def env(key: str) -> str:
    for line in ENV.read_text().splitlines():
        if line.startswith(key + "="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit(f"{key} missing from .env")


def auth_url() -> str:
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": env("GOOGLE_ADS_CLIENT_ID"),
        "redirect_uri": REDIRECT,
        "response_type": "code",
        "scope": SCOPE,
        # offline + consent together are what actually produce a refresh
        # token. Without prompt=consent Google silently returns only an
        # access token on any repeat authorisation, and the whole thing
        # looks like it worked until it stops an hour later.
        "access_type": "offline",
        "prompt": "consent",
    })


def exchange(pasted: str) -> None:
    q = urllib.parse.parse_qs(urllib.parse.urlparse(pasted.strip()).query)
    if "error" in q:
        raise SystemExit(f"Google returned an error: {q['error'][0]}")
    code = (q.get("code") or [None])[0]
    if not code:
        raise SystemExit("No ?code= in that URL. Paste the whole address bar.")
    body = urllib.parse.urlencode({
        "code": code,
        "client_id": env("GOOGLE_ADS_CLIENT_ID"),
        "client_secret": env("GOOGLE_ADS_CLIENT_SECRET"),
        "redirect_uri": REDIRECT,
        "grant_type": "authorization_code",
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=body)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            tok = json.load(r)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Token exchange failed {e.code}: {e.read().decode()[:300]}")

    rt = tok.get("refresh_token")
    if not rt:
        raise SystemExit(
            "Google returned no refresh token. That happens when the code has "
            "already been used, or prompt=consent was dropped. Start again.")

    text = ENV.read_text()
    line = f"GOOGLE_ADS_REFRESH_TOKEN={rt}"
    if "GOOGLE_ADS_REFRESH_TOKEN=" in text:
        text = "\n".join(line if l.startswith("GOOGLE_ADS_REFRESH_TOKEN=") else l
                         for l in text.splitlines()) + "\n"
    else:
        text = text.rstrip("\n") + "\n" + line + "\n"
    ENV.write_text(text)
    print(f"refresh token saved to .env ({len(rt)} chars). Access token valid "
          f"{tok.get('expires_in')}s, which we don't need to keep.")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("url", "exchange"):
        raise SystemExit(__doc__)
    if sys.argv[1] == "url":
        print(auth_url())
    else:
        exchange(sys.argv[2])
