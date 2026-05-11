"""VebAPI REST client — stdlib-only wrapper.

Loads VEBAPI_KEY from the project .env, uses X-API-KEY header, retries on
429 and 5xx with exponential backoff.
"""

from __future__ import annotations

import json
import os
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

API_BASE = "https://vebapi.com"
DEFAULT_TIMEOUT = 60
MAX_RETRIES = 4
RETRY_STATUSES = {429, 500, 502, 503, 504}


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_env(env_path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not env_path.exists():
        return env
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


class VebAPIError(Exception):
    pass


class VebAPIClient:
    def __init__(self, api_key: str | None = None, timeout: int = DEFAULT_TIMEOUT) -> None:
        if api_key is None:
            env = _load_env(_project_root() / ".env")
            api_key = env.get("VEBAPI_KEY") or os.environ.get("VEBAPI_KEY")
        if not api_key:
            raise VebAPIError("VEBAPI_KEY not found in .env or environment")
        self._key = api_key
        self._timeout = timeout

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = API_BASE + (path if path.startswith("/") else "/" + path)
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"
        headers = {
            "X-API-KEY": self._key,
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) bettercallwes-seo/1.0",
        }
        last_err: Exception | None = None
        for attempt in range(MAX_RETRIES + 1):
            req = urllib.request.Request(url, headers=headers, method="GET")
            try:
                with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                    raw = resp.read()
                    return json.loads(raw.decode("utf-8"))
            except urllib.error.HTTPError as e:
                last_err = e
                if e.code in RETRY_STATUSES and attempt < MAX_RETRIES:
                    self._sleep(attempt)
                    continue
                try:
                    err_body = e.read().decode("utf-8", errors="replace")
                except Exception:
                    err_body = ""
                raise VebAPIError(f"HTTP {e.code} {e.reason}: {err_body[:500]}") from e
            except urllib.error.URLError as e:
                last_err = e
                if attempt < MAX_RETRIES:
                    self._sleep(attempt)
                    continue
                raise VebAPIError(f"Network error: {e}") from e
        raise VebAPIError(f"Exhausted retries: {last_err}")

    @staticmethod
    def _sleep(attempt: int) -> None:
        time.sleep((2 ** attempt) + random.uniform(0, 0.5))


if __name__ == "__main__":
    c = VebAPIClient()
    r = c.get("/api/seo/backlinkdata", {"website": "bettercallwes.co.uk"})
    counts = r.get("counts") or {}
    print("backlinks:", (counts.get("backlinks") or {}).get("total"))
    print("ref domains:", (counts.get("domains") or {}).get("total"))
    print("sample rows:", len(r.get("backlinks") or []))
