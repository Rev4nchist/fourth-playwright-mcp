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
    async def test_returns_links_key(self):
        """DOM extraction returns 'links' key instead of 'snapshot'."""
        mock_links = [{"text": "Test", "href": "https://example.com"}]
        ctx = make_ctx()
        ctx.fastmcp.call_tool = AsyncMock(return_value=mock_links)
        result = await self.tool(ctx=ctx)
        assert "links" in result

    @pytest.mark.asyncio
    async def test_returns_count_key(self):
        """DOM extraction returns 'count' key instead of 'instruction'."""
        mock_links = [{"text": "Test", "href": "https://example.com"}]
        ctx = make_ctx()
        ctx.fastmcp.call_tool = AsyncMock(return_value=mock_links)
        result = await self.tool(ctx=ctx)
        assert "count" in result

    @pytest.mark.asyncio
    async def test_returns_filter(self):
        mock_links = [{"text": "Test", "href": "https://example.com"}]
        ctx = make_ctx()
        ctx.fastmcp.call_tool = AsyncMock(return_value=mock_links)
        result = await self.tool(ctx=ctx)
        assert "filter" in result
        assert result["filter"] is None

    @pytest.mark.asyncio
    async def test_with_filter_text(self):
        mock_links = [
            {"text": "Reports", "href": "https://example.com/reports"},
            {"text": "Home", "href": "https://example.com/"},
        ]
        ctx = make_ctx()
        ctx.fastmcp.call_tool = AsyncMock(return_value=mock_links)
        result = await self.tool(ctx=ctx, filter_text="reports")
        assert result["filter"] == "reports"

    @pytest.mark.asyncio
    async def test_calls_evaluate_for_dom_extraction(self):
        """web_extract_links should use playwright_browser_evaluate for DOM extraction."""
        ctx = make_ctx()
        await self.tool(ctx=ctx)
        calls = ctx.fastmcp.call_tool.call_args_list
        evaluate_calls = [c for c in calls if c[0][0] == "playwright_browser_evaluate"]
        assert len(evaluate_calls) == 1, "Should call playwright_browser_evaluate once"

    @pytest.mark.asyncio
    async def test_returns_links_list(self):
        """web_extract_links should return structured links data."""
        mock_links = [
            {"text": "Home", "href": "https://example.com/"},
            {"text": "About", "href": "https://example.com/about"},
        ]
        ctx = make_ctx()
        ctx.fastmcp.call_tool = AsyncMock(return_value=mock_links)
        result = await self.tool(ctx=ctx)
        assert "links" in result
        assert result["links"] == mock_links

    @pytest.mark.asyncio
    async def test_returns_count(self):
        """web_extract_links should return count of links."""
        mock_links = [
            {"text": "Home", "href": "https://example.com/"},
            {"text": "About", "href": "https://example.com/about"},
        ]
        ctx = make_ctx()
        ctx.fastmcp.call_tool = AsyncMock(return_value=mock_links)
        result = await self.tool(ctx=ctx)
        assert "count" in result
        assert result["count"] == 2

    @pytest.mark.asyncio
    async def test_filter_text_filters_links(self):
        """filter_text should filter results case-insensitively on text or href."""
        mock_links = [
            {"text": "Home", "href": "https://example.com/"},
            {"text": "Reports Dashboard", "href": "https://example.com/reports"},
            {"text": "About", "href": "https://example.com/about"},
        ]
        ctx = make_ctx()
        ctx.fastmcp.call_tool = AsyncMock(return_value=mock_links)
        result = await self.tool(ctx=ctx, filter_text="reports")
        assert len(result["links"]) == 1
        assert result["links"][0]["text"] == "Reports Dashboard"
        assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_filter_text_matches_href(self):
        """filter_text should also match against href."""
        mock_links = [
            {"text": "Click Here", "href": "https://example.com/dashboard"},
            {"text": "Other Link", "href": "https://example.com/other"},
        ]
        ctx = make_ctx()
        ctx.fastmcp.call_tool = AsyncMock(return_value=mock_links)
        result = await self.tool(ctx=ctx, filter_text="dashboard")
        assert len(result["links"]) == 1
        assert result["links"][0]["text"] == "Click Here"

    @pytest.mark.asyncio
    async def test_filter_text_case_insensitive(self):
        """Filtering should be case-insensitive."""
        mock_links = [
            {"text": "HOME PAGE", "href": "https://example.com/"},
        ]
        ctx = make_ctx()
        ctx.fastmcp.call_tool = AsyncMock(return_value=mock_links)
        result = await self.tool(ctx=ctx, filter_text="home")
        assert len(result["links"]) == 1

    @pytest.mark.asyncio
    async def test_fallback_on_evaluate_failure(self):
        """If evaluate fails, should fall back to snapshot + instruction approach."""

        async def side_effect(tool_name, args):
            if tool_name == "playwright_browser_evaluate":
                raise Exception("evaluate failed")
            return "<snapshot content>"

        ctx = make_ctx()
        ctx.fastmcp.call_tool = AsyncMock(side_effect=side_effect)
        result = await self.tool(ctx=ctx)
        # Fallback should return instruction-based result
        assert "instruction" in result
        assert "snapshot" in result

    @pytest.mark.asyncio
    async def test_filter_in_result(self):
        """Result should include filter value."""
        mock_links = [{"text": "Home", "href": "https://example.com/"}]
        ctx = make_ctx()
        ctx.fastmcp.call_tool = AsyncMock(return_value=mock_links)
        result = await self.tool(ctx=ctx, filter_text="test")
        assert result["filter"] == "test"


