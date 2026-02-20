# Fourth Workflows

## Overview
Patterns and instructions for automating Fourth application workflows.

## Login Flow
1. Navigate to the Fourth login page
2. Use `fourth_login` with credentials and optional SSO provider
3. Use `fourth_wait_for_load` to confirm the dashboard loads
4. Use `fourth_get_user_context` to verify the correct user/restaurant

## Module Navigation
1. Use `fourth_navigate_module` with the module name (e.g., 'scheduling', 'inventory')
2. Use `fourth_wait_for_load` after navigation for SPA content
3. Common modules: dashboard, scheduling, labor, inventory, recipes, purchasing, reports

## Data Extraction
1. Navigate to the target page/report
2. Use `fourth_wait_for_load` to ensure content is ready
3. Use `fourth_extract_table` for tabular data
4. Use `fourth_extract_report` for full report extraction (includes screenshot option)

## Scheduling Workflow
1. `fourth_navigate_module("scheduling")`
2. `fourth_wait_for_load()`
3. Select date range using date pickers
4. `fourth_extract_table("weekly schedule")`

## Inventory Workflow
1. `fourth_navigate_module("inventory")`
2. `fourth_wait_for_load()`
3. Select location/category filters
4. `fourth_extract_table("inventory items")`

## Reporting Workflow
1. `fourth_navigate_module("reports")`
2. Select report type from the menu
3. Configure report parameters (date range, location, etc.)
4. `fourth_extract_report("report name", include_screenshot=True)`

## Tips
- Always verify login state before starting workflows
- Fourth SPAs may take 2-5 seconds to fully load - use `fourth_wait_for_load`
- For date pickers, use ISO format dates (YYYY-MM-DD)
- Check `fourth_navigate_module("list")` for all available modules
