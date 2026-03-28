"""Tests for web form automation tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.tools.forms import register_form_tools


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
    """Register form tools and return the registered tool functions."""
    register_form_tools(mcp)
    return mcp._registered_tools


# --- web_discover_form tests ---


class TestWebDiscoverForm:
    """Tests for the web_discover_form tool."""

    def test_tool_is_registered(self, tools):
        assert "web_discover_form" in tools

    @pytest.mark.asyncio
    async def test_returns_snapshot_and_instruction(self, tools, ctx):
        ctx.fastmcp.call_tool.return_value = "[snapshot data]"

        result = await tools["web_discover_form"](ctx=ctx)

        assert "snapshot" in result
        assert result["snapshot"] == "[snapshot data]"
        assert "instruction" in result
        assert "form_description" in result

    @pytest.mark.asyncio
    async def test_default_form_description(self, tools, ctx):
        ctx.fastmcp.call_tool.return_value = "[snapshot]"

        result = await tools["web_discover_form"](ctx=ctx)

        assert result["form_description"] == "main form on page"

    @pytest.mark.asyncio
    async def test_custom_form_description(self, tools, ctx):
        ctx.fastmcp.call_tool.return_value = "[snapshot]"

        result = await tools["web_discover_form"](
            ctx=ctx, form_description="login form"
        )

        assert result["form_description"] == "login form"
        assert "login form" in result["instruction"]

    @pytest.mark.asyncio
    async def test_calls_browser_snapshot(self, tools, ctx):
        ctx.fastmcp.call_tool.return_value = "[snapshot]"

        await tools["web_discover_form"](ctx=ctx)

        ctx.fastmcp.call_tool.assert_any_call(
            "playwright_browser_snapshot", {}
        )

    @pytest.mark.asyncio
    async def test_reports_progress(self, tools, ctx):
        ctx.fastmcp.call_tool.return_value = "[snapshot]"

        await tools["web_discover_form"](ctx=ctx)

        ctx.report_progress.assert_called()

    @pytest.mark.asyncio
    async def test_instruction_mentions_field_attributes(self, tools, ctx):
        ctx.fastmcp.call_tool.return_value = "[snapshot]"

        result = await tools["web_discover_form"](ctx=ctx)

        instruction = result["instruction"]
        for keyword in ["label", "type", "ref", "current_value", "options"]:
            assert keyword in instruction, f"Instruction missing '{keyword}'"


class TestWebDiscoverFormJsContent:
    """Tests that the form extraction JS contains expected label resolution logic."""

    @pytest.mark.asyncio
    async def test_js_contains_getFieldLabel(self, tools, ctx):
        """The JS expression should define a getFieldLabel helper."""
        captured_js = None

        async def side_effect(tool_name, args):
            nonlocal captured_js
            if tool_name == "playwright_browser_evaluate":
                captured_js = args.get("expression", "")
                return []
            return "[snapshot]"

        ctx.fastmcp.call_tool = AsyncMock(side_effect=side_effect)
        await tools["web_discover_form"](ctx=ctx)
        assert captured_js is not None
        assert "getFieldLabel" in captured_js

    @pytest.mark.asyncio
    async def test_js_checks_aria_labelledby(self, tools, ctx):
        """The JS should check aria-labelledby (W3C priority 1)."""
        captured_js = None

        async def side_effect(tool_name, args):
            nonlocal captured_js
            if tool_name == "playwright_browser_evaluate":
                captured_js = args.get("expression", "")
                return []
            return "[snapshot]"

        ctx.fastmcp.call_tool = AsyncMock(side_effect=side_effect)
        await tools["web_discover_form"](ctx=ctx)
        assert "aria-labelledby" in captured_js

    @pytest.mark.asyncio
    async def test_js_checks_aria_label(self, tools, ctx):
        """The JS should check aria-label (W3C priority 2)."""
        captured_js = None

        async def side_effect(tool_name, args):
            nonlocal captured_js
            if tool_name == "playwright_browser_evaluate":
                captured_js = args.get("expression", "")
                return []
            return "[snapshot]"

        ctx.fastmcp.call_tool = AsyncMock(side_effect=side_effect)
        await tools["web_discover_form"](ctx=ctx)
        assert "aria-label" in captured_js

    @pytest.mark.asyncio
    async def test_js_checks_enclosing_label(self, tools, ctx):
        """The JS should check for enclosing <label> (implicit association)."""
        captured_js = None

        async def side_effect(tool_name, args):
            nonlocal captured_js
            if tool_name == "playwright_browser_evaluate":
                captured_js = args.get("expression", "")
                return []
            return "[snapshot]"

        ctx.fastmcp.call_tool = AsyncMock(side_effect=side_effect)
        await tools["web_discover_form"](ctx=ctx)
        assert "closest" in captured_js
        assert "'label'" in captured_js

    @pytest.mark.asyncio
    async def test_js_checks_fieldset_legend(self, tools, ctx):
        """The JS should check for fieldset legend."""
        captured_js = None

        async def side_effect(tool_name, args):
            nonlocal captured_js
            if tool_name == "playwright_browser_evaluate":
                captured_js = args.get("expression", "")
                return []
            return "[snapshot]"

        ctx.fastmcp.call_tool = AsyncMock(side_effect=side_effect)
        await tools["web_discover_form"](ctx=ctx)
        assert "fieldset" in captured_js
        assert "legend" in captured_js

    @pytest.mark.asyncio
    async def test_js_checks_form_builder_wrappers(self, tools, ctx):
        """The JS should handle HubSpot, Marketo, MUI, Bootstrap wrappers."""
        captured_js = None

        async def side_effect(tool_name, args):
            nonlocal captured_js
            if tool_name == "playwright_browser_evaluate":
                captured_js = args.get("expression", "")
                return []
            return "[snapshot]"

        ctx.fastmcp.call_tool = AsyncMock(side_effect=side_effect)
        await tools["web_discover_form"](ctx=ctx)
        for selector in ["hs-form-field", "gfield", "mktoFieldWrap", "MuiFormControl"]:
            assert selector in captured_js, f"Missing form builder selector '{selector}'"

    @pytest.mark.asyncio
    async def test_js_filters_hidden_fields(self, tools, ctx):
        """The JS should skip display:none and visibility:hidden fields."""
        captured_js = None

        async def side_effect(tool_name, args):
            nonlocal captured_js
            if tool_name == "playwright_browser_evaluate":
                captured_js = args.get("expression", "")
                return []
            return "[snapshot]"

        ctx.fastmcp.call_tool = AsyncMock(side_effect=side_effect)
        await tools["web_discover_form"](ctx=ctx)
        assert "getComputedStyle" in captured_js
        assert "display" in captured_js
        assert "visibility" in captured_js

    @pytest.mark.asyncio
    async def test_js_checks_preceding_sibling(self, tools, ctx):
        """The JS should check preceding sibling text as a label fallback."""
        captured_js = None

        async def side_effect(tool_name, args):
            nonlocal captured_js
            if tool_name == "playwright_browser_evaluate":
                captured_js = args.get("expression", "")
                return []
            return "[snapshot]"

        ctx.fastmcp.call_tool = AsyncMock(side_effect=side_effect)
        await tools["web_discover_form"](ctx=ctx)
        assert "previousElementSibling" in captured_js

    @pytest.mark.asyncio
    async def test_js_checks_parent_text_nodes(self, tools, ctx):
        """The JS should check parent's direct text nodes (wrapper-div pattern)."""
        captured_js = None

        async def side_effect(tool_name, args):
            nonlocal captured_js
            if tool_name == "playwright_browser_evaluate":
                captured_js = args.get("expression", "")
                return []
            return "[snapshot]"

        ctx.fastmcp.call_tool = AsyncMock(side_effect=side_effect)
        await tools["web_discover_form"](ctx=ctx)
        assert "parentElement" in captured_js
        assert "childNodes" in captured_js
        assert "TEXT_NODE" in captured_js or "nodeType" in captured_js


