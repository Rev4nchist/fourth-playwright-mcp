"""Tests for stealth anti-detection script and subprocess integration."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


STEALTH_JS = Path(__file__).resolve().parents[2] / "src" / "stealth.js"
SUBPROCESS_PY = Path(__file__).resolve().parents[2] / "src" / "providers" / "playwright_subprocess.py"


class TestStealthScriptExists:
    """Verify src/stealth.js exists and contains required patches."""

    def test_stealth_js_exists(self):
        assert STEALTH_JS.exists(), "src/stealth.js must exist"

    def test_stealth_js_not_empty(self):
        content = STEALTH_JS.read_text(encoding="utf-8")
        assert len(content) > 100, "stealth.js should have substantive content"

    def test_patches_navigator_webdriver(self):
        content = STEALTH_JS.read_text(encoding="utf-8")
        assert "webdriver" in content, "Must patch navigator.webdriver"

    def test_patches_chrome_runtime(self):
        content = STEALTH_JS.read_text(encoding="utf-8")
        assert "chrome" in content.lower(), "Must patch chrome runtime"

    def test_patches_plugins(self):
        content = STEALTH_JS.read_text(encoding="utf-8")
        assert "plugins" in content, "Must patch navigator.plugins"

    def test_patches_languages(self):
        content = STEALTH_JS.read_text(encoding="utf-8")
        assert "languages" in content, "Must patch navigator.languages"

    def test_patches_webgl(self):
        content = STEALTH_JS.read_text(encoding="utf-8")
        assert "WebGL" in content or "webgl" in content or "getParameter" in content, \
            "Must patch WebGL renderer"


class TestSubprocessStealthIntegration:
    """Verify playwright_subprocess.py passes stealth args."""

    def _read_source(self) -> str:
        return SUBPROCESS_PY.read_text(encoding="utf-8")

    def test_imports_os(self):
        source = self._read_source()
        assert "import os" in source, "Must import os for path resolution"

    def test_references_stealth_js(self):
        source = self._read_source()
        assert "stealth.js" in source, "Must reference stealth.js"

    def test_uses_init_script_flag(self):
        source = self._read_source()
        assert "--init-script" in source, "Must use --init-script flag for stealth injection"

    def test_uses_user_agent_flag(self):
        source = self._read_source()
        assert "--user-agent" in source, "Must set a realistic user-agent"

    def test_uses_viewport_flag(self):
        source = self._read_source()
        assert "--viewport" in source, "Must set viewport dimensions"

    def test_user_agent_is_chrome(self):
        source = self._read_source()
        assert "Chrome/" in source, "User agent should identify as Chrome"

    def test_still_has_headless_flag(self):
        source = self._read_source()
        assert "--headless" in source, "Must keep --headless flag"

    def test_still_has_no_sandbox_flag(self):
        source = self._read_source()
        assert "--no-sandbox" in source, "Must keep --no-sandbox flag"
