# Testing Guide

Three ways to exercise the server locally, plus the unit and smoke suites.

## Prerequisites

1. `cp config-alaska-geoportal.yaml config.yaml` (the verified deployable config)
2. `uv sync` (or `pip install -r requirements.txt -r requirements-dev.txt`)
3. `PYTHONIOENCODING=utf-8 python scripts/local_server.py`

The server runs at `http://localhost:8000/mcp` and queries the live
`soa-dnr` org read-only; nothing is mocked. Keep it running while you test.

## Fastest check: the smoke suite

```bash
SMOKE_URL=http://localhost:8000/mcp python scripts/smoke_prod.py   # 20 checks
python scripts/smoke_aggregate.py                                   # aggregation, direct plugin
```

---

## Method 1: Terminal (cURL)

Use the terminal to send requests directly to the server.

**Ping:**

```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"ping"}'
```

**List tools:**

```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'
```

**Call a tool:**

```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"alaska_geoportal__find_gis_content","arguments":{"topic":"wildfire","limit":3}}}'
```

For a full test (initialize, list tools, call tool), run:

```bash
./scripts/test_streamable_http.sh
```

---

## Method 2: Claude (Connectors)

1. Connect via Claude Connectors (see [Getting Started](GETTING_STARTED.md))
2. Add a custom connector with URL: `http://localhost:8000/mcp`
3. Enable the connector in your conversation (click "+" → Connectors → toggle on)
4. Ask Claude to search your data or list available tools

**Note:** Localhost only works with Claude Desktop. For Claude.ai (web), use MCP Inspector or deploy first.

---

## Method 3: MCP Inspector

MCP Inspector is a web-based tool for testing MCP servers.

1. With the server running, open a new terminal
2. Run: `npx @modelcontextprotocol/inspector`
3. The Inspector UI opens in your browser (typically `http://localhost:6274`)
4. In the Inspector, select **streamable-http** as the transport
5. Enter the URL: `http://localhost:8000/mcp`
6. Use the Tools tab to list and call tools

---

## Quick Checks

Optional checks before starting the server.

**Config validation:**

```bash
python3 -c "
import yaml
from core.validators import load_and_validate_config
config = load_and_validate_config('config.yaml')
print('Config valid:', config['server_name'])
"
```

**Plugin loading:**

```bash
python3 -c "
import asyncio, yaml
from core.plugin_manager import PluginManager
async def t():
    with open('config.yaml') as f: config = yaml.safe_load(f)
    pm = PluginManager(config)
    await pm.load_plugins()
    print('Tools:', [t['name'] for t in pm.get_all_tools()])
    await pm.shutdown()
asyncio.run(t())
"
```

---

## Unit Tests

```bash
uv run ruff check core/ plugins/ server/ tests/
uv run pytest tests/ -n auto --cov=core --cov=plugins --cov-fail-under=80
uv run pytest tests/test_alaska_geoportal_plugin.py -v
```

CI (`.github/workflows/ci.yml`) runs the same plus pip-audit and the Go
client's tests on every push and PR to `main`. Do not run `ruff format`
across the repo; `ruff check` is the bar.

---

## Testing Against Production

```bash
SMOKE_URL=https://alaska-geoportal.codeforanchorage.org/mcp python scripts/smoke_prod.py

curl -X POST https://alaska-geoportal.codeforanchorage.org/mcp \
  -H "Content-Type: application/json" -H "Accept: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"ping"}'
```

Production is rate-limited (5 rps, 300 per IP per 5 minutes); the smoke
script paces itself. See [Deployment](DEPLOYMENT.md) and the
[Runbook](RUNBOOK.md).
