"""Simple in-memory caching primitives for SDK GET requests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional


@dataclass
class CacheEntry:
    value: Any
    expires_at: datetime


class MemoryCache:
    """A tiny TTL cache used to reduce repeated read requests."""

    def __init__(self, ttl_seconds: int = 30, max_entries: int = 256):
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._entries: Dict[str, CacheEntry] = {}

    def get(self, key: str) -> Optional[Any]:
        entry = self._entries.get(key)
        if entry is None:
            return None

        if entry.expires_at <= datetime.now(timezone.utc):
            self._entries.pop(key, None)
            return None

        return entry.value

    def set(self, key: str, value: Any) -> None:
        if self.max_entries <= 0:
            return

        if len(self._entries) >= self.max_entries:
            oldest_key = next(iter(self._entries))
            self._entries.pop(oldest_key, None)

        self._entries[key] = CacheEntry(
            value=value,
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=self.ttl_seconds),
        )

    def clear(self) -> None:
        self._entries.clear()
