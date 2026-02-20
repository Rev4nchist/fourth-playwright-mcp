"""Fourth Playwright MCP Server.

FastMCP v3 orchestration layer with @playwright/mcp subprocess integration.
Designed for Railway deployment as a Claude.ai Custom Connector.
"""

import os

from fastmcp import Context, FastMCP

from src.auth import create_oauth_proxy
from src.providers.playwright_subprocess import mount_playwright
from src.providers.skills import mount_skills
from src.tools.auth import register_auth_tools
from src.tools.extraction import register_extraction_tools
from src.tools.navigation import register_navigation_tools

SERVER_INSTRUCTIONS = """
## Browser Automation Guidelines

1. **Snapshot before acting.** Always call playwright_browser_snapshot before clicking or typing.
   Never act on stale element references.

2. **playwright_browser_wait_for time is in SECONDS, not milliseconds.**
   Pass 2 for a 2-second wait, not 2000. The time parameter must be a number.

3. **fourth_get_user_context requires an active browser session.**
   Call fourth_login first to authenticate before requesting user context.

4. **Use playwright_browser_snapshot (accessibility tree) for element targeting.**
   Only use playwright_browser_take_screenshot for human-readable output or documentation.

5. **After navigation, wait for the page to stabilise before snapshotting.**
   Use playwright_browser_wait_for with { "text": "expected-element" } rather than
   a fixed time wait where possible.

6. **Tab management:** playwright_browser_tabs with action "close" without an index
   closes the current tab and auto-switches to the previous one.
""".strip()

# Create server with OAuth if configured
oauth = create_oauth_proxy()
mcp = FastMCP(
    "Fourth Playwright MCP",
    instructions=SERVER_INSTRUCTIONS,
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


# --- Wrapper: browser_wait_for with type coercion ---

@mcp.tool
async def browser_wait_for(
    ctx: Context,
    time: float | None = None,
    text: str | None = None,
    textGone: str | None = None,
) -> str:
    """Wait for text to appear/disappear or a specified time to pass.

    Wrapper around playwright_browser_wait_for with proper type handling.

    Args:
        time: Time to wait in SECONDS (e.g., 2 for 2 seconds). Must be a number.
        text: Text to wait for on the page.
        textGone: Text to wait to disappear from the page.
    """
    args: dict = {}
    if time is not None:
        args["time"] = float(time)
    if text is not None:
        args["text"] = text
    if textGone is not None:
        args["textGone"] = textGone

    return await ctx.fastmcp.call_tool("playwright_browser_wait_for", args)


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
