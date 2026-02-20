"""Fourth navigation tools."""

from fastmcp import Context, FastMCP

# Known Fourth module paths
FOURTH_MODULES: dict[str, str] = {
    "dashboard": "/dashboard",
    "scheduling": "/scheduling",
    "labor": "/labor",
    "inventory": "/inventory",
    "recipes": "/recipes",
    "purchasing": "/purchasing",
    "reports": "/reports",
    "admin": "/admin",
    "employees": "/employees",
    "timekeeping": "/timekeeping",
    "forecasting": "/forecasting",
    "menu": "/menu",
    "operations": "/operations",
}


def register_navigation_tools(mcp: FastMCP) -> None:
    """Register Fourth navigation tools on the MCP server."""

    @mcp.tool
    async def fourth_navigate_module(
        module: str,
        ctx: Context,
        base_url: str = "https://app.fourth.com",
    ) -> dict:
        """Navigate to a specific Fourth module by name.

        Args:
            module: Module name (e.g., 'scheduling', 'inventory', 'reports').
                    Use 'list' to see all available modules.
            base_url: Base URL of the Fourth application
        """
        if module == "list":
            return {"available_modules": list(FOURTH_MODULES.keys())}

        module_lower = module.lower()
        if module_lower not in FOURTH_MODULES:
            return {
                "error": f"Unknown module: {module}",
                "available_modules": list(FOURTH_MODULES.keys()),
            }

        path = FOURTH_MODULES[module_lower]
        url = f"{base_url}{path}"

        await ctx.report_progress(
            progress=0.3, total=1.0, message=f"Navigating to {module}"
        )

        await ctx.session.call_tool("playwright_browser_navigate", {"url": url})

        await ctx.report_progress(
            progress=0.8, total=1.0, message="Waiting for page load"
        )

        # Wait for SPA to load
        snapshot = await ctx.session.call_tool("playwright_browser_snapshot", {})

        return {
            "module": module_lower,
            "url": url,
            "snapshot": snapshot,
        }

    @mcp.tool
    async def fourth_wait_for_load(
        ctx: Context,
        timeout_seconds: int = 10,
    ) -> dict:
        """Wait for Fourth SPA to fully load.

        Polls the page snapshot until the main content area is detected
        or timeout is reached. Useful after navigation or login.

        Args:
            timeout_seconds: Maximum wait time in seconds
        """
        import asyncio

        for attempt in range(timeout_seconds):
            await ctx.report_progress(
                progress=attempt / timeout_seconds,
                total=1.0,
                message=f"Checking page load ({attempt + 1}s)",
            )

            snapshot = await ctx.session.call_tool("playwright_browser_snapshot", {})

            # If we got a non-empty snapshot, the page has content
            if snapshot and str(snapshot).strip():
                return {
                    "loaded": True,
                    "wait_seconds": attempt + 1,
                    "snapshot": snapshot,
                }

            await asyncio.sleep(1)

        return {
            "loaded": False,
            "wait_seconds": timeout_seconds,
            "message": "Page did not fully load within timeout",
        }
