"""Re-seed the Google OAuth token with ALL THREE scopes (GSC + GA4 + GBP).

Split into two steps so the auth URL can be generated in one process and the
token exchanged in another (avoids the PKCE/state-lost-between-processes bug).

Usage:
  python3 gbp_reauth.py --start
      -> prints a Google sign-in URL, saves the PKCE verifier to /tmp.

  python3 gbp_reauth.py --finish "http://localhost/?code=...&scope=..."
      -> exchanges the pasted redirect URL for a token, writes gsc-token.json.

Re-seeds .credentials/gsc-token.json with a fresh refresh token.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from google_auth_oauthlib.flow import Flow

ROOT = Path(__file__).resolve().parents[3]
CLIENT_SECRET = ROOT / ".credentials" / "gsc-oauth-client.json"
TOKEN_PATH = ROOT / ".credentials" / "gsc-token.json"
STATE_PATH = Path("/tmp/bcw_oauth_reauth_state.json")

SCOPES = [
    "https://www.googleapis.com/auth/webmasters.readonly",
    "https://www.googleapis.com/auth/analytics.readonly",
    "https://www.googleapis.com/auth/business.manage",
]
REDIRECT_URI = "http://localhost"


def _new_flow() -> Flow:
    return Flow.from_client_secrets_file(
        str(CLIENT_SECRET),
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )


def start() -> int:
    if not CLIENT_SECRET.exists():
        print(f"Missing OAuth client secret at {CLIENT_SECRET}", file=sys.stderr)
        return 1

    flow = _new_flow()
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",   # forces a fresh refresh token
    )

    # Persist what we need to finish the exchange in a separate process.
    STATE_PATH.write_text(
        json.dumps({
            "state": state,
            "code_verifier": flow.code_verifier,
        }),
        encoding="utf-8",
    )

    print("\n" + "=" * 72)
    print("STEP 1 — open this URL (phone or Mac), sign in as the Google account")
    print("         that owns the Better Call Wes GBP + Search Console:")
    print()
    print(auth_url)
    print()
    print("STEP 2 — approve ALL requested permissions (Search Console, Analytics,")
    print("         AND Business Profile — say yes to each).")
    print()
    print("STEP 3 — Google redirects to a 'http://localhost/?code=...' page that")
    print("         WON'T LOAD. That's expected. Copy the FULL address-bar URL.")
    print()
    print("STEP 4 — paste it back and I'll finish the exchange.")
    print("=" * 72 + "\n")
    return 0


def finish(redirect_response: str) -> int:
    if not STATE_PATH.exists():
        print("No saved state — run `--start` first.", file=sys.stderr)
        return 1
    saved = json.loads(STATE_PATH.read_text(encoding="utf-8"))

    redirect_response = redirect_response.strip()
    if not redirect_response.startswith("http://localhost"):
        print(f"That doesn't look like a localhost URL: {redirect_response[:80]}", file=sys.stderr)
        return 1

    flow = _new_flow()
    flow.code_verifier = saved.get("code_verifier")
    flow.fetch_token(authorization_response=redirect_response)
    creds = flow.credentials

    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
    }
    TOKEN_PATH.write_text(json.dumps(token_data, indent=2), encoding="utf-8")
    TOKEN_PATH.chmod(0o600)
    STATE_PATH.unlink(missing_ok=True)

    print(f"\n✓ Token re-seeded at {TOKEN_PATH}")
    print(f"  Refresh token present: {bool(creds.refresh_token)}")
    print(f"  Scopes granted: {creds.scopes}")
    missing = [s for s in SCOPES if s not in (creds.scopes or [])]
    if missing:
        print(f"  ⚠ Missing scopes (you may have unticked one): {missing}")
    print("\nNext: python3 website/scripts/seo/gbp_probe.py")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", action="store_true", help="print the auth URL")
    ap.add_argument("--finish", metavar="REDIRECT_URL", help="exchange the pasted redirect URL")
    args = ap.parse_args()

    if args.start:
        return start()
    if args.finish:
        return finish(args.finish)
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
