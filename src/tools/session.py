"""Web session persistence tools."""

import json

from fastmcp import Context, FastMCP

# Session store persists across MCP calls within the same server process.
# Sessions are lost on server restart (Railway redeploy).
# For persistent sessions across restarts, use web_save_session with
# a known session_name, then web_load_session at the start of each research session.
_session_store: dict[str, dict] = {}

SAVE_SESSION_JS = """
() => ({
    url: window.location.href,
    origin: window.location.origin,
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
    })(),
    userAgent: navigator.userAgent,
    timestamp: new Date().toISOString()
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
                "playwright_browser_evaluate", {"function": SAVE_SESSION_JS}
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
                    "playwright_browser_evaluate", {"function": cookie_js}
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
                    "playwright_browser_evaluate", {"function": ls_js}
                )
            except Exception:
                pass

        await ctx.report_progress(
            progress=0.7, total=1.0, message="Restoring sessionStorage"
        )

        # Inject sessionStorage
        session_storage = (
            session_data.get("sessionStorage", {})
            if isinstance(session_data, dict)
            else {}
        )
        if session_storage and isinstance(session_storage, dict):
            ss_data = json.dumps(session_storage)
            ss_js = (
                f"() => {{ const items = {ss_data};"
                " for (const [k, v] of Object.entries(items))"
                " { sessionStorage.setItem(k, v); } }"
            )
            try:
                await ctx.fastmcp.call_tool(
                    "playwright_browser_evaluate", {"function": ss_js}
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

    @mcp.tool
    async def web_list_sessions(ctx: Context) -> dict:
        """List all saved browser sessions.

        Returns the names and metadata of all sessions saved in this server process.
        Useful for checking what sessions are available before loading one.
        """
        sessions = {}
        for name, data in _session_store.items():
            sessions[name] = {
                "url": data.get("url", "unknown") if isinstance(data, dict) else "unknown",
                "timestamp": (
                    data.get("timestamp", "unknown") if isinstance(data, dict) else "unknown"
                ),
            }
        return {"sessions": sessions, "count": len(sessions)}
