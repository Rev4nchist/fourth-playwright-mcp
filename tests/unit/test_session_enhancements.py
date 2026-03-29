"""Tests for session persistence enhancements."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.tools.session import register_session_tools, _session_store, SAVE_SESSION_JS


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


class TestSaveSessionJsEnhancements:
    """SAVE_SESSION_JS should capture extended session data."""

    def test_captures_origin(self):
        assert "origin" in SAVE_SESSION_JS, \
            "SAVE_SESSION_JS should capture window.location.origin"

    def test_captures_user_agent(self):
        assert "userAgent" in SAVE_SESSION_JS, \
            "SAVE_SESSION_JS should capture navigator.userAgent"

    def test_captures_timestamp(self):
        assert "timestamp" in SAVE_SESSION_JS, \
            "SAVE_SESSION_JS should capture a timestamp"

    def test_captures_session_storage(self):
        assert "sessionStorage" in SAVE_SESSION_JS, \
            "SAVE_SESSION_JS should capture sessionStorage"

    def test_captures_local_storage(self):
        assert "localStorage" in SAVE_SESSION_JS, \
            "SAVE_SESSION_JS should capture localStorage"

    def test_captures_cookies(self):
        assert "cookies" in SAVE_SESSION_JS or "cookie" in SAVE_SESSION_JS


class TestSessionStorageRestoration:
    """web_load_session should restore sessionStorage."""

    def setup_method(self):
        _session_store.clear()
        self.mcp = make_mcp()
        register_session_tools(self.mcp)
        self.load_tool = self.mcp._registered_tools["web_load_session"]

    def teardown_method(self):
        _session_store.clear()

    @pytest.mark.asyncio
    async def test_restores_session_storage(self):
        """web_load_session should inject sessionStorage items."""
        _session_store["test"] = {
            "url": "https://example.com",
            "cookies": "",
            "localStorage": {},
            "sessionStorage": {"key1": "val1", "key2": "val2"},
            "origin": "https://example.com",
            "userAgent": "test",
            "timestamp": "2026-03-27T00:00:00Z",
        }

        evaluate_calls = []

        async def side_effect(tool_name, args):
            if tool_name == "playwright_browser_evaluate":
                evaluate_calls.append(args)
            return "<snapshot>"

        ctx = make_ctx(call_tool_side_effect=side_effect)
        await self.load_tool(ctx=ctx, session_name="test")

        # Should have at least one evaluate call that mentions sessionStorage
        session_storage_calls = [
            c for c in evaluate_calls
            if "sessionStorage" in c.get("function", "")
        ]
        assert len(session_storage_calls) >= 1, \
            "web_load_session should inject sessionStorage data"


class TestWebListSessions:
    """Tests for the new web_list_sessions tool."""

    def setup_method(self):
        _session_store.clear()
        self.mcp = make_mcp()
        register_session_tools(self.mcp)
        self.tool = self.mcp._registered_tools.get("web_list_sessions")

    def teardown_method(self):
        _session_store.clear()

    def test_tool_registered(self):
        assert self.tool is not None, "web_list_sessions tool must be registered"

    @pytest.mark.asyncio
    async def test_empty_store(self):
        ctx = make_ctx()
        result = await self.tool(ctx=ctx)
        assert result["count"] == 0
        assert result["sessions"] == {}

    @pytest.mark.asyncio
    async def test_with_sessions(self):
        _session_store["alpha"] = {
            "url": "https://alpha.com",
            "timestamp": "2026-03-27T10:00:00Z",
        }
        _session_store["beta"] = {
            "url": "https://beta.com",
            "timestamp": "2026-03-27T11:00:00Z",
        }
        ctx = make_ctx()
        result = await self.tool(ctx=ctx)
        assert result["count"] == 2
        assert "alpha" in result["sessions"]
        assert "beta" in result["sessions"]
        assert result["sessions"]["alpha"]["url"] == "https://alpha.com"
        assert result["sessions"]["beta"]["timestamp"] == "2026-03-27T11:00:00Z"

    @pytest.mark.asyncio
    async def test_with_non_dict_session_data(self):
        """Should handle sessions stored as non-dict gracefully."""
        _session_store["weird"] = "not a dict"
        ctx = make_ctx()
        result = await self.tool(ctx=ctx)
        assert result["count"] == 1
        assert result["sessions"]["weird"]["url"] == "unknown"

    @pytest.mark.asyncio
    async def test_has_docstring(self):
        assert self.tool.__doc__ is not None
        assert "session" in self.tool.__doc__.lower()


class TestSessionToolRegistration:
    """Verify all session tools are registered."""

    def test_registers_three_tools(self):
        mcp = make_mcp()
        register_session_tools(mcp)
        expected = {"web_save_session", "web_load_session", "web_list_sessions"}
        assert set(mcp._registered_tools.keys()) == expected

    def test_session_module_has_lifecycle_comment(self):
        """session.py should have a session lifecycle doccomment."""
        source = Path(__file__).resolve().parents[2] / "src" / "tools" / "session.py"
        content = source.read_text(encoding="utf-8")
        assert "persist" in content.lower() or "restart" in content.lower(), \
            "session.py should document session lifecycle"
