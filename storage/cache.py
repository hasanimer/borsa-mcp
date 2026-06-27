from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path


@dataclass
class CacheEntry:
    url: str
    fetched_at: datetime
    body: str
    content_hash: str
    status_code: int
    is_stale: bool


class SQLiteHttpCache:
    def __init__(self, path: str | Path = ".cache/http_cache.sqlite3") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS http_cache (
                    source_url TEXT PRIMARY KEY,
                    fetched_at TEXT NOT NULL,
                    response_body TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    status_code INTEGER NOT NULL,
                    expires_at TEXT NOT NULL
                )
            """)

    def get(self, url: str) -> CacheEntry | None:
        with sqlite3.connect(self.path) as conn:
            row = conn.execute(
                "SELECT source_url, fetched_at, response_body, content_hash, status_code, expires_at FROM http_cache WHERE source_url=?",
                (url,),
            ).fetchone()
        if not row:
            return None
        now = datetime.utcnow()
        return CacheEntry(row[0], datetime.fromisoformat(row[1]), row[2], row[3], row[4], datetime.fromisoformat(row[5]) < now)

    def set(self, url: str, body: str, status_code: int, ttl_seconds: int) -> CacheEntry:
        fetched_at = datetime.utcnow()
        expires_at = fetched_at + timedelta(seconds=ttl_seconds)
        content_hash = hashlib.sha256(body.encode("utf-8", errors="ignore")).hexdigest()
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "REPLACE INTO http_cache VALUES (?, ?, ?, ?, ?, ?)",
                (url, fetched_at.isoformat(), body, content_hash, status_code, expires_at.isoformat()),
            )
        return CacheEntry(url, fetched_at, body, content_hash, status_code, False)
