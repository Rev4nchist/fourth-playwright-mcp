"""Playwright MCP subprocess integration.

Proxies all @playwright/mcp tools through FastMCP v3 via stdio subprocess.
"""

from fastmcp import FastMCP
from fastmcp.client.transports import NpxStdioTransport
from fastmcp.server import create_proxy


def mount_playwright(mcp: FastMCP) -> None:
    """Mount @playwright/mcp as a proxied subprocess.

    Uses NpxStdioTransport to spawn @playwright/mcp via npx,
    then proxies all discovered tools through the FastMCP server.

    Tools are namespaced under "playwright_" prefix (e.g., playwright_browser_navigate).
    """
    transport = NpxStdioTransport(
        package="@playwright/mcp",
        args=["--headless", "--no-sandbox"],
    )

    proxy = create_proxy(transport)
    mcp.mount(proxy, namespace="playwright")
