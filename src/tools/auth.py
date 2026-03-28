"""Web authentication tools."""

from fastmcp import Context, FastMCP


def register_auth_tools(mcp: FastMCP) -> None:
    """Register web authentication tools on the MCP server."""

    @mcp.tool
    async def web_login(
        url: str,
        username: str,
        password: str,
        ctx: Context,
        submit_method: str = "click",
    ) -> dict:
        """Navigate to a login page and capture its form for credential entry.

        Navigates to the given URL and takes a snapshot of the page so that
        the caller can identify form fields and complete the login flow.
        This tool does NOT fill in fields itself -- it returns instructions
        for the caller to do so using the appropriate Playwright tools.

        Args:
            url: Login page URL (any site)
            username: Username or email to enter
            password: Password to enter
            submit_method: How to submit the form -- "click" or "enter"
        """
        await ctx.report_progress(
            progress=0.2, total=1.0, message="Navigating to login page"
        )

        await ctx.fastmcp.call_tool("playwright_browser_navigate", {"url": url})

        await ctx.report_progress(
            progress=0.6, total=1.0, message="Capturing login form"
        )

        snapshot = await ctx.fastmcp.call_tool("playwright_browser_snapshot", {})

        if submit_method == "click":
            submit_instruction = (
                "click the submit/login button using playwright_browser_click"
            )
        else:
            submit_instruction = (
                "press Enter using playwright_browser_press_key with key Enter"
            )

        instruction = (
            f"From the snapshot, identify the username/email field and password "
            f"field by their labels or placeholders. Use playwright_browser_type "
            f"to fill '{username}' into the username field and '{password}' into "
            f"the password field. Then {submit_instruction}. After submitting, "
            f"use playwright_browser_snapshot to verify login succeeded."
        )

        return {
            "url": url,
            "username": username,
            "submit_method": submit_method,
            "snapshot": snapshot,
            "instruction": instruction,
        }

    @mcp.tool
    async def web_check_auth_state(ctx: Context) -> dict:
        """Check the current authentication state of the active page.

        Takes a snapshot of the current page and returns it along with
        instructions for analyzing whether the user is logged in or out.
        """
        snapshot = await ctx.fastmcp.call_tool("playwright_browser_snapshot", {})

        return {
            "snapshot": snapshot,
            "instruction": (
                "Analyze the page snapshot to determine authentication state. "
                "Look for indicators of being logged in (profile menus, user "
                "name displays, logout/sign-out buttons, account links, "
                "dashboard content) or indicators of being logged out (login "
                "forms, sign-in buttons, registration prompts). Report whether "
                "the user appears to be authenticated and any visible user "
                "identity information."
            ),
        }
