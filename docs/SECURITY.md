# Security Model — Alaska Geoportal MCP

This document describes the threat model and the defenses enforced for
the (planned) public deployment at
`https://alaska-geoportal.codeforanchorage.org/mcp`. Future contributors
should read this before changing anything in `plugins/alaska_geoportal/`,
`server/`, or `terraform/aws/`.

## Threat model

- **Endpoint:** publicly reachable, unauthenticated, read-only over
  HTTPS. Anyone can issue JSON-RPC calls. Browsers, native MCP clients,
  and arbitrary HTTP clients all reach the same Lambda.
- **Data:** the MCP only proxies to the State of Alaska Geoportal's
  ArcGIS Online org (`soa-dnr.maps.arcgis.com`, org id
  `7HDiw78fcUiM2BWn`) and on-prem State of Alaska GIS hosts
  (`*.alaska.gov` -- in practice `arcgis.dnr.alaska.gov` and
  `geoportal.dggs.dnr.alaska.gov`). No write paths exist; no secrets
  are stored.
- **Realistic risks:**
  1. Denial of wallet (Lambda invocations, upstream Esri API spam).
  2. Tenant-scope creep — using the MCP as an open proxy for arbitrary
     ArcGIS Online tenants.
  3. Prompt injection — attacker-controlled item descriptions reaching
     the calling LLM as context.
  4. Accidental PII exposure when a publisher misconfigures a layer.
  5. Sensitive values landing in CloudWatch logs in plaintext.

## Defenses in place

### Network and request shape

- **WAF per-IP rate limit** at 300 req / 5 min, blocking mode
  (`terraform/aws/waf.tf`).
- **API Gateway throttling** at 5 rps / 10 burst with a 3000 req/day
  quota (`terraform/aws/api_gateway.tf`, `prod.tfvars`).
- **AWS managed rule sets** (`KnownBadInputsRuleSet`,
  `CommonRuleSet`) in block mode (`waf.tf`).
- **Lambda reserved concurrency** capped at 10 to bound cost and blast
  radius if WAF is bypassed (`main.tf`, `prod.tfvars`).
- **HTTP method allowlist:** only `POST /mcp` and `OPTIONS /mcp`
  reach plugin code; `GET`/`DELETE` return 405 (`server/http_handler.py`).

### Cross-origin and session

- **CORS allowlist** is enforced in Lambda (not API Gateway) so the
  preflight check honors the same list as the actual request
  (`server/http_handler.py:_get_cors_headers`,
  `terraform/aws/api_gateway.tf` — OPTIONS uses AWS_PROXY, not MOCK).
- **`mcp-session-id` is a logging/tracing identifier**, not an auth
  token (`server/http_handler.py`). Do not extend authorization
  decisions to depend on it without adding a real signing/verification
  step.

### Outbound calls (the load-bearing checks)

These two checks together close the SSRF and tenant-scope-creep
surface, and must stay in sync:

- **Service-URL host allowlist**
  (`plugins/alaska_geoportal/plugin.py::_validate_service_url`):
  - `*.alaska.gov` is accepted by suffix (exact suffix match: a
    look-alike such as `evil-alaska.gov` or `alaska.gov.evil.com` is
    refused).
  - For `*.arcgis.com`, the URL must either match the configured portal
    host (`soa-dnr.maps.arcgis.com`) or carry the configured `org_id`
    (`7HDiw78fcUiM2BWn`) as the first path segment. This rejects
    `services.arcgis.com/<other-org>/...`,
    `tiles.arcgis.com/<other-org>/...`, etc.
  - All other hosts are refused.
- **Item-ID ownership check**
  (`plugins/alaska_geoportal/plugin.py::_assert_owned_by_configured_org`):
  - `get_dataset` rejects any item whose `orgId` does not match the
    configured org (case-insensitive). This is the choke point for
    every tool that resolves an item by ID, including
    `get_item_details`, `query_data`, `spatial_query_*`,
    `aggregate_by_polygon`, and `filter_by_polygon`.
  - **Fail-closed:** items missing `orgId` are also rejected.
  - `_search_org_layers` post-filters its results by `orgId` as
    defense-in-depth in case Esri ever returns matches that bypass the
    `orgid:` query clause.
  - `_search_gallery` is intentionally *not* org-filtered — the
    gallery is scoped by the configured `gallery_group_ids` and may
    list cross-org items. Any drill-down still goes through
    `get_dataset` and is rejected if not owned by an allowed org.
  - **Allowed orgs = the state org + `partner_orgs`.** Since 2026-09-16
    the config lists 13 Alaska partner organizations (boroughs, ADF&G,
    DEC, DCRA, DOT&PF, AEA, UAA ACCS, Anchorage). Each entry widens the
    allowlist by exactly one org id, and optionally by exact on-prem
    hostnames (`maps.matsugov.us`, `gisportal.fnsb.gov`,
    `www.ancgis.com`). The ownership check and the service-URL check
    both consult the same set, so a partner's items can be queried
    from its own ArcGIS Online tenant or its own server.
  - **Federal tenants are deliberately not partners.** The state-owned
    "Federal Partner" groups (Census, USGS, NOAA, USFS, BLM, FEMA ...)
    contain item records owned by `soa-dnr` that point at federal
    tenants' services; those fail `_validate_service_url` with a
    message naming the reason. ARRC is also out: its items carry no
    `orgId` at all, and the ownership check is fail-closed. Adding any
    of these is a scope decision to make in `config-alaska-geoportal.yaml`,
    never by relaxing the checks.

