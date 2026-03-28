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

        # DOM extraction of form fields with comprehensive label resolution.
        # Follows W3C Accessible Name priority order, plus form-builder
        # heuristics for HubSpot, Marketo, MUI, Bootstrap, Gravity Forms.
        form_extract_js = """() => {
    function getFieldLabel(el) {
        // 1. aria-labelledby
        const labelledBy = el.getAttribute('aria-labelledby');
        if (labelledBy) {
            const label = labelledBy.split(' ')
                .map(id => document.getElementById(id)?.textContent?.trim())
                .filter(Boolean).join(' ');
            if (label) return label;
        }
        // 2. aria-label
        const ariaLabel = el.getAttribute('aria-label');
        if (ariaLabel) return ariaLabel;
        // 3. Explicit <label for="id">
        if (el.labels && el.labels.length > 0) {
            return el.labels[0].textContent.trim();
        }
        // 4. Enclosing <label> (implicit association)
        const enclosingLabel = el.closest('label');
        if (enclosingLabel) {
            const clone = enclosingLabel.cloneNode(true);
            clone.querySelectorAll('input, select, textarea').forEach(c => c.remove());
            const text = clone.textContent.trim();
            if (text) return text;
        }
        // 5. Fieldset legend
        const fieldset = el.closest('fieldset');
        if (fieldset) {
            const legend = fieldset.querySelector('legend');
            if (legend) return legend.textContent.trim();
        }
        // 6. title attribute
        if (el.title) return el.title;
        // 7. placeholder
        if (el.placeholder) return el.placeholder;
        // 8. Form-builder heuristics (HubSpot, Marketo, MUI, Bootstrap, Gravity Forms, generic)
        const builderSelectors = [
            '.hs-form-field', '.gfield', '.mktoFieldWrap',
            '.MuiFormControl-root', '.form-group', '.form-field',
            '.field', '.input-group', '[class*="field"]', '[class*="form-row"]'
        ];
        for (const sel of builderSelectors) {
            const wrapper = el.closest(sel);
            if (wrapper) {
                const wrapperLabel = wrapper.querySelector(
                    'label, .hs-form-label, .gfield_label, .MuiFormLabel-root, .form-label, legend'
                );
                if (wrapperLabel) return wrapperLabel.textContent.trim();
                const heading = wrapper.querySelector('h1, h2, h3, h4, h5, h6, strong, b');
                if (heading) return heading.textContent.trim();
            }
        }
        // 9. Preceding sibling text
        const prevSibling = el.previousElementSibling;
        if (prevSibling && ['LABEL', 'SPAN', 'DIV', 'P'].includes(prevSibling.tagName)) {
            const text = prevSibling.textContent.trim();
            if (text && text.length < 100) return text;
        }
        // 10. Parent's direct text nodes (wrapper-div pattern)
        const parent = el.parentElement;
        if (parent) {
            const textNodes = [...parent.childNodes]
                .filter(n => n.nodeType === 3)
                .map(n => n.textContent.trim())
                .filter(Boolean);
            if (textNodes.length > 0 && textNodes[0].length < 100) return textNodes[0];
        }
        // 11. Last resort: name or id
        return el.name || el.id || '';
    }

    const fields = [];
    const inputs = document.querySelectorAll('input, select, textarea');
    inputs.forEach(el => {
        if (el.type === 'hidden') return;
        const style = window.getComputedStyle(el);
        if (style.display === 'none' || style.visibility === 'hidden') return;
        const field = {
            tag: el.tagName.toLowerCase(),
            type: el.type || el.tagName.toLowerCase(),
            name: el.name || null,
            id: el.id || null,
            label: getFieldLabel(el),
            value: el.value || '',
            required: el.required,
            disabled: el.disabled,
        };
        if (el.tagName === 'SELECT') {
            field.options = [...el.options].map(o => ({
                value: o.value,
                text: o.textContent.trim(),
                selected: o.selected
            }));
        }
        if (el.type === 'checkbox' || el.type === 'radio') {
            field.checked = el.checked;
        }
        fields.push(field);
    });
    return fields;
}"""

        extracted_fields: list = []
        try:
            extracted_fields = await ctx.fastmcp.call_tool(
                "playwright_browser_evaluate",
                {"expression": form_extract_js},
            )
        except Exception:
            pass  # Fall back to snapshot + instruction

        return {
            "form_description": form_description,
            "fields": extracted_fields,
            "fields_count": len(extracted_fields),
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
