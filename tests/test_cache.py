from pathlib import Path

from storage.cache import SQLiteHttpCache, default_cache_path


def test_cache_uses_borsa_mcp_cache_dir(monkeypatch, tmp_path):
    cache_dir = tmp_path / "custom-cache"
    monkeypatch.setenv("BORSA_MCP_CACHE_DIR", str(cache_dir))
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
    assert default_cache_path() == cache_dir / "http_cache.sqlite3"
    cache = SQLiteHttpCache()
    assert cache.path == cache_dir / "http_cache.sqlite3"
    assert cache.path.parent.exists()


def test_cache_round_trip_json_serializable_datetime(tmp_path):
    cache = SQLiteHttpCache(tmp_path / "nested" / "cache.sqlite3")
    entry = cache.set("https://example.test", "body", 200, ttl_seconds=60)
    cached = cache.get("https://example.test")
    assert cached is not None
    assert cached.body == "body"
    assert cached.fetched_at.isoformat() == entry.fetched_at.isoformat()
    assert Path(cache.path).parent.exists()
