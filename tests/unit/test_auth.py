"""Tests for web authentication tools."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from fastmcp import FastMCP

from src.tools.auth import register_auth_tools


@pytest.fixture
def mcp():
    app = FastMCP("test")
    register_auth_tools(app)
    return app


@pytest.fixture
def mock_ctx():
    ctx = AsyncMock()
    ctx.report_progress = AsyncMock()
    ctx.fastmcp = AsyncMock()
    ctx.fastmcp.call_tool = AsyncMock(return_value={"snapshot": "page content"})
    return ctx


def _extract_tools():
    tools = {}
    capture_mcp = MagicMock()
    def capture_tool(fn):
        tools[fn.__name__] = fn
        return fn
    capture_mcp.tool = capture_tool
    register_auth_tools(capture_mcp)
    return tools


class TestRegisterAuthTools:

    def test_registers_web_login(self):
        tools = _extract_tools()
        assert "web_login" in tools

    def test_registers_web_check_auth_state(self):
        tools = _extract_tools()
        assert "web_check_auth_state" in tools

    def test_does_not_register_fourth_login(self):
        tools = _extract_tools()
        assert "fourth_login" not in tools

    def test_does_not_register_fourth_get_user_context(self):
        tools = _extract_tools()
        assert "fourth_get_user_context" not in tools


class TestWebLogin:

    async def test_navigates_to_url(self, mock_ctx):
        tools = _extract_tools()
        result = await tools["web_login"](
            url="https://example.com/login",
            username="testuser",
            password="testpass",
            ctx=mock_ctx,
        )
        calls = mock_ctx.fastmcp.call_tool.call_args_list
        navigate_calls = [c for c in calls if c[0][0] == "playwright_browser_navigate"]
        assert len(navigate_calls) == 1
        assert navigate_calls[0][0][1] == {"url": "https://example.com/login"}

    async def test_takes_snapshot(self, mock_ctx):
        tools = _extract_tools()
        await tools["web_login"](
            url="https://example.com/login",
            username="testuser",
            password="testpass",
            ctx=mock_ctx,
        )
        calls = mock_ctx.fastmcp.call_tool.call_args_list
        snapshot_calls = [c for c in calls if c[0][0] == "playwright_browser_snapshot"]
        assert len(snapshot_calls) == 1

    async def test_returns_expected_keys(self, mock_ctx):
        tools = _extract_tools()
        result = await tools["web_login"](
            url="https://example.com/login",
            username="testuser",
            password="testpass",
            ctx=mock_ctx,
        )
        assert "url" in result
        assert "username" in result
        assert "submit_method" in result
        assert "snapshot" in result
        assert "instruction" in result

    async def test_returns_url_and_username(self, mock_ctx):
        tools = _extract_tools()
        result = await tools["web_login"](
            url="https://mysite.com/auth",
            username="admin@test.com",
            password="secret",
            ctx=mock_ctx,
        )
        assert result["url"] == "https://mysite.com/auth"
        assert result["username"] == "admin@test.com"

    async def test_default_submit_method_is_click(self, mock_ctx):
        tools = _extract_tools()
        result = await tools["web_login"](
            url="https://example.com/login",
            username="user",
            password="pass",
            ctx=mock_ctx,
        )
        assert result["submit_method"] == "click"

    async def test_enter_submit_method(self, mock_ctx):
        tools = _extract_tools()
        result = await tools["web_login"](
            url="https://example.com/login",
            username="user",
            password="pass",
            ctx=mock_ctx,
            submit_method="enter",
        )
        assert result["submit_method"] == "enter"

    async def test_click_instruction_mentions_click(self, mock_ctx):
        tools = _extract_tools()
        result = await tools["web_login"](
            url="https://example.com/login",
            username="user",
            password="pass",
            ctx=mock_ctx,
            submit_method="click",
        )
        assert "playwright_browser_click" in result["instruction"]

    async def test_enter_instruction_mentions_press_key(self, mock_ctx):
        tools = _extract_tools()
        result = await tools["web_login"](
            url="https://example.com/login",
            username="user",
            password="pass",
            ctx=mock_ctx,
            submit_method="enter",
        )
        assert "playwright_browser_press_key" in result["instruction"]

    async def test_instruction_contains_credentials(self, mock_ctx):
        tools = _extract_tools()
        result = await tools["web_login"](
            url="https://example.com/login",
            username="myuser",
            password="mypass",
            ctx=mock_ctx,
        )
        assert "myuser" in result["instruction"]
        assert "mypass" in result["instruction"]

    async def test_reports_progress(self, mock_ctx):
        tools = _extract_tools()
        await tools["web_login"](
            url="https://example.com/login",
            username="user",
            password="pass",
            ctx=mock_ctx,
        )
        assert mock_ctx.report_progress.call_count >= 2

    async def test_does_not_fill_fields_directly(self, mock_ctx):
        tools = _extract_tools()
        await tools["web_login"](
            url="https://example.com/login",
            username="user",
            password="pass",
            ctx=mock_ctx,
        )
        calls = mock_ctx.fastmcp.call_tool.call_args_list
        type_calls = [c for c in calls if c[0][0] == "playwright_browser_type"]
        assert len(type_calls) == 0


class TestWebCheckAuthState:

    async def test_takes_snapshot(self, mock_ctx):
        tools = _extract_tools()
        result = await tools["web_check_auth_state"](ctx=mock_ctx)
        calls = mock_ctx.fastmcp.call_tool.call_args_list
        snapshot_calls = [c for c in calls if c[0][0] == "playwright_browser_snapshot"]
        assert len(snapshot_calls) == 1

    async def test_returns_expected_keys(self, mock_ctx):
        tools = _extract_tools()
        result = await tools["web_check_auth_state"](ctx=mock_ctx)
        assert "snapshot" in result
        assert "instruction" in result

    async def test_instruction_mentions_auth_indicators(self, mock_ctx):
        tools = _extract_tools()
        result = await tools["web_check_auth_state"](ctx=mock_ctx)
        instruction = result["instruction"].lower()
        assert "logged in" in instruction or "authenticated" in instruction
        assert "logged out" in instruction or "login form" in instruction

    async def test_no_navigate_call(self, mock_ctx):
        tools = _extract_tools()
        await tools["web_check_auth_state"](ctx=mock_ctx)
        calls = mock_ctx.fastmcp.call_tool.call_args_list
        nav_calls = [c for c in calls if c[0][0] == "playwright_browser_navigate"]
        assert len(nav_calls) == 0

