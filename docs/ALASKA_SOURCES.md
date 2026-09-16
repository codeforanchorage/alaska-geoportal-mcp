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

### Alaska partner orgs (configured 2026-09-16)

Each is a `partner_orgs` entry in `config-alaska-geoportal.yaml`, which
admits its items to the ownership check and its tenant (plus any listed
on-prem hosts) to the service-URL allowlist, and its groups are added to
`gallery_group_ids`. Counts are public Feature/Map Services in the
catalogued group(s); hosts were read from those items' service URLs.

| Org | `org_id` | On-prem hosts admitted | Group(s) | Services |
|---|---|---|---|---|
| Municipality of Anchorage | `Ce3DhLRthdwbHlfF` | `www.ancgis.com` | `805318360e5046cb9d7b252ee0c3105b`, `c34ed10758ec4f4eb8aa6826ee5be3ff` (apps) | 76 |
| Matanuska-Susitna Borough | `fX5IGselyy1TirdY` | `maps.matsugov.us` | `2277e4402d15474eb22ad64b410292b5`, `7ae0e98a30e840d28cea2e97fb86d15d` (apps) | 60 |
| Kenai Peninsula Borough | `ba4DH9pIcqkXJVfl` | -- | `9f50b42277a94f369002f2e7db25384b` | 39 (3 point at other tenants and stay refused) |
| Fairbanks North Star Borough | `f4rR7WnIfGBdVYFd` | `gisportal.fnsb.gov` | `9b70d86fb59848e99ba979e4fb68b577` | 39 |
| Kodiak Island Borough | `R5BNizttyFKxRSMm` | -- (`gistest.kodiakak.us` is a test host, not admitted) | `593bb33b063f4327b2d3beea351d0fe8` | 26 |
| City of Unalaska | `XYRnCwZ037YZHYH0` | -- | `cceaf377149d4657871e224c25cf756d` | 6 |
| Haines Borough | `pMlUMMROURtJLUZt` | -- | `27f53ccba1dc49f0a8605dac3290d66c` (apps only) | 0 |
| ADF&G | `VdkVOAHovLuozJG4` | `gis.adfg.alaska.gov` (already `*.alaska.gov`) | `503809f0fdf7478eb2cba0015179e226` | 27 |
| DEC | `8MMg7skvEbOESlSM` | `dec.alaska.gov` (already `*.alaska.gov`) | `a3ff58da1bf04e209e44a1f50efab18c` | 39 |
| DCRA | `0DjevcWawQ1dy3il` | `maps.commerce.alaska.gov` (already `*.alaska.gov`) | `37ac60c091744e80a379c33c80fbf64d`, `031b68d1f04943d6969a3f764b98377e` | 136 |
| DOT&PF | `r4A0V7UzH9fcLVvv` | -- | `d02c85d843ee4231850b68e7359f316f` | 61 |
| Alaska Energy Authority | `aJhsucjqSbYNmsuZ` | -- | `e2dffb4a9f834e4e968e8ffb5be3a822` | 7 |
| UAA Alaska Center for Conservation Science | `DlE4MSUhoXlyq64t` | -- | `0c27db95e5754212b0ecc1ea3b3b6cb7` | 6 |

Deliberately **not** configured:

- **Alaska Railroad (ARRC)** group `9c08399657674ee8af2bd48f6227a94c`: its
  five Feature Services (on `geo.akrr.com`) carry no `orgId` in either the
  search or the item record, so the fail-closed ownership check cannot
  admit them without a per-owner exception. Revisit if ARRC data is asked for.
- **Southeast Alaska GIS Library** groups (`dc223b8c…`, `3bd5a02c…`, org
  `GuxCnhbHpvpWeAM1`): the items point at the USFS Alaska Region tenant
  (`services1.arcgis.com/gGHDlz6USftL5Pau`) and `apps.fs.usda.gov`, i.e.
  federal data, so they fall under the federal exclusion.
- **Non-government groups** (Alaska Food Policy Council, "Public Map").
- **Federal partner groups** (`Alaska Geoportal Federal Partner - USGS / DOT /
  FEMA / NPS / BOEM / HUD / NOAA / USFS / USACE / DOD / US Census Bureau / GSA /
  BLM / USFWS`). These are owned by `soa-dnr` and their items are owned by the
  `AlaskaGeospatialOffice` user, but the items point at the federal tenants'
  own services (e.g. `services2.arcgis.com/FiaPA4ga0iQKduv3/...` for Census).
  The service-URL allowlist in `_validate_service_url` rejects those hosts, so
  the layers would be discoverable but not queryable. Adding them needs a
  deliberate change to the tenant-scoping model documented in
  [SECURITY.md](SECURITY.md).
- **Federal-org groups** (USFS Alaska Region, Tongass, FWS, BLM Hub AK).
  Their items carry federal `orgId`s and are refused by
  `_assert_owned_by_configured_org`.

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

## The same orgs as candidates for sibling forks

The partner orgs above are served *through* this server, scoped to what
they share into the Geoportal catalog. An org's full catalog (everything
it publishes, not only the Geoportal groups) would need its own fork with
its own `org_id`, and the ids below are what that fork would use. The Hub
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
