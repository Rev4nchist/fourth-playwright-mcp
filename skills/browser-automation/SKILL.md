# Browser Automation

## Overview
This skill provides patterns for effective web automation using Playwright Web MCP. The server exposes ~70 low-level Playwright tools (prefixed `playwright_`) plus 10 higher-level orchestration tools (prefixed `web_`).

## Quick Start
1. Navigate: `web_navigate_and_wait` — goes to URL and waits for content
2. Discover: `playwright_browser_snapshot` — see what's on the page
3. Interact: `playwright_browser_click` / `playwright_browser_type` — click and type
4. Extract: `web_extract_table` / `web_extract_page_data` — get structured data

## Authentication
- Use `web_login` to navigate to a login page and discover form fields
- The tool returns a snapshot — identify username/password fields from the snapshot
- Use `playwright_browser_type` to fill each field, then submit
- Verify with `web_check_auth_state` after login

## Navigation
- **`web_navigate_and_wait`** — Primary navigation tool. Combines URL navigation with SPA-aware content waiting. Pass `wait_for_text` for content-based waiting.
- **`web_wait_for_ready`** — Wait for current page to finish loading after any action. Use `indicator_text` to wait for specific content.
- **`web_discover_navigation`** — Identify all navigation elements on a page (menus, sidebars, tabs, breadcrumbs, pagination).

## Data Extraction
- **`web_extract_table`** — Extract tabular data in rows/csv/markdown format. Reports pagination if present.
- **`web_extract_page_data`** — Extract targeted content from any page. Use `include_screenshot=True` for visual data (charts, graphs).
- **`web_extract_links`** — Extract all links as {text, href} objects. Use `filter_text` to narrow results.

## Form Filling
- **`web_discover_form`** — Identify all form fields with their labels, types, refs, and options
- **`web_fill_form`** — Batch-fill fields using ref+value+type from discovery. Handles text, select, checkbox, and radio inputs.
- Workflow: discover form → review fields → fill form → submit

## Element Interaction (Playwright Primitives)
- Use `playwright_browser_snapshot` to discover element ref IDs
- `playwright_browser_click` for buttons and links
- `playwright_browser_type` for text inputs
- `playwright_browser_select_option` for dropdowns
- `playwright_browser_press_key` for keyboard actions

## Error Recovery
- If an element is not found, re-snapshot (page may have changed)
- If navigation fails, check URL and retry
- Use `playwright_browser_console_messages` for JavaScript errors
- `web_fill_form` continues on individual field errors and reports them

## Performance Tips
- Prefer snapshots over screenshots (cheaper, more structured)
- Use `web_navigate_and_wait` instead of separate navigate + wait calls
- Use `web_fill_form` for batch input instead of individual type calls
- Batch related actions together

## Anti-Patterns
- Don't take screenshots when a snapshot would suffice
- Don't click elements without first snapshotting to find refs
- Don't assume page state — always verify with a fresh snapshot
- Don't navigate and immediately snapshot — use `web_navigate_and_wait` or `web_wait_for_ready`