### Input validation

- **WHERE clauses** validated against a SQL-injection denylist
  (`plugins/arcgis/where_validator.py`). Forbidden keywords include
  `INSERT/UPDATE/DELETE/DROP/UNION/EXEC/...`; forbidden substrings
  include `;`, `--`, `/*`, `0x`, `xp_`, `sp_`. Max length 2000 chars.
- **`out_fields` and `order_by`** validated for syntax via
  `OutFieldsValidator` and `OrderByValidator`.
- **Item IDs** must be 32-char hex (`_validate_item_id`).
- **Coordinates** validated to WGS84 ranges (`_validate_lonlat`).

### Logs

- **Sensitive headers and request-body keys redacted** by name match
  in `core/logging_utils.py` (`api_key`, `authorization`, `cookie`,
  `password`, `secret`, `token`, etc.).
- **CloudWatch retention** is 14 days (Lambda logs) and 30 days (API
  Gateway access logs) — `terraform/aws/main.tf`,
  `terraform/aws/access_logs.tf`.

### Configuration and secrets

- **No secrets in `config.yaml`.** The file ships in plaintext inside
  the Lambda deployment zip (readable by anyone with `lambda:GetFunction`)
  and is committed to a public repo; the `OPENCONTEXT_CONFIG` env var is
  kept empty. This is an **invariant**: any future plugin secret must go
  via AWS Secrets Manager or SSM Parameter Store with KMS, never the
  config file or an env var. CI should enforce this if a secret-bearing
  plugin is ever added. Today the plugin needs none: the Geoportal is
  queried anonymously.

## Architectural invariants

These are enforced by code today; do not relax them without explicit
discussion.

1. **One fork = one MCP server.** The single-plugin rule is enforced
   at config validation (`core/validators.py`) and at runtime
   (`PluginManager.load_plugins()`). Multiple enabled plugins is a
   hard error.
2. **No write paths.** No tool calls `applyEdits`, `/admin/`, or any
   non-`/query` Feature Service path. `WhereValidator` blocks DML
   keywords. If a plugin ever needs writes, treat it as a security-
   review-required change.
3. **Tenant scope = the configured org.** See `_validate_service_url`
   and `_assert_owned_by_configured_org`. These two checks together
   keep the MCP from being a free public proxy for other ArcGIS
   Online tenants.

## Deferred / known gaps

These are documented in the security review and not yet shipped.

| # | Issue | Status |
|---|---|---|
| 3 | No field-level PII denylist on returned records (e.g. emails, phones, applicant names) | open — proposal drafted |
| 4 | Response bodies dumped to CloudWatch by name-key redaction only — no value-pattern scrub for emails/phones | open |
| 5 | Access-log `sourceIp` is raw; not hashed | open |
| 6 | `/mcp` is fully unauthenticated; rate-limit bypass via rotating IPs is feasible | accepted given public-data scope |
| 7 | CORS allowlist includes `localhost:6274` (MCP Inspector) in prod | accepted; revisit when non-public tools land |
| 9 | Config in plaintext env var | accepted as invariant; see above |
| 10 | No request-body size cap at API Gateway (Lambda's 6 MB ceiling applies) | open |

## Verifying a change

Before merging anything that touches `plugins/alaska_geoportal/`,
`server/`, `terraform/aws/`, or `core/`:

1. `pytest tests/test_alaska_geoportal_plugin.py -q` — all must pass,
   including `TestValidateServiceUrl`, `TestItemOwnership`, and
   `TestSearchOrgLayersFilter`.
2. Smoke-test locally:
   ```bash
   PYTHONIOENCODING=utf-8 venv/Scripts/python scripts/local_server.py
   ```
   Then issue `query_data` against a known state item
   (e.g. Fire Service Areas `45072954dcd84d78947a4294ed990657`, or the
   on-prem RS2477 Trails `f97ec4306fb14ed59c71b02ee8cf0f47`). Records
   should return. `scripts/smoke_prod.py` does both.
3. For changes to `_validate_service_url` or `_assert_owned_*`, also
   confirm a partner-org item ID (e.g. DOT&PF Roads and Highways
   `bbe5cd90520e41348eef242a8f754172`) is rejected with a clear error.
4. Deploy with `./scripts/deploy.sh --environment prod`; this script
   plans first and requires explicit `yes` before applying.

## Reporting issues

Email `brendanbabb@gmail.com` for sensitive reports. Public issues
can go to <https://github.com/codeforanchorage/alaska-geoportal-mcp/issues>.
