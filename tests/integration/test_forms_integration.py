"""Integration tests for web form automation tools.

Verifies that web_discover_form and web_fill_form call the correct Playwright
tools with correct arguments, handle different field types, and recover
gracefully from per-field errors.
"""

from __future__ import annotations

import pytest


class TestWebDiscoverFormIntegration:
    """End-to-end verification of web_discover_form."""

    @pytest.mark.asyncio
    async def test_calls_snapshot(self, form_tools, mock_context, tool_calls):
        await form_tools["web_discover_form"](ctx=mock_context)

        assert len(tool_calls) == 1
        assert tool_calls[0]["tool"] == "playwright_browser_snapshot"

    @pytest.mark.asyncio
    async def test_return_structure(self, form_tools, mock_context):
        result = await form_tools["web_discover_form"](ctx=mock_context)

        assert set(result.keys()) == {"form_description", "snapshot", "instruction"}

    @pytest.mark.asyncio
    async def test_default_description(self, form_tools, mock_context):
        result = await form_tools["web_discover_form"](ctx=mock_context)

        assert result["form_description"] == "main form on page"

    @pytest.mark.asyncio
    async def test_custom_description(self, form_tools, mock_context):
        result = await form_tools["web_discover_form"](
            ctx=mock_context, form_description="employee onboarding form",
        )

        assert result["form_description"] == "employee onboarding form"
        assert "employee onboarding form" in result["instruction"]

    @pytest.mark.asyncio
    async def test_instruction_mentions_field_attributes(self, form_tools, mock_context):
        result = await form_tools["web_discover_form"](ctx=mock_context)
        instruction = result["instruction"]

        for attr in ["label", "type", "ref", "current_value", "options"]:
            assert attr in instruction, f"Missing '{attr}' in instruction"

    @pytest.mark.asyncio
    async def test_progress_reported(self, form_tools, mock_context):
        await form_tools["web_discover_form"](ctx=mock_context)

        mock_context.report_progress.assert_called()


class TestWebFillFormTextFields:
    """Verify web_fill_form dispatches correctly for text-type fields."""

    @pytest.mark.asyncio
    async def test_single_text_field(self, form_tools, mock_context, tool_calls):
        fields = [{"ref": "r10", "value": "John Doe", "type": "text"}]

        result = await form_tools["web_fill_form"](
            ctx=mock_context, fields=fields,
        )

        # Find the type call (not the final snapshot)
        type_calls = [c for c in tool_calls if c["tool"] == "playwright_browser_type"]
        assert len(type_calls) == 1
        assert type_calls[0]["args"] == {
            "element": "form field",
            "ref": "r10",
            "text": "John Doe",
        }

    @pytest.mark.asyncio
    async def test_multiple_text_fields(self, form_tools, mock_context, tool_calls):
        fields = [
            {"ref": "r10", "value": "Alice", "type": "text"},
            {"ref": "r11", "value": "alice@co.com", "type": "email"},
            {"ref": "r12", "value": "s3cret!", "type": "password"},
        ]

        result = await form_tools["web_fill_form"](
            ctx=mock_context, fields=fields,
        )

        type_calls = [c for c in tool_calls if c["tool"] == "playwright_browser_type"]
        assert len(type_calls) == 3
        assert result["filled_count"] == 3
        assert result["total_fields"] == 3
        assert result["errors"] == []

    @pytest.mark.asyncio
    async def test_textarea_uses_type(self, form_tools, mock_context, tool_calls):
        fields = [{"ref": "r20", "value": "Long note here", "type": "textarea"}]

        await form_tools["web_fill_form"](ctx=mock_context, fields=fields)

        type_calls = [c for c in tool_calls if c["tool"] == "playwright_browser_type"]
        assert len(type_calls) == 1
        assert type_calls[0]["args"]["text"] == "Long note here"


class TestWebFillFormSelectFields:
    """Verify web_fill_form uses select_option for select-type fields."""

    @pytest.mark.asyncio
    async def test_select_field(self, form_tools, mock_context, tool_calls):
        fields = [{"ref": "r15", "value": "option_b", "type": "select"}]

        await form_tools["web_fill_form"](ctx=mock_context, fields=fields)

        select_calls = [c for c in tool_calls if c["tool"] == "playwright_browser_select_option"]
        assert len(select_calls) == 1
        assert select_calls[0]["args"] == {
            "element": "form field",
            "ref": "r15",
            "values": ["option_b"],
        }

    @pytest.mark.asyncio
    async def test_select_not_typed(self, form_tools, mock_context, tool_calls):
        """Select fields should NOT use playwright_browser_type."""
        fields = [{"ref": "r15", "value": "opt", "type": "select"}]

        await form_tools["web_fill_form"](ctx=mock_context, fields=fields)

        type_calls = [c for c in tool_calls if c["tool"] == "playwright_browser_type"]
        assert len(type_calls) == 0


class TestWebFillFormCheckboxRadio:
    """Verify web_fill_form uses click for checkbox and radio fields."""

    @pytest.mark.asyncio
    async def test_checkbox_clicked(self, form_tools, mock_context, tool_calls):
        fields = [{"ref": "r18", "value": "on", "type": "checkbox"}]

        await form_tools["web_fill_form"](ctx=mock_context, fields=fields)

        click_calls = [c for c in tool_calls if c["tool"] == "playwright_browser_click"]
        assert len(click_calls) == 1
        assert click_calls[0]["args"] == {
            "element": "form field",
            "ref": "r18",
        }

    @pytest.mark.asyncio
    async def test_radio_clicked(self, form_tools, mock_context, tool_calls):
        fields = [{"ref": "r19", "value": "yes", "type": "radio"}]

        await form_tools["web_fill_form"](ctx=mock_context, fields=fields)

        click_calls = [c for c in tool_calls if c["tool"] == "playwright_browser_click"]
        assert len(click_calls) == 1
        assert click_calls[0]["args"]["ref"] == "r19"


