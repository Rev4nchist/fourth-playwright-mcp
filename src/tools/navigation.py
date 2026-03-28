"""Web navigation tools."""

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
            await ctx.fastmcp.call_tool(
                "playwright_browser_wait_for", {"time": 2}
            )
            loaded = True
            elapsed = 2

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

        await ctx.fastmcp.call_tool(
            "playwright_browser_wait_for", {"time": 2}
        )
        snapshot = await ctx.fastmcp.call_tool(
            "playwright_browser_snapshot", {}
        )
        return {
            "loaded": True,
            "wait_seconds": 2,
            "snapshot": snapshot,
        }

    @mcp.tool
    async def web_discover_navigation(
        ctx: Context,
    ) -> dict:
        """Discover navigation structure on the current page.

        Returns the page snapshot with instructions to identify all
        navigable elements.
        """
        snapshot = await ctx.fastmcp.call_tool("playwright_browser_snapshot", {})

        return {
            "snapshot": snapshot,
            "instruction": (
                "Identify all navigation elements on this page: "
                "main menus, navigation bars, sidebars, breadcrumbs, "
                "tab bars, pagination controls, and important links. "
                "For each element, provide its text label and ref ID "
                "from the snapshot."
            ),
        }
