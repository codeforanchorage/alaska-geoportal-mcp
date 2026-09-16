# OpenContext Architecture

## Overview

OpenContext is a plugin-based framework. Each deployment runs **one** server with **one** plugin. This keeps deployments simple, independently scalable, and easy to maintain.

## One Fork = One Server

**Enforcement:**
- `scripts/deploy.sh` validates config before deployment
- `plugin_manager.py` fails if multiple plugins are enabled

**Multiple servers:** Fork again per plugin, deploy each separately.

## Components

```
core/
├── interfaces.py       # MCPPlugin, DataPlugin, ToolDefinition
├── plugin_manager.py   # Discovery, loading, routing
├── mcp_server.py       # MCP JSON-RPC handler
├── validators.py       # Config validation
└── logging_utils.py   # Structured logging

server/
├── adapters/
│   └── aws_lambda.py   # Lambda handler entry point
└── http_handler.py     # HTTP request handling

plugins/
├── alaska_geoportal/   # THE plugin this fork deploys (14 tools)
│   ├── plugin.py
│   └── config_schema.py
├── arcgis/             # generic ArcGIS Hub plugin (disabled) + the shared
│   └── where_validator.py   #   WHERE/out_fields/order_by validators
├── ckan/               # generic CKAN plugin (disabled)
└── socrata/            # generic Socrata plugin (disabled)

custom_plugins/         # User plugins (auto-discovered)
├── template/
│   └── plugin_template.py

terraform/aws/          # Lambda, API Gateway, custom domain, WAF assoc, alarms
scripts/                # deploy.sh, local_server.py, smoke_*.py

client/                 # Go stdio-to-HTTP client (optional)
tests/                  # Unit tests
```

### Request Flow

```
Claude Desktop / App
    → stdio bridge (npx) or Go client
Lambda / Local Server
    → server.adapters.aws_lambda or scripts/local_server.py
    → MCP Server (core/mcp_server.py)
    → Plugin Manager
    → Plugin (alaska_geoportal)
    → ArcGIS Online portal / ArcGIS Server REST APIs
```

## Plugins

Each deployment enables **exactly one** plugin.

### This deployment: Alaska Geoportal

`plugins/alaska_geoportal/` targets one ArcGIS Online organization (the
State of Alaska Geoportal, `soa-dnr`) and exposes 14 read-only tools:
catalog discovery (`find_gis_content`, `browse_gallery`,
`search_spatial_layers`, `search_layers_by_field`), schema
(`get_item_details`, `get_layer_schema`, `get_distinct_values`), queries
(`query_data`, `spatial_query_point`, `spatial_query_polygon`) and
aggregation (`aggregate_by_polygon`, `coverage_by_polygon`,
`filter_by_polygon`, `find_features_spanning_classifications`). Every
tool goes through the same choke points: item ownership must match the
configured `org_id`, and service URLs must be the org's own tenant or an
allowlisted on-prem host (`*.alaska.gov`). See `CLAUDE.md` for the
statewide specifics (two spatial references, antimeridian-aware coverage,
grouped catalog search) and [SECURITY.md](SECURITY.md) for the model.

The framework plugins below remain in the tree for reference and are
disabled in `config.yaml`.

### Framework reference: CKAN

For CKAN-based open data portals (e.g., data.boston.gov, data.gov, data.gov.uk).

**Configuration:**

```yaml
plugins:
  ckan:
    enabled: true
    base_url: "https://data.yourcity.gov"
    portal_url: "https://data.yourcity.gov"
    city_name: "Your City"
    timeout: 120
    api_key: "${CKAN_API_KEY}"  # Optional
```

**Tools:**

| Tool | Description |
|------|-------------|
| `ckan__search_datasets(query, limit)` | Search for datasets |
| `ckan__get_dataset(dataset_id)` | Get dataset metadata |
| `ckan__query_data(resource_id, filters, limit)` | Query data from a resource |
| `ckan__get_schema(resource_id)` | Get schema for a resource |
| `ckan__execute_sql(sql)` | Execute PostgreSQL SELECT queries (advanced) |

**SQL execution:** The `execute_sql` tool allows complex PostgreSQL queries (CTEs, window functions, joins). Only SELECT is allowed. INSERT, UPDATE, DELETE, DROP, and other destructive operations are blocked. Resource IDs must be valid UUIDs in double quotes: `FROM "uuid-here"`. See [CKAN API docs](https://docs.ckan.org/en/latest/api/) for details.

### Custom Plugins

Add your own plugins in `custom_plugins/`. They are auto-discovered.

**Quick start:**

```bash
mkdir -p custom_plugins/my_plugin
cp custom_plugins/template/plugin_template.py custom_plugins/my_plugin/plugin.py
```

Edit the plugin, add config to `config.yaml` (create from `config-example.yaml` if needed), then `./scripts/deploy.sh`.

**Structure:**
- Inherit from `MCPPlugin` (or `DataPlugin` for data sources)
- Set: `plugin_name`, `plugin_type`, `plugin_version`
- Place in: `custom_plugins/your_plugin_name/plugin.py`
- Tool names: no prefix—Plugin Manager adds it (e.g., `my_plugin__search`)

**Required methods:**

```python
def __init__(self, config: Dict[str, Any]) -> None
async def initialize() -> bool
async def shutdown() -> None
def get_tools() -> List[ToolDefinition]
async def execute_tool(tool_name, arguments) -> ToolResult
async def health_check() -> bool
```

**DataPlugin:** For data sources, inherit from `DataPlugin` and implement `search_datasets`, `get_dataset`, and `query_data`.

**Best practices:** Return `ToolResult(success=False, error_message=...)` on failure. Use `logging.getLogger(__name__)`. Validate config in `initialize()`.

**Reference:**
- [Plugin template](../custom_plugins/template/plugin_template.py)
- [Alaska Geoportal plugin](../plugins/alaska_geoportal/) – the deployed implementation
- [CKAN plugin](../plugins/ckan/) – a smaller reference implementation

## Plugin Interface

```python
class MCPPlugin(ABC):
    plugin_name: str
    plugin_type: PluginType
    plugin_version: str

    async def initialize() -> bool
    async def shutdown() -> None
    def get_tools() -> List[ToolDefinition]
    async def execute_tool(tool_name, arguments) -> ToolResult
    async def health_check() -> bool
```

## Endpoints

| Endpoint | Auth | Use |
|----------|------|-----|
| API Gateway `/mcp` (custom domain `alaska-geoportal.codeforanchorage.org`) | none; stage throttle + fleet WAF | Production |
| API Gateway `/` | none | Static landing page (MOCK, no Lambda) |
| Local `scripts/local_server.py` | none | Development; same handler as Lambda |

No Lambda Function URL is created.

## Configuration

Single `config.yaml`, packaged inside the Lambda zip and read from
`$LAMBDA_TASK_ROOT` (not the `OPENCONTEXT_CONFIG` env var, which is kept
empty because of Lambda's 4 KB env-var cap). Validated at deploy and
runtime. See [DEPLOYMENT.md](DEPLOYMENT.md).

## Security & Scalability

- **API Gateway:** stage throttle 5 rps / burst 10; reserved Lambda concurrency 10
- **WAF:** fleet web ACL, 300 requests per IP per 5 minutes on this host
- **Stateless:** No shared state; Lambda auto-scales
- **Logging:** CloudWatch, structured JSON, request IDs
