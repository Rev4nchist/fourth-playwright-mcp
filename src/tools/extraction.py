"""Web data extraction tools."""

from fastmcp import Context, FastMCP


def register_extraction_tools(mcp: FastMCP) -> None:
    """Register web data extraction tools on the MCP server."""

    @mcp.tool
    async def web_extract_table(
        ctx: Context,
        table_description: str = "main data table",
        format: str = "rows",
    ) -> dict:
        """Extract structured data from a table on the current page.

        Takes a snapshot of the current page and returns the table data
        with format-specific parsing instructions.

        Args:
            table_description: Description of which table to extract
                             (e.g., 'employee schedule', 'inventory list')
            format: Output format - 'rows' (list of dicts), 'csv', or 'markdown'
        """
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
    ) -> dict:
        """Extract data from the current page.

        Captures the accessibility snapshot and optionally a screenshot
        for visual data extraction (charts, graphs, images).

        Args:
            target: Description of what to extract (e.g., 'sidebar metrics',
                    'header summary', 'all visible content')
            include_screenshot: Whether to also capture a screenshot for visual data
        """
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

        Returns the page snapshot with instructions to extract link data.

        Args:
            filter_text: Optional text to filter links by (matches text or URL)
        """
        snapshot = await ctx.fastmcp.call_tool("playwright_browser_snapshot", {})

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
