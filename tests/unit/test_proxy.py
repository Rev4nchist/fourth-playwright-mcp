"""Tests for proxy support in playwright subprocess."""

from __future__ import annotations

from pathlib import Path


SUBPROCESS_PY = Path(__file__).resolve().parents[2] / "src" / "providers" / "playwright_subprocess.py"
ENV_EXAMPLE = Path(__file__).resolve().parents[2] / ".env.example"


class TestProxyEnvVarSupport:
    """Verify proxy env vars are referenced in the subprocess module."""

    def _read_source(self) -> str:
        return SUBPROCESS_PY.read_text(encoding="utf-8")

    def test_references_proxy_server_env(self):
        source = self._read_source()
        assert "PLAYWRIGHT_PROXY_SERVER" in source, \
            "Must read PLAYWRIGHT_PROXY_SERVER env var"

    def test_references_proxy_user_env(self):
        source = self._read_source()
        assert "PLAYWRIGHT_PROXY_USER" in source, \
            "Must read PLAYWRIGHT_PROXY_USER env var"

    def test_references_proxy_pass_env(self):
        source = self._read_source()
        assert "PLAYWRIGHT_PROXY_PASS" in source, \
            "Must read PLAYWRIGHT_PROXY_PASS env var"

    def test_imports_json_for_config(self):
        source = self._read_source()
        assert "import json" in source, \
            "Must import json for --config serialization"

    def test_uses_config_flag(self):
        source = self._read_source()
        assert "--config" in source, \
            "Must use --config flag to pass proxy configuration"


class TestEnvExample:
    """Verify .env.example contains proxy env vars."""

    def _read_env(self) -> str:
        return ENV_EXAMPLE.read_text(encoding="utf-8")

    def test_has_proxy_server(self):
        content = self._read_env()
        assert "PLAYWRIGHT_PROXY_SERVER" in content

    def test_has_proxy_user(self):
        content = self._read_env()
        assert "PLAYWRIGHT_PROXY_USER" in content

    def test_has_proxy_pass(self):
        content = self._read_env()
        assert "PLAYWRIGHT_PROXY_PASS" in content

    def test_has_proxy_comment(self):
        content = self._read_env()
        assert "Proxy" in content or "proxy" in content, \
            ".env.example should have a comment about proxy"