class TestWebExtractTableDom:
    """Tests for the use_dom parameter on web_extract_table."""

    def setup_method(self):
        self.mcp = make_mcp()
        register_extraction_tools(self.mcp)
        self.tool = self.mcp._registered_tools["web_extract_table"]

    @pytest.mark.asyncio
    async def test_use_dom_false_returns_instruction(self):
        """Default (use_dom=False) should use snapshot + instruction approach."""
        ctx = make_ctx()
        result = await self.tool(ctx=ctx, use_dom=False)
        assert "instruction" in result
        assert "snapshot" in result

    @pytest.mark.asyncio
    async def test_use_dom_true_calls_evaluate(self):
        """use_dom=True should call playwright_browser_evaluate."""
        mock_tables = [
            {"index": 0, "headers": ["Name", "Age"], "rows": [["Alice", "30"]], "row_count": 1}
        ]
        ctx = make_ctx()
        ctx.fastmcp.call_tool = AsyncMock(return_value=mock_tables)
        await self.tool(ctx=ctx, use_dom=True)
        calls = ctx.fastmcp.call_tool.call_args_list
        evaluate_calls = [c for c in calls if c[0][0] == "playwright_browser_evaluate"]
        assert len(evaluate_calls) == 1

    @pytest.mark.asyncio
    async def test_use_dom_true_returns_tables(self):
        """use_dom=True should return structured table data."""
        mock_tables = [
            {"index": 0, "headers": ["Name", "Age"], "rows": [["Alice", "30"]], "row_count": 1}
        ]
        ctx = make_ctx()
        ctx.fastmcp.call_tool = AsyncMock(return_value=mock_tables)
        result = await self.tool(ctx=ctx, use_dom=True)
        assert "tables" in result
        assert "count" in result
        assert result["count"] == 1
        assert result["tables"][0]["headers"] == ["Name", "Age"]

    @pytest.mark.asyncio
    async def test_use_dom_default_is_false(self):
        """Default behavior should be snapshot + instruction (use_dom=False)."""
        ctx = make_ctx()
        result = await self.tool(ctx=ctx)
        assert "instruction" in result
        assert "snapshot" in result


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
