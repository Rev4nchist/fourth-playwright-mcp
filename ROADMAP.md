# Project Roadmap

## Current Focus
**Rewrite EBR Project Instructions + Orchestrator Skill**
- User decisions: *; Old `ebr-data-prep` skill references and workflow diagram showing it as a pre-step
- Started: 2026-03-29

## Completed
- [x] [fix] rename evaluate param from 'expression' to 'function' for @playwright/mcp 0.0.68 (2026-03-28) `79db112`
- [x] [fix] parse accessibility tree for form fields when DOM extraction fails (2026-03-28) `8a46e34`
- [x] [fix] resolve 4 issues from Donna's retest (commit 4fc1e83) (2026-03-28) `a294ac7`
- [x] [fix] resolve 3 live test failures from Donna's validation (2026-03-28) `4fc1e83`
- [x] [feat] DOM extraction upgrades, perf/a11y tools, bug fixes (2026-03-28) `c77ceb0`
- [x] [fix] install chrome channel in Dockerfile (not just chromium) (2026-03-28) `8bc9c33`
- [x] [feat] fix subprocess proxy + add search, content, session, scripting tools (2026-03-28) `ff6a79e`
- [x] Fix + Enhance Playwright Web MCP (2026-03-28)
- [x] [test] add integration test suite for all web automation tools (2026-03-28) `cdaf492`
- [x] [refactor] rebuild as general-purpose web automation MCP server (2026-03-28) `3da172d`
- [x] Rebuild fourth-playwright-mcp as General-Purpose Web Automation Connector (2026-03-27)

## Planned
_No planned items yet._

## Recent Planning Sessions
### 2026-03-29: Rewrite EBR Project Instructions + Orchestrator Skill
**Key Decisions:**
- User decisions: *
- Old `ebr-data-prep` skill references and workflow diagram showing it as a pre-step
- Knowledge Base table: Remove data-prep row, add connector name (`fourth-playwright`)
- Connector awareness: Note that browser research uses `fourth-playwright` MCP connector with Bing as default search engine; Google/DDG unreliable from server environments
- "The Problem We Are Solving" section (still accurate)

**Verification:** Line count check — both should be under 500 lines

### 2026-03-28: Fix + Enhance Playwright Web MCP
**Key Decisions:**
- Bug: Lines 27-36 construct a minimal `env` dict with only PATH, NODE_PATH, HOME, and a few Playwright vars. Setting `NODE_PATH=""` when it wasn't set breaks Node.js module resolution for `@playwright/mcp`. The `env_vars` parameter on `NpxStdioTransport` updates (not replaces) `os.environ`, but explicit empty strings override working defaults.
- Fix: Remove the entire `env` dict construction. Don't pass `env_vars` at all — let the subprocess inherit the full Railway environment. `PLAYWRIGHT_BROWSERS_PATH` is already set via `ENV` in the Dockerfile.
- Change `"@playwright/mcp": "^0.0.28"` to `"@playwright/mcp": "^0.0.68"`
- Remove `postinstall` script (causes double Chromium install; Dockerfile handles it)
- Update Node.js from `setup_20.x` to `setup_22.x` (Node 20 EOL April 2026)

### 2026-03-27: Rebuild fourth-playwright-mcp as General-Purpose Web Automation Connector
**Key Decisions:**
- Delete: `skills/fourth-workflows/` directory entirely (Fourth login/module/extraction recipes)
- Update imports to add `from src.tools.forms import register_form_tools`
- Update `SERVER_INSTRUCTIONS` to remove Fourth references, add guidance for new `web_*` tools
- Add `register_form_tools(mcp)` call
- Change `"--- Custom Fourth Tools ---"` comment to `"--- Web Automation Tools ---"`
