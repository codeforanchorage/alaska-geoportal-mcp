# Alaska GIS sources

The target of this fork, plus the other Alaska ArcGIS Online organizations
that are candidates for the same fork (one fork = one org, per
[ARCHITECTURE.md](ARCHITECTURE.md)). "Verified" means the org id and public
Feature Service count were checked live on 2026-09-15 with the probes at the
bottom of this page; anything else is a pointer to check, not a fact.

## This fork: State of Alaska Geoportal (Alaska Geospatial Office / DNR)

| | |
|---|---|
| Hub site | <https://gis.data.alaska.gov> (canonical `alaska-geoportal-soa-dnr.hub.arcgis.com`, also `akgeoportal.alaska.gov`) |
| Hub site item | `7dd7c86dd0cc40f6a516eb77001977c1` |
| AGOL org | `soa-dnr` -> `https://soa-dnr.maps.arcgis.com/sharing/rest` |
| `org_id` | `7HDiw78fcUiM2BWn` ("Alaska Department of Natural Resources ArcGIS Online") |
| Public Feature Services owned by the org | 665 |
| Service hosts | `services1.arcgis.com/7HDiw78fcUiM2BWn/...` (hosted), `arcgis.dnr.alaska.gov` (on-prem DNR ArcGIS Server, EPSG:3338), `geoportal.dggs.dnr.alaska.gov` (DGGS) |

### Catalog groups

The Hub site's `catalogV2` scope lists **45 groups**. Only the ones owned by
`soa-dnr` with queryable content are configured in `gallery_group_ids`:

| Group id | Title | Public Feature Services |
|---|---|---|
| `a5055ea72899425c8cc4e01b32658a45` | Alaska Department of Natural Resources Open Data Content | 109 |
| `18028130a7a14132bd922bcd830f27c6` | AK DNR: Open Data Services | 62 |
| `112a233ad29c46ae861fdeb0475aff8b` | DGGS Geoportal Collaboration v2 | 20 |
| `e09f40dee931443485e5f36b55d7dd09` | DOG OpenData (Division of Oil and Gas) | 15 |
| `705db769b7624af18a0367d58225aed4` | Alaska Geoportal Content (apps, story maps) | 4 |
| `b5dceabe78cd45108f098e11d6f9738e` | Alaska Division of Oil and Gas Open Data Content | 1 |

Deliberately **not** configured:

- **Federal partner groups** (`Alaska Geoportal Federal Partner - USGS / DOT /
  FEMA / NPS / BOEM / HUD / NOAA / USFS / USACE / DOD / US Census Bureau / GSA /
  BLM / USFWS`). These are owned by `soa-dnr` and their items are owned by the
  `AlaskaGeospatialOffice` user, but the items point at the federal tenants'
  own services (e.g. `services2.arcgis.com/FiaPA4ga0iQKduv3/...` for Census).
  The service-URL allowlist in `_validate_service_url` rejects those hosts, so
  the layers would be discoverable but not queryable. Adding them needs a
  deliberate change to the tenant-scoping model documented in
  [SECURITY.md](SECURITY.md).
