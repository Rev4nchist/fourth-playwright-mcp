"""Integration tests for web navigation tools.

Verifies that web_navigate_and_wait, web_wait_for_ready, and
web_discover_navigation call the correct Playwright tools in the right order
and return well-structured results.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.integration.conftest import REALISTIC_SNAPSHOT


class TestWebNavigateAndWaitIntegration:
    """End-to-end verification of web_navigate_and_wait."""

    @pytest.mark.asyncio
    async def test_navigates_to_url(self, navigation_tools, mock_context, tool_calls):
        url = "https://dashboard.example.com/reports"
        await navigation_tools["web_navigate_and_wait"](
            url=url, ctx=mock_context,
        )

        nav_calls = [c for c in tool_calls if c["tool"] == "playwright_browser_navigate"]
        assert len(nav_calls) == 1
        assert nav_calls[0]["args"]["url"] == url

    @pytest.mark.asyncio
    async def test_without_wait_for_text_polls_via_snapshot(
        self, navigation_tools, mock_context, tool_calls,
    ):
        """When no wait_for_text, should poll via snapshot then do a final snapshot."""
        await navigation_tools["web_navigate_and_wait"](
            url="https://example.com", ctx=mock_context,
        )

        tool_names = [c["tool"] for c in tool_calls]
        # First: navigate, then at least one polling snapshot, then final snapshot
        assert tool_names[0] == "playwright_browser_navigate"
        snapshot_calls = [n for n in tool_names if n == "playwright_browser_snapshot"]
        # At least 2: one from polling loop (which succeeds immediately) + final snapshot
        assert len(snapshot_calls) >= 2

    @pytest.mark.asyncio
    async def test_with_wait_for_text_uses_wait_for(
        self, navigation_tools, mock_context, tool_calls,
    ):
        """When wait_for_text is provided, should use playwright_browser_wait_for."""
        await navigation_tools["web_navigate_and_wait"](
            url="https://example.com",
            wait_for_text="Dashboard loaded",
            ctx=mock_context,
        )

        tool_names = [c["tool"] for c in tool_calls]
        assert "playwright_browser_wait_for" in tool_names

        wait_call = next(c for c in tool_calls if c["tool"] == "playwright_browser_wait_for")
        assert wait_call["args"]["text"] == "Dashboard loaded"

    @pytest.mark.asyncio
    async def test_with_wait_for_text_no_polling_snapshots(
        self, navigation_tools, mock_context, tool_calls,
    ):
        """wait_for_text path should NOT use polling snapshots, only the final one."""
        await navigation_tools["web_navigate_and_wait"](
            url="https://example.com",
            wait_for_text="Ready",
            ctx=mock_context,
        )

        tool_names = [c["tool"] for c in tool_calls]
        # navigate, wait_for, final snapshot
        assert tool_names == [
            "playwright_browser_navigate",
            "playwright_browser_wait_for",
            "playwright_browser_snapshot",
        ]

    @pytest.mark.asyncio
    async def test_return_structure(self, navigation_tools, mock_context):
        result = await navigation_tools["web_navigate_and_wait"](
            url="https://example.com", ctx=mock_context,
        )

        assert set(result.keys()) == {"url", "loaded", "wait_seconds", "snapshot"}

    @pytest.mark.asyncio
    async def test_loaded_true_on_success(self, navigation_tools, mock_context):
        result = await navigation_tools["web_navigate_and_wait"](
            url="https://example.com", ctx=mock_context,
        )

        assert result["loaded"] is True

    @pytest.mark.asyncio
    async def test_url_echoed_back(self, navigation_tools, mock_context):
        result = await navigation_tools["web_navigate_and_wait"](
            url="https://specific.example.com/path", ctx=mock_context,
        )

        assert result["url"] == "https://specific.example.com/path"

    @pytest.mark.asyncio
    async def test_wait_seconds_is_positive(self, navigation_tools, mock_context):
        result = await navigation_tools["web_navigate_and_wait"](
            url="https://example.com", ctx=mock_context,
        )

        assert isinstance(result["wait_seconds"], (int, float))
        assert result["wait_seconds"] >= 1

    @pytest.mark.asyncio
    async def test_progress_reported(self, navigation_tools, mock_context):
        await navigation_tools["web_navigate_and_wait"](
            url="https://example.com", ctx=mock_context,
        )

        assert mock_context.report_progress.call_count >= 2


class TestWebWaitForReadyIntegration:
    """End-to-end verification of web_wait_for_ready."""

    @pytest.mark.asyncio
    async def test_with_indicator_text_uses_wait_for(
        self, navigation_tools, mock_context, tool_calls,
    ):
        result = await navigation_tools["web_wait_for_ready"](
            ctx=mock_context, indicator_text="Table loaded",
        )

        tool_names = [c["tool"] for c in tool_calls]
        assert "playwright_browser_wait_for" in tool_names

        wait_call = next(c for c in tool_calls if c["tool"] == "playwright_browser_wait_for")
        assert wait_call["args"]["text"] == "Table loaded"

    @pytest.mark.asyncio
    async def test_with_indicator_text_returns_loaded_true(
        self, navigation_tools, mock_context,
    ):
        result = await navigation_tools["web_wait_for_ready"](
            ctx=mock_context, indicator_text="Ready",
        )

        assert result["loaded"] is True
        assert result["wait_seconds"] == 1

    @pytest.mark.asyncio
    async def test_with_indicator_text_tool_sequence(
        self, navigation_tools, mock_context, tool_calls,
    ):
        """indicator_text path: wait_for, then snapshot."""
        await navigation_tools["web_wait_for_ready"](
            ctx=mock_context, indicator_text="Content",
        )

        tool_names = [c["tool"] for c in tool_calls]
        assert tool_names == [
            "playwright_browser_wait_for",
            "playwright_browser_snapshot",
        ]

    @pytest.mark.asyncio
    async def test_polling_without_indicator(
        self, navigation_tools, mock_context, tool_calls,
    ):
        """Without indicator_text, should poll via snapshot."""
        result = await navigation_tools["web_wait_for_ready"](ctx=mock_context)

        # Should succeed on first poll since our mock returns non-empty snapshot
        assert result["loaded"] is True
        assert result["wait_seconds"] == 1

        tool_names = [c["tool"] for c in tool_calls]
        assert all(t == "playwright_browser_snapshot" for t in tool_names)

    @pytest.mark.asyncio
    async def test_polling_returns_snapshot(self, navigation_tools, mock_context):
        result = await navigation_tools["web_wait_for_ready"](ctx=mock_context)

        assert result["snapshot"] is not None
        assert "snapshot" in result

    @pytest.mark.asyncio
    async def test_return_structure_with_indicator(self, navigation_tools, mock_context):
        result = await navigation_tools["web_wait_for_ready"](
            ctx=mock_context, indicator_text="Done",
        )

        assert set(result.keys()) == {"loaded", "wait_seconds", "snapshot"}


class TestWebDiscoverNavigationIntegration:
    """End-to-end verification of web_discover_navigation."""

    @pytest.mark.asyncio
    async def test_calls_only_snapshot(
        self, navigation_tools, mock_context, tool_calls,
    ):
        await navigation_tools["web_discover_navigation"](ctx=mock_context)

        assert len(tool_calls) == 1
        assert tool_calls[0]["tool"] == "playwright_browser_snapshot"

    @pytest.mark.asyncio
    async def test_return_structure(self, navigation_tools, mock_context):
        result = await navigation_tools["web_discover_navigation"](ctx=mock_context)

        assert set(result.keys()) == {"snapshot", "instruction"}

    @pytest.mark.asyncio
    async def test_instruction_mentions_nav_elements(self, navigation_tools, mock_context):
        result = await navigation_tools["web_discover_navigation"](ctx=mock_context)
        instruction = result["instruction"].lower()

        for element_type in ["menu", "navigation", "breadcrumb", "link"]:
            assert element_type in instruction, f"Missing '{element_type}' in instruction"

    @pytest.mark.asyncio
    async def test_instruction_mentions_ref_id(self, navigation_tools, mock_context):
        result = await navigation_tools["web_discover_navigation"](ctx=mock_context)

        assert "ref" in result["instruction"].lower()
