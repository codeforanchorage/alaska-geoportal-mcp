# Alaska Geoportal MCP

A statewide [Model Context Protocol](https://modelcontextprotocol.io/) server
over the **State of Alaska Geoportal** -- the Alaska Geospatial Office's
ArcGIS Online organization (`soa-dnr`), which publishes several hundred public
Feature Services from DNR (land status, statewide parcels, forestry, state
parks, oil & gas, DGGS geology) and hosts the catalog that other state
agencies and boroughs share into.

Ask a connected model "how many miles of forestry road are in the Mat-Su
Borough", "which fire service area is this point in", or "list the CWPP
areas", and it answers from the official layers: discover the layer, read
its schema, query or aggregate it, and report the number with the caveats the
data carries (regional coverage, Web Mercator area inflation, capped fetches).

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io/)

This is a standalone fork of
[codeforanchorage/anchorage-gis-mcp](https://github.com/codeforanchorage/anchorage-gis-mcp),
pointed at the state org instead of the Municipality of Anchorage, with the
two MOA-only parcel tools removed and the Anchorage-specific geometry
(coverage bbox, area correction) generalized to the whole state. Both are
built on [OpenContext](https://github.com/srihari-raman/opencontext).

---

## Scope

| | |
|---|---|
| Hub site | <https://gis.data.alaska.gov> |
| ArcGIS Online org | `soa-dnr` (`7HDiw78fcUiM2BWn`) |
| Public Feature Services | ~665, hosted on `services1.arcgis.com` and the on-prem `arcgis.dnr.alaska.gov` / `geoportal.dggs.dnr.alaska.gov` servers |
| Catalog groups searched | 6 state-owned groups (see `config-alaska-geoportal.yaml`) |

**Only layers owned by the state org are queryable.** The Geoportal catalog
also lists content from boroughs, ADF&G, DOT&PF, DEC and federal partners
under their own organizations; those show up in search but are refused on
query, by design (see [docs/SECURITY.md](docs/SECURITY.md)). Each of those orgs
is a candidate for its own fork -- [docs/ALASKA_SOURCES.md](docs/ALASKA_SOURCES.md)
lists them with verified org ids.

## Tools (14, all read-only)

| Tool | What it does |
|---|---|
| `find_gis_content` | Combined search of the catalog groups (maps/apps) and the org's spatial layers by topic |
| `browse_gallery` | Browse or keyword-search the catalog groups (viewers, not queryable) |
| `search_spatial_layers` | Search Feature/Map Services and downloadable data by keyword |
| `get_item_details` | Full portal item description, URL, extent, tags |
| `get_layer_schema` | Real, case-sensitive field names, types and coded-value domains |
| `get_distinct_values` | Exact stored values of a field (for building WHERE clauses) |
| `search_layers_by_field` | Find layers that carry a given field name |
| `query_data` | Attribute query with WHERE / out_fields / order_by; leads with TOTAL COUNT |
| `spatial_query_point` | "What is at lon/lat" against a polygon layer |
| `spatial_query_polygon` | "Which X are inside / within N miles of Y", filter by another layer's polygon or inline GeoJSON |
| `aggregate_by_polygon` | Count / sum source features per polygon (with optional buffer) |
| `coverage_by_polygon` | Share of each target polygon covered by an overlay layer |
| `filter_by_polygon` | Source features inside a named container polygon |
| `find_features_spanning_classifications` | Source features that touch >= N distinct values of a classification layer |

## Quick start

```bash
uv sync                                   # or: pip install -r requirements.txt
cp config-alaska-geoportal.yaml config.yaml
PYTHONIOENCODING=utf-8 python scripts/local_server.py   # http://localhost:8000/mcp

# in another shell: 19 end-to-end checks against the live org
SMOKE_URL=http://localhost:8000/mcp python scripts/smoke_prod.py
```

Connect Claude Desktop / Claude Code through `stdio_bridge.py` or the Go client
in `client/`, or add the URL as a custom connector once deployed. See
[docs/GETTING_STARTED.md](docs/GETTING_STARTED.md).

## Deploy

AWS Lambda + API Gateway via Terraform (`terraform/aws/`), one Lambda per
fork. `./scripts/deploy.sh -e prod` packages `config.yaml` into the zip and
plans before applying. This fork is configured but **not yet deployed**; the
go-live TODOs (state bucket, alarms topic, fleet WAF entry) are in
`terraform/aws/prod.tfvars` and [docs/RUNBOOK.md](docs/RUNBOOK.md).

## Documentation

| Doc | Description |
|---|---|
| [Alaska sources](docs/ALASKA_SOURCES.md) | The state org, its catalog groups, and the other Alaska orgs (verified ids) |
| [Security](docs/SECURITY.md) | Threat model, tenant scoping, host allowlist |
| [Runbook](docs/RUNBOOK.md) | Kill switch, traffic postures, alarms, smoke |
| [Architecture](docs/ARCHITECTURE.md) | OpenContext plugin design (one fork = one server) |
| [Custom plugins](docs/CUSTOM_PLUGINS.md) | Writing a plugin |
| [Deployment](docs/DEPLOYMENT.md) | AWS, Terraform, monitoring |
| [Testing](docs/TESTING.md) | Local testing (terminal, Claude, MCP Inspector) |
| [SMOKE.md](SMOKE.md) | Output of the initial live smoke against `soa-dnr` |

## Contributing

```bash
uv run ruff check core/ plugins/ server/ tests/
uv run pytest tests/ -n auto
```

Pre-commit hooks (Ruff, yamllint, gofmt): `pip install pre-commit && pre-commit install`.

## License and attribution

MIT -- see [LICENSE](LICENSE).

- **OpenContext** (the plugin framework, `core/`, `server/`, the generic
  `ckan` / `arcgis` / `socrata` plugins, Terraform and deploy tooling):
  Srihari Raman, City of Boston Department of Innovation and Technology.
- **Anchorage GIS MCP** (the ArcGIS Portal plugin this one is derived from,
  the spatial tools, caveat machinery and security model) and this
  statewide fork: [Code for Anchorage](https://codeforanchorage.org).
- Data: State of Alaska, Alaska Geospatial Office / Department of Natural
  Resources, via the public Alaska Geoportal. Check each layer's own terms
  of use in its item description.
