"""Tests for web data extraction tools."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.tools.extraction import register_extraction_tools


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


class TestWebExtractTable:
    def setup_method(self):
        self.mcp = make_mcp()
        register_extraction_tools(self.mcp)
        self.tool = self.mcp._registered_tools["web_extract_table"]

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

    @pytest.mark.asyncio
    async def test_returns_table_description(self):
        ctx = make_ctx()
        result = await self.tool(ctx=ctx)
        assert "table_description" in result
        assert result["table_description"] == "main data table"

    @pytest.mark.asyncio
    async def test_returns_format(self):
        ctx = make_ctx()
        result = await self.tool(ctx=ctx)
        assert "format" in result
        assert result["format"] == "rows"

    @pytest.mark.asyncio
    async def test_custom_table_description(self):
        ctx = make_ctx()
        result = await self.tool(ctx=ctx, table_description="employee schedule")
        assert result["table_description"] == "employee schedule"
        assert "employee schedule" in result["instruction"]

    @pytest.mark.asyncio
    async def test_format_rows(self):
        ctx = make_ctx()
        result = await self.tool(ctx=ctx, format="rows")
        assert "list of dictionaries" in result["instruction"].lower() or "structured data" in result["instruction"].lower()

    @pytest.mark.asyncio
    async def test_format_csv(self):
        ctx = make_ctx()
        result = await self.tool(ctx=ctx, format="csv")
        assert result["format"] == "csv"
        assert "csv" in result["instruction"].lower()

    @pytest.mark.asyncio
    async def test_format_markdown(self):
        ctx = make_ctx()
        result = await self.tool(ctx=ctx, format="markdown")
        assert result["format"] == "markdown"
        assert "markdown" in result["instruction"].lower()

    @pytest.mark.asyncio
    async def test_pagination_mentioned(self):
        ctx = make_ctx()
        result = await self.tool(ctx=ctx)
        assert "pagination" in result["instruction"].lower()

    @pytest.mark.asyncio
    async def test_reports_progress(self):
        ctx = make_ctx()
        await self.tool(ctx=ctx)
        assert ctx.report_progress.call_count >= 1

    @pytest.mark.asyncio
    async def test_calls_snapshot(self):
        ctx = make_ctx()
        await self.tool(ctx=ctx)
        ctx.fastmcp.call_tool.assert_any_call("playwright_browser_snapshot", {})


class TestWebExtractPageData:
    def setup_method(self):
        self.mcp = make_mcp()
        register_extraction_tools(self.mcp)
        self.tool = self.mcp._registered_tools["web_extract_page_data"]

    @pytest.mark.asyncio
    async def test_returns_snapshot(self):
        ctx = make_ctx()
        result = await self.tool(ctx=ctx)
        assert "snapshot" in result

    @pytest.mark.asyncio
    async def test_returns_target(self):
        ctx = make_ctx()
        result = await self.tool(ctx=ctx)
        assert "target" in result
        assert result["target"] == "all visible content"

    @pytest.mark.asyncio
    async def test_returns_instruction(self):
        ctx = make_ctx()
        result = await self.tool(ctx=ctx)
        assert "instruction" in result

    @pytest.mark.asyncio
    async def test_custom_target(self):
        ctx = make_ctx()
        result = await self.tool(ctx=ctx, target="sidebar metrics")
        assert result["target"] == "sidebar metrics"
        assert "sidebar metrics" in result["instruction"]

    @pytest.mark.asyncio
    async def test_without_screenshot(self):
        ctx = make_ctx()
        result = await self.tool(ctx=ctx, include_screenshot=False)
        assert "screenshot" not in result

    @pytest.mark.asyncio
    async def test_with_screenshot(self):
        ctx = make_ctx()
        result = await self.tool(ctx=ctx, include_screenshot=True)
        assert "screenshot" in result
        ctx.fastmcp.call_tool.assert_any_call("playwright_browser_take_screenshot", {})

    @pytest.mark.asyncio
    async def test_screenshot_instruction_mentions_visual(self):
        ctx = make_ctx()
        result = await self.tool(ctx=ctx, include_screenshot=True)
        assert "visual" in result["instruction"].lower() or "screenshot" in result["instruction"].lower()

    @pytest.mark.asyncio
    async def test_reports_progress(self):
        ctx = make_ctx()
        await self.tool(ctx=ctx)
        assert ctx.report_progress.call_count >= 1


class TestWebExtractLinks:
    def setup_method(self):
        self.mcp = make_mcp()
        register_extraction_tools(self.mcp)
        self.tool = self.mcp._registered_tools["web_extract_links"]

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
        assert "link" in result["instruction"].lower()

    @pytest.mark.asyncio
    async def test_returns_filter(self):
        ctx = make_ctx()
        result = await self.tool(ctx=ctx)
        assert "filter" in result
        assert result["filter"] is None

    @pytest.mark.asyncio
    async def test_with_filter_text(self):
        ctx = make_ctx()
        result = await self.tool(ctx=ctx, filter_text="reports")
        assert result["filter"] == "reports"
        assert "reports" in result["instruction"]

    @pytest.mark.asyncio
    async def test_calls_snapshot(self):
        ctx = make_ctx()
        await self.tool(ctx=ctx)
        ctx.fastmcp.call_tool.assert_called_with("playwright_browser_snapshot", {})


class TestExtractionRegistration:
    def test_registers_three_tools(self):
        mcp = make_mcp()
        register_extraction_tools(mcp)
        assert len(mcp._registered_tools) == 3

    def test_tool_names(self):
        mcp = make_mcp()
        register_extraction_tools(mcp)
        expected = {"web_extract_table", "web_extract_page_data", "web_extract_links"}
        assert set(mcp._registered_tools.keys()) == expected

    def test_no_fourth_prefixed_tools(self):
        mcp = make_mcp()
        register_extraction_tools(mcp)
        for name in mcp._registered_tools:
            assert not name.startswith("fourth_"), f"Found Fourth-specific tool: {name}"