class TestWebDiscoverFormDomExtraction:
    """Tests for DOM extraction in web_discover_form."""

    @pytest.mark.asyncio
    async def test_returns_fields_key(self, tools, ctx):
        """web_discover_form should return extracted 'fields' via DOM."""
        mock_fields = [
            {"tag": "input", "type": "text", "name": "username", "id": "user",
             "label": "Username", "value": "", "required": True, "disabled": False},
        ]

        async def side_effect(tool_name, args):
            if tool_name == "playwright_browser_evaluate":
                return mock_fields
            return "[snapshot]"

        ctx.fastmcp.call_tool = AsyncMock(side_effect=side_effect)
        result = await tools["web_discover_form"](ctx=ctx)
        assert "fields" in result
        assert len(result["fields"]) == 1
        assert result["fields"][0]["name"] == "username"

    @pytest.mark.asyncio
    async def test_returns_fields_count(self, tools, ctx):
        """web_discover_form should return 'fields_count'."""
        mock_fields = [
            {"tag": "input", "type": "text", "name": "a", "id": "", "label": "",
             "value": "", "required": False, "disabled": False},
            {"tag": "input", "type": "email", "name": "b", "id": "", "label": "",
             "value": "", "required": False, "disabled": False},
        ]

        async def side_effect(tool_name, args):
            if tool_name == "playwright_browser_evaluate":
                return mock_fields
            return "[snapshot]"

        ctx.fastmcp.call_tool = AsyncMock(side_effect=side_effect)
        result = await tools["web_discover_form"](ctx=ctx)
        assert "fields_count" in result
        assert result["fields_count"] == 2

    @pytest.mark.asyncio
    async def test_calls_evaluate(self, tools, ctx):
        """web_discover_form should call playwright_browser_evaluate."""

        async def side_effect(tool_name, args):
            if tool_name == "playwright_browser_evaluate":
                return []
            return "[snapshot]"

        ctx.fastmcp.call_tool = AsyncMock(side_effect=side_effect)
        await tools["web_discover_form"](ctx=ctx)
        calls = ctx.fastmcp.call_tool.call_args_list
        evaluate_calls = [c for c in calls if c[0][0] == "playwright_browser_evaluate"]
        assert len(evaluate_calls) == 1

    @pytest.mark.asyncio
    async def test_still_returns_snapshot(self, tools, ctx):
        """web_discover_form should still include snapshot for ref IDs."""

        async def side_effect(tool_name, args):
            if tool_name == "playwright_browser_evaluate":
                return []
            return "[snapshot data]"

        ctx.fastmcp.call_tool = AsyncMock(side_effect=side_effect)
        result = await tools["web_discover_form"](ctx=ctx)
        assert "snapshot" in result

    @pytest.mark.asyncio
    async def test_still_returns_instruction(self, tools, ctx):
        """web_discover_form should still include instruction as fallback."""

        async def side_effect(tool_name, args):
            if tool_name == "playwright_browser_evaluate":
                return []
            return "[snapshot]"

        ctx.fastmcp.call_tool = AsyncMock(side_effect=side_effect)
        result = await tools["web_discover_form"](ctx=ctx)
        assert "instruction" in result

    @pytest.mark.asyncio
    async def test_fallback_on_evaluate_failure(self, tools, ctx):
        """If evaluate fails, should fall back to snapshot+instruction, fields empty."""

        async def side_effect(tool_name, args):
            if tool_name == "playwright_browser_evaluate":
                raise Exception("JS eval failed")
            return "[snapshot]"

        ctx.fastmcp.call_tool = AsyncMock(side_effect=side_effect)
        result = await tools["web_discover_form"](ctx=ctx)
        assert "snapshot" in result
        assert "instruction" in result
        assert "fields" in result
        assert result["fields"] == []


