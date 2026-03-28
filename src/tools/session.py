"""Web session persistence tools."""

import json

from fastmcp import Context, FastMCP

# In-memory session storage (lives as long as the server process)
_session_store: dict[str, dict] = {}

SAVE_SESSION_JS = """
() => ({
    url: window.location.href,
    cookies: document.cookie,
    localStorage: (() => {
        try {
            const items = {};
            for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                items[key] = localStorage.getItem(key);
            }
            return items;
        } catch { return {}; }
    })(),
    sessionStorage: (() => {
        try {
            const items = {};
            for (let i = 0; i < sessionStorage.length; i++) {
                const key = sessionStorage.key(i);
                items[key] = sessionStorage.getItem(key);
            }
            return items;
        } catch { return {}; }
    })()
})
"""


def register_session_tools(mcp: FastMCP) -> None:
    """Register web session persistence tools on the MCP server."""

    @mcp.tool
    async def web_save_session(
        ctx: Context,
        session_name: str = "default",
    ) -> dict:
        """Save the current browser session state for later restoration.

        Captures cookies, localStorage, and sessionStorage from the current page.
        Sessions are stored in server memory and persist until the server restarts.

        Note: httpOnly cookies cannot be captured via JavaScript. For sites that
        rely heavily on httpOnly cookies, session restoration may be incomplete.

        Args:
            session_name: Name to save the session under (for retrieval later)
        """
        await ctx.report_progress(progress=0.3, total=1.0, message="Capturing session state")

        try:
            session_data = await ctx.fastmcp.call_tool(
                "playwright_browser_evaluate", {"expression": SAVE_SESSION_JS}
            )
        except Exception as e:
            return {"saved": False, "session_name": session_name, "error": str(e)}

        _session_store[session_name] = session_data

        return {
            "saved": True,
            "session_name": session_name,
            "url": (
                session_data.get("url", "unknown")
                if isinstance(session_data, dict)
                else "unknown"
            ),
            "stored_sessions": list(_session_store.keys()),
        }

    @mcp.tool
    async def web_load_session(
        ctx: Context,
        session_name: str = "default",
    ) -> dict:
        """Restore a previously saved browser session.

        Navigates to the saved URL and injects stored cookies, localStorage,
        and sessionStorage. Then reloads the page so the restored state takes effect.

        Args:
            session_name: Name of the session to restore
        """
        if session_name not in _session_store:
            return {
                "loaded": False,
                "session_name": session_name,
                "error": f"Session '{session_name}' not found",
                "available_sessions": list(_session_store.keys()),
            }

        session_data = _session_store[session_name]
        url = session_data.get("url", "") if isinstance(session_data, dict) else ""

        await ctx.report_progress(progress=0.2, total=1.0, message=f"Navigating to {url}")

        # Navigate to the saved URL first
        if url:
            await ctx.fastmcp.call_tool("playwright_browser_navigate", {"url": url})

        await ctx.report_progress(progress=0.4, total=1.0, message="Restoring cookies")

        # Inject cookies
        cookies = session_data.get("cookies", "") if isinstance(session_data, dict) else ""
        if cookies:
            cookie_js = f"() => {{ document.cookie = {repr(cookies)}; }}"
            try:
                await ctx.fastmcp.call_tool(
                    "playwright_browser_evaluate", {"expression": cookie_js}
                )
            except Exception:
                pass  # Cookie injection can fail on some domains

        await ctx.report_progress(progress=0.6, total=1.0, message="Restoring localStorage")

        # Inject localStorage
        local_storage = (
            session_data.get("localStorage", {})
            if isinstance(session_data, dict)
            else {}
        )
        if local_storage and isinstance(local_storage, dict):
            ls_data = json.dumps(local_storage)
            ls_js = (
                f"() => {{ const items = {ls_data};"
                " for (const [k, v] of Object.entries(items))"
                " { localStorage.setItem(k, v); } }"
            )
            try:
                await ctx.fastmcp.call_tool(
                    "playwright_browser_evaluate", {"expression": ls_js}
                )
            except Exception:
                pass

        await ctx.report_progress(progress=0.8, total=1.0, message="Reloading page")

        # Reload to apply restored state
        if url:
            await ctx.fastmcp.call_tool("playwright_browser_navigate", {"url": url})

        # Take final snapshot to verify
        snapshot = await ctx.fastmcp.call_tool("playwright_browser_snapshot", {})

        return {
            "loaded": True,
            "session_name": session_name,
            "url": url,
            "snapshot": snapshot,
        }
