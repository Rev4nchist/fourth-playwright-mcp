"""Playwright MCP subprocess integration.

Proxies all @playwright/mcp tools through FastMCP v3 via stdio subprocess.
Includes stealth patches, proxy support, and realistic browser fingerprinting.
"""

import json
import os

from fastmcp import FastMCP
from fastmcp.client.transports import NpxStdioTransport
from fastmcp.server import create_proxy


def mount_playwright(mcp: FastMCP) -> None:
    """Mount @playwright/mcp as a proxied subprocess.

    Uses NpxStdioTransport to spawn @playwright/mcp via npx,
    then proxies all discovered tools through the FastMCP server.

    Tools are namespaced under "playwright_" prefix (e.g., playwright_browser_navigate).

    Stealth features:
        - Anti-detection script injected via --init-script (src/stealth.js)
        - Realistic Chrome user-agent string
        - Standard viewport dimensions (1366x768)

    Proxy support (via environment variables):
        - PLAYWRIGHT_PROXY_SERVER: proxy URL (http or socks5)
        - PLAYWRIGHT_PROXY_USER: proxy username (optional)
        - PLAYWRIGHT_PROXY_PASS: proxy password (optional)
    """
    # Build args
    args = ["--headless", "--no-sandbox"]

    # Stealth: inject anti-detection script before page scripts
    stealth_path = os.path.join(os.path.dirname(__file__), "..", "stealth.js")
    stealth_path = os.path.normpath(stealth_path)
    if os.path.exists(stealth_path):
        args.extend(["--init-script", stealth_path])

    # Realistic user agent
    args.extend([
        "--user-agent",
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
    ])

    # Viewport for consistent rendering
    args.extend(["--viewport", "1366,768"])

    # Proxy support via environment variables
    proxy_server = os.environ.get("PLAYWRIGHT_PROXY_SERVER")
    if proxy_server:
        config: dict = {"browser": {"proxy": {"server": proxy_server}}}
        proxy_user = os.environ.get("PLAYWRIGHT_PROXY_USER")
        proxy_pass = os.environ.get("PLAYWRIGHT_PROXY_PASS")
        if proxy_user:
            config["browser"]["proxy"]["username"] = proxy_user
        if proxy_pass:
            config["browser"]["proxy"]["password"] = proxy_pass
        args.extend(["--config", json.dumps(config)])

    transport = NpxStdioTransport(
        package="@playwright/mcp",
        args=args,
    )

    proxy = create_proxy(transport)
    mcp.mount(proxy, namespace="playwright")
