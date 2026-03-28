"""Shared fixtures for integration tests.

Provides a realistic mock context that simulates the FastMCP tool dispatch
pattern, tracking all tool calls for assertion while returning plausible
responses for each proxied Playwright tool.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.tools.auth import register_auth_tools
from src.tools.extraction import register_extraction_tools
from src.tools.forms import register_form_tools
from src.tools.navigation import register_navigation_tools


# ---------------------------------------------------------------------------
# Realistic snapshot content that exercises downstream parsing logic
# ---------------------------------------------------------------------------

REALISTIC_SNAPSHOT = (
    "- navigation 'Main Menu'\n"
    "  - link 'Home' [ref=1]\n"
    "  - link 'Dashboard' [ref=2]\n"
    "  - link 'Settings' [ref=3]\n"
    "- heading 'Welcome back, testuser' [ref=4]\n"
    "- form 'Login Form'\n"
    "  - textbox 'Username' [ref=10]\n"
    "  - textbox 'Password' [ref=11]\n"
    "  - button 'Sign In' [ref=12]\n"
    "- table 'Employee Schedule'\n"
    "  - row 'Name | Shift | Hours'\n"
    "  - row 'Alice | Morning | 8'\n"
    "  - row 'Bob | Evening | 6'\n"
    "- link 'Privacy Policy' [ref=20]\n"
    "- link 'Terms of Service' [ref=21]\n"
    "- link 'Contact Us' [ref=22]\n"
)


# ---------------------------------------------------------------------------
# Tool call dispatcher
# ---------------------------------------------------------------------------

def _make_dispatch(tool_calls: list[dict], *, fail_refs: set[str] | None = None):
    """Return an async callable that logs calls and returns realistic responses.

    Parameters
    ----------
    tool_calls:
        Mutable list that accumulates every call for later assertion.
    fail_refs:
        Optional set of field ref IDs that should raise an exception when
        a form-filling tool targets them.  Used to test error-recovery paths.
    """
    fail_refs = fail_refs or set()

    async def dispatch(tool_name: str, args: dict | None = None):
        args = args or {}
        tool_calls.append({"tool": tool_name, "args": dict(args)})

        # Simulate failures for specific refs
        if fail_refs and args.get("ref") in fail_refs:
            raise RuntimeError(f"Element ref={args['ref']} not interactable")

        # Return type-appropriate responses
        if "snapshot" in tool_name:
            return REALISTIC_SNAPSHOT
        if "screenshot" in tool_name:
            return "[base64-encoded-screenshot-data]"
        if "navigate" in tool_name:
            return "Navigated to page"
        if "wait_for" in tool_name:
            return "Condition met"
        if "type" in tool_name:
            return "Typed text into field"
        if "click" in tool_name:
            return "Clicked element"
        if "select_option" in tool_name:
            return "Selected option"
        if "press_key" in tool_name:
            return "Key pressed"
        return "OK"

    return dispatch


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tool_calls() -> list[dict]:
    """Shared mutable list that collects every proxied tool call."""
    return []


@pytest.fixture
def mock_context(tool_calls):
    """Create a mock Context whose fastmcp.call_tool dispatches realistically.

    The fixture exposes ``ctx._tool_calls`` so tests can inspect the sequence
    of Playwright tool invocations made by the web_* tools.
    """
    ctx = MagicMock()
    ctx.report_progress = AsyncMock()
    ctx.fastmcp = MagicMock()
    ctx.fastmcp.call_tool = AsyncMock(side_effect=_make_dispatch(tool_calls))
    ctx._tool_calls = tool_calls
    return ctx


@pytest.fixture
def mock_context_with_failures(tool_calls):
    """Context where specific field refs will fail during form filling.

    Returns a factory so tests can specify which refs should fail.
    """

    def _factory(fail_refs: set[str]):
        ctx = MagicMock()
        ctx.report_progress = AsyncMock()
        ctx.fastmcp = MagicMock()
        ctx.fastmcp.call_tool = AsyncMock(
            side_effect=_make_dispatch(tool_calls, fail_refs=fail_refs)
        )
        ctx._tool_calls = tool_calls
        return ctx

    return _factory


def _extract_tools(*register_fns):
    """Call one or more register_*_tools functions and collect the tool closures."""
    tools: dict[str, callable] = {}
    mock_mcp = MagicMock()

    def tool_decorator(fn):
        tools[fn.__name__] = fn
        return fn

    mock_mcp.tool = tool_decorator
    for register_fn in register_fns:
        register_fn(mock_mcp)
    return tools


@pytest.fixture
def auth_tools():
    return _extract_tools(register_auth_tools)


@pytest.fixture
def navigation_tools():
    return _extract_tools(register_navigation_tools)


@pytest.fixture
def extraction_tools():
    return _extract_tools(register_extraction_tools)


@pytest.fixture
def form_tools():
    return _extract_tools(register_form_tools)


@pytest.fixture
def all_tools():
    """Every web_* tool in a single dict -- useful for cross-tool tests."""
    return _extract_tools(
        register_auth_tools,
        register_navigation_tools,
        register_extraction_tools,
        register_form_tools,
    )
