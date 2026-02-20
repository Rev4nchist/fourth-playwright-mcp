"""Fourth data extraction tools."""

from fastmcp import Context, FastMCP


def register_extraction_tools(mcp: FastMCP) -> None:
    """Register Fourth data extraction tools on the MCP server."""

    @mcp.tool
    async def fourth_extract_table(
        ctx: Context,
        table_description: str = "main data table",
    ) -> dict:
        """Extract structured data from a Fourth data table.

        Takes a snapshot of the current page and returns the table data
        in a structured format for further processing.

        Args:
            table_description: Description of which table to extract
                             (e.g., 'employee schedule table', 'inventory list')
        """
        await ctx.report_progress(
            progress=0.3, total=1.0, message="Capturing page snapshot"
        )

        snapshot = await ctx.fastmcp.call_tool("playwright_browser_snapshot", {})

        return {
            "table_description": table_description,
            "snapshot": snapshot,
            "instruction": (
                f"Parse the snapshot to extract the '{table_description}' as structured data. "
                "Return rows as a list of dictionaries with column headers as keys. "
                "Include pagination info if present."
            ),
        }

    @mcp.tool
    async def fourth_extract_report(
        ctx: Context,
        report_name: str = "current report",
        include_screenshot: bool = False,
    ) -> dict:
        """Generate a structured report from the current Fourth page.

        Captures both the accessibility snapshot and optionally a screenshot
        for visual data extraction (charts, graphs).

        Args:
            report_name: Name/description of the report being extracted
            include_screenshot: Whether to also capture a screenshot for visual data
        """
        results: dict = {"report_name": report_name}

        await ctx.report_progress(
            progress=0.2, total=1.0, message="Capturing accessibility snapshot"
        )

        results["snapshot"] = await ctx.fastmcp.call_tool(
            "playwright_browser_snapshot", {}
        )

        if include_screenshot:
            await ctx.report_progress(
                progress=0.6, total=1.0, message="Capturing screenshot"
            )
            results["screenshot"] = await ctx.fastmcp.call_tool(
                "playwright_browser_screenshot", {}
            )

        results["instruction"] = (
            f"Extract all data from the '{report_name}' report. Include: "
            "1) Report title and date range, "
            "2) Summary metrics/KPIs, "
            "3) Table data as structured rows, "
            "4) Any chart/graph descriptions if screenshot provided."
        )

        return results