class TestWebFillFormMixedTypes:
    """Verify web_fill_form handles a mixture of field types correctly."""

    @pytest.mark.asyncio
    async def test_mixed_fields_dispatched_correctly(
        self, form_tools, mock_context, tool_calls,
    ):
        fields = [
            {"ref": "r1", "value": "Jane", "type": "text"},
            {"ref": "r2", "value": "Manager", "type": "select"},
            {"ref": "r3", "value": "true", "type": "checkbox"},
            {"ref": "r4", "value": "jane@co.com", "type": "email"},
            {"ref": "r5", "value": "full-time", "type": "radio"},
        ]

        result = await form_tools["web_fill_form"](
            ctx=mock_context, fields=fields,
        )

        assert result["filled_count"] == 5
        assert result["total_fields"] == 5
        assert result["errors"] == []

        type_calls = [c for c in tool_calls if c["tool"] == "playwright_browser_type"]
        select_calls = [c for c in tool_calls if c["tool"] == "playwright_browser_select_option"]
        click_calls = [c for c in tool_calls if c["tool"] == "playwright_browser_click"]

        assert len(type_calls) == 2      # text + email
        assert len(select_calls) == 1    # select
        assert len(click_calls) == 2     # checkbox + radio

    @pytest.mark.asyncio
    async def test_mixed_fields_order_preserved(
        self, form_tools, mock_context, tool_calls,
    ):
        """Fields should be filled in the order they appear in the list."""
        fields = [
            {"ref": "r1", "value": "a", "type": "text"},
            {"ref": "r2", "value": "b", "type": "select"},
            {"ref": "r3", "value": "c", "type": "checkbox"},
        ]

        await form_tools["web_fill_form"](ctx=mock_context, fields=fields)

        # Exclude the final snapshot call
        fill_calls = [c for c in tool_calls if c["tool"] != "playwright_browser_snapshot"]
        assert fill_calls[0]["args"]["ref"] == "r1"
        assert fill_calls[1]["args"]["ref"] == "r2"
        assert fill_calls[2]["args"]["ref"] == "r3"


class TestWebFillFormErrorRecovery:
    """Verify web_fill_form continues filling after per-field errors."""

    @pytest.mark.asyncio
    async def test_continues_after_error(self, form_tools, mock_context_with_failures, tool_calls):
        ctx = mock_context_with_failures(fail_refs={"r2"})

        fields = [
            {"ref": "r1", "value": "ok_field", "type": "text"},
            {"ref": "r2", "value": "will_fail", "type": "text"},
            {"ref": "r3", "value": "also_ok", "type": "text"},
        ]

        result = await form_tools["web_fill_form"](ctx=ctx, fields=fields)

        assert result["filled_count"] == 2
        assert result["total_fields"] == 3
        assert len(result["errors"]) == 1
        assert result["errors"][0]["ref"] == "r2"

    @pytest.mark.asyncio
    async def test_error_contains_message(self, form_tools, mock_context_with_failures, tool_calls):
        ctx = mock_context_with_failures(fail_refs={"r5"})

        fields = [{"ref": "r5", "value": "x", "type": "text"}]

        result = await form_tools["web_fill_form"](ctx=ctx, fields=fields)

        assert len(result["errors"]) == 1
        assert "r5" in result["errors"][0]["error"]

    @pytest.mark.asyncio
    async def test_snapshot_still_taken_after_errors(
        self, form_tools, mock_context_with_failures, tool_calls,
    ):
        """Final snapshot should still be taken even when some fields fail."""
        ctx = mock_context_with_failures(fail_refs={"r1"})

        fields = [{"ref": "r1", "value": "x", "type": "text"}]

        result = await form_tools["web_fill_form"](ctx=ctx, fields=fields)

        snapshot_calls = [c for c in tool_calls if c["tool"] == "playwright_browser_snapshot"]
        assert len(snapshot_calls) == 1
        assert result["snapshot"] is not None

    @pytest.mark.asyncio
    async def test_multiple_errors(self, form_tools, mock_context_with_failures, tool_calls):
        ctx = mock_context_with_failures(fail_refs={"r1", "r3"})

        fields = [
            {"ref": "r1", "value": "a", "type": "text"},
            {"ref": "r2", "value": "b", "type": "text"},
            {"ref": "r3", "value": "c", "type": "select"},
        ]

        result = await form_tools["web_fill_form"](ctx=ctx, fields=fields)

        assert result["filled_count"] == 1
        assert len(result["errors"]) == 2

    @pytest.mark.asyncio
    async def test_progress_reported_per_field(self, form_tools, mock_context, tool_calls):
        fields = [
            {"ref": "r1", "value": "a", "type": "text"},
            {"ref": "r2", "value": "b", "type": "text"},
            {"ref": "r3", "value": "c", "type": "text"},
        ]

        await form_tools["web_fill_form"](ctx=mock_context, fields=fields)

        # Initial progress + per-field + final = at least len(fields) + 2
        assert mock_context.report_progress.call_count >= len(fields) + 1


class TestWebFillFormDefaultType:
    """Verify default field type when 'type' key is missing."""

    @pytest.mark.asyncio
    async def test_missing_type_defaults_to_text(self, form_tools, mock_context, tool_calls):
        """Fields without explicit type should be treated as text."""
        fields = [{"ref": "r10", "value": "fallback"}]

        await form_tools["web_fill_form"](ctx=mock_context, fields=fields)

        type_calls = [c for c in tool_calls if c["tool"] == "playwright_browser_type"]
        assert len(type_calls) == 1
