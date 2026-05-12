"""Tiny in-memory TTL cache.

We don't need Redis for this app — single-instance, low traffic, the SM8
rate limit (180/min) protects us if cache fails. Keep it simple.
"""
from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class TTLCache(Generic[T]):
    """Single-value async TTL cache. Coalesces concurrent fetches."""

    def __init__(self, ttl_seconds: float, fetch: Callable[[], Awaitable[T]]) -> None:
        self._ttl = ttl_seconds
        self._fetch = fetch
        self._value: T | None = None
        self._fetched_at: float = 0.0
        self._lock = asyncio.Lock()

    async def get(self) -> T:
        now = time.monotonic()
        if self._value is not None and (now - self._fetched_at) < self._ttl:
            return self._value
        async with self._lock:
            # Re-check after acquiring the lock (another caller may have refreshed)
            now = time.monotonic()
            if self._value is not None and (now - self._fetched_at) < self._ttl:
                return self._value
            self._value = await self._fetch()
            self._fetched_at = now
            return self._value

    def invalidate(self) -> None:
        self._value = None
        self._fetched_at = 0.0


class KeyedTTLCache(Generic[T]):
    """Keyed async TTL cache (one TTL per key)."""

    def __init__(self, ttl_seconds: float) -> None:
        self._ttl = ttl_seconds
        self._store: dict[str, tuple[T, float]] = {}
        self._lock = asyncio.Lock()

    async def get_or_set(self, key: str, fetch: Callable[[], Awaitable[T]]) -> T:
        now = time.monotonic()
        if key in self._store:
            value, ts = self._store[key]
            if (now - ts) < self._ttl:
                return value
        async with self._lock:
            if key in self._store:
                value, ts = self._store[key]
                if (time.monotonic() - ts) < self._ttl:
                    return value
            value = await fetch()
            self._store[key] = (value, time.monotonic())
            return value

    def invalidate(self, key: str | None = None) -> None:
        if key is None:
            self._store.clear()
        else:
            self._store.pop(key, None)
