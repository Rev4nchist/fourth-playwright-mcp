# Playwright Web MCP

General-purpose web automation MCP server built on [FastMCP v3](https://github.com/jlowin/fastmcp) and [@playwright/mcp](https://github.com/anthropics/playwright-mcp).

Gives Claude browser automation capabilities over HTTP — navigate websites, fill forms, extract data, and interact with any web application.

## Architecture

```
Claude.ai / Cowork Plugin
    │  Streamable HTTP
    ▼
FastMCP v3 (Python)
    │
    ├── 70+ playwright_* tools (proxied via subprocess)
    ├── 19 web_* orchestration tools
    ├── 1 browser_wait_for wrapper
    └── Skills (MCP resources)
```

## Tools

### Web Automation (custom orchestration)

| Tool | Purpose |
|------|---------|
| `web_login` | Navigate to login page, discover form fields (auto_fill option) |
| `web_check_auth_state` | Check if user is authenticated |
| `web_navigate_and_wait` | Navigate + SPA-aware content waiting |
| `web_wait_for_ready` | Wait for page content after any action |
| `web_discover_navigation` | Identify menus, tabs, pagination |
| `web_extract_table` | Extract table data (rows/csv/markdown, DOM mode) |
| `web_extract_page_data` | Extract targeted page content |
| `web_extract_links` | Extract links via DOM (structured data) |
| `web_discover_form` | Identify form fields, types, refs |
| `web_fill_form` | Batch-fill form fields |
| `web_search` | Search Google/DuckDuckGo with filters |
| `web_search_and_extract` | Search + multi-page content extraction |
| `web_extract_article` | Clean article text via DOM parsing |
| `web_extract_metadata` | Page metadata (OG, JSON-LD, meta tags) |
| `web_save_pdf` | Save page as PDF |
| `web_save_session` | Save browser session state |
| `web_load_session` | Restore saved session |
| `web_execute_js` | Run JavaScript with error handling |
| `web_extract_structured_data` | CSS selector-based data extraction |

### Playwright Primitives (proxied)

All 70+ `@playwright/mcp` tools are available with a `playwright_` prefix:
`playwright_browser_navigate`, `playwright_browser_snapshot`, `playwright_browser_click`, `playwright_browser_type`, `playwright_browser_take_screenshot`, and more.

### Utility

| Tool | Purpose |
|------|---------|
| `browser_wait_for` | Type-safe wrapper for `playwright_browser_wait_for` |

## Deployment

### Railway (production)

The server deploys to Railway via Dockerfile. Set these environment variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PORT` | No | Set by Railway | HTTP port |
| `HOST` | No | `0.0.0.0` | Bind address |
| `OAUTH_CLIENT_ID` | No | — | OAuth client ID (omit to disable auth) |
| `OAUTH_CLIENT_SECRET` | No | — | OAuth client secret |
| `OAUTH_AUTHORIZATION_ENDPOINT` | No | Google OIDC | Authorization endpoint |
| `OAUTH_TOKEN_ENDPOINT` | No | Google OIDC | Token endpoint |
| `BASE_URL` | No | `http://127.0.0.1:8000` | Server public URL (for OAuth redirects) |

### Local development

```bash
# Install dependencies
uv sync

# Start server
uv run python src/server.py
# → http://localhost:8000/health
```

### Docker

```bash
docker build -t playwright-web-mcp .
docker run -p 8000:8000 playwright-web-mcp
```

## Usage

### Claude.ai Custom Connector

Add as a Custom Connector in Claude.ai Project settings:
- URL: `https://<your-app>.railway.app/mcp`
- Auth: OAuth 2.1 (if configured)

### Cowork Plugin

Reference the MCP endpoint in your plugin's `.mcp.json`:
```json
{
  "mcpServers": {
    "web": {
      "url": "https://<your-app>.railway.app/mcp"
    }
  }
}
```

## Development

```bash
# Run tests
uv run pytest

# Lint
uv run ruff check src/

# Type check
uv run ruff format --check src/
```

## License

Internal use — Fourth Enterprises.
