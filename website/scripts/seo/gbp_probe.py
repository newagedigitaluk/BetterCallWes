"""Quick probe: is the Google Business Profile API quota approved yet?

Reuses the same OAuth user token as gsc_client.py (it already carries the
business.manage scope). Calls the Account Management API to list accounts.

Exit / output meaning:
  - Lists account(s)            -> quota APPROVED, we're in business
  - HTTP 429 RESOURCE_EXHAUSTED -> still throttled at 0/min (NOT approved)
  - HTTP 403 ... has not been used / disabled -> API not enabled on project
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from google.oauth2.credentials import Credentials as UserCredentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

ROOT = Path(__file__).resolve().parents[3]
TOKEN_PATH = ROOT / ".credentials" / "gsc-token.json"


def load_creds():
    data = json.loads(TOKEN_PATH.read_text(encoding="utf-8"))
    creds = UserCredentials(
        token=data.get("token"),
        refresh_token=data.get("refresh_token"),
        token_uri=data.get("token_uri"),
        client_id=data.get("client_id"),
        client_secret=data.get("client_secret"),
        scopes=data.get("scopes"),
    )
    if not creds.valid:
        creds.refresh(Request())
        data["token"] = creds.token
        TOKEN_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return creds


def main() -> int:
    creds = load_creds()
    print("Token refreshed OK. Scopes:", creds.scopes)

    # Account Management API — this is the one that was capped at 0 req/min.
    try:
        svc = build(
            "mybusinessaccountmanagement",
            "v1",
            credentials=creds,
            cache_discovery=False,
        )
        resp = svc.accounts().list().execute()
        accounts = resp.get("accounts", [])
        print(f"\n✅ QUOTA APPROVED — Account Management API responded.")
        print(f"   Accounts visible: {len(accounts)}")
        for a in accounts:
            print(f"   - {a.get('name')}  |  {a.get('accountName')}  |  type={a.get('type')}")
        if not accounts:
            print("   (No accounts returned — token works but no GBP account is linked to this Google user.)")
        return 0
    except HttpError as e:
        status = getattr(e.resp, "status", "?")
        body = e.content.decode("utf-8", "replace") if hasattr(e, "content") else str(e)
        print(f"\n❌ HTTP {status}")
        print(body[:800])
        if status == 429 or "RESOURCE_EXHAUSTED" in body:
            print("\n→ Verdict: STILL THROTTLED. Quota increase not approved yet.")
        elif status == 403 and ("has not been used" in body or "disabled" in body or "SERVICE_DISABLED" in body):
            print("\n→ Verdict: API not enabled on the Cloud project (separate from quota).")
        elif status == 403:
            print("\n→ Verdict: 403 — likely permission/quota. Check message above.")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {type(e).__name__}: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
