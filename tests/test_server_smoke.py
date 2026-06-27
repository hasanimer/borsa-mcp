"""Smoke test: the unified server exposes the expected tool surface."""
import asyncio

from unified_mcp_server import app


async def _list_tool_names():
    if hasattr(app, "list_tools"):
        tools = await app.list_tools()
    elif hasattr(app, "get_tools"):
        tools = await app.get_tools()
    else:
        tools = await app._list_tools()
    if isinstance(tools, dict):
        return set(tools)
    return {tool.name for tool in tools}


def test_server_exposes_expected_tools():
    names = asyncio.run(_list_tool_names())
    assert len(names) == 38
    for name in ["get_spk_data_sources", "get_equity_investor_summary", "get_takasbank_kyp_options"]:
        assert name in names
