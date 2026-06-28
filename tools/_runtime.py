"""Shared runtime helpers for the advanced (MKK/SPK/Takasbank) tool modules.

These tools wrap synchronous ``httpx`` + SQLite access. Calling them directly
inside an ``async def`` would block the FastMCP event loop, so :func:`run_tool`
offloads the work to a worker thread. It also applies ``strip_nulls`` so the
responses honor the same null-stripping contract the 28 unified tools rely on.
"""
from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from providers.response_shaper import strip_nulls


async def run_tool(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Run a blocking provider/service call off the event loop, null-strip result."""
    result = await asyncio.to_thread(fn, *args, **kwargs)
    return strip_nulls(result)
