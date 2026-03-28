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

## Search
- **`web_search`** — Search Google or DuckDuckGo with optional site and date filters. Returns a snapshot with extraction instructions for result links.
- **`web_search_and_extract`** — Search + multi-page extraction workflow. Searches, then visits top result pages and extracts content.

## Content Extraction
- **`web_extract_article`** — Extract clean article text via DOM parsing. Returns structured data: title, author, date, and body text. Faster and more reliable than snapshot-based extraction for article content.
- **`web_extract_metadata`** — Extract page metadata: OpenGraph tags, JSON-LD structured data, and standard meta tags.
- **`web_save_pdf`** — Save the current page as a PDF file.

## Session Management
- **`web_save_session`** — Capture cookies and localStorage for later restoration. Note: httpOnly cookies cannot be captured via JavaScript — session persistence is best-effort.
- **`web_load_session`** — Restore a previously saved session (cookies + localStorage).

## Scripting
- **`web_execute_js`** — Run arbitrary JavaScript in the page context with error handling. Returns the result as JSON.
- **`web_extract_structured_data`** — CSS selector-based data extraction. Pass a map of field names to CSS selectors for direct DOM extraction without LLM parsing. Returns actual extracted data.

## Enhanced Tools
- **`web_extract_links`** — Now returns actual `{text, href}` objects via DOM extraction (not just LLM instructions). Use `filter_text` to narrow results.
- **`web_extract_table`** — New `use_dom=True` option for direct table extraction from the DOM, bypassing snapshot-based parsing.
- **`web_login`** — New `auto_fill=True` option for automatic credential filling when username and password are provided.

## Anti-Patterns
- Don't take screenshots when a snapshot would suffice
- Don't click elements without first snapshotting to find refs
- Don't assume page state — always verify with a fresh snapshot
- Don't navigate and immediately snapshot — use `web_navigate_and_wait` or `web_wait_for_ready`
