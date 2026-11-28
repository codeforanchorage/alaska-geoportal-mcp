# Smoke record

The live smoke suite is `scripts/smoke_prod.py` (23 checks: JSON-RPC
surface, the 14 tools across state, partner-org and on-prem layers, tenant scoping,
error hints, and the `GET /` landing page). Run it against any environment:

```bash
PYTHONIOENCODING=utf-8 SMOKE_URL=https://alaska-geoportal.codeforanchorage.org/mcp python scripts/smoke_prod.py
PYTHONIOENCODING=utf-8 SMOKE_URL=http://localhost:8000/mcp python scripts/smoke_prod.py
PYTHONIOENCODING=utf-8 python scripts/smoke_aggregate.py     # direct-plugin aggregation smoke
```

## Latest result

2026-11-28, against `https://alaska-geoportal.codeforanchorage.org/mcp`
(API Gateway `ae6gj7yvfg`, Lambda `alaska-geoportal-mcp-prod`): **23/23**.

Notable live figures (they drift as the state republishes):

| Check | Result |
|---|---|
| Fire Service Areas | 32 features; Fairbanks point lookup → `CITY OF FAIRBANKS` (FNSB) |
| RS2477 Trails (on-prem DNR, EPSG:3338) | 2,586 features |
| Alaska Statewide Parcels, `local_gov='Fairbanks North Star Borough'` | 63,888 of ~415,000 (item made private by the state 2026-11; check replaced by State Mining Claim) |
| State Mining Claim (on-prem DNR) | 41,377 features |
| Forestry road miles by borough (polyline aggregation) | layer now has 6,144 segments, above the 5,000 source cap: the run reads 5,000 (8 boroughs, 1,661 outside any borough) and its totals are partial. Single-borough check via `spatial_query_polygon`: 123 segments in the Mat-Su |
| DOT&PF Roads and Highways (partner tenant) | queryable since the 2026-09-16 partner-org change, 27,926 features |
| Mat-Su easements (partner on-prem, `maps.matsugov.us`) | 24,934 features |
| Census layer in a federal tenant | refused by the service-URL allowlist, as designed |

## Verified org values

Recorded 2026-09-15 and used by `config-alaska-geoportal.yaml`; the probes
are written up in `docs/ALASKA_SOURCES.md`.

| | |
|---|---|
| `portal_base_url` | `https://soa-dnr.maps.arcgis.com/sharing/rest` |
| `org_id` | `7HDiw78fcUiM2BWn` |
| Hub site item | `7dd7c86dd0cc40f6a516eb77001977c1` (`https://gis.data.alaska.gov`) |
| Catalog groups in the Hub site | 45, of which 6 state-owned groups with Feature Services are configured |
| Public Feature Services owned by the org | 665 |

Two things differed from the Anchorage fork's assumptions and shaped the
plugin: the on-prem host suffix is `.alaska.gov`, and many layers, hosted
and on-prem alike, are in Alaska Albers (EPSG:3338) rather than Web
Mercator, so the area correction and the coverage check both handle 3338.

## History

- 2026-09-15: initial local smoke (19/19) through `scripts/local_server.py`
  before the first deploy; first prod smoke 19/19 on the raw API Gateway
  URL and again on the custom domain after DNS.
- 2026-09-16: first real session surfaced `Unable to complete operation`
  on a text-typed numeric field (DNR well logs); error hint and validator
  fixed and redeployed. Landing page added; suite grew to 20 checks.
  Later the same day the partner-org scope added three checks (23).
- 2026-11: the state made Alaska Statewide Parcels private; the
  large-layer check moved to State Mining Claim. Forestry Roads passed
  the 5,000-feature aggregation cap (6,144 segments on 2026-11-28).
