"""
Linke URL shortener client.

API docs: https://api.linke.to/

Used to create per-post short links inside the "Better Call Wes" folder so
we can attribute clicks back to individual social posts. The folder must
already exist on the linke.to dashboard before any create_short_link call
referencing it — there is no API endpoint to create folders.

Auth: Bearer token via LINKE_API_KEY env var.
Rate limit: 500 requests/day, 15,000/month.
"""

import os
import requests


LINKE_API_KEY = os.environ.get("LINKE_API_KEY", "")
BASE_URL = "https://api.linke.to"
DEFAULT_FOLDER = "Better Call Wes"
DEFAULT_DOMAIN = "u.bettercallwes.co.uk"


class LinkeClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or LINKE_API_KEY
        if not self.api_key:
            raise ValueError("LINKE_API_KEY environment variable is not set.")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })

    # ---- Account ----

    def account_info(self) -> dict:
        """Return the account info payload (email, status, link counts, etc.)."""
        resp = self.session.get(f"{BASE_URL}/account")
        resp.raise_for_status()
        return resp.json()

    # ---- Short links ----

    def create_short_link(
        self,
        url: str,
        name: str = None,
        folder: str = DEFAULT_FOLDER,
        title: str = None,
        domain: str = DEFAULT_DOMAIN,
    ) -> dict:
        """
        Create a short link inside `folder`.

        Args:
            url:    Long URL to shorten (required).
            name:   Desired short slug (optional — Linke generates one if omitted).
            folder: Folder name on the Linke dashboard (must already exist).
            title:  Display title for the short link (optional).
            domain: Domain for the short link (defaults to linke.to).

        Returns:
            Parsed JSON response. The short URL is at result['data']['short_link'].

        Raises:
            requests.HTTPError if Linke returns a non-2xx.
            RuntimeError if the response indicates an error.
        """
        payload = {"url": url, "domain": domain, "folder": folder}
        if name:
            payload["name"] = name
        if title:
            payload["title"] = title

        resp = self.session.post(f"{BASE_URL}/shorts/add", json=payload)
        resp.raise_for_status()
        data = resp.json()
        if data.get("message") != "Ok":
            raise RuntimeError(f"Linke create_short_link failed: {data}")
        return data

    def list_short_links(self, folder: str = DEFAULT_FOLDER, page: int = 1) -> list:
        """
        List short links inside a folder (50 per page).

        Note: the API silently 301-redirects /shorts to /shorts/ and drops
        the Authorization header on the redirect, so we hit /shorts/ directly.
        """
        params = {"folder": folder, "page": page}
        resp = self.session.get(f"{BASE_URL}/shorts/", params=params)
        resp.raise_for_status()
        data = resp.json()
        if data.get("message") != "Ok":
            raise RuntimeError(f"Linke list_short_links failed: {data}")
        return data.get("data", [])

    def view_short_link(self, short_link: str) -> dict:
        """
        Get info + click analytics for a single short link.

        Args:
            short_link: Full short URL, e.g. https://linke.to/bcw-radiator-bleed
        """
        resp = self.session.get(f"{BASE_URL}/view", params={"link": short_link})
        resp.raise_for_status()
        data = resp.json()
        if data.get("message") != "Ok":
            raise RuntimeError(f"Linke view_short_link failed: {data}")
        return data.get("data", {})

    def delete_short_link(self, short_link: str) -> dict:
        """Permanently delete a short link and all its analytics. Irreversible."""
        resp = self.session.post(f"{BASE_URL}/delete", json={"link": short_link})
        resp.raise_for_status()
        return resp.json()


if __name__ == "__main__":
    # Quick smoke test — fetch account info to verify the key works
    client = LinkeClient()
    info = client.account_info()
    print("✅ Linke API key works")
    print(f"   Status: {info.get('status')}")
    print(f"   Short links: {info.get('short_links')}")
    print(f"   Total hits across all links: {info.get('total_hits')}")
