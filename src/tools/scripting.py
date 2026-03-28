"""Web scripting and structured data extraction tools."""

import json

from fastmcp import Context, FastMCP


def register_scripting_tools(mcp: FastMCP) -> None:
    """Register web scripting tools on the MCP server."""

    @mcp.tool
    async def web_execute_js(
        script: str,
        ctx: Context,
    ) -> dict:
        """Execute JavaScript on the current page and return the result.

        A thin wrapper around playwright_browser_evaluate with structured
        error handling. The script should be a JavaScript expression or
        an IIFE (immediately-invoked function expression).

        Args:
            script: JavaScript code to execute (expression or IIFE)
        """
        try:
            result = await ctx.fastmcp.call_tool(
                "playwright_browser_evaluate", {"function": script}
            )
            return {"success": True, "result": result, "error": None}
        except Exception as e:
            return {"success": False, "result": None, "error": str(e)}

    @mcp.tool
    async def web_extract_structured_data(
        selectors: dict,
        ctx: Context,
    ) -> dict:
        """Extract structured data from the current page using CSS selectors.

        Accepts a mapping of field names to CSS selectors and returns the
        text content of each matched element. This extracts data server-side
        from the DOM — no LLM parsing required.

        Args:
            selectors: Mapping of field names to CSS selectors.
                Example: {"title": "h1", "price": ".price-tag",
                "description": ".product-desc"}
        """
        selectors_json = json.dumps(selectors)

        extract_js = f"""
() => {{
    const selectors = {selectors_json};
    const results = {{}};
    for (const [key, selector] of Object.entries(selectors)) {{
        const el = document.querySelector(selector);
        results[key] = el ? el.textContent.trim() : null;
    }}
    return results;
}}
"""

        try:
            result = await ctx.fastmcp.call_tool(
                "playwright_browser_evaluate", {"function": extract_js}
            )
            result_dict = result if isinstance(result, dict) else {}
            return {
                "success": True,
                "data": result,
                "selectors_used": selectors,
                "fields_found": sum(
                    1 for v in result_dict.values() if v is not None
                ),
                "fields_missing": [
                    k for k, v in result_dict.items() if v is None
                ],
            }
        except Exception as e:
            return {"success": False, "data": None, "error": str(e)}
