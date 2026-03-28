"""Integration tests for web data extraction tools.

Verifies that web_extract_table, web_extract_page_data, and web_extract_links
call the correct Playwright tools and return format-appropriate instructions.
"""

from __future__ import annotations

import pytest


class TestWebExtractTableIntegration:
    """End-to-end verification of web_extract_table."""

    @pytest.mark.asyncio
    async def test_calls_snapshot(self, extraction_tools, mock_context, tool_calls):
        await extraction_tools["web_extract_table"](ctx=mock_context)

        assert len(tool_calls) == 1
        assert tool_calls[0]["tool"] == "playwright_browser_snapshot"

    @pytest.mark.asyncio
    async def test_return_structure(self, extraction_tools, mock_context):
        result = await extraction_tools["web_extract_table"](ctx=mock_context)

        assert set(result.keys()) == {"table_description", "format", "snapshot", "instruction"}

    @pytest.mark.asyncio
    async def test_default_format_is_rows(self, extraction_tools, mock_context):
        result = await extraction_tools["web_extract_table"](ctx=mock_context)

        assert result["format"] == "rows"

    @pytest.mark.asyncio
    async def test_rows_format_mentions_dictionaries(self, extraction_tools, mock_context):
        result = await extraction_tools["web_extract_table"](
            ctx=mock_context, format="rows",
        )

        assert "dictionar" in result["instruction"].lower()

    @pytest.mark.asyncio
    async def test_csv_format_instruction(self, extraction_tools, mock_context):
        result = await extraction_tools["web_extract_table"](
            ctx=mock_context, format="csv",
        )

        assert "csv" in result["instruction"].lower()

    @pytest.mark.asyncio
    async def test_markdown_format_instruction(self, extraction_tools, mock_context):
        result = await extraction_tools["web_extract_table"](
            ctx=mock_context, format="markdown",
        )

        assert "markdown" in result["instruction"].lower()

    @pytest.mark.asyncio
    async def test_instruction_always_mentions_pagination(self, extraction_tools, mock_context):
        """All formats should mention pagination controls."""
        for fmt in ("rows", "csv", "markdown"):
            result = await extraction_tools["web_extract_table"](
                ctx=mock_context, format=fmt,
            )
            assert "pagination" in result["instruction"].lower(), (
                f"format={fmt} instruction missing pagination mention"
            )

    @pytest.mark.asyncio
    async def test_custom_table_description(self, extraction_tools, mock_context):
        result = await extraction_tools["web_extract_table"](
            ctx=mock_context, table_description="employee schedule",
        )

        assert result["table_description"] == "employee schedule"
        assert "employee schedule" in result["instruction"]

    @pytest.mark.asyncio
    async def test_progress_reported(self, extraction_tools, mock_context):
        await extraction_tools["web_extract_table"](ctx=mock_context)

        mock_context.report_progress.assert_called()


class TestWebExtractPageDataIntegration:
    """End-to-end verification of web_extract_page_data."""

    @pytest.mark.asyncio
    async def test_without_screenshot_calls_only_snapshot(
        self, extraction_tools, mock_context, tool_calls,
    ):
        await extraction_tools["web_extract_page_data"](ctx=mock_context)

        tool_names = [c["tool"] for c in tool_calls]
        assert "playwright_browser_evaluate" in tool_names

    @pytest.mark.asyncio
    async def test_with_screenshot_calls_both(
        self, extraction_tools, mock_context, tool_calls,
    ):
        await extraction_tools["web_extract_page_data"](
            ctx=mock_context, include_screenshot=True,
        )

        tool_names = [c["tool"] for c in tool_calls]
        assert "playwright_browser_evaluate" in tool_names
        assert "playwright_browser_take_screenshot" in tool_names

    @pytest.mark.asyncio
    async def test_with_screenshot_snapshot_before_screenshot(
        self, extraction_tools, mock_context, tool_calls,
    ):
        """Evaluate should come before screenshot in call order."""
        await extraction_tools["web_extract_page_data"](
            ctx=mock_context, include_screenshot=True,
        )

        tool_names = [c["tool"] for c in tool_calls]
        eval_idx = tool_names.index("playwright_browser_evaluate")
        shot_idx = tool_names.index("playwright_browser_take_screenshot")
        assert eval_idx < shot_idx

    @pytest.mark.asyncio
    async def test_return_structure_without_screenshot(self, extraction_tools, mock_context):
        result = await extraction_tools["web_extract_page_data"](ctx=mock_context)

        assert "content" in result
        assert "target" in result
        assert "snapshot" in result
        assert "screenshot" not in result or result["screenshot"] is None

    @pytest.mark.asyncio
    async def test_return_structure_with_screenshot(self, extraction_tools, mock_context):
        result = await extraction_tools["web_extract_page_data"](
            ctx=mock_context, include_screenshot=True,
        )

        assert "content" in result
        assert "screenshot" in result
        assert "target" in result
        assert "snapshot" in result

    @pytest.mark.asyncio
    async def test_custom_target(self, extraction_tools, mock_context):
        result = await extraction_tools["web_extract_page_data"](
            ctx=mock_context, target="sidebar metrics",
        )

        assert result["target"] == "sidebar metrics"

    @pytest.mark.asyncio
    async def test_default_target(self, extraction_tools, mock_context):
        result = await extraction_tools["web_extract_page_data"](ctx=mock_context)

        assert result["target"] == "all visible content"

    @pytest.mark.asyncio
    async def test_progress_reported(self, extraction_tools, mock_context):
        await extraction_tools["web_extract_page_data"](ctx=mock_context)

        mock_context.report_progress.assert_called()


class TestWebExtractLinksIntegration:
    """End-to-end verification of web_extract_links with DOM extraction."""

    @pytest.mark.asyncio
    async def test_calls_evaluate(
        self, extraction_tools, mock_context, tool_calls,
    ):
        await extraction_tools["web_extract_links"](ctx=mock_context)

        assert len(tool_calls) == 1
        assert tool_calls[0]["tool"] == "playwright_browser_evaluate"

    @pytest.mark.asyncio
    async def test_return_structure(self, extraction_tools, mock_context):
        result = await extraction_tools["web_extract_links"](ctx=mock_context)

        assert set(result.keys()) == {"links", "count", "filter"}

    @pytest.mark.asyncio
    async def test_returns_structured_links(self, extraction_tools, mock_context):
        result = await extraction_tools["web_extract_links"](ctx=mock_context)

        assert isinstance(result["links"], list)
        assert result["count"] == len(result["links"])
        assert result["filter"] is None

    @pytest.mark.asyncio
    async def test_with_filter_text(self, extraction_tools, mock_context):
        result = await extraction_tools["web_extract_links"](
            ctx=mock_context, filter_text="privacy",
        )

        assert result["filter"] == "privacy"
        # Should only contain links matching "privacy"
        for link in result["links"]:
            text_lower = link.get("text", "").lower()
            href_lower = link.get("href", "").lower()
            assert "privacy" in text_lower or "privacy" in href_lower

    @pytest.mark.asyncio
    async def test_filter_reduces_count(self, extraction_tools, mock_context):
        all_result = await extraction_tools["web_extract_links"](ctx=mock_context)
        filtered = await extraction_tools["web_extract_links"](
            ctx=mock_context, filter_text="dashboard",
        )

        assert filtered["count"] <= all_result["count"]
        assert filtered["count"] == len(filtered["links"])

    @pytest.mark.asyncio
    async def test_links_have_text_and_href(self, extraction_tools, mock_context):
        result = await extraction_tools["web_extract_links"](ctx=mock_context)

        for link in result["links"]:
            assert "text" in link
            assert "href" in link
