"""Web data extraction tools."""

from fastmcp import Context, FastMCP


def register_extraction_tools(mcp: FastMCP) -> None:
    """Register web data extraction tools on the MCP server."""

    @mcp.tool
    async def web_extract_table(
        ctx: Context,
        table_description: str = "main data table",
        format: str = "rows",
        use_dom: bool = False,
    ) -> dict:
        """Extract structured data from a table on the current page.

        Takes a snapshot of the current page and returns the table data
        with format-specific parsing instructions, or extracts directly
        from the DOM when use_dom is True.

        Args:
            table_description: Description of which table to extract
                             (e.g., 'employee schedule', 'inventory list')
            format: Output format - 'rows' (list of dicts), 'csv', or 'markdown'
            use_dom: When True, extract tables directly via JS DOM queries
                    instead of using the snapshot + instruction approach
        """
        if use_dom:
            await ctx.report_progress(
                progress=0.3, total=1.0, message="Extracting tables from DOM"
            )

            table_js = """() => {
    const tables = [...document.querySelectorAll('table')];
    return tables.map((t, i) => {
        const headers = [...t.querySelectorAll('th')].map(th => th.textContent.trim());
        const rows = [...t.querySelectorAll('tbody tr, tr')].slice(headers.length ? 0 : 1).map(tr =>
            [...tr.querySelectorAll('td')].map(td => td.textContent.trim())
        );
        return { index: i, headers, rows, row_count: rows.length };
    });
}"""
            tables = await ctx.fastmcp.call_tool(
                "playwright_browser_evaluate", {"expression": table_js}
            )

            return {
                "tables": tables,
                "count": len(tables),
            }

        await ctx.report_progress(
            progress=0.3, total=1.0, message="Capturing page snapshot"
        )

        snapshot = await ctx.fastmcp.call_tool("playwright_browser_snapshot", {})

        if format == "csv":
            instruction = (
                f"Parse the '{table_description}' from the snapshot as CSV. "
                "Return a header row followed by data rows, comma-separated."
            )
        elif format == "markdown":
            instruction = (
                f"Parse the '{table_description}' from the snapshot as a "
                "markdown table with aligned columns."
            )
        else:
            instruction = (
                f"Parse the '{table_description}' from the snapshot as "
                "structured data. Return a list of dictionaries where each "
                "dictionary represents a row with column headers as keys."
            )

        instruction += (
            " If pagination controls are visible, report them "
            "(current page, total pages, next/previous buttons)."
        )

        return {
            "table_description": table_description,
            "format": format,
            "snapshot": snapshot,
            "instruction": instruction,
        }

    @mcp.tool
    async def web_extract_page_data(
        ctx: Context,
        target: str = "all visible content",
        include_screenshot: bool = False,
        use_dom: bool = True,
    ) -> dict:
        """Extract data from the current page.

        By default, uses DOM evaluation to extract headings, text, and images
        directly. Set use_dom=False to use the legacy snapshot + instruction
        approach instead.

        Args:
            target: Description of what to extract (e.g., 'sidebar metrics',
                    'header summary', 'all visible content')
            include_screenshot: Whether to also capture a screenshot for visual data
            use_dom: When True (default), extract content directly via JS DOM
                    queries instead of using the snapshot + instruction approach
        """
        if use_dom:
            await ctx.report_progress(
                progress=0.2, total=1.0, message="Extracting page content from DOM"
            )

            page_extract_js = """() => {
    const main = document.querySelector(
        'main, [role="main"], article, .content, #content'
    ) || document.body;
    const clone = main.cloneNode(true);
    clone.querySelectorAll(
        'script, style, nav, footer, header, aside, .ad, .ads'
    ).forEach(el => el.remove());
    const headings = [...clone.querySelectorAll('h1, h2, h3, h4')].map(h => ({
        level: parseInt(h.tagName[1]),
        text: h.textContent.trim()
    }));
    const text = clone.textContent.replace(/\\s+/g, ' ').trim().substring(0, 15000);
    const images = [...document.querySelectorAll('img[src]')].slice(0, 10).map(
        img => ({ src: img.src, alt: img.alt || '' })
    );
    return {
        headings, text, images,
        url: window.location.href,
        title: document.title
    };
}"""

            try:
                extracted = await ctx.fastmcp.call_tool(
                    "playwright_browser_evaluate",
                    {"expression": page_extract_js},
                )

                result: dict = {
                    "target": target,
                    "content": extracted,
                    "snapshot": None,
                    "screenshot": None,
                }

                if include_screenshot:
                    await ctx.report_progress(
                        progress=0.6,
                        total=1.0,
                        message="Capturing screenshot",
                    )
                    result["snapshot"] = await ctx.fastmcp.call_tool(
                        "playwright_browser_snapshot", {}
                    )
                    result["screenshot"] = await ctx.fastmcp.call_tool(
                        "playwright_browser_take_screenshot", {}
                    )

                return result

            except Exception:
                pass  # Fall back to snapshot + instruction below

        # Legacy snapshot + instruction approach (use_dom=False or fallback)
        await ctx.report_progress(
            progress=0.2, total=1.0, message="Capturing page snapshot"
        )

        snapshot = await ctx.fastmcp.call_tool("playwright_browser_snapshot", {})

        results: dict = {
            "target": target,
            "snapshot": snapshot,
        }

        if include_screenshot:
            await ctx.report_progress(
                progress=0.6, total=1.0, message="Capturing screenshot"
            )
            results["screenshot"] = await ctx.fastmcp.call_tool(
                "playwright_browser_take_screenshot", {}
            )

        results["instruction"] = (
            f"Extract {target} from the page snapshot. "
            "Include headings, body text, metrics, and any structured data visible. "
            "If a screenshot is provided, also describe visual elements "
            "(charts, graphs, images, layout)."
        )

        return results

    @mcp.tool
    async def web_extract_links(
        ctx: Context,
        filter_text: str | None = None,
    ) -> dict:
        """Extract all links from the current page.

        Uses DOM evaluation to extract link data directly. Falls back to
        a snapshot + instruction approach if evaluation fails.

        Args:
            filter_text: Optional text to filter links by (matches text or URL,
                        case-insensitive)
        """
        links_js = (
            "() => [...document.querySelectorAll('a[href]')].map(a => ({"
            "    text: a.textContent.trim(),"
            "    href: a.href"
            "})).filter(l => l.text && l.href)"
        )

        try:
            links = await ctx.fastmcp.call_tool(
                "playwright_browser_evaluate", {"expression": links_js}
            )

            if filter_text:
                ft = filter_text.lower()
                links = [
                    link
                    for link in links
                    if ft in link.get("text", "").lower()
                    or ft in link.get("href", "").lower()
                ]

            return {
                "links": links,
                "count": len(links),
                "filter": filter_text,
            }

        except Exception:
            # Fallback to snapshot + instruction approach
            snapshot = await ctx.fastmcp.call_tool(
                "playwright_browser_snapshot", {}
            )

            instruction = (
                "Extract all links from the page snapshot as a list of objects "
                "with 'text' (link text) and 'href' (URL) properties."
            )

            if filter_text:
                instruction += (
                    f" Only include links where the text or URL contains "
                    f"'{filter_text}'."
                )

            return {
                "snapshot": snapshot,
                "filter": filter_text,
                "instruction": instruction,
            }
