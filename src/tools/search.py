"""Web search tools."""

import urllib.parse

from fastmcp import Context, FastMCP


def register_search_tools(mcp: FastMCP) -> None:
    """Register web search tools on the MCP server."""

    @mcp.tool
    async def web_search(
        query: str,
        ctx: Context,
        engine: str = "bing",
        num_results: int = 5,
        site_filter: str | None = None,
        date_filter: str | None = None,
    ) -> dict:
        """Search the web using DuckDuckGo, Bing, or Google.

        Navigates to a search engine, executes the query with optional filters,
        and returns the results page for extraction.

        Note: Google may be unreliable from server environments due to bot
        detection. DuckDuckGo (HTML-lite) or Bing are recommended for best
        reliability from datacenter IPs.

        Args:
            query: Search query string
            engine: Search engine ("duckduckgo", "bing", or "google")
            num_results: Number of results to extract (guidance for the LLM)
            site_filter: Optional site: filter (e.g., "nrn.com")
            date_filter: Optional time filter ("day", "week", "month", "year")
        """
        # Build search query with filters
        search_query = query
        if site_filter:
            search_query += f" site:{site_filter}"

        # Build URL based on engine
        if engine == "duckduckgo":
            date_map = {"day": "d", "week": "w", "month": "m", "year": "y"}
            params: dict[str, str] = {"q": search_query}
            if date_filter:
                params["df"] = date_map.get(date_filter, "")
            url = f"https://html.duckduckgo.com/html/?{urllib.parse.urlencode(params)}"
        elif engine == "bing":
            bing_date_map = {"day": "1", "week": "7", "month": "30", "year": "365"}
            params = {"q": search_query}
            if date_filter:
                days = bing_date_map.get(date_filter, "")
                params["filters"] = f'ex1:"ez{days}"'
            url = f"https://www.bing.com/search?{urllib.parse.urlencode(params)}"
        else:  # google
            date_map = {"day": "d", "week": "w", "month": "m", "year": "y"}
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

        # DOM extraction of search results (engine-aware)
        search_extract_js = """() => {
    const results = [];
    const url = window.location.href;

    if (url.includes('google.com')) {
        document.querySelectorAll('div.g').forEach((el, i) => {
            const titleEl = el.querySelector('h3');
            const linkEl = el.querySelector('a[href]');
            const snippetEl = el.querySelector('.VwiC3b, [data-sncf]');
            if (titleEl && linkEl) {
                results.push({
                    position: i + 1,
                    title: titleEl.textContent.trim(),
                    url: linkEl.href,
                    snippet: snippetEl ? snippetEl.textContent.trim() : ''
                });
            }
        });
    } else if (url.includes('duckduckgo.com')) {
        document.querySelectorAll('.result, .results_links, .result--default').forEach((el, i) => {
            const titleEl = el.querySelector('.result__title a, .result__a, a.result__url');
            const snippetEl = el.querySelector('.result__snippet');
            if (titleEl) {
                results.push({
                    position: i + 1,
                    title: titleEl.textContent.trim(),
                    url: titleEl.href || '',
                    snippet: snippetEl ? snippetEl.textContent.trim() : ''
                });
            }
        });
    } else if (url.includes('bing.com')) {
        document.querySelectorAll('#b_results .b_algo').forEach((el, i) => {
            const titleEl = el.querySelector('h2 a');
            const snippetEl = el.querySelector('.b_caption p, .b_lineclamp2');
            if (titleEl) {
                results.push({
                    position: i + 1,
                    title: titleEl.textContent.trim(),
                    url: titleEl.href,
                    snippet: snippetEl ? snippetEl.textContent.trim() : ''
                });
            }
        });
    }

    return results;
}"""

        extracted_results: list = []
        try:
            extracted_results = await ctx.fastmcp.call_tool(
                "playwright_browser_evaluate",
                {"expression": search_extract_js},
            )
        except Exception:
            pass  # Fall back to snapshot + instruction

        return {
            "query": query,
            "engine": engine,
            "url": url,
            "results": extracted_results[:num_results],
            "results_count": len(extracted_results[:num_results]),
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

        Combines web search (via DuckDuckGo HTML-lite by default) with guidance
        for navigating to and extracting content from the most relevant results.

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
