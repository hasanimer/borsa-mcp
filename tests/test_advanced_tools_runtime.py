"""run_tool offloads blocking work to a thread and null-strips the result."""
import asyncio
import threading

from tools._runtime import run_tool


def test_run_tool_strips_nulls_recursively():
    def sync_fn(x):
        return {
            "a": x,
            "b": None,
            "nested": {"c": None, "d": 2},
            "items": [{"e": None, "f": 3}],
            "empty": [],
        }

    result = asyncio.run(run_tool(sync_fn, 5))
    assert result == {"a": 5, "nested": {"d": 2}, "items": [{"f": 3}], "empty": []}


def test_run_tool_runs_off_event_loop_thread():
    main_thread = threading.get_ident()
    captured = {}

    def sync_fn():
        captured["thread"] = threading.get_ident()
        return {"ok": True}

    result = asyncio.run(run_tool(sync_fn))
    assert result == {"ok": True}
    assert captured["thread"] != main_thread  # executed in a worker thread, not the loop
