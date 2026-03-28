"""Tests for web navigation tools."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.tools.navigation import register_navigation_tools


def make_mcp():
    mcp = MagicMock()
    tools = {}
    def tool_decorator(fn):
        tools[fn.__name__] = fn
        return fn
    mcp.tool = tool_decorator
    mcp._registered_tools = tools
    return mcp


def make_ctx(call_tool_side_effect=None):
    ctx = AsyncMock()
    ctx.report_progress = AsyncMock()
    ctx.fastmcp = AsyncMock()
    if call_tool_side_effect:
        ctx.fastmcp.call_tool = AsyncMock(side_effect=call_tool_side_effect)
    else:
        ctx.fastmcp.call_tool = AsyncMock(return_value="<snapshot content>")
    return ctx


class TestWebNavigateAndWait:
    def setup_method(self):
        self.mcp = make_mcp()
        register_navigation_tools(self.mcp)
        self.tool = self.mcp._registered_tools["web_navigate_and_wait"]

    @pytest.mark.asyncio
    async def test_navigates_to_url(self):
        ctx = make_ctx()
        await self.tool(url="https://example.com", ctx=ctx)
        ctx.fastmcp.call_tool.assert_any_call("playwright_browser_navigate", {"url": "https://example.com"})

    @pytest.mark.asyncio
    async def test_returns_url(self):
        ctx = make_ctx()
        result = await self.tool(url="https://example.com", ctx=ctx)
        assert result["url"] == "https://example.com"

    @pytest.mark.asyncio
    async def test_returns_loaded_flag(self):
        ctx = make_ctx()
        result = await self.tool(url="https://example.com", ctx=ctx)
        assert "loaded" in result and isinstance(result["loaded"], bool)

    @pytest.mark.asyncio
    async def test_returns_snapshot(self):
        ctx = make_ctx()
        result = await self.tool(url="https://example.com", ctx=ctx)
        assert "snapshot" in result

    @pytest.mark.asyncio
    async def test_returns_wait_seconds(self):
        ctx = make_ctx()
        result = await self.tool(url="https://example.com", ctx=ctx)
        assert "wait_seconds" in result

    @pytest.mark.asyncio
    async def test_with_wait_for_text(self):
        ctx = make_ctx()
        await self.tool(url="https://example.com", ctx=ctx, wait_for_text="Dashboard")
        ctx.fastmcp.call_tool.assert_any_call("playwright_browser_wait_for", {"text": "Dashboard"})

    @pytest.mark.asyncio
    async def test_wait_for_text_timeout_graceful(self):
        async def side_effect(tool_name, args):
            if tool_name == "playwright_browser_wait_for":
                raise TimeoutError("Text not found")
            return "<snapshot>"
        ctx = make_ctx(call_tool_side_effect=side_effect)
        result = await self.tool(url="https://example.com", ctx=ctx, wait_for_text="Missing")
        assert result["url"] == "https://example.com"

    @pytest.mark.asyncio
    async def test_without_wait_for_text_polls_snapshot(self):
        ctx = make_ctx()
        await self.tool(url="https://example.com", ctx=ctx)
        snapshot_calls = [c for c in ctx.fastmcp.call_tool.call_args_list if c[0][0] == "playwright_browser_snapshot"]
        assert len(snapshot_calls) >= 1

    @pytest.mark.asyncio
    async def test_reports_progress(self):
        ctx = make_ctx()
        await self.tool(url="https://example.com", ctx=ctx)
        assert ctx.report_progress.call_count >= 1

    @pytest.mark.asyncio
    async def test_docstring(self):
        assert self.tool.__doc__ is not None
        assert "Navigate" in self.tool.__doc__


class TestWebWaitForReady:
    def setup_method(self):
        self.mcp = make_mcp()
        register_navigation_tools(self.mcp)
        self.tool = self.mcp._registered_tools["web_wait_for_ready"]

    @pytest.mark.asyncio
    async def test_returns_loaded(self):
        ctx = make_ctx()
        result = await self.tool(ctx=ctx)
        assert "loaded" in result and isinstance(result["loaded"], bool)

    @pytest.mark.asyncio
    async def test_returns_wait_seconds(self):
        ctx = make_ctx()
        result = await self.tool(ctx=ctx)
        assert "wait_seconds" in result

    @pytest.mark.asyncio
    async def test_returns_snapshot(self):
        ctx = make_ctx()
        result = await self.tool(ctx=ctx)
        assert "snapshot" in result

    @pytest.mark.asyncio
    async def test_with_indicator_text(self):
        ctx = make_ctx()
        await self.tool(ctx=ctx, indicator_text="Ready")
        ctx.fastmcp.call_tool.assert_any_call("playwright_browser_wait_for", {"text": "Ready"})

    @pytest.mark.asyncio
    async def test_without_indicator_polls(self):
        ctx = make_ctx()
        await self.tool(ctx=ctx)
        snapshot_calls = [c for c in ctx.fastmcp.call_tool.call_args_list if c[0][0] == "playwright_browser_snapshot"]
        assert len(snapshot_calls) >= 1

    @pytest.mark.asyncio
    async def test_timeout_returns_false(self):
        ctx = make_ctx()
        ctx.fastmcp.call_tool = AsyncMock(return_value="")
        result = await self.tool(ctx=ctx, timeout_seconds=2)
        assert result["loaded"] is False

    @pytest.mark.asyncio
    async def test_docstring(self):
        assert self.tool.__doc__ is not None


class TestWebDiscoverNavigation:
    def setup_method(self):
        self.mcp = make_mcp()
        register_navigation_tools(self.mcp)
        self.tool = self.mcp._registered_tools["web_discover_navigation"]

    @pytest.mark.asyncio
    async def test_returns_snapshot(self):
        ctx = make_ctx()
        result = await self.tool(ctx=ctx)
        assert "snapshot" in result

    @pytest.mark.asyncio
    async def test_returns_instruction(self):
        ctx = make_ctx()
        result = await self.tool(ctx=ctx)
        assert "instruction" in result
        assert "navigation" in result["instruction"].lower()

    @pytest.mark.asyncio
    async def test_calls_snapshot(self):
        ctx = make_ctx()
        await self.tool(ctx=ctx)
        ctx.fastmcp.call_tool.assert_called_with("playwright_browser_snapshot", {})

    @pytest.mark.asyncio
    async def test_docstring(self):
        assert self.tool.__doc__ is not None
        assert "navigation" in self.tool.__doc__.lower()


class TestNavigationRegistration:
    def test_registers_three_tools(self):
        mcp = make_mcp()
        register_navigation_tools(mcp)
        assert len(mcp._registered_tools) == 3

    def test_tool_names(self):
        mcp = make_mcp()
        register_navigation_tools(mcp)
        expected = {"web_navigate_and_wait", "web_wait_for_ready", "web_discover_navigation"}
        assert set(mcp._registered_tools.keys()) == expected

    def test_no_fourth_modules_dict(self):
        from src.tools import navigation
        assert not hasattr(navigation, "FOURTH_MODULES")

    def test_no_fourth_prefixed_tools(self):
        mcp = make_mcp()
        register_navigation_tools(mcp)
        for name in mcp._registered_tools:
            assert not name.startswith("fourth_"), f"Found Fourth-specific tool: {name}"