- **Partner-org groups** (Mat-Su, Kenai Peninsula, Kodiak, Unalaska, Haines,
  FNSB, ADF&G, DEC, DOT&PF, DCRA, AEA, ACCS, ARRC, USFS Alaska Region,
  Tongass, SEAKGIS, FWS, BLM, Anchorage's two groups). Their items carry a
  different `orgId` and are refused by `_assert_owned_by_configured_org`.
  They belong in their own forks (below).

### Layers used by the smoke scripts

| Item id | Title | Geometry | Rows | SR |
|---|---|---|---|---|
| `45072954dcd84d78947a4294ed990657` | Fire Service Areas Public View | polygon | 32 | 3338 (hosted) |
| `9a91ae205d544b53a35842591afcc2a1` | CWPP Areas Public View | polygon | 12 | 3338 (hosted) |
| `72868306fe0648d49cd653bcdf22ea0e` | CLG_borough_POLY (boroughs, field `NAME`) | polygon | 20 | 3857 |
| `f3298e00f4fa40fdb0d443bb61dcfee3` | Alaska Forestry Roads Public View (`SegmentLengthMiles`) | polyline | 3,190 | 3338 (hosted) |
| `e9bfc953765d4b279d3316de7967cc08` | Forestry Bridges Public View | point | 183 | 3338 (hosted) |
| `458be3d8aafa47cd882af05cee983f6b` | Alaska Statewide Parcels (`AK_Parcels`) | polygon | ~415,000 | 3857 |
| `f97ec4306fb14ed59c71b02ee8cf0f47` | RS2477 Trails (on-prem `arcgis.dnr.alaska.gov`) | polyline | 2,586 | 3338 |

Note the mix of spatial references: hosted layers are NOT uniformly Web
Mercator here. `_true_area_m2` corrects 3857 per feature and passes 3338
through as true square metres.

## Candidate orgs for sibling forks

All of these appear as partner groups in the Geoportal catalog, which is how
the org ids below were obtained (group `orgId`, checked 2026-09-15). The Hub
URLs and "what they publish" are from the group titles and the Hub sites
themselves; FS counts are public Feature Services **in the catalogued group**,
not in the whole org.

| Org | `org_id` | Hub / portal | Publishes | Status |
|---|---|---|---|---|
| DNR Open Data (same org as this fork) | `7HDiw78fcUiM2BWn` | <https://data-soa-dnr.opendata.arcgis.com> | Land status, parcels, forestry, parks, oil & gas, geology (DGGS) | **Verified** -- it is this fork; the Open Data site is another Hub view of the same groups |
| ADF&G GIS Hub (Fish & Game) | `VdkVOAHovLuozJG4` | <https://gis.adfg.alaska.gov> (group "Alaska Department of Fish & Game Open Data", 27 FS) | Anadromous waters catalog, game management units, habitat | Org id verified via group; Hub URL not probed |
| Alaska DOT&PF | `r4A0V7UzH9fcLVvv` | group "Alaska DOT Open Data Content" (61 FS); services at `services.arcgis.com/r4A0V7UzH9fcLVvv` | Roads & highways functional class, AMHS, airports, bridges | Org id verified via group; Hub URL not probed |
| Alaska DEC | `8MMg7skvEbOESlSM` | group "ADEC Open Data Layers" (20 FS) | Contaminated sites, air/water permits, spill response | Org id verified via group; Hub URL not probed |
| DCRA (Commerce, Community & Economic Development) | `0DjevcWawQ1dy3il` | group "Open Data DCRA-SOA" (128 FS, 656 items) | Community profiles, boundaries, infrastructure (largest partner catalog) | Org id verified via group; Hub URL not probed |
| Alaska Energy Authority | `aJhsucjqSbYNmsuZ` | group "Alaska Energy Authority Open Data" (7 FS) | Power plants, energy infrastructure | Org id verified via group |
| Matanuska-Susitna Borough | `fX5IGselyy1TirdY` | group "Matanuska-Susitna Borough Open Data" (60 FS); on-prem `maps.matsugov.us` | Parcels, easements, recreation, zoning | Org id verified via group; note on-prem host needs an allowlist entry |
| Kenai Peninsula Borough | `ba4DH9pIcqkXJVfl` | group "KPB GeoHub Content" (39 FS, 106 items) | Parcels, zoning, hazards | Org id verified via group |
| Fairbanks North Star Borough | `f4rR7WnIfGBdVYFd` | group "FNSB GIS Data Content" (25 FS) | Parcels, zoning, air quality | Org id verified via group |
| Kodiak Island Borough | `R5BNizttyFKxRSMm` | group "Kodiak Island Borough Open Data" (26 FS) | Parcels, zoning | Org id verified via group |
| City & Borough of Juneau | -- | <https://juneau.org> GIS / `epv.juneau.org` (not in the Geoportal catalog) | Parcels, zoning, trails | **Not verified** -- no group in the catalog; org id must be looked up |
| Municipality of Anchorage | `Ce3DhLRthdwbHlfF` | `muniorg.maps.arcgis.com` | Parcels, zoning, assessor | Verified -- served by the parent fork `codeforanchorage/anchorage-gis-mcp` |
| Southeast Alaska GIS Library | `GuxCnhbHpvpWeAM1` | group "Southeast Alaska GIS Library" (19 FS) + "SEAKGIS Library USFS Data" (20 FS) | Regional Southeast layers | Org id verified via group |

## How the values above were obtained

```bash
# org id
curl -s "https://soa-dnr.maps.arcgis.com/sharing/rest/portals/self?f=json" | jq '{id,name,urlKey}'

# Hub site item id (from the site HTML), then its catalog groups
curl -sL https://gis.data.alaska.gov/ | grep -o 'siteId[^,]*'
curl -s "https://www.arcgis.com/sharing/rest/content/items/7dd7c86dd0cc40f6a516eb77001977c1/data?f=json" \
  | jq '.values.catalogV2.scopes.item.filters[0].predicates[0].group.any'

# per group: owner org + public Feature Service count
curl -s "https://www.arcgis.com/sharing/rest/community/groups/<gid>?f=json" | jq '{title,orgId,access}'
curl -s "https://www.arcgis.com/sharing/rest/search?q=group:<gid>%20type:%22Feature%20Service%22&num=1&f=json" | jq .total

# public Feature Services owned by the org
curl -s "https://www.arcgis.com/sharing/rest/search?q=orgid:7HDiw78fcUiM2BWn%20type:%22Feature%20Service%22%20access:public&num=10&f=json" \
  | jq '.total, (.results[] | {id,title,url})'
```
