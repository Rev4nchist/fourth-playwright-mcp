"""Playwright Web MCP Server.

General-purpose web automation MCP server with @playwright/mcp subprocess integration.
Designed for Railway deployment as a Claude.ai Custom Connector.
"""

import os

from fastmcp import Context, FastMCP

from src.auth import create_oauth_proxy
from src.providers.playwright_subprocess import mount_playwright
from src.providers.skills import mount_skills
from src.tools.auth import register_auth_tools
from src.tools.content import register_content_tools
from src.tools.extraction import register_extraction_tools
from src.tools.forms import register_form_tools
from src.tools.navigation import register_navigation_tools
from src.tools.scripting import register_scripting_tools
from src.tools.search import register_search_tools
from src.tools.session import register_session_tools

SERVER_INSTRUCTIONS = """
## Browser Automation Guidelines

1. **Snapshot before acting.** Always call playwright_browser_snapshot before clicking or typing.
   Never act on stale element references.

2. **playwright_browser_wait_for time is in SECONDS, not milliseconds.**
   Pass 2 for a 2-second wait, not 2000. The time parameter must be a number.

3. **Use web_navigate_and_wait for navigation.** It combines navigation with SPA-aware waiting
   in a single call. Pass wait_for_text for content-based waiting.

4. **Use web_discover_form before web_fill_form.** Discover identifies field refs and types,
   then fill uses those refs for efficient batch input.

5. **Use playwright_browser_snapshot (accessibility tree) for element targeting.**
   Only use playwright_browser_take_screenshot for human-readable output or visual data.

6. **After actions, wait for the page to stabilise before snapshotting.**
   Use playwright_browser_wait_for with { "text": "expected-element" } or
   web_wait_for_ready for SPA content loading.

7. **Tab management:** playwright_browser_tabs with action "close" without an index
   closes the current tab and auto-switches to the previous one.

8. **Use web_search for research tasks.** It navigates to Google or DuckDuckGo with
   optional site and date filters. Use web_search_and_extract for multi-page research.

9. **Use web_extract_article for news and article pages.** It extracts clean article
   text, title, author, and date via DOM parsing — faster and more reliable than
   snapshot-based extraction for article content.

10. **Use web_extract_structured_data for known page layouts.** Pass CSS selectors
    mapped to field names for direct DOM extraction without LLM parsing.

11. **Session persistence is best-effort.** web_save_session captures cookies and
    localStorage via JavaScript. httpOnly cookies cannot be captured this way.
    Use for sites where re-login is expensive.
""".strip()

# Create server with OAuth if configured
oauth = create_oauth_proxy()
mcp = FastMCP(
    "Playwright Web MCP",
    instructions=SERVER_INSTRUCTIONS,
    auth=oauth,
)

# --- Providers ---

# Mount @playwright/mcp subprocess (70+ browser automation tools)
mount_playwright(mcp)

# Mount skills directory provider
mount_skills(mcp)

# --- Web Automation Tools ---

register_auth_tools(mcp)
register_navigation_tools(mcp)
register_extraction_tools(mcp)
register_form_tools(mcp)
register_search_tools(mcp)
register_content_tools(mcp)
register_session_tools(mcp)
register_scripting_tools(mcp)


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

    return JSONResponse({"status": "healthy", "server": "playwright-web-mcp"})


# --- Entry Point ---

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    mcp.run(transport="http", host=host, port=port, stateless_http=True)
