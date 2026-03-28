"""Tests for server.py wiring and configuration changes.

Since server.py depends on fastmcp.server.create_proxy (available in deployed env
but not in local dev), we test the file content directly rather than importing it.
"""

from __future__ import annotations

import ast
from pathlib import Path

SERVER_PY = Path(__file__).resolve().parents[2] / "src" / "server.py"


def _read_server() -> str:
    return SERVER_PY.read_text(encoding="utf-8")


def _parse_server() -> ast.Module:
    return ast.parse(_read_server(), filename=str(SERVER_PY))


class TestServerConfiguration:
    """Verify server.py content after edits."""

    def test_module_docstring_updated(self):
        tree = _parse_server()
        docstring = ast.get_docstring(tree)
        assert "Playwright Web MCP Server" in docstring

    def test_server_name_in_source(self):
        source = _read_server()
        assert '"Playwright Web MCP"' in source

    def test_server_instructions_no_fourth_login_ref(self):
        source = _read_server()
        # Extract the SERVER_INSTRUCTIONS block
        start = source.index('SERVER_INSTRUCTIONS = """')
        end = source.index('""".strip()', start) + len('""".strip()')
        instructions_block = source[start:end]
        assert "fourth_login" not in instructions_block

    def test_server_instructions_mentions_discover_form(self):
        source = _read_server()
        assert "web_discover_form" in source

    def test_server_instructions_mentions_fill_form(self):
        source = _read_server()
        assert "web_fill_form" in source

    def test_server_instructions_mentions_navigate_and_wait(self):
        source = _read_server()
        assert "web_navigate_and_wait" in source

    def test_server_instructions_mentions_web_wait_for_ready(self):
        source = _read_server()
        assert "web_wait_for_ready" in source

    def test_health_check_server_name(self):
        source = _read_server()
        assert '"playwright-web-mcp"' in source

    def test_forms_import_exists(self):
        """Verify that the forms module can be imported standalone."""
        from src.tools.forms import register_form_tools

        assert callable(register_form_tools)

    def test_forms_import_in_server(self):
        """Verify server.py has the forms import line."""
        source = _read_server()
        assert "from src.tools.forms import register_form_tools" in source

    def test_forms_registration_in_server(self):
        """Verify server.py calls register_form_tools(mcp)."""
        source = _read_server()
        assert "register_form_tools(mcp)" in source

    def test_web_automation_tools_comment(self):
        """Verify the section comment was updated."""
        source = _read_server()
        assert "# --- Web Automation Tools ---" in source
        assert "# --- Custom Fourth Tools ---" not in source

    def test_description_comment_updated(self):
        """Verify the module description was updated."""
        tree = _parse_server()
        docstring = ast.get_docstring(tree)
        assert "General-purpose web automation" in docstring or "web automation" in docstring.lower()
