from __future__ import annotations

import time
import httpx
from storage.cache import SQLiteHttpCache, CacheEntry

UA = "borsa-mcp/0.9 (+https://github.com/hasanimer/borsa-mcp)"

class ProviderHttpClient:
    def __init__(self, *, timeout: float = 20.0, retries: int = 2, cache_ttl: int = 3600):
        self.timeout = timeout
        self.retries = retries
        self.cache_ttl = cache_ttl
        self.cache = SQLiteHttpCache()

    def get_text(self, url: str, *, headers: dict[str, str] | None = None) -> tuple[str, CacheEntry, list[str]]:
        cached = self.cache.get(url)
        warnings: list[str] = []
        if cached and not cached.is_stale and cached.status_code < 400:
            return cached.body, cached, ["Response served from local cache."]
        merged_headers = {"User-Agent": UA, "Accept": "text/html,application/json,*/*"}
        if headers:
            merged_headers.update(headers)
        last_exc: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                with httpx.Client(timeout=self.timeout, follow_redirects=True, headers=merged_headers) as client:
                    response = client.get(url)
                    response.raise_for_status()
                    entry = self.cache.set(url, response.text, response.status_code, self.cache_ttl)
                    if cached and cached.is_stale:
                        warnings.append("Cached response was stale and has been refreshed.")
                    return response.text, entry, warnings
            except Exception as exc:  # preserved and surfaced below
                last_exc = exc
                if attempt < self.retries:
                    time.sleep(0.3 * (attempt + 1))
        if cached:
            cached.is_stale = True
            return cached.body, cached, [f"Live fetch failed; stale cached response used: {last_exc}"]
        raise RuntimeError(f"HTTP fetch failed for {url}: {last_exc}")
