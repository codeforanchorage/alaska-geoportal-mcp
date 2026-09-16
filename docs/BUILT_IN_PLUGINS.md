# Built-in Plugins Reference

This fork deploys one plugin, **Alaska Geoportal**. The framework's generic
CKAN, ArcGIS Hub and Socrata plugins are still in `plugins/` for reference
and are disabled in `config.yaml`; only one plugin may be enabled.

## Alaska Geoportal Plugin (`alaska_geoportal`)

Statewide access to the State of Alaska Geoportal (Alaska Geospatial
Office / DNR ArcGIS Online org `soa-dnr`). 14 read-only tools; the full
list with one-line descriptions is in the [README](../README.md#tools-14-all-read-only).

### Configuration

```yaml
plugins:
  alaska_geoportal:
    enabled: true
    portal_base_url: "https://soa-dnr.maps.arcgis.com/sharing/rest"
    org_id: "7HDiw78fcUiM2BWn"
    gallery_group_ids:                # ArcGIS group ids searched as a union
      - "a5055ea72899425c8cc4e01b32658a45"
      - "18028130a7a14132bd922bcd830f27c6"
      # ... see config-alaska-geoportal.yaml for the verified full list
    city_name: "State of Alaska"
    gallery_url: "https://gis.data.alaska.gov/search"
    timeout: 20                       # must stay below aws.lambda_timeout
```

`gallery_group_ids` entries must be 32-character hex ArcGIS group ids.
The verified org and group ids, and the reasoning for which groups are
included, are in [ALASKA_SOURCES.md](ALASKA_SOURCES.md).

### Behaviour worth knowing

- Only items owned by `org_id` are queryable; partner-org layers in the
  catalog are listed by search but refused on query ([SECURITY.md](SECURITY.md)).
- Service URLs must be on the org's own ArcGIS Online tenant or on
  `*.alaska.gov` (DNR / DGGS ArcGIS Servers).
- Web Mercator `Shape__Area` is corrected per feature by `cos²(lat)`;
  EPSG:3338 areas pass through as true square metres.
- Every query response carries data-freshness and coverage caveats; the
  coverage check is statewide and antimeridian-aware.
- WHERE clauses go through the shared validator in
  `plugins/arcgis/where_validator.py` (keyword denylist, identifier check
  against the layer schema, `CAST(field AS <type>)` allowed).

### Example

```
find_gis_content(topic="forestry roads")
get_layer_schema(item_id="f3298e00f4fa40fdb0d443bb61dcfee3")
aggregate_by_polygon(source_item_id="f3298e00f4fa40fdb0d443bb61dcfee3",
                     aggregation_item_id="72868306fe0648d49cd653bcdf22ea0e",
                     group_by_field="NAME", sum_fields=["SegmentLengthMiles"])
```

---

## CKAN Plugin (framework, disabled here)

For CKAN-based open data portals (e.g., data.boston.gov, data.gov, data.gov.uk).

### Configuration

```yaml
plugins:
  ckan:
    enabled: true
    base_url: "https://data.yourcity.gov"       # CKAN API base URL
    portal_url: "https://data.yourcity.gov"     # Public portal URL
    city_name: "Your City"                      # City/organization name
    timeout: 120                                # HTTP timeout in seconds
    api_key: "${CKAN_API_KEY}"                  # Optional: API key
```

### Tools

- `ckan__search_datasets(query, limit)` - Search for datasets
- `ckan__get_dataset(dataset_id)` - Get dataset metadata
- `ckan__query_data(resource_id, filters, limit)` - Query data from a resource
- `ckan__get_schema(resource_id)` - Get schema for a resource

### Examples

**Search datasets:**
```
Search for datasets about housing in Boston
```

**Get dataset:**
```
Get details about the "311 Service Requests" dataset
```

**Query data:**
```
Query the first 10 records from resource abc123
```

## CKAN API

This plugin uses CKAN's Action API:
- `/api/3/action/package_search` - Search datasets
- `/api/3/action/package_show` - Get dataset
- `/api/3/action/datastore_search` - Query data

See [CKAN API documentation](https://docs.ckan.org/en/latest/api/) for details.

## Socrata Plugin (framework, disabled here)

For Socrata-based open data portals (e.g., data.cityofchicago.org, data.cityofnewyork.us, data.seattle.gov).

**Note:** Socrata requires a free app token. Register at [https://dev.socrata.com/register](https://dev.socrata.com/register).

### Configuration

```yaml
plugins:
  socrata:
    enabled: true
    base_url: "https://data.cityofboston.gov"
    portal_url: "https://data.cityofboston.gov"
    city_name: "Boston"
    app_token: "${SOCRATA_APP_TOKEN}"   # Required
    timeout: 30.0                        # HTTP timeout (default: 30)
```

### Tools

- `socrata__search_datasets(query, limit)` - Search for datasets in the portal catalog
- `socrata__get_dataset(dataset_id)` - Get full metadata for a dataset (4x4 ID)
- `socrata__get_schema(dataset_id)` - Get column schema for constructing SoQL queries
- `socrata__query_dataset(dataset_id, soql_query)` - Query data using SoQL
- `socrata__execute_sql(dataset_id, soql)` - Execute raw SoQL query (advanced, similar to CKAN execute_sql)
- `socrata__list_categories()` - List all categories with dataset counts

### Examples

**Search datasets:**
```
Search for datasets about housing in Boston
```

**Get dataset:**
```
Get details about dataset wc4w-4jew
```

**Get schema (call before query_dataset):**
```
Get schema for dataset wc4w-4jew
```

**Query data:**
```
Query dataset wc4w-4jew with: SELECT * WHERE year > 2020 LIMIT 50
```

**List categories:**
```
List all dataset categories on Boston's open data portal
```

### Socrata API

This plugin uses two Socrata API layers:
- **Discovery API** (api.us.socrata.com) - Catalog search, categories
- **SODA3** (portal domain) - Dataset metadata, schema, data queries

See [Socrata developer documentation](https://dev.socrata.com/) for details.

## Custom Plugins

If your portal doesn't use CKAN, you can create a custom plugin. See [Custom Plugins Guide](CUSTOM_PLUGINS.md) for instructions.

## Examples

`config-alaska-geoportal.yaml` is the complete, deployed configuration for
this fork; `config-example.yaml` shows every plugin's keys.
