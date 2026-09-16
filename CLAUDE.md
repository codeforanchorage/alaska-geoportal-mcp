# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**What this repo is:** the Alaska Geoportal MCP server -- a statewide MCP over
the State of Alaska Geoportal (the Alaska Geospatial Office's ArcGIS Online
org `soa-dnr`, org id `7HDiw78fcUiM2BWn`). It is a standalone fork of
`codeforanchorage/anchorage-gis-mcp` (itself an OpenContext fork). The single
enabled plugin is `plugins/alaska_geoportal/`; there is no upstream to stay
compatible with, so edit it directly. Verified org/group ids and the other
Alaska orgs that could get the same treatment are in `docs/ALASKA_SOURCES.md`.

## Build & Development Commands

```bash
# Install dependencies (uv preferred, pip fallback)
uv sync                              # or: pip install -r requirements.txt

# Run local MCP server (no Lambda needed)
python3 scripts/local_server.py      # Serves on http://localhost:8000/mcp

# Validate config
python3 -c "from core.validators import load_and_validate_config; load_and_validate_config('config.yaml')"

# Tests
uv run pytest tests/ -n auto                                    # All tests, parallel
uv run pytest tests/test_alaska_geoportal_plugin.py -v          # Single file
uv run pytest tests/test_alaska_geoportal_plugin.py::TestClass::test_name -v  # Single test
uv run pytest tests/ --cov=core --cov=plugins --cov-report=term-missing  # With coverage (80% minimum)

# Linting (ruff)
uv run ruff check core/ plugins/ server/ tests/      # Check
uv run ruff check core/ plugins/ server/ tests/ --fix # Auto-fix
# Do NOT run `ruff format` across the repo. The source is hand-wrapped to
# ~79 cols and is not format-clean; a wholesale run produces a diff
# thousands of lines long that buries real changes. `ruff check` is the bar.

# Pre-commit hooks
pre-commit run --all-files

# Go client (requires Go 1.21+)
cd client && make build

# Deploy to AWS
./scripts/deploy.sh --environment staging
```

## Architecture

**Core rule: One Fork = One MCP Server.** Each deployment runs exactly ONE plugin. This is enforced at config validation time (`core/validators.py`) and at runtime (`PluginManager.load_plugins()`). To deploy multiple MCP servers, fork the repo per plugin.

**Request flow:**
```
Claude (stdio) → Go client (client/) or stdio_bridge.py → HTTP POST /mcp
  → Lambda (server/adapters/aws_lambda.py) or scripts/local_server.py
  → both call UniversalHTTPHandler (server/http_handler.py), so local
    dev enforces the same Origin allowlist and MCP-Protocol-Version
    checks as prod
  → server/http_handler.py → core/mcp_server.py (JSON-RPC 2.0)
  → core/plugin_manager.py → Plugin → External API
```

**Key modules:**
- `core/interfaces.py` — Abstract bases: `MCPPlugin`, `DataPlugin`, plus `ToolDefinition`, `ToolResult`, `PluginType` enum
- `core/plugin_manager.py` — Discovers plugins by scanning `plugins/` and `custom_plugins/` for `plugin.py` files. Registers tools with `pluginname__toolname` prefix. Routes `tools/call` to the correct plugin.
- `core/mcp_server.py` — Handles MCP JSON-RPC methods: `initialize`, `tools/list`, `tools/call`, `ping`
- `core/validators.py` — Loads and validates config; enforces the single-plugin rule. On Lambda the file comes from the deployment package, not the env var — see Configuration below.
- `server/adapters/aws_lambda.py` — AWS Lambda entry point (handler: `server.adapters.aws_lambda.lambda_handler`). The only one; a second, unreferenced `server/lambda_handler.py` was removed.
- `server/http_handler.py` — Cloud-agnostic HTTP handler shared by Lambda and local server
- `stdio_bridge.py` — Python stdio-to-HTTP bridge for connecting Claude Desktop/Code to the local server (alternative to Go client)

**Built-in plugins** (`plugins/`): `alaska_geoportal` (the one this fork deploys), plus the generic `ckan`, `arcgis`, `socrata` — each implements `DataPlugin` with `search_datasets`, `get_dataset`, `query_data`. Custom plugins go in `custom_plugins/` and are auto-discovered.

## The Alaska Geoportal plugin

`plugins/alaska_geoportal/plugin.py` exposes 14 read-only tools:
`find_gis_content`, `browse_gallery`, `search_spatial_layers`,
`get_item_details`, `get_layer_schema`, `get_distinct_values`,
`search_layers_by_field`, `query_data`, `spatial_query_point`,
`spatial_query_polygon`, `aggregate_by_polygon`, `coverage_by_polygon`,
`filter_by_polygon`, `find_features_spanning_classifications`. The two
MOA-only parcel tools from the Anchorage fork (`find_parcel`,
`footprint_for_parcel`) were removed along with their config keys.

Statewide specifics worth knowing before editing:

