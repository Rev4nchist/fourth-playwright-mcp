"""Fourth Playwright MCP Server.

FastMCP v3 orchestration layer with @playwright/mcp subprocess integration.
Designed for Railway deployment as a Claude.ai Custom Connector.
"""

import os

from fastmcp import FastMCP

from src.auth import create_oauth_proxy
from src.providers.playwright_subprocess import mount_playwright
from src.providers.skills import mount_skills
from src.tools.auth import register_auth_tools
from src.tools.extraction import register_extraction_tools
from src.tools.navigation import register_navigation_tools

# Create server with OAuth if configured
oauth = create_oauth_proxy()
mcp = FastMCP(
    "Fourth Playwright MCP",
    auth=oauth,
)

# --- Providers ---

# Mount @playwright/mcp subprocess (70+ browser automation tools)
mount_playwright(mcp)

# Mount skills directory provider
mount_skills(mcp)

# --- Custom Fourth Tools ---

register_auth_tools(mcp)
register_navigation_tools(mcp)
register_extraction_tools(mcp)


# --- Health Check ---

@mcp.custom_route("/health", methods=["GET"])
async def health(request):
    """Health check endpoint for Railway."""
    from starlette.responses import JSONResponse

    return JSONResponse({"status": "healthy", "server": "fourth-playwright-mcp"})


# --- Entry Point ---

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    mcp.run(transport="http", host=host, port=port, stateless_http=True)
