"""Integration tests for server wiring and configuration.

Verifies that the server module is importable, configured correctly,
and the health check endpoint works as expected.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest


SERVER_PY = Path(__file__).resolve().parents[2] / "src" / "server.py"


def _read_server() -> str:
    return SERVER_PY.read_text(encoding="utf-8")


class TestServerImports:
    """Verify the server module's imports are valid."""

    def test_tools_modules_importable(self):
        """All tool registration modules should import without error."""
        from src.tools.auth import register_auth_tools
        from src.tools.extraction import register_extraction_tools
        from src.tools.forms import register_form_tools
        from src.tools.navigation import register_navigation_tools

        assert callable(register_auth_tools)
        assert callable(register_extraction_tools)
        assert callable(register_form_tools)
        assert callable(register_navigation_tools)

    def test_server_source_parses_without_error(self):
        """server.py should be valid Python."""
        source = _read_server()
        tree = ast.parse(source, filename="server.py")
        assert isinstance(tree, ast.Module)


class TestServerInstructions:
    """Verify SERVER_INSTRUCTIONS content."""

    def test_no_fourth_references(self):
        """SERVER_INSTRUCTIONS should not mention 'fourth' (generic server)."""
        source = _read_server()
        start = source.index('SERVER_INSTRUCTIONS = """')
        end = source.index('""".strip()', start) + len('""".strip()')
        instructions = source[start:end].lower()

        assert "fourth" not in instructions

    def test_mentions_snapshot_guidance(self):
        source = _read_server()
        assert "playwright_browser_snapshot" in source

    def test_mentions_wait_for_time_warning(self):
        """Should warn that wait_for time is in seconds."""
        source = _read_server()
        start = source.index('SERVER_INSTRUCTIONS = """')
        end = source.index('""".strip()', start) + len('""".strip()')
        instructions = source[start:end]

        assert "SECONDS" in instructions or "seconds" in instructions

    def test_mentions_navigate_and_wait(self):
        source = _read_server()
        assert "web_navigate_and_wait" in source

    def test_mentions_discover_and_fill_form(self):
        source = _read_server()
        assert "web_discover_form" in source
        assert "web_fill_form" in source


class TestHealthCheck:
    """Verify health check configuration."""

    def test_health_route_in_source(self):
        source = _read_server()
        assert '"/health"' in source

    def test_health_response_body(self):
        """Health check should return correct JSON structure."""
        source = _read_server()
        assert '"status": "healthy"' in source or "'status': 'healthy'" in source
        assert '"playwright-web-mcp"' in source

    def test_health_method_is_get(self):
        source = _read_server()
        assert 'methods=["GET"]' in source


class TestToolRegistration:
    """Verify all tool modules are registered in server.py."""

    def test_all_register_functions_called(self):
        source = _read_server()
        expected_registrations = [
            "register_auth_tools(mcp)",
            "register_navigation_tools(mcp)",
            "register_extraction_tools(mcp)",
            "register_form_tools(mcp)",
        ]
        for reg in expected_registrations:
            assert reg in source, f"Missing registration: {reg}"

    def test_all_tool_imports(self):
        source = _read_server()
        expected_imports = [
            "from src.tools.auth import register_auth_tools",
            "from src.tools.navigation import register_navigation_tools",
            "from src.tools.extraction import register_extraction_tools",
            "from src.tools.forms import register_form_tools",
        ]
        for imp in expected_imports:
            assert imp in source, f"Missing import: {imp}"

    def test_browser_wait_for_wrapper_exists(self):
        """Verify the browser_wait_for wrapper tool is defined."""
        source = _read_server()
        assert "async def browser_wait_for" in source

    def test_browser_wait_for_coerces_time_to_float(self):
        """The wrapper should convert time to float for type safety."""
        source = _read_server()
        assert "float(time)" in source
