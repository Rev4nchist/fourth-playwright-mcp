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


class TestNewToolModuleWiring:
    """Verify new tool modules (search, content, session, scripting) are wired in."""

    def test_search_import_in_server(self):
        source = _read_server()
        assert "from src.tools.search import register_search_tools" in source

    def test_content_import_in_server(self):
        source = _read_server()
        assert "from src.tools.content import register_content_tools" in source

    def test_session_import_in_server(self):
        source = _read_server()
        assert "from src.tools.session import register_session_tools" in source

    def test_scripting_import_in_server(self):
        source = _read_server()
        assert "from src.tools.scripting import register_scripting_tools" in source

    def test_search_registration_in_server(self):
        source = _read_server()
        assert "register_search_tools(mcp)" in source

    def test_content_registration_in_server(self):
        source = _read_server()
        assert "register_content_tools(mcp)" in source

    def test_session_registration_in_server(self):
        source = _read_server()
        assert "register_session_tools(mcp)" in source

    def test_scripting_registration_in_server(self):
        source = _read_server()
        assert "register_scripting_tools(mcp)" in source

    def test_search_module_importable(self):
        from src.tools.search import register_search_tools
        assert callable(register_search_tools)

    def test_content_module_importable(self):
        from src.tools.content import register_content_tools
        assert callable(register_content_tools)

    def test_session_module_importable(self):
        from src.tools.session import register_session_tools
        assert callable(register_session_tools)

    def test_scripting_module_importable(self):
        from src.tools.scripting import register_scripting_tools
        assert callable(register_scripting_tools)

    def test_server_instructions_mentions_web_search(self):
        source = _read_server()
        assert "web_search" in source

    def test_server_instructions_mentions_web_extract_article(self):
        source = _read_server()
        assert "web_extract_article" in source

    def test_server_instructions_mentions_web_extract_structured_data(self):
        source = _read_server()
        assert "web_extract_structured_data" in source

    def test_performance_import_in_server(self):
        source = _read_server()
        assert "from src.tools.performance import register_performance_tools" in source

    def test_performance_registration_in_server(self):
        source = _read_server()
        assert "register_performance_tools(mcp)" in source

    def test_performance_module_importable(self):
        from src.tools.performance import register_performance_tools

        assert callable(register_performance_tools)

    def test_server_instructions_mentions_web_save_session(self):
        source = _read_server()
        assert "web_save_session" in source
