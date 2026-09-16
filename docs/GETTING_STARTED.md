# Getting Started

Run the Alaska Geoportal MCP server locally, connect a client, and (if you
operate the production stack) deploy a change. This repo is a single-plugin
deployment of the OpenContext framework; the framework docs
([Architecture](ARCHITECTURE.md), [Custom Plugins](CUSTOM_PLUGINS.md)) still
apply, but the examples here are this server's.

## Just want to use it?

You don't need to run anything. The production server is public and
read-only:

```
https://alaska-geoportal.codeforanchorage.org/mcp
```

In Claude: **Settings → Connectors → Add custom connector**, paste that URL.
The `/mcp` path is required. Then enable the connector in a chat and ask,
for example, "how many miles of forestry road are in the Mat-Su Borough" or
"which fire service area is Fairbanks in".

## Prerequisites (for running or deploying)

- Python 3.11+ and [uv](https://docs.astral.sh/uv/) (pip works too)
- For deployment only: Terraform >= 1.0, AWS CLI with access to account
  `420839047325`, and permission to run `./scripts/deploy.sh`

## Run it locally

```bash
git clone https://github.com/codeforanchorage/alaska-geoportal-mcp.git
cd alaska-geoportal-mcp
uv sync                                        # or: pip install -r requirements.txt -r requirements-dev.txt
cp config-alaska-geoportal.yaml config.yaml    # the deployable config; already verified
PYTHONIOENCODING=utf-8 python scripts/local_server.py
```

The server listens at `http://localhost:8000/mcp` and talks to the live
`soa-dnr` ArcGIS Online org (read-only). It enforces the same Origin
allowlist and protocol-version checks as production, so local behaviour is
representative.

### Check it

```bash
# 23 end-to-end checks against the live org
SMOKE_URL=http://localhost:8000/mcp python scripts/smoke_prod.py

# or a single call
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" -H "Accept: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"alaska_geoportal__find_gis_content","arguments":{"topic":"wildfire","limit":5}}}'
```

### Connect a client to the local server

- **Claude Desktop / Claude Code:** `stdio_bridge.py` bridges stdio to the
  local HTTP server, or build the Go client in `client/` (`make build`).
- **MCP Inspector:** `npx @modelcontextprotocol/inspector`, transport
  *streamable-http*, URL `http://localhost:8000/mcp`.
- **claude.ai (web)** cannot reach `localhost`; use the production URL.

See [Testing](TESTING.md) for more.

## Change the configuration

`config-alaska-geoportal.yaml` is the source of truth; `config.yaml` is the
copy that `scripts/local_server.py` reads and that `deploy.sh` bundles into
the Lambda package. Edit the former, then `cp` it over the latter. The
`instructions` block is what the model sees at `initialize`; the
`gallery_group_ids` list is which Geoportal groups are searched. Verified
org and group ids, and why only state-owned groups are listed, are in
[ALASKA_SOURCES.md](ALASKA_SOURCES.md).

Validate before deploying:

```bash
python -c "from core.validators import load_and_validate_config; load_and_validate_config('config.yaml')"
```

## Deploy a change

```bash
uv run ruff check core/ plugins/ server/ tests/
uv run pytest tests/ -n auto --cov=core --cov=plugins --cov-fail-under=80
./scripts/deploy.sh -e prod          # plans, shows a summary, waits for "yes"
SMOKE_URL=https://alaska-geoportal.codeforanchorage.org/mcp python scripts/smoke_prod.py
```

There is no staging environment in this fork; prod is the only stack. The
script packages the code and `config.yaml`, runs Terraform in workspace
`alaska-geoportal-prod`, and prints the API Gateway URL. Details, the
timeout ladder, and the custom-domain caveat are in
[Deployment](DEPLOYMENT.md); day-2 operations (kill switch, traffic
postures, alarms, logs) are in the [Runbook](RUNBOOK.md).

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Claude "can't connect" | The saved URL must end in `/mcp`. The bare hostname serves a landing page that says so. |
| `Multiple Plugins Enabled` at startup | Only `alaska_geoportal` may be `enabled: true` in `config.yaml`. |
| A layer is refused: "belongs to org … not the configured org" | It's a partner-org layer (borough, ADF&G, DOT&PF, federal). By design; see [SECURITY.md](SECURITY.md) and [ALASKA_SOURCES.md](ALASKA_SOURCES.md). |
| `Unable to complete operation` on a WHERE clause | Usually a numeric comparison on a String-typed field. The error now tells you which field and gives the guarded `CAST` form. |
| Lambda 5xx | `aws logs tail /aws/lambda/alaska-geoportal-mcp-prod --since 30m`; see the Runbook. |

## Next

- [Architecture](ARCHITECTURE.md) – framework design, plugin interface
- [Alaska sources](ALASKA_SOURCES.md) – the state org, its groups, other Alaska orgs
- [Security](SECURITY.md) – tenant scoping, host allowlist
- [Runbook](RUNBOOK.md) – operations
