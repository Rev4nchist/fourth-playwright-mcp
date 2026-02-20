# Fourth Playwright MCP Server

Remote MCP server combining FastMCP v3 (Python) orchestration with @playwright/mcp (Node.js) browser automation. Designed for deployment to Railway as a Claude.ai Custom Connector.

## Architecture

```
FastMCP v3 (Python) ─── SSE/Streamable HTTP ──→ Claude.ai
       │
       └── subprocess (stdio) ──→ @playwright/mcp (Node.js)
```

- **FastMCP v3**: OAuth 2.1 proxy, Skills system, custom tools, HTTP transport
- **@playwright/mcp**: 70+ browser automation tools via stdio subprocess
- **Custom tools**: Fourth-specific authentication, navigation, data extraction

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- [uv](https://docs.astral.sh/uv/) (Python package manager)

### Install

```bash
# Python dependencies
uv sync

# Node dependencies (installs @playwright/mcp + Chromium)
npm install
```

### Run locally

```bash
uv run python src/server.py
# Server starts on http://localhost:8000
# Health check: curl http://localhost:8000/health
# MCP endpoint: http://localhost:8000/mcp
```

### List tools

```bash
uv run fastmcp list src/server.py
```

## Deployment (Railway)

1. Connect this repo to Railway
2. Railway auto-detects the Dockerfile
3. Set environment variables (see `.env.example`)
4. Railway sets `PORT` automatically

### Claude.ai Custom Connector

1. Go to Claude.ai → Settings → Connectors → Add Custom
2. SSE URL: `https://<app>.railway.app/mcp`
3. Configure OAuth with your Client ID/Secret

## Custom Fourth Tools

| Tool | Description |
|------|-------------|
| `fourth_login` | Automated login with credentials/SSO |
| `fourth_navigate_module` | Navigate to Fourth module by name |
| `fourth_extract_table` | Extract structured data from tables |
| `fourth_extract_report` | Generate structured report from page |
| `fourth_wait_for_load` | Smart wait for Fourth SPA |
| `fourth_get_user_context` | Get current user/permissions/restaurant |

## Skills

Skills are exposed as MCP resources from the `skills/` directory:

- `browser-automation` - General browser automation patterns
- `fourth-workflows` - Fourth-specific workflow instructions

## Environment Variables

See `.env.example` for all configuration options.
