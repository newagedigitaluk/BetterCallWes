"""One-time OAuth flow to authorise GSC access using a user Google account.

Run this once. It prints a Google sign-in URL, you open it on any device
(phone/Mac), grant access, and Google redirects to a localhost URL that
will fail to load — that's expected. Copy the FULL URL from your
browser's address bar and paste it back here. We extract the auth code,
exchange it for tokens, and save a refresh token to .credentials/gsc-token.json.

After this runs successfully, gsc_client.py can use the saved token
indefinitely (it auto-refreshes when needed).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from google_auth_oauthlib.flow import Flow

ROOT = Path(__file__).resolve().parents[3]
CLIENT_SECRET = ROOT / ".credentials" / "gsc-oauth-client.json"
TOKEN_PATH = ROOT / ".credentials" / "gsc-token.json"
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]


def main() -> int:
    if not CLIENT_SECRET.exists():
        print(f"Missing OAuth client secret at {CLIENT_SECRET}", file=sys.stderr)
        return 1

    flow = Flow.from_client_secrets_file(
        str(CLIENT_SECRET),
        scopes=SCOPES,
        redirect_uri="http://localhost",
    )
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    print("\n" + "=" * 70)
    print("STEP 1: Open this URL on any device (phone, Mac, anywhere):")
    print()
    print(auth_url)
    print()
    print("STEP 2: Sign in with the Google account that owns the GSC property.")
    print("        (The 'Better Call Wes' account that can see bettercallwes.co.uk.)")
    print()
    print("STEP 3: Approve the access request.")
    print()
    print("STEP 4: Google will redirect to a URL that starts with 'http://localhost?code=...'")
    print("        Your browser will say 'This site can't be reached' or similar —")
    print("        THAT IS EXPECTED. Copy the FULL URL from your browser's address bar.")
    print()
    print("STEP 5: Paste it below.")
    print("=" * 70 + "\n")

    redirect_response = input("Paste the full localhost redirect URL here: ").strip()
    if not redirect_response.startswith("http://localhost"):
        print(f"That doesn't look like a localhost URL: {redirect_response[:80]}", file=sys.stderr)
        return 1

    flow.fetch_token(authorization_response=redirect_response)
    creds = flow.credentials

    # Save the credentials in the format google.oauth2.credentials.Credentials can reload
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

    print(f"\n✓ Token saved to {TOKEN_PATH}")
    print(f"  Refresh token present: {bool(creds.refresh_token)}")
    print(f"  Scopes: {creds.scopes}")
    print("\nDone. You can now run: python3 website/scripts/seo/gsc_client.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
