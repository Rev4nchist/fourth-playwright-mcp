"""Tests for web search tools."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.tools.search import register_search_tools


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


class TestWebSearchDomExtraction:
    """Tests for DOM extraction in web_search."""

    def setup_method(self):
        self.mcp = make_mcp()
        register_search_tools(self.mcp)
        self.tool = self.mcp._registered_tools["web_search"]

    @pytest.mark.asyncio
    async def test_returns_results_key(self):
        """web_search should return a 'results' key with extracted data."""
        mock_results = [
            {"position": 1, "title": "Example", "url": "https://example.com", "snippet": "A test"},
        ]

        async def side_effect(tool_name, args):
            if tool_name == "playwright_browser_evaluate":
                return mock_results
            return "<snapshot>"

        ctx = make_ctx(call_tool_side_effect=side_effect)
        result = await self.tool(query="test", ctx=ctx)
        assert "results" in result
        assert len(result["results"]) == 1
        assert result["results"][0]["title"] == "Example"

    @pytest.mark.asyncio
    async def test_returns_results_count(self):
        """web_search should return a 'results_count' key."""
        mock_results = [
            {"position": 1, "title": "A", "url": "https://a.com", "snippet": ""},
            {"position": 2, "title": "B", "url": "https://b.com", "snippet": ""},
        ]

        async def side_effect(tool_name, args):
            if tool_name == "playwright_browser_evaluate":
                return mock_results
            return "<snapshot>"

        ctx = make_ctx(call_tool_side_effect=side_effect)
        result = await self.tool(query="test", ctx=ctx)
        assert "results_count" in result
        assert result["results_count"] == 2

    @pytest.mark.asyncio
    async def test_results_limited_by_num_results(self):
        """Results should be sliced to num_results."""
        mock_results = [
            {"position": i, "title": f"R{i}", "url": f"https://r{i}.com", "snippet": ""}
            for i in range(1, 11)
        ]

        async def side_effect(tool_name, args):
            if tool_name == "playwright_browser_evaluate":
                return mock_results
            return "<snapshot>"

        ctx = make_ctx(call_tool_side_effect=side_effect)
        result = await self.tool(query="test", ctx=ctx, num_results=3)
        assert result["results_count"] == 3
        assert len(result["results"]) == 3

    @pytest.mark.asyncio
    async def test_still_returns_snapshot(self):
        """web_search should still include the snapshot as fallback."""

        async def side_effect(tool_name, args):
            if tool_name == "playwright_browser_evaluate":
                return []
            return "<snapshot>"

        ctx = make_ctx(call_tool_side_effect=side_effect)
        result = await self.tool(query="test", ctx=ctx)
        assert "snapshot" in result

    @pytest.mark.asyncio
    async def test_still_returns_instruction(self):
        """web_search should still include instruction as fallback guidance."""

        async def side_effect(tool_name, args):
            if tool_name == "playwright_browser_evaluate":
                return []
            return "<snapshot>"

        ctx = make_ctx(call_tool_side_effect=side_effect)
        result = await self.tool(query="test", ctx=ctx)
        assert "instruction" in result

    @pytest.mark.asyncio
    async def test_calls_evaluate_for_dom_extraction(self):
        """web_search should call playwright_browser_evaluate after snapshot."""

        async def side_effect(tool_name, args):
            if tool_name == "playwright_browser_evaluate":
                return []
            return "<snapshot>"

        ctx = make_ctx(call_tool_side_effect=side_effect)
        await self.tool(query="test", ctx=ctx)
        calls = ctx.fastmcp.call_tool.call_args_list
        evaluate_calls = [c for c in calls if c[0][0] == "playwright_browser_evaluate"]
        assert len(evaluate_calls) == 1

    @pytest.mark.asyncio
    async def test_fallback_on_evaluate_failure(self):
        """If evaluate fails, should still return snapshot + instruction."""

        async def side_effect(tool_name, args):
            if tool_name == "playwright_browser_evaluate":
                raise Exception("JS eval failed")
            return "<snapshot>"

        ctx = make_ctx(call_tool_side_effect=side_effect)
        result = await self.tool(query="test", ctx=ctx)
        assert "snapshot" in result
        assert "instruction" in result
        # results should be empty on failure, not missing
        assert "results" in result
        assert result["results"] == []

    @pytest.mark.asyncio
    async def test_preserves_query_and_engine(self):
        """Result should always include query and engine."""

        async def side_effect(tool_name, args):
            if tool_name == "playwright_browser_evaluate":
                return []
            return "<snapshot>"

        ctx = make_ctx(call_tool_side_effect=side_effect)
        result = await self.tool(query="test query", ctx=ctx, engine="duckduckgo")
        assert result["query"] == "test query"
        assert result["engine"] == "duckduckgo"

    @pytest.mark.asyncio
    async def test_preserves_url(self):
        """Result should always include the search URL."""

        async def side_effect(tool_name, args):
            if tool_name == "playwright_browser_evaluate":
                return []
            return "<snapshot>"

        ctx = make_ctx(call_tool_side_effect=side_effect)
        result = await self.tool(query="test", ctx=ctx)
        assert "url" in result


class TestSearchRegistration:
    def test_registers_two_tools(self):
        mcp = make_mcp()
        register_search_tools(mcp)
        assert len(mcp._registered_tools) == 2

    def test_tool_names(self):
        mcp = make_mcp()
        register_search_tools(mcp)
        expected = {"web_search", "web_search_and_extract"}
        assert set(mcp._registered_tools.keys()) == expected
