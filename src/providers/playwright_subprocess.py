"""Playwright MCP subprocess integration.

Proxies all 70+ @playwright/mcp tools through FastMCP v3 via stdio subprocess.
"""

import os
import shutil

from fastmcp import FastMCP
from fastmcp.client.transports import NpxStdioTransport
from fastmcp.server import create_proxy


def mount_playwright(mcp: FastMCP) -> None:
    """Mount @playwright/mcp as a proxied subprocess.

    Uses NpxStdioTransport to spawn @playwright/mcp via npx,
    then proxies all discovered tools through the FastMCP server.

    Tools are namespaced under "playwright_" prefix (e.g., playwright_browser_navigate).
    """
    # Determine npx path - prefer local node_modules
    local_npx = os.path.join(os.path.dirname(__file__), "..", "..", "node_modules", ".bin", "npx")
    npx_path = local_npx if os.path.exists(local_npx) else shutil.which("npx")

    # Build environment for the subprocess
    env = {
        "PATH": os.environ.get("PATH", ""),
        "NODE_PATH": os.environ.get("NODE_PATH", ""),
        "HOME": os.environ.get("HOME", os.environ.get("USERPROFILE", "")),
    }

    # Pass through Playwright-specific env vars
    for key in ("PLAYWRIGHT_BROWSERS_PATH", "DISPLAY", "PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH"):
        if key in os.environ:
            env[key] = os.environ[key]

    transport = NpxStdioTransport(
        package="@playwright/mcp",
        args=["--headless", "--isolated", "--no-sandbox"],
        env_vars=env,
    )

    proxy = create_proxy(transport)
    mcp.mount(proxy, namespace="playwright")
