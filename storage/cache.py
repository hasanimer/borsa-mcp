from __future__ import annotations

import hashlib
import os
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path


def _default_cache_dir() -> Path:
    """Resolve a user-writable cache directory for Borsa MCP HTTP cache files."""
    env_dir = os.getenv("BORSA_MCP_CACHE_DIR")
    if env_dir:
        return Path(env_dir).expanduser()

    xdg_cache_home = os.getenv("XDG_CACHE_HOME")
    if xdg_cache_home:
        return Path(xdg_cache_home).expanduser() / "borsa-mcp"

    local_app_data = os.getenv("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data).expanduser() / "borsa-mcp" / "Cache"

    return Path.home() / ".cache" / "borsa-mcp"


def default_cache_path() -> Path:
    return _default_cache_dir() / "http_cache.sqlite3"


@dataclass
class CacheEntry:
    url: str
    fetched_at: datetime
    body: str
    content_hash: str
    status_code: int
    is_stale: bool


class SQLiteHttpCache:
    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path).expanduser() if path is not None else default_cache_path()
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
        now = datetime.now(UTC)
        fetched_at = datetime.fromisoformat(row[1])
        expires_at = datetime.fromisoformat(row[5])
        return CacheEntry(row[0], fetched_at, row[2], row[3], row[4], expires_at < now)

    def set(self, url: str, body: str, status_code: int, ttl_seconds: int) -> CacheEntry:
        fetched_at = datetime.now(UTC)
        expires_at = fetched_at + timedelta(seconds=ttl_seconds)
        content_hash = hashlib.sha256(body.encode("utf-8", errors="ignore")).hexdigest()
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "REPLACE INTO http_cache VALUES (?, ?, ?, ?, ?, ?)",
                (url, fetched_at.isoformat(), body, content_hash, status_code, expires_at.isoformat()),
            )
        return CacheEntry(url, fetched_at, body, content_hash, status_code, False)