- **Tenant scoping is the security model.** The allowed set is the state
  org `7HDiw78fcUiM2BWn` plus every `partner_orgs` entry in the config (13
  Alaska boroughs and agencies as of 2026-09-16). `_assert_owned_by_configured_org`
  rejects items outside that set, and `_validate_service_url` only proxies
  `*.arcgis.com` URLs whose first path segment is an allowed org id, the
  portal host, on-prem `*.alaska.gov` hosts, or a partner's declared
  `hosts`. Federal-partner layers catalogued in the Geoportal are therefore
  discoverable but refused on query. Widen only by adding a `partner_orgs`
  entry, never by relaxing the checks; see `docs/SECURITY.md`.
- **Search results are labelled by agency** (`_org_label`): the item's
  `orgId`, else the org id in its service URL, else a partner host.
- **Two spatial references are common.** Hosted layers are Web Mercator OR
  Alaska Albers (EPSG:3338); the on-prem DNR/DGGS servers are all 3338.
  `_true_area_m2` corrects 3857 areas per feature by `cos^2(lat)` (2.5x at
  Ketchikan to 10x at Utqiagvik -- never a flat divisor) and passes 3338
  through as true square metres.
- **Coverage caveat is statewide and antimeridian-aware.** `ALASKA_BBOXES_WGS84`
  is two boxes (mainland + western Aleutians); `_alaska_coverage_pct` handles
  4326/4269, Web Mercator and 3338 extents (inline inverse Albers, no pyproj).
- **`gallery_group_ids` is a list**: the Hub catalog spans 45 groups, so
  `_search_gallery` ORs the configured ids in one portal query.
- Leave `core/`, the WHERE validator, limit clamps and item-id format checks
  alone unless the change is deliberate.

## Plugin Development

New plugins must implement `MCPPlugin` (or `DataPlugin` for data sources). Place in `custom_plugins/<name>/plugin.py`. The class must define `plugin_name`, `plugin_type`, `plugin_version` and implement `initialize()`, `shutdown()`, `get_tools()`, `execute_tool()`, `health_check()`. Tool names are auto-prefixed — return bare names from `get_tools()`.

## Configuration

Copy `config-example.yaml` to `config.yaml`. Enable exactly one plugin. Config supports `${ENV_VAR}` substitution.

`config.yaml` is a regular file here (the parent fork committed it as a symlink); `cp config-alaska-geoportal.yaml config.yaml` after editing the source copy.

**On Lambda, `config.yaml` ships INSIDE the deployment zip** — `scripts/deploy.sh` copies it into the package and `http_handler.py` reads it from `$LAMBDA_TASK_ROOT` at runtime. Terraform deliberately sets `OPENCONTEXT_CONFIG = ""`. The env var is still honoured when non-empty, but it must stay empty: AWS caps total Lambda env-var size at 4KB, and serialising the config there broke `terraform apply` once the `instructions` block grew past ~3KB. Do not move config back into it, and keep other env vars small.

Two AWS sizing values are read from `config.yaml` in preference to `terraform/aws/prod.tfvars` — `lambda_memory` and `lambda_timeout` (see the `locals` block in `terraform/aws/main.tf`). Editing them in the tfvars alone silently does nothing. `lambda_name` uses the opposite precedence, so check `main.tf` per variable rather than assuming.

**`terraform/aws/config.yaml` is a BUILD ARTIFACT, not a source file.** `scripts/deploy.sh` (line 307) copies the repo-root `config.yaml` over it during packaging, and it is gitignored. Two consequences: edits made directly to it vanish on the next deploy, and a bare `terraform plan` run inside `terraform/aws/` (without the packaging steps) reads the STALE copy — so a config change shows up as nothing but a code-hash diff, and a "timeout fix" can appear to apply while changing nothing. Always go through `./scripts/deploy.sh -e prod`, which repackages before planning.

**Timeout ladder** — each layer must sit under the one above it:

| Layer | Value | Why |
|---|---|---|
| API Gateway integration | 29s | hard REST limit, not adjustable |
| Lambda (`lambda_timeout`) | 28s | self-terminates before the gateway gives up |
| Plugin HTTP (`plugins.*.timeout`) | 20s | a hung upstream returns a readable tool error instead of the Lambda being killed mid-flight |

## Deploy status

Terraform and the deploy script are configured for `alaska-geoportal-prod` /
`alaska-geoportal-staging` (workspaces, Lambda names, tfstate bucket
`alaska-geoportal-opencontext-tfstate`, custom domain
`alaska-geoportal.codeforanchorage.org`). First prod apply ran 2026-09-15:
API Gateway `ae6gj7yvfg`, raw URL in `docs/RUNBOOK.md`. The tfstate bucket,
alarms SNS topic and mcp-stats `fleet_waf_members` entry all exist. The
custom domain binds on the next deploy after the ACM certificate is ISSUED
(DNS validation CNAME lives in Dreamhost).

## CI

`.github/workflows/ci.yml` runs on pushes and PRs to `main`: ruff lint, a
validation of `config-alaska-geoportal.yaml` (exactly one plugin enabled),
pip-audit, gofmt, pytest with the 80% coverage gate, and Go tests. Run
`uv run ruff check core/ plugins/ server/ tests/` and `uv run pytest tests/ -n auto --cov=core --cov=plugins --cov-fail-under=80`
locally before pushing. Smoke against the live org: `PYTHONIOENCODING=utf-8 python scripts/local_server.py`
then `SMOKE_URL=http://localhost:8000/mcp python scripts/smoke_prod.py`; see `SMOKE.md`.
