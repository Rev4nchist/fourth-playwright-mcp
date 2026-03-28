# Project Roadmap

## Current Focus

_No current goal. Next planned item will be promoted on next planning session._

## Completed
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
### 2026-03-28: Fix + Enhance Playwright Web MCP
**Key Decisions:**
- Bug: Lines 27-36 construct a minimal `env` dict with only PATH, NODE_PATH, HOME, and a few Playwright vars. Setting `NODE_PATH=""` when it wasn't set breaks Node.js module resolution for `@playwright/mcp`. The `env_vars` parameter on `NpxStdioTransport` updates (not replaces) `os.environ`, but explicit empty strings override working defaults.
- Fix: Remove the entire `env` dict construction. Don't pass `env_vars` at all — let the subprocess inherit the full Railway environment. `PLAYWRIGHT_BROWSERS_PATH` is already set via `ENV` in the Dockerfile.
- Change `"@playwright/mcp": "^0.0.28"` to `"@playwright/mcp": "^0.0.68"`
- Remove `postinstall` script (causes double Chromium install; Dockerfile handles it)
- Update Node.js from `setup_20.x` to `setup_22.x` (Node 20 EOL April 2026)

**Files:** playwright_subprocess.py, src/providers/playwright_subprocess.py, package.json, pyproject.toml, src/tools/navigation.py, src/tools/forms.py, src/tools/search.py, src/tools/content.py

**Verification:** All existing tests pass + new tests for all new tools

### 2026-03-27: Rebuild fourth-playwright-mcp as General-Purpose Web Automation Connector
**Key Decisions:**
- Delete: `skills/fourth-workflows/` directory entirely (Fourth login/module/extraction recipes)
- Update imports to add `from src.tools.forms import register_form_tools`
- Update `SERVER_INSTRUCTIONS` to remove Fourth references, add guidance for new `web_*` tools
- Add `register_form_tools(mcp)` call
- Change `"--- Custom Fourth Tools ---"` comment to `"--- Web Automation Tools ---"`
