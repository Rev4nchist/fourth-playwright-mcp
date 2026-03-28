"""Tests for web performance and accessibility tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.tools.performance import register_performance_tools


@pytest.fixture
def mcp():
    """Create a mock FastMCP instance that captures tool registrations."""
    mock_mcp = MagicMock()
    registered_tools: dict[str, callable] = {}

    def tool_decorator(func):
        registered_tools[func.__name__] = func
        return func

    mock_mcp.tool = tool_decorator
    mock_mcp._registered_tools = registered_tools
    return mock_mcp


@pytest.fixture
def ctx():
    """Create a mock Context with fastmcp call_tool support."""
    mock_ctx = MagicMock()
    mock_ctx.report_progress = AsyncMock()
    mock_ctx.fastmcp = MagicMock()
    mock_ctx.fastmcp.call_tool = AsyncMock()
    return mock_ctx


@pytest.fixture
def tools(mcp):
    """Register performance tools and return the registered tool functions."""
    register_performance_tools(mcp)
    return mcp._registered_tools


# --- web_performance tests ---


class TestWebPerformanceRegistration:
    """Tests for tool registration."""

    def test_tool_is_registered(self, tools):
        assert "web_performance" in tools

    def test_has_docstring(self, tools):
        assert tools["web_performance"].__doc__ is not None
        assert "performance" in tools["web_performance"].__doc__.lower()


class TestWebPerformanceSuccess:
    """Tests for successful performance profiling."""

    @pytest.mark.asyncio
    async def test_calls_browser_evaluate(self, tools, ctx):
        ctx.fastmcp.call_tool.return_value = {"navigation": {}}

        await tools["web_performance"](ctx=ctx)

        ctx.fastmcp.call_tool.assert_called_once()
        call_args = ctx.fastmcp.call_tool.call_args
        assert call_args[0][0] == "playwright_browser_evaluate"

    @pytest.mark.asyncio
    async def test_passes_expression_argument(self, tools, ctx):
        ctx.fastmcp.call_tool.return_value = {"navigation": {}}

        await tools["web_performance"](ctx=ctx)

        call_args = ctx.fastmcp.call_tool.call_args
        assert "function" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_expression_is_iife(self, tools, ctx):
        """The JS expression should be an IIFE starting with ()."""
        ctx.fastmcp.call_tool.return_value = {}

        await tools["web_performance"](ctx=ctx)

        call_args = ctx.fastmcp.call_tool.call_args
        expression = call_args[0][1]["function"]
        stripped = expression.strip()
        assert stripped.startswith("(") or stripped.startswith("\n(")

    @pytest.mark.asyncio
    async def test_returns_success_true(self, tools, ctx):
        ctx.fastmcp.call_tool.return_value = {"navigation": {"ttfb_ms": 50}}

        result = await tools["web_performance"](ctx=ctx)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_returns_metrics(self, tools, ctx):
        mock_metrics = {
            "navigation": {"ttfb_ms": 50, "dom_complete_ms": 200},
            "resources": {"count": 10},
        }
        ctx.fastmcp.call_tool.return_value = mock_metrics

        result = await tools["web_performance"](ctx=ctx)

        assert result["metrics"] == mock_metrics

    @pytest.mark.asyncio
    async def test_returns_no_error_on_success(self, tools, ctx):
        ctx.fastmcp.call_tool.return_value = {}

        result = await tools["web_performance"](ctx=ctx)

        assert result.get("error") is None or "error" not in result


class TestWebPerformanceFailure:
    """Tests for error handling in performance profiling."""

    @pytest.mark.asyncio
    async def test_returns_success_false_on_error(self, tools, ctx):
        ctx.fastmcp.call_tool.side_effect = RuntimeError("No page loaded")

        result = await tools["web_performance"](ctx=ctx)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_returns_error_message(self, tools, ctx):
        ctx.fastmcp.call_tool.side_effect = RuntimeError("No page loaded")

        result = await tools["web_performance"](ctx=ctx)

        assert "No page loaded" in result["error"]

    @pytest.mark.asyncio
    async def test_returns_none_metrics_on_error(self, tools, ctx):
        ctx.fastmcp.call_tool.side_effect = RuntimeError("fail")

        result = await tools["web_performance"](ctx=ctx)

        assert result["metrics"] is None


class TestWebPerformanceJavaScript:
    """Tests for the JavaScript expression content."""

    @pytest.mark.asyncio
    async def test_js_references_navigation_timing(self, tools, ctx):
        ctx.fastmcp.call_tool.return_value = {}

        await tools["web_performance"](ctx=ctx)

        expression = ctx.fastmcp.call_tool.call_args[0][1]["function"]
        assert "getEntriesByType" in expression
        assert "'navigation'" in expression

    @pytest.mark.asyncio
    async def test_js_references_resource_timing(self, tools, ctx):
        ctx.fastmcp.call_tool.return_value = {}

        await tools["web_performance"](ctx=ctx)

        expression = ctx.fastmcp.call_tool.call_args[0][1]["function"]
        assert "'resource'" in expression

    @pytest.mark.asyncio
    async def test_js_references_lcp(self, tools, ctx):
        ctx.fastmcp.call_tool.return_value = {}

        await tools["web_performance"](ctx=ctx)

        expression = ctx.fastmcp.call_tool.call_args[0][1]["function"]
        assert "largest-contentful-paint" in expression

    @pytest.mark.asyncio
    async def test_js_references_cls(self, tools, ctx):
        ctx.fastmcp.call_tool.return_value = {}

        await tools["web_performance"](ctx=ctx)

        expression = ctx.fastmcp.call_tool.call_args[0][1]["function"]
        assert "layout-shift" in expression

    @pytest.mark.asyncio
    async def test_js_references_fcp(self, tools, ctx):
        ctx.fastmcp.call_tool.return_value = {}

        await tools["web_performance"](ctx=ctx)

        expression = ctx.fastmcp.call_tool.call_args[0][1]["function"]
        assert "first-contentful-paint" in expression


# --- web_accessibility_audit tests ---


class TestWebAccessibilityAuditRegistration:
    """Tests for tool registration."""

    def test_tool_is_registered(self, tools):
        assert "web_accessibility_audit" in tools

    def test_has_docstring(self, tools):
        assert tools["web_accessibility_audit"].__doc__ is not None
        assert "accessibility" in tools["web_accessibility_audit"].__doc__.lower()


class TestWebAccessibilityAuditSuccess:
    """Tests for successful accessibility auditing."""

    @pytest.mark.asyncio
    async def test_calls_browser_evaluate(self, tools, ctx):
        ctx.fastmcp.call_tool.return_value = {"issues": [], "summary": {}}

        await tools["web_accessibility_audit"](ctx=ctx)

        ctx.fastmcp.call_tool.assert_called_once()
        call_args = ctx.fastmcp.call_tool.call_args
        assert call_args[0][0] == "playwright_browser_evaluate"

    @pytest.mark.asyncio
    async def test_passes_expression_argument(self, tools, ctx):
        ctx.fastmcp.call_tool.return_value = {"issues": [], "summary": {}}

        await tools["web_accessibility_audit"](ctx=ctx)

        call_args = ctx.fastmcp.call_tool.call_args
        assert "function" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_expression_is_iife(self, tools, ctx):
        ctx.fastmcp.call_tool.return_value = {"issues": [], "summary": {}}

        await tools["web_accessibility_audit"](ctx=ctx)

        expression = ctx.fastmcp.call_tool.call_args[0][1]["function"]
        stripped = expression.strip()
        assert stripped.startswith("(") or stripped.startswith("\n(")

    @pytest.mark.asyncio
    async def test_returns_success_true(self, tools, ctx):
        ctx.fastmcp.call_tool.return_value = {"issues": [], "summary": {}}

        result = await tools["web_accessibility_audit"](ctx=ctx)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_returns_audit_data(self, tools, ctx):
        mock_audit = {
            "issues": [{"type": "img-no-alt", "severity": "critical"}],
            "summary": {"total_issues": 1, "critical": 1, "warnings": 0},
        }
        ctx.fastmcp.call_tool.return_value = mock_audit

        result = await tools["web_accessibility_audit"](ctx=ctx)

        assert result["audit"] == mock_audit

    @pytest.mark.asyncio
    async def test_returns_no_error_on_success(self, tools, ctx):
        ctx.fastmcp.call_tool.return_value = {"issues": [], "summary": {}}

        result = await tools["web_accessibility_audit"](ctx=ctx)

        assert result.get("error") is None or "error" not in result


class TestWebAccessibilityAuditFailure:
    """Tests for error handling in accessibility auditing."""

    @pytest.mark.asyncio
    async def test_returns_success_false_on_error(self, tools, ctx):
        ctx.fastmcp.call_tool.side_effect = RuntimeError("No page loaded")

        result = await tools["web_accessibility_audit"](ctx=ctx)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_returns_error_message(self, tools, ctx):
        ctx.fastmcp.call_tool.side_effect = RuntimeError("No page loaded")

        result = await tools["web_accessibility_audit"](ctx=ctx)

        assert "No page loaded" in result["error"]

    @pytest.mark.asyncio
    async def test_returns_none_audit_on_error(self, tools, ctx):
        ctx.fastmcp.call_tool.side_effect = RuntimeError("fail")

        result = await tools["web_accessibility_audit"](ctx=ctx)

        assert result["audit"] is None


class TestWebAccessibilityAuditJavaScript:
    """Tests for the JavaScript expression content."""

    @pytest.mark.asyncio
    async def test_js_checks_img_alt(self, tools, ctx):
        ctx.fastmcp.call_tool.return_value = {"issues": [], "summary": {}}

        await tools["web_accessibility_audit"](ctx=ctx)

        expression = ctx.fastmcp.call_tool.call_args[0][1]["function"]
        assert "img" in expression.lower()
        assert "alt" in expression

    @pytest.mark.asyncio
    async def test_js_checks_form_labels(self, tools, ctx):
        ctx.fastmcp.call_tool.return_value = {"issues": [], "summary": {}}

        await tools["web_accessibility_audit"](ctx=ctx)

        expression = ctx.fastmcp.call_tool.call_args[0][1]["function"]
        assert "aria-label" in expression

    @pytest.mark.asyncio
    async def test_js_checks_heading_hierarchy(self, tools, ctx):
        ctx.fastmcp.call_tool.return_value = {"issues": [], "summary": {}}

        await tools["web_accessibility_audit"](ctx=ctx)

        expression = ctx.fastmcp.call_tool.call_args[0][1]["function"]
        assert "h1" in expression
        assert "heading" in expression.lower()

    @pytest.mark.asyncio
    async def test_js_checks_accessible_names(self, tools, ctx):
        ctx.fastmcp.call_tool.return_value = {"issues": [], "summary": {}}

        await tools["web_accessibility_audit"](ctx=ctx)

        expression = ctx.fastmcp.call_tool.call_args[0][1]["function"]
        assert "button" in expression.lower()
        assert "accessible" in expression.lower() or "textContent" in expression

    @pytest.mark.asyncio
    async def test_js_checks_lang_attribute(self, tools, ctx):
        ctx.fastmcp.call_tool.return_value = {"issues": [], "summary": {}}

        await tools["web_accessibility_audit"](ctx=ctx)

        expression = ctx.fastmcp.call_tool.call_args[0][1]["function"]
        assert "lang" in expression

    @pytest.mark.asyncio
    async def test_js_checks_aria_roles(self, tools, ctx):
        ctx.fastmcp.call_tool.return_value = {"issues": [], "summary": {}}

        await tools["web_accessibility_audit"](ctx=ctx)

        expression = ctx.fastmcp.call_tool.call_args[0][1]["function"]
        assert "role" in expression
