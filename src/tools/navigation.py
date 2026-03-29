"""Web navigation tools."""

import random

from fastmcp import Context, FastMCP


def register_navigation_tools(mcp: FastMCP) -> None:
    """Register web navigation tools on the MCP server."""

    @mcp.tool
    async def web_navigate_and_wait(
        url: str,
        ctx: Context,
        wait_for_text: str | None = None,
        timeout_seconds: int = 10,
    ) -> dict:
        """Navigate to a URL and wait for the page to be ready.

        Combines navigation with SPA-aware content waiting.

        Args:
            url: The URL to navigate to
            wait_for_text: Optional text to wait for on the page
            timeout_seconds: Maximum wait time in seconds
        """
        await ctx.report_progress(
            progress=0.2, total=1.0, message="Navigating to URL"
        )

        await ctx.fastmcp.call_tool("playwright_browser_navigate", {"url": url})

        loaded = False
        elapsed = 0

        if wait_for_text:
            try:
                await ctx.fastmcp.call_tool(
                    "playwright_browser_wait_for", {"text": wait_for_text}
                )
                loaded = True
                elapsed = 1
            except Exception:
                loaded = False
                elapsed = timeout_seconds
        else:
            # Human-like delay: 0.5-2s random pause after navigation
            wait_time = round(random.uniform(0.5, 2.0), 1)
            await ctx.fastmcp.call_tool(
                "playwright_browser_wait_for", {"time": wait_time}
            )
            loaded = True
            elapsed = wait_time

        await ctx.report_progress(
            progress=0.9, total=1.0, message="Page loaded"
        )

        snapshot = await ctx.fastmcp.call_tool("playwright_browser_snapshot", {})

        return {
            "url": url,
            "loaded": loaded,
            "wait_seconds": elapsed,
            "snapshot": snapshot,
        }

    @mcp.tool
    async def web_wait_for_ready(
        ctx: Context,
        timeout_seconds: int = 10,
        indicator_text: str | None = None,
    ) -> dict:
        """Wait for the current page to finish loading.

        Useful after navigation, form submission, or any action that
        triggers a page update.

        Args:
            timeout_seconds: Maximum wait time in seconds
            indicator_text: Optional specific text to wait for
        """
        snapshot = None

        if indicator_text:
            await ctx.fastmcp.call_tool(
                "playwright_browser_wait_for", {"text": indicator_text}
            )
            snapshot = await ctx.fastmcp.call_tool(
                "playwright_browser_snapshot", {}
            )
            return {
                "loaded": True,
                "wait_seconds": 1,
                "snapshot": snapshot,
            }

        # Human-like delay: 0.5-2s random pause
        wait_time = round(random.uniform(0.5, 2.0), 1)
        await ctx.fastmcp.call_tool(
            "playwright_browser_wait_for", {"time": wait_time}
        )
        snapshot = await ctx.fastmcp.call_tool(
            "playwright_browser_snapshot", {}
        )
        return {
            "loaded": True,
            "wait_seconds": wait_time,
            "snapshot": snapshot,
        }

    @mcp.tool
    async def web_discover_navigation(
        ctx: Context,
    ) -> dict:
        """Discover navigation structure on the current page.

        Extracts navigation elements via DOM queries and returns structured
        data for navigation links, breadcrumbs, and pagination. Also includes
        the page snapshot for ref IDs.
        """
        snapshot = await ctx.fastmcp.call_tool("playwright_browser_snapshot", {})

        # DOM extraction of navigation elements
        nav_extract_js = """() => {
    const nav = [];
    document.querySelectorAll(
        'nav a, [role="navigation"] a, header a, .navbar a, .nav a, .menu a'
    ).forEach(a => {
        nav.push({
            text: a.textContent.trim(),
            href: a.href,
            section: a.closest(
                'nav, [role="navigation"], header'
            )?.getAttribute('aria-label') || 'main'
        });
    });
    const breadcrumbs = [];
    document.querySelectorAll(
        '[aria-label="breadcrumb"] a, .breadcrumb a, nav.breadcrumbs a'
    ).forEach(a => {
        breadcrumbs.push({ text: a.textContent.trim(), href: a.href });
    });
    const pagination = [];
    document.querySelectorAll(
        '[aria-label="pagination"] a, .pagination a, nav.pager a'
    ).forEach(a => {
        pagination.push({ text: a.textContent.trim(), href: a.href });
    });
    return { navigation: nav, breadcrumbs, pagination };
}"""

        extracted: dict = {"navigation": [], "breadcrumbs": [], "pagination": []}
        try:
            raw = await ctx.fastmcp.call_tool(
                "playwright_browser_evaluate",
                {"function": nav_extract_js},
            )
            if isinstance(raw, dict):
                extracted = raw
        except Exception:
            pass  # Fall back to snapshot + instruction

        return {
            "navigation": extracted.get("navigation", []),
            "breadcrumbs": extracted.get("breadcrumbs", []),
            "pagination": extracted.get("pagination", []),
            "snapshot": snapshot,
            "instruction": (
                "Identify all navigation elements on this page: "
                "main menus, navigation bars, sidebars, breadcrumbs, "
                "tab bars, pagination controls, and important links. "
                "For each element, provide its text label and ref ID "
                "from the snapshot."
            ),
        }
