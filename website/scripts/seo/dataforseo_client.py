"""DataForSEO REST API client — thin stdlib-only wrapper.

Loads credentials from project .env (DATAFORSEO_LOGIN, DATAFORSEO_PASSWORD),
uses HTTP Basic auth, retries on 429 and 5xx with exponential backoff.
"""

from __future__ import annotations

import base64
import json
import os
import random
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

API_BASE = "https://api.dataforseo.com"
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


class DataForSEOError(Exception):
    pass


class DataForSEOClient:
    def __init__(
        self,
        login: str | None = None,
        password: str | None = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        if login is None or password is None:
            env = _load_env(_project_root() / ".env")
            login = login or env.get("DATAFORSEO_LOGIN") or os.environ.get("DATAFORSEO_LOGIN")
            password = (
                password
                or env.get("DATAFORSEO_PASSWORD")
                or os.environ.get("DATAFORSEO_PASSWORD")
            )
        if not login or not password:
            raise DataForSEOError(
                "DATAFORSEO_LOGIN / DATAFORSEO_PASSWORD not found in .env or environment"
            )
        token = base64.b64encode(f"{login}:{password}".encode()).decode()
        self._auth_header = f"Basic {token}"
        self._timeout = timeout

    def post(self, path: str, payload: list[dict[str, Any]] | dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", path, payload)

    def get(self, path: str) -> dict[str, Any]:
        return self._request("GET", path, None)

    def _request(
        self,
        method: str,
        path: str,
        payload: list[dict[str, Any]] | dict[str, Any] | None,
    ) -> dict[str, Any]:
        url = API_BASE + (path if path.startswith("/") else "/" + path)
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {
            "Authorization": self._auth_header,
            "Accept": "application/json",
        }
        if body is not None:
            headers["Content-Type"] = "application/json"
        last_err: Exception | None = None
        for attempt in range(MAX_RETRIES + 1):
            req = urllib.request.Request(url, data=body, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                    raw = resp.read()
                    data = json.loads(raw.decode("utf-8"))
                    status_code = data.get("status_code")
                    if status_code is not None and status_code >= 40000:
                        raise DataForSEOError(
                            f"API error {status_code}: {data.get('status_message')}"
                        )
                    return data
            except urllib.error.HTTPError as e:
                last_err = e
                if e.code in RETRY_STATUSES and attempt < MAX_RETRIES:
                    self._sleep(attempt)
                    continue
                try:
                    err_body = e.read().decode("utf-8", errors="replace")
                except Exception:
                    err_body = ""
                raise DataForSEOError(f"HTTP {e.code} {e.reason}: {err_body[:500]}") from e
            except urllib.error.URLError as e:
                last_err = e
                if attempt < MAX_RETRIES:
                    self._sleep(attempt)
                    continue
                raise DataForSEOError(f"Network error: {e}") from e
        raise DataForSEOError(f"Exhausted retries: {last_err}")

    @staticmethod
    def _sleep(attempt: int) -> None:
        base = 2 ** attempt
        jitter = random.uniform(0, 0.5)
        time.sleep(base + jitter)


if __name__ == "__main__":
    client = DataForSEOClient()
    result = client.get("/v3/appendix/user_data")
    print(json.dumps(result, indent=2)[:2000])
