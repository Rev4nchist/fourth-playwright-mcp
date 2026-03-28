"""Web search tools."""

import urllib.parse

from fastmcp import Context, FastMCP


def register_search_tools(mcp: FastMCP) -> None:
    """Register web search tools on the MCP server."""

    @mcp.tool
    async def web_search(
        query: str,
        ctx: Context,
        engine: str = "google",
        num_results: int = 5,
        site_filter: str | None = None,
        date_filter: str | None = None,
    ) -> dict:
        """Search the web using Google or DuckDuckGo.

        Navigates to a search engine, executes the query with optional filters,
        and returns the results page for extraction.

        Args:
            query: Search query string
            engine: Search engine to use ("google" or "duckduckgo")
            num_results: Number of results to extract (guidance for the LLM)
            site_filter: Optional site: filter (e.g., "nrn.com")
            date_filter: Optional time filter ("day", "week", "month", "year")
        """
        # Build search query with filters
        search_query = query
        if site_filter:
            search_query += f" site:{site_filter}"

        date_map = {"day": "d", "week": "w", "month": "m", "year": "y"}

        # Build URL based on engine
        if engine == "duckduckgo":
            params: dict[str, str] = {"q": search_query}
            if date_filter:
                params["df"] = date_map.get(date_filter, "")
            url = f"https://duckduckgo.com/?{urllib.parse.urlencode(params)}"
        else:  # google
            params = {"q": search_query}
            if date_filter:
                params["tbs"] = f"qdr:{date_map.get(date_filter, '')}"
            url = f"https://www.google.com/search?{urllib.parse.urlencode(params)}"

        await ctx.report_progress(
            progress=0.2, total=1.0, message=f"Searching {engine}"
        )

        # Navigate to search engine
        await ctx.fastmcp.call_tool("playwright_browser_navigate", {"url": url})

        await ctx.report_progress(
            progress=0.5, total=1.0, message="Waiting for results"
        )

        # Wait for results to load
        try:
            await ctx.fastmcp.call_tool(
                "playwright_browser_wait_for", {"time": 3}
            )
        except Exception:
            pass  # Continue even if wait times out

        await ctx.report_progress(
            progress=0.8, total=1.0, message="Capturing results"
        )

        # Snapshot the results page
        snapshot = await ctx.fastmcp.call_tool(
            "playwright_browser_snapshot", {}
        )

        return {
            "query": query,
            "engine": engine,
            "url": url,
            "snapshot": snapshot,
            "instruction": (
                f"Extract the top {num_results} search results from the snapshot. "
                "For each result, provide: title, URL, and snippet/description text. "
                "Skip ads, 'People also ask', and other non-organic results."
            ),
        }

    @mcp.tool
    async def web_search_and_extract(
        query: str,
        ctx: Context,
        num_results: int = 3,
    ) -> dict:
        """Search the web and provide instructions to extract content from top results.

        Combines web search with guidance for navigating to and extracting
        content from the most relevant results.

        Args:
            query: Search query string
            num_results: Number of top results to plan extraction for
        """
        # Use web_search internally
        search_result = await web_search(
            query=query, ctx=ctx, num_results=num_results
        )

        search_result["instruction"] = (
            f"Extract the top {num_results} URLs from the search results. "
            "Then for each URL:\n"
            "1. Use web_navigate_and_wait to go to the page\n"
            "2. Use web_extract_article to get clean article text "
            "(or web_extract_page_data if not an article)\n"
            "3. Collect the key findings\n\n"
            "Return a summary of findings from all pages."
        )

        return search_result
