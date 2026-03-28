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
        auto_fill: bool = False,
    ) -> dict:
        """Navigate to a login page and fill in credentials.

        When auto_fill is False (default), navigates to the URL, takes a
        snapshot, and returns instructions for the caller to complete the
        login. When auto_fill is True, attempts to find and fill common
        login field selectors directly via DOM evaluation.

        Args:
            url: Login page URL (any site)
            username: Username or email to enter
            password: Password to enter
            submit_method: How to submit the form -- "click" or "enter"
            auto_fill: When True, attempt to fill fields directly via JS
        """
        await ctx.report_progress(
            progress=0.2, total=1.0, message="Navigating to login page"
        )

        await ctx.fastmcp.call_tool("playwright_browser_navigate", {"url": url})

        await ctx.report_progress(
            progress=0.6, total=1.0, message="Capturing login form"
        )

        snapshot = await ctx.fastmcp.call_tool("playwright_browser_snapshot", {})

        if not auto_fill:
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

        # auto_fill=True: use DOM evaluation to fill fields directly
        await ctx.report_progress(
            progress=0.7, total=1.0, message="Auto-filling login fields"
        )

        fill_js = f"""() => {{
    const username = {repr(username)};
    const password = {repr(password)};
    const userFields = document.querySelectorAll(
        'input[type="email"], input[type="text"][name*="user"], '
        + 'input[type="text"][name*="email"], input[name="username"], '
        + 'input[id*="user"], input[id*="email"]'
    );
    const passFields = document.querySelectorAll('input[type="password"]');

    let filled = {{ username: false, password: false }};
    if (userFields.length > 0) {{
        userFields[0].value = username;
        userFields[0].dispatchEvent(new Event('input', {{ bubbles: true }}));
        filled.username = true;
    }}
    if (passFields.length > 0) {{
        passFields[0].value = password;
        passFields[0].dispatchEvent(new Event('input', {{ bubbles: true }}));
        filled.password = true;
    }}
    return filled;
}}"""

        filled = await ctx.fastmcp.call_tool(
            "playwright_browser_evaluate", {"function": fill_js}
        )

        # Submit the form
        await ctx.report_progress(
            progress=0.85, total=1.0, message="Submitting login form"
        )

        if submit_method == "click":
            await ctx.fastmcp.call_tool(
                "playwright_browser_click",
                {"element": "Submit button", "ref": "submit"},
            )
        else:
            await ctx.fastmcp.call_tool(
                "playwright_browser_press_key", {"key": "Enter"}
            )

        # Wait and take final snapshot
        await ctx.report_progress(
            progress=0.95, total=1.0, message="Verifying login result"
        )

        final_snapshot = await ctx.fastmcp.call_tool(
            "playwright_browser_snapshot", {}
        )

        return {
            "url": url,
            "username": username,
            "submit_method": submit_method,
            "auto_filled": True,
            "filled": filled,
            "snapshot": final_snapshot,
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