# --- web_fill_form tests ---


class TestWebFillForm:
    """Tests for the web_fill_form tool."""

    def test_tool_is_registered(self, tools):
        assert "web_fill_form" in tools

    @pytest.mark.asyncio
    async def test_fills_text_fields(self, tools, ctx):
        ctx.fastmcp.call_tool.return_value = "[snapshot]"
        fields = [
            {"ref": "r1", "value": "hello", "type": "text"},
            {"ref": "r2", "value": "world", "type": "text"},
        ]

        result = await tools["web_fill_form"](ctx=ctx, fields=fields)

        assert result["filled_count"] == 2
        assert result["total_fields"] == 2
        assert result["errors"] == []

    @pytest.mark.asyncio
    async def test_fills_select_field(self, tools, ctx):
        ctx.fastmcp.call_tool.return_value = "[snapshot]"
        fields = [{"ref": "r1", "value": "option1", "type": "select"}]

        await tools["web_fill_form"](ctx=ctx, fields=fields)

        # Should call select_option, not type
        calls = ctx.fastmcp.call_tool.call_args_list
        select_call = calls[0]
        assert select_call[0][0] == "playwright_browser_select_option"
        assert select_call[0][1]["values"] == ["option1"]

    @pytest.mark.asyncio
    async def test_fills_checkbox_field(self, tools, ctx):
        ctx.fastmcp.call_tool.return_value = "[snapshot]"
        fields = [{"ref": "r1", "value": "on", "type": "checkbox"}]

        await tools["web_fill_form"](ctx=ctx, fields=fields)

        calls = ctx.fastmcp.call_tool.call_args_list
        click_call = calls[0]
        assert click_call[0][0] == "playwright_browser_click"

    @pytest.mark.asyncio
    async def test_fills_radio_field(self, tools, ctx):
        ctx.fastmcp.call_tool.return_value = "[snapshot]"
        fields = [{"ref": "r1", "value": "opt", "type": "radio"}]

        await tools["web_fill_form"](ctx=ctx, fields=fields)

        calls = ctx.fastmcp.call_tool.call_args_list
        click_call = calls[0]
        assert click_call[0][0] == "playwright_browser_click"

    @pytest.mark.asyncio
    async def test_default_type_is_text(self, tools, ctx):
        ctx.fastmcp.call_tool.return_value = "[snapshot]"
        fields = [{"ref": "r1", "value": "hello"}]  # no type specified

        await tools["web_fill_form"](ctx=ctx, fields=fields)

        calls = ctx.fastmcp.call_tool.call_args_list
        type_call = calls[0]
        assert type_call[0][0] == "playwright_browser_type"

    @pytest.mark.asyncio
    async def test_continues_on_error(self, tools, ctx):
        """Errors on one field should not prevent filling remaining fields."""
        call_count = 0

        async def side_effect(tool_name, args):
            nonlocal call_count
            call_count += 1
            if tool_name == "playwright_browser_type" and call_count == 1:
                raise RuntimeError("Element not found")
            return "[snapshot]"

        ctx.fastmcp.call_tool = AsyncMock(side_effect=side_effect)

        fields = [
            {"ref": "r1", "value": "fail", "type": "text"},
            {"ref": "r2", "value": "succeed", "type": "text"},
        ]

        result = await tools["web_fill_form"](ctx=ctx, fields=fields)

        assert result["filled_count"] == 1
        assert result["total_fields"] == 2
        assert len(result["errors"]) == 1
        assert result["errors"][0]["ref"] == "r1"

    @pytest.mark.asyncio
    async def test_returns_verification_snapshot(self, tools, ctx):
        ctx.fastmcp.call_tool.return_value = "[snapshot]"
        fields = [{"ref": "r1", "value": "hello", "type": "text"}]

        result = await tools["web_fill_form"](ctx=ctx, fields=fields)

        assert "snapshot" in result
        # Last call should be the verification snapshot
        last_call = ctx.fastmcp.call_tool.call_args_list[-1]
        assert last_call[0][0] == "playwright_browser_snapshot"

    @pytest.mark.asyncio
    async def test_reports_progress_for_each_field(self, tools, ctx):
        ctx.fastmcp.call_tool.return_value = "[snapshot]"
        fields = [
            {"ref": "r1", "value": "a", "type": "text"},
            {"ref": "r2", "value": "b", "type": "text"},
        ]

        await tools["web_fill_form"](ctx=ctx, fields=fields)

        # Should report at least: initial, per-field, and verification
        assert ctx.report_progress.call_count >= 3

    @pytest.mark.asyncio
    async def test_empty_fields_list(self, tools, ctx):
        ctx.fastmcp.call_tool.return_value = "[snapshot]"

        result = await tools["web_fill_form"](ctx=ctx, fields=[])

        assert result["filled_count"] == 0
        assert result["total_fields"] == 0
        assert result["errors"] == []

    @pytest.mark.asyncio
    async def test_email_and_password_use_type(self, tools, ctx):
        """Email and password fields should use playwright_browser_type."""
        ctx.fastmcp.call_tool.return_value = "[snapshot]"
        fields = [
            {"ref": "r1", "value": "user@test.com", "type": "email"},
            {"ref": "r2", "value": "secret123", "type": "password"},
        ]

        await tools["web_fill_form"](ctx=ctx, fields=fields)

        type_calls = [
            c for c in ctx.fastmcp.call_tool.call_args_list
            if c[0][0] == "playwright_browser_type"
        ]
        assert len(type_calls) == 2
