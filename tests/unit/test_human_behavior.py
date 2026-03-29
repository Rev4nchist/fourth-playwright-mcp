"""Tests for human-like behavior defaults in navigation tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, call

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


class TestNavigateHumanDelay:
    """web_navigate_and_wait should add a random delay when no wait_for_text."""

    def setup_method(self):
        self.mcp = make_mcp()
        register_navigation_tools(self.mcp)
        self.tool = self.mcp._registered_tools["web_navigate_and_wait"]

    @pytest.mark.asyncio
    async def test_else_branch_uses_random_delay(self):
        """Without wait_for_text, wait time should be randomized (0.5-2.0s)."""
        ctx = make_ctx()
        result = await self.tool(url="https://example.com", ctx=ctx)

        # Find the wait_for call (not navigate, not snapshot)
        wait_calls = [
            c for c in ctx.fastmcp.call_tool.call_args_list
            if c[0][0] == "playwright_browser_wait_for"
        ]
        assert len(wait_calls) >= 1, "Should call wait_for at least once"

        # The time value should be between 0.5 and 2.0
        wait_args = wait_calls[0][0][1]
        assert "time" in wait_args, "Wait call should have 'time' argument"
        time_val = wait_args["time"]
        assert 0.5 <= time_val <= 2.0, \
            f"Random delay should be 0.5-2.0s, got {time_val}"

    @pytest.mark.asyncio
    async def test_else_branch_wait_seconds_matches(self):
        """Return dict's wait_seconds should match the random delay used."""
        ctx = make_ctx()
        result = await self.tool(url="https://example.com", ctx=ctx)
        assert 0.5 <= result["wait_seconds"] <= 2.0

    @pytest.mark.asyncio
    async def test_wait_for_text_branch_unchanged(self):
        """With wait_for_text, should still use text-based waiting (not random delay)."""
        ctx = make_ctx()
        await self.tool(
            url="https://example.com", ctx=ctx, wait_for_text="Dashboard"
        )
        ctx.fastmcp.call_tool.assert_any_call(
            "playwright_browser_wait_for", {"text": "Dashboard"}
        )

    @pytest.mark.asyncio
    async def test_random_delay_varies(self):
        """Multiple calls should produce different wait times (randomness check)."""
        results = []
        for _ in range(10):
            ctx = make_ctx()
            result = await self.tool(url="https://example.com", ctx=ctx)
            results.append(result["wait_seconds"])

        unique_values = set(results)
        assert len(unique_values) > 1, \
            "Random delays should vary across calls"


class TestWaitForReadyHumanDelay:
    """web_wait_for_ready should add a random delay when no indicator_text."""

    def setup_method(self):
        self.mcp = make_mcp()
        register_navigation_tools(self.mcp)
        self.tool = self.mcp._registered_tools["web_wait_for_ready"]

    @pytest.mark.asyncio
    async def test_else_branch_uses_random_delay(self):
        """Without indicator_text, wait time should be randomized (0.5-2.0s)."""
        ctx = make_ctx()
        result = await self.tool(ctx=ctx)

        wait_calls = [
            c for c in ctx.fastmcp.call_tool.call_args_list
            if c[0][0] == "playwright_browser_wait_for"
        ]
        assert len(wait_calls) >= 1

        wait_args = wait_calls[0][0][1]
        assert "time" in wait_args
        time_val = wait_args["time"]
        assert 0.5 <= time_val <= 2.0, \
            f"Random delay should be 0.5-2.0s, got {time_val}"

    @pytest.mark.asyncio
    async def test_else_branch_wait_seconds_in_range(self):
        ctx = make_ctx()
        result = await self.tool(ctx=ctx)
        assert 0.5 <= result["wait_seconds"] <= 2.0

    @pytest.mark.asyncio
    async def test_indicator_text_branch_unchanged(self):
        """With indicator_text, should still use text-based waiting."""
        ctx = make_ctx()
        await self.tool(ctx=ctx, indicator_text="Ready")
        ctx.fastmcp.call_tool.assert_any_call(
            "playwright_browser_wait_for", {"text": "Ready"}
        )
