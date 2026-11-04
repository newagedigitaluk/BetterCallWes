"""Tiny HighLevel (LeadConnector) API client for the BCW sub-account.

Reads GHL_PIT_TOKEN and GHL_LOCATION_ID from the environment. Load them with
`with-secret .env -- python3 ...` from the project root; never print them.
"""
import json
import os
import urllib.error
import urllib.request

BASE = "https://services.leadconnectorhq.com"


def call(method, path, body=None, version="2021-07-28"):
    """Return (status, json). `{LOC}` in path is replaced with the location id."""
    path = path.replace("{LOC}", os.environ["GHL_LOCATION_ID"])
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method, headers={
        "Authorization": "Bearer " + os.environ["GHL_PIT_TOKEN"],
        "Version": version,
        "Accept": "application/json",
        "Content-Type": "application/json",
        # Cloudflare blocks Python's default User-Agent.
        "User-Agent": "bcw-ghl-setup/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"{}")
        except ValueError:
            return e.code, {}
