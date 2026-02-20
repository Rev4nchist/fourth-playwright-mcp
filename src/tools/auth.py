"""Fourth authentication tools."""

from fastmcp import Context, FastMCP


def register_auth_tools(mcp: FastMCP) -> None:
    """Register Fourth authentication tools on the MCP server."""

    @mcp.tool
    async def fourth_login(
        url: str,
        username: str,
        password: str,
        ctx: Context,
        sso_provider: str | None = None,
    ) -> dict:
        """Log into Fourth application.

        Automates the Fourth login flow including SSO handling.
        Uses the mounted Playwright tools to perform browser-based authentication.

        Args:
            url: Fourth application URL (e.g., https://app.fourth.com)
            username: Login username or email
            password: Login password
            sso_provider: Optional SSO provider name (e.g., 'azure', 'okta')
        """
        await ctx.report_progress(progress=0.1, total=1.0, message="Navigating to login page")

        # Navigate to the login URL
        await ctx.session.call_tool("playwright_browser_navigate", {"url": url})

        await ctx.report_progress(progress=0.3, total=1.0, message="Entering credentials")

        if sso_provider:
            # Click SSO button first
            await ctx.session.call_tool(
                "playwright_browser_click",
                {"element": f"SSO login button for {sso_provider}", "ref": "sso-button"},
            )

        # Fill username
        await ctx.session.call_tool(
            "playwright_browser_type",
            {"element": "username field", "ref": "username", "text": username},
        )

        # Fill password
        await ctx.session.call_tool(
            "playwright_browser_type",
            {"element": "password field", "ref": "password", "text": password},
        )

        await ctx.report_progress(progress=0.6, total=1.0, message="Submitting login")

        # Submit
        await ctx.session.call_tool(
            "playwright_browser_click",
            {"element": "login submit button", "ref": "submit"},
        )

        await ctx.report_progress(progress=0.9, total=1.0, message="Verifying login success")

        # Take snapshot to verify login succeeded
        result = await ctx.session.call_tool("playwright_browser_snapshot", {})

        return {
            "status": "logged_in",
            "url": url,
            "sso": sso_provider or "direct",
            "snapshot": result,
        }

    @mcp.tool
    async def fourth_get_user_context(ctx: Context) -> dict:
        """Get current Fourth user context.

        Returns the current user, their permissions, and active restaurant/location
        from the Fourth application UI.
        """
        snapshot = await ctx.session.call_tool("playwright_browser_snapshot", {})

        return {
            "snapshot": snapshot,
            "instruction": (
                "Parse the snapshot to extract: current user name, role, "
                "active restaurant/location, and any visible permissions or menu items."
            ),
        }
