"""Web form automation tools."""

from fastmcp import Context, FastMCP


def register_form_tools(mcp: FastMCP) -> None:
    """Register web form automation tools on the MCP server."""

    @mcp.tool
    async def web_discover_form(
        ctx: Context,
        form_description: str = "main form on page",
    ) -> dict:
        """Discover form fields on the current page.

        Returns the page snapshot with instructions to identify all form inputs,
        their types, and ref IDs.

        Args:
            form_description: Description of the form to discover
                            (e.g., 'login form', 'search form', 'registration form')
        """
        await ctx.report_progress(
            progress=0.3, total=1.0, message="Capturing page snapshot"
        )

        snapshot = await ctx.fastmcp.call_tool("playwright_browser_snapshot", {})

        return {
            "form_description": form_description,
            "snapshot": snapshot,
            "instruction": (
                f"Identify all form fields for the '{form_description}' in the page snapshot. "
                "For each field provide: label (visible label text), type (text, email, password, "
                "number, select, checkbox, radio, textarea, date, or other), ref (the element's "
                "ref ID from the snapshot), current_value (if pre-filled), and options (list of "
                "choices for select/radio fields). List fields in their visual order on the page."
            ),
        }

    @mcp.tool
    async def web_fill_form(
        ctx: Context,
        fields: list[dict],
    ) -> dict:
        """Fill multiple form fields in batch.

        Use web_discover_form first to identify field refs and types,
        then pass them here for efficient batch filling.

        Args:
            fields: List of field dicts, each with:
                    - ref: Element ref ID from snapshot
                    - value: Text to fill or option to select
                    - type: Field type (text, email, password, select, checkbox, radio, textarea)

        Note:
            For checkbox and radio fields, the click toggles the current state. Use
            web_discover_form first to check current values, and only include checkboxes
            in the fields list if they need to be toggled.
        """
        await ctx.report_progress(
            progress=0.1, total=1.0, message="Filling form fields"
        )

        filled = 0
        errors: list[dict] = []

        for i, field in enumerate(fields):
            await ctx.report_progress(
                progress=0.1 + (0.7 * (i + 1) / max(len(fields), 1)),
                total=1.0,
                message=f"Filling field {i + 1} of {len(fields)}",
            )

            field_type = field.get("type", "text")

            try:
                if field_type == "select":
                    await ctx.fastmcp.call_tool(
                        "playwright_browser_select_option",
                        {
                            "element": "form field",
                            "ref": field["ref"],
                            "values": [field["value"]],
                        },
                    )
                elif field_type in ("checkbox", "radio"):
                    await ctx.fastmcp.call_tool(
                        "playwright_browser_click",
                        {
                            "element": "form field",
                            "ref": field["ref"],
                        },
                    )
                else:
                    # text, email, password, textarea, number, date, etc.
                    await ctx.fastmcp.call_tool(
                        "playwright_browser_type",
                        {
                            "element": "form field",
                            "ref": field["ref"],
                            "text": field["value"],
                        },
                    )
                filled += 1
            except Exception as e:
                errors.append({"ref": field["ref"], "error": str(e)})

        await ctx.report_progress(
            progress=0.9, total=1.0, message="Verifying form state"
        )

        snapshot = await ctx.fastmcp.call_tool("playwright_browser_snapshot", {})

        return {
            "filled_count": filled,
            "total_fields": len(fields),
            "errors": errors,
            "snapshot": snapshot,
        }
