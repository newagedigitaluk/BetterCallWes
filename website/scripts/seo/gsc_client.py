"""Google Search Console REST client.

Prefers OAuth user credentials (saved token from gsc_oauth_setup.py).
Falls back to service-account if/when Google fixes the user-add bug.

Run directly to list the GSC properties your account can read.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from google.oauth2.credentials import Credentials as UserCredentials
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

ROOT = Path(__file__).resolve().parents[3]
TOKEN_PATH = ROOT / ".credentials" / "gsc-token.json"
SERVICE_ACCOUNT_PATH = ROOT / ".credentials" / "gsc-service-account.json"
DEFAULT_PROPERTY = "sc-domain:bettercallwes.co.uk"
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]


class GSCError(Exception):
    pass


def _load_credentials():
    """Load OAuth user creds if available; refresh if needed."""
    if TOKEN_PATH.exists():
        data = json.loads(TOKEN_PATH.read_text(encoding="utf-8"))
        creds = UserCredentials(
            token=data.get("token"),
            refresh_token=data.get("refresh_token"),
            token_uri=data.get("token_uri"),
            client_id=data.get("client_id"),
            client_secret=data.get("client_secret"),
            scopes=data.get("scopes") or SCOPES,
        )
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Persist the refreshed access token
            data["token"] = creds.token
            TOKEN_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return creds

    if SERVICE_ACCOUNT_PATH.exists():
        return service_account.Credentials.from_service_account_file(
            str(SERVICE_ACCOUNT_PATH), scopes=SCOPES
        )

    raise GSCError(
        "No GSC credentials found. Run: python3 website/scripts/seo/gsc_oauth_setup.py"
    )


class GSCClient:
    def __init__(self) -> None:
        creds = _load_credentials()
        self._service = build(
            "searchconsole", "v1", credentials=creds, cache_discovery=False
        )

    def list_sites(self) -> list[dict[str, Any]]:
        resp = self._service.sites().list().execute()
        return resp.get("siteEntry", [])

    def search_analytics(
        self,
        site_url: str = DEFAULT_PROPERTY,
        start_date: str = "",
        end_date: str = "",
        dimensions: list[str] | None = None,
        row_limit: int = 5000,
        start_row: int = 0,
        filters: list[dict[str, str]] | None = None,
        search_type: str = "web",
        data_state: str = "all",
    ) -> list[dict[str, Any]]:
        body: dict[str, Any] = {
            "startDate": start_date,
            "endDate": end_date,
            "dimensions": dimensions or [],
            "rowLimit": row_limit,
            "startRow": start_row,
            "type": search_type,
            "dataState": data_state,
        }
        if filters:
            body["dimensionFilterGroups"] = [{"filters": filters}]
        resp = (
            self._service.searchanalytics()
            .query(siteUrl=site_url, body=body)
            .execute()
        )
        return resp.get("rows", [])


if __name__ == "__main__":
    import sys

    c = GSCClient()
    sites = c.list_sites()
    print("GSC properties the credentials can read:")
    for s in sites:
        print(f"  {s.get('siteUrl')}  ({s.get('permissionLevel')})")
    if not sites:
        print("  (none — credentials are valid but no properties are accessible)")
        sys.exit(1)
