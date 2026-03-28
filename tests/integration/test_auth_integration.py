"""Integration tests for web authentication tools.

Verifies that web_login and web_check_auth_state call the correct sequence
of proxied Playwright tools and return the expected structure.
"""

from __future__ import annotations

import pytest


class TestWebLoginIntegration:
    """End-to-end verification of the web_login tool."""

    @pytest.mark.asyncio
    async def test_calls_navigate_then_snapshot(self, auth_tools, mock_context, tool_calls):
        """web_login must navigate to the URL, then snapshot the page."""
        result = await auth_tools["web_login"](
            url="https://app.example.com/login",
            username="admin@example.com",
            password="s3cret",
            ctx=mock_context,
        )

        tool_names = [c["tool"] for c in tool_calls]
        assert tool_names == [
            "playwright_browser_navigate",
            "playwright_browser_snapshot",
        ]

    @pytest.mark.asyncio
    async def test_navigate_receives_correct_url(self, auth_tools, mock_context, tool_calls):
        url = "https://sso.fourth.com/identity"
        await auth_tools["web_login"](
            url=url, username="u", password="p", ctx=mock_context,
        )

        nav_call = tool_calls[0]
        assert nav_call["tool"] == "playwright_browser_navigate"
        assert nav_call["args"] == {"url": url}

    @pytest.mark.asyncio
    async def test_return_structure_keys(self, auth_tools, mock_context):
        result = await auth_tools["web_login"](
            url="https://example.com/login",
            username="user1",
            password="pass1",
            ctx=mock_context,
        )

        assert set(result.keys()) == {"url", "username", "submit_method", "snapshot", "instruction"}

    @pytest.mark.asyncio
    async def test_return_contains_username_in_instruction(self, auth_tools, mock_context):
        result = await auth_tools["web_login"](
            url="https://example.com/login",
            username="dave@fourth.com",
            password="pw",
            ctx=mock_context,
        )

        assert "dave@fourth.com" in result["instruction"]

    @pytest.mark.asyncio
    async def test_return_contains_password_in_instruction(self, auth_tools, mock_context):
        result = await auth_tools["web_login"](
            url="https://example.com/login",
            username="u",
            password="hunter2",
            ctx=mock_context,
        )

        assert "hunter2" in result["instruction"]

    @pytest.mark.asyncio
    async def test_click_submit_method_instruction(self, auth_tools, mock_context):
        """Default submit_method='click' should mention clicking the submit button."""
        result = await auth_tools["web_login"](
            url="https://example.com/login",
            username="u",
            password="p",
            ctx=mock_context,
        )

        assert result["submit_method"] == "click"
        assert "click" in result["instruction"].lower()
        assert "Enter" not in result["instruction"] or "press Enter" not in result["instruction"]

    @pytest.mark.asyncio
    async def test_enter_submit_method_instruction(self, auth_tools, mock_context):
        """submit_method='enter' should instruct to press Enter, not click."""
        result = await auth_tools["web_login"](
            url="https://example.com/login",
            username="u",
            password="p",
            submit_method="enter",
            ctx=mock_context,
        )

        assert result["submit_method"] == "enter"
        assert "press Enter" in result["instruction"] or "press_key" in result["instruction"]

    @pytest.mark.asyncio
    async def test_snapshot_is_populated(self, auth_tools, mock_context):
        result = await auth_tools["web_login"](
            url="https://example.com/login",
            username="u",
            password="p",
            ctx=mock_context,
        )

        assert result["snapshot"] is not None
        assert len(str(result["snapshot"])) > 0

    @pytest.mark.asyncio
    async def test_progress_reported(self, auth_tools, mock_context):
        await auth_tools["web_login"](
            url="https://example.com/login",
            username="u",
            password="p",
            ctx=mock_context,
        )

        assert mock_context.report_progress.call_count >= 2


class TestWebCheckAuthStateIntegration:
    """End-to-end verification of the web_check_auth_state tool."""

    @pytest.mark.asyncio
    async def test_calls_only_snapshot(self, auth_tools, mock_context, tool_calls):
        await auth_tools["web_check_auth_state"](ctx=mock_context)

        assert len(tool_calls) == 1
        assert tool_calls[0]["tool"] == "playwright_browser_snapshot"
        assert tool_calls[0]["args"] == {}

    @pytest.mark.asyncio
    async def test_return_structure(self, auth_tools, mock_context):
        result = await auth_tools["web_check_auth_state"](ctx=mock_context)

        assert set(result.keys()) == {"snapshot", "instruction"}

    @pytest.mark.asyncio
    async def test_instruction_mentions_auth_indicators(self, auth_tools, mock_context):
        result = await auth_tools["web_check_auth_state"](ctx=mock_context)
        instruction = result["instruction"].lower()

        assert "logged in" in instruction or "authenticated" in instruction
        assert "logged out" in instruction or "login" in instruction

    @pytest.mark.asyncio
    async def test_instruction_mentions_profile_indicators(self, auth_tools, mock_context):
        result = await auth_tools["web_check_auth_state"](ctx=mock_context)
        instruction = result["instruction"]

        # Should mention common auth indicators
        assert "logout" in instruction.lower() or "sign-out" in instruction.lower()
