# Browser Automation

## Overview
This skill provides patterns for effective browser automation using the Playwright MCP tools.

## Key Patterns

### Navigation
1. Always use `playwright_browser_navigate` for initial page loads
2. After navigation, use `playwright_browser_snapshot` to get the page state
3. For SPAs, wait 1-2 seconds after navigation before reading the page

### Element Interaction
1. Use `playwright_browser_snapshot` to discover element references
2. Reference elements by their accessibility snapshot ref IDs
3. Prefer `playwright_browser_click` for buttons and links
4. Use `playwright_browser_type` for text inputs
5. Use `playwright_browser_select_option` for dropdowns

### Data Extraction
1. `playwright_browser_snapshot` returns the accessibility tree - best for text data
2. `playwright_browser_screenshot` returns a visual capture - best for charts/layouts
3. Combine both for comprehensive data extraction

### Error Recovery
- If an element is not found, re-take a snapshot (the page may have changed)
- If navigation fails, check the URL and try again
- Use `playwright_browser_console_messages` to check for JavaScript errors

### Performance
- Minimize screenshots (they are expensive) - prefer snapshots for text data
- Batch related actions together
- Use `playwright_browser_wait` when timing is critical

## Anti-Patterns
- Don't take screenshots when a snapshot would suffice
- Don't click elements without first taking a snapshot to find their refs
- Don't assume page state - always verify with a fresh snapshot after actions
