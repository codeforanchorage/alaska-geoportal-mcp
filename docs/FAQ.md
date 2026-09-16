# Frequently Asked Questions

## About the server

### What is this?

An MCP (Model Context Protocol) server that lets an AI assistant query the
State of Alaska Geoportal, the Alaska Geospatial Office's ArcGIS Online
catalog of statewide GIS layers, through 14 read-only tools: catalog
search, layer schema, attribute and spatial queries, and aggregation. It
answers questions like "how many miles of forestry road are in the Mat-Su
Borough" from the official layers and states each layer's caveats.

### How do I use it?

Add `https://alaska-geoportal.codeforanchorage.org/mcp` as a custom
connector in Claude (Settings → Connectors). Any MCP client that speaks
streamable HTTP works. The `/mcp` path is required. There is no login.

### Is it free? Is there a rate limit?

Free and public. Traffic is capped at roughly 5 requests per second overall
and 300 requests per IP per five minutes; you get a 429 beyond that. All
claude.ai users share a handful of egress IPs, so that limit is effectively
shared among them.

### What data can it reach?

Layers **owned by** the `soa-dnr` ArcGIS Online org: DNR land status,
statewide parcels, forestry, state parks, oil & gas, DGGS geology, and the
layers other state divisions publish through that org, whether hosted on
ArcGIS Online or on DNR's own servers (`arcgis.dnr.alaska.gov`,
`geoportal.dggs.dnr.alaska.gov`). About 665 public Feature Services at
last count.

### Why does it refuse a layer I can see on gis.data.alaska.gov?

The Geoportal catalog also lists content from other organizations
(boroughs, ADF&G, DOT&PF, DEC, USFS, BLM, Census and other federal
partners). Those layers live in other ArcGIS tenants, and this server only
proxies the state org's own services. That is the security model (no open
proxy for arbitrary tenants), not an oversight; see [SECURITY.md](SECURITY.md).
Each of those orgs is a candidate for its own copy of this server;
[ALASKA_SOURCES.md](ALASKA_SOURCES.md) lists them with verified ids.

### Is the data authoritative / current?

It is whatever the publishing division has put on the Geoportal. Every
response carries the layer's last-edit date and, where relevant, a
coverage caveat (a layer named for a region or map quad does not cover the
state). The assistant is instructed to repeat those caveats.

### Can it change anything?

No. Every tool is read-only and the server holds no credentials for the
Geoportal.

## Operating it

### One fork, one server?

Yes. This repo deploys exactly one plugin (`alaska_geoportal`). The
framework it is built on (OpenContext) enforces that at config validation.
To serve another org, fork again and change the config; see
[ARCHITECTURE.md](ARCHITECTURE.md).

### How do I change the model-facing instructions or the searched groups?

Edit `config-alaska-geoportal.yaml` (`instructions`, `gallery_group_ids`),
copy it to `config.yaml`, run the tests, deploy. See
[GETTING_STARTED.md](GETTING_STARTED.md).

### How do I deploy?

`./scripts/deploy.sh -e prod`, which plans and asks before applying. There
is no staging stack. Details and the first-time custom-domain sequence are
in [DEPLOYMENT.md](DEPLOYMENT.md); day-2 operations in [RUNBOOK.md](RUNBOOK.md).

### Where are the logs?

CloudWatch, `/aws/lambda/alaska-geoportal-mcp-prod` (application) and
`/aws/apigateway/alaska-geoportal-mcp-prod-access` (every request, including
the ones the WAF or API Gateway rejected before the Lambda ran).

### How much does it cost?

A few dollars a month at current traffic, mostly CloudWatch logs.

## Developing

### How do I run it locally?

```bash
uv sync
cp config-alaska-geoportal.yaml config.yaml
PYTHONIOENCODING=utf-8 python scripts/local_server.py
SMOKE_URL=http://localhost:8000/mcp python scripts/smoke_prod.py
```

The local server hits the live org; nothing is mocked. See
[TESTING.md](TESTING.md).

### How do I run the tests?

```bash
uv run ruff check core/ plugins/ server/ tests/
uv run pytest tests/ -n auto --cov=core --cov=plugins --cov-fail-under=80
```

CI runs the same on every push and PR to `main`.

### Where does the plugin live?

`plugins/alaska_geoportal/plugin.py` (tools, spatial helpers, caveats) and
`config_schema.py`. The generic `ckan`, `arcgis` and `socrata` plugins from
the framework are still present but disabled; the shared WHERE-clause
validator in `plugins/arcgis/where_validator.py` is used by this plugin.

### I want to point this at a different ArcGIS Online org.

Change `portal_base_url`, `org_id`, `gallery_group_ids`, `gallery_url` and
`city_name` in the config, and `ONPREM_HOST_SUFFIXES` in the plugin if that
org publishes from its own ArcGIS Server. The process used to verify the
values for this org is written up at the bottom of
[ALASKA_SOURCES.md](ALASKA_SOURCES.md).

## Support

- Issues: <https://github.com/codeforanchorage/alaska-geoportal-mcp/issues>
- Security reports: see the contact in [SECURITY.md](SECURITY.md)
- Framework credit: OpenContext by Srihari Raman (City of Boston); the
  spatial plugin and this fork by Code for Anchorage.
