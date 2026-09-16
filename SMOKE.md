# Live smoke against the State of Alaska Geoportal (`soa-dnr`)

Run on 2026-09-15 with `scripts/local_server.py` on `config.yaml`
(the committed `config-alaska-geoportal.yaml`), read-only, against the live
`https://soa-dnr.maps.arcgis.com/sharing/rest` org. No Lambda involved.

Verified values used by the config:

| | |
|---|---|
| `org_id` | `7HDiw78fcUiM2BWn` |
| Hub site item | `7dd7c86dd0cc40f6a516eb77001977c1` (`https://gis.data.alaska.gov`) |
| Catalog groups in the Hub site | 45 (30-odd owned by partner orgs) |
| `gallery_group_ids` (state-owned, with Feature Services) | `a5055ea72899425c8cc4e01b32658a45`, `18028130a7a14132bd922bcd830f27c6`, `112a233ad29c46ae861fdeb0475aff8b`, `e09f40dee931443485e5f36b55d7dd09`, `705db769b7624af18a0367d58225aed4`, `b5dceabe78cd45108f098e11d6f9738e` |
| Public Feature Services owned by the org | 665 (Feature Services dominate; Map Services are a minority, mostly duplicates of on-prem Feature Services) |

**Content type finding:** the org's public content is overwhelmingly Feature
Services (hosted on `services1.arcgis.com/7HDiw78fcUiM2BWn` and on the on-prem
`arcgis.dnr.alaska.gov` / `geoportal.dggs.dnr.alaska.gov` ArcGIS Servers). The
plan holds. Two things did change from the Anchorage assumptions: the on-prem
host suffix is `.alaska.gov`, and many layers (on-prem and hosted alike) are in
Alaska Albers EPSG:3338 rather than Web Mercator, so the area correction and the
coverage check both handle 3338 now.

## 1. Work-order calls

```text
$ initialize -> {"name": "Alaska Geoportal MCP", "version": "0.1.0"} | instructions bytes: 4752
$ tools/list -> 14 tools: ['find_gis_content', 'browse_gallery', 'search_spatial_layers', 'get_item_details', 'get_layer_schema', 'get_distinct_values', 'search_layers_by_field', 'query_data', 'spatial_query_point', 'spatial_query_polygon', 'aggregate_by_polygon', 'coverage_by_polygon', 'filter_by_polygon', 'find_features_spanning_classifications']



$ find_gis_content({"topic": "wildfire", "limit": 8})   [isError=None]

## State of Alaska GIS Content: 'wildfire'

### Geoportal catalog -- layers, maps & apps (4 found)

_Feature/Map Services here are queryable; Web Maps, Dashboards and Apps are viewers._

**Fire Service Areas Public View**  _Feature Service_ -- ID: `45072954dcd84d78947a4294ed990657`
Spatial data depicting designated fire service areas across Alaska to support wildfire management and emergency response activities.
Tags: Alaska, fire protection, wildfire management, fire service areas, forestry, emergency response
https://soa-dnr.maps.arcgis.com/home/item.html?id=45072954dcd84d78947a4294ed990657
**Land Permit Or Lease**  _Feature Service_ -- ID: `f00277cf01664f8eb2cb7eece25b8256`
This data set was developed to provide the general public with easy access to land records information
as it appears on the State status plats.
Tags: planningCadastre, land estate - permit or lease, mental health trust, competitive lease, oddlot, auction
https://soa-dnr.maps.arcgis.com/home/item.html?id=f00277cf01664f8eb2cb7eece25b8256
**Land Permit Or Lease**  _Map Service_ -- ID: `1fef4a5ac90545438a27ba17e281189d`
This data set was developed to provide the general public with easy access to land records information
as it appears on the State status plats.
Tags: planningCadastre, land estate - permit or lease, mental health trust, competitive lease, oddlot, auction
https://soa-dnr.maps.arcgis.com/home/item.html?id=1fef4a5ac90545438a27ba17e281189d
**Alaska Mushroom Hunter App**  _Web Mapping Application_ -- ID: `be179e560cbc4d1580deb824b4f9db6a`
A public map to aid in the location of mushrooms in fire-scarred areas. Picking on State of Alaska lands may require a permit. It is the end users' responsibility to confirm land ownership.
Tags: mushroom, Alaska, wildland fire, morel, Natural Resources, Forestry
https://soa-dnr.maps.arcgis.com/apps/webappviewer/index.html?id=be179e560cbc4d1580deb824b4f9db6a
### Spatial Layers & Data (8 found)

#### QUERYABLE -- Feature/Map Services (5)
_Use these directly with `query_data`, `get_layer_schema`, `spatial_query_*`._

> **AMBIGUITY WARNING:** multiple queryable layers match this topic. They may be maintained by different agencies (e.g. DNR vs borough vs federal) or cover different subsets or REGIONS (e.g. all trails vs state-park trails only; a statewide layer vs a Southeast-only one). For 'how many?' / 'list all' questions, do NOT silently pick the first one -- either (a) query each layer with `limit=1` and report a breakdown of totals, or (b) ask the user which subset they mean (e.g. 'state-managed', 'a specific borough', 'all combined'). The titles below hint at scope (look for agency or region prefixes like 'ADNR', 'DGGS', 'USFS', 'MatSu', 'SE_').

**CWPP  Areas Public View**  _Feature Service_ -- ID: `9a91ae205d544b53a35842591afcc2a1`
This service offers boundary data for Community Wildfire Protection Plan areas in Alaska, aiding in wildfire management and community planning.
Tags: wildfire protection, Alaska communities, community planning, fire mitigation, Alaska Division of Forestry, BUMO
https://soa-dnr.maps.arcgis.com/home/item.html?id=9a91ae205d544
... [truncated] ...


$ find_gis_content({"topic": "roads", "limit": 8})   [isError=None]

## State of Alaska GIS Content: 'roads'

### Geoportal catalog -- layers, maps & apps (8 found)

_Feature/Map Services here are queryable; Web Maps, Dashboards and Apps are viewers._

**Alaska Forestry Roads Public View**  _Feature Service_ -- ID: `f3298e00f4fa40fdb0d443bb61dcfee3`
This service provides public access to Alaska Division of Forestry road features, including road classification, status, ownership, management, and forestry network information across Alaska.
Tags: Alaska forestry roads, road management, Alaska Division of Forestry, road condition, forest road network, state forest roads
https://soa-dnr.maps.arcgis.com/home/item.html?id=f3298e00f4fa40fdb0d443bb61dcfee3
**State Park Roads**  _Feature Service_ -- ID: `83bd9717139d4c26aeb016e624ea23fd`
This dataset is for mapping and for identifying areas available for public recreation.
Tags: ASP, Alaska State Parks, ADNR, Alaska DNR, Alaska, DNR
https://soa-dnr.maps.arcgis.com/home/item.html?id=83bd9717139d4c26aeb016e624ea23fd
**Forestry Mile Posts Public View**  _Feature Service_ -- ID: `374ba939dbd545608e760b82cd4d5ceb`
This service displays mile posts associated with Alaska Division of Forestry roads.
Tags: Alaska, DOF, Mileposts, infrastructure, roads, forestry
https://soa-dnr.maps.arcgis.com/home/item.html?id=374ba939dbd545608e760b82cd4d5ceb
**Alaska State Park Boundary and Facility**  _Feature Service_ -- ID: `8a439547724041a5aa9045d2c8f8fd3b`
Web service showing Alaska State Park managed boundaries, facilities, trails and roads.
Tags: Alaska, ASP, Park Boundary, Alaska State Parks, Recreational, trail
https://soa-dnr.maps.arcgis.com/home/item.html?id=8a439547724041a5aa9045d2c8f8fd3b
**Alaska Division of Forestry Resources Web Map New Viewer**  _Web Map_ -- ID: `d093457405e9415d9ec538534e8a9ba8`
This map shows the public the Division of Forestry timber sales, terminated, current, and proposed.
Tags: resources, timbersales, forest roads, Infrastructure, BUMO
https://soa-dnr.maps.arcgis.com/home/item.html?id=d093457405e9415d9ec538534e8a9ba8
**Alaska DNR Forestry Resources Viewer**  _Web Experience_ -- ID: `82e11f6660d34b568319643cadee80ab`
A web experience app to display the authoritative data for the Alaska DNR Division Forestry Resources
Tags: Resources, Timber Sales, forest roads, DNR Featured Content
https://experience.arcgis.com/experience/82e11f6660d34b568319643cadee80ab
**Forestry Culverts Public View**  _Feature Service_ -- ID: `0921c900c32a4c5a81c672c98d68ed47`
To display culverts on non-federal forest roads which must be in compliance with the Alaska Forest Resources and Practices Act.
Tags: Culverts, DOF, Alaska, DNR, Fish passage, Infrastructure
https://soa-dnr.maps.arcgis.com/home/item.html?id=0921c900c32a4c5a81c672c98d68ed47
**Tundra Travel**  _Web Map_ -- ID: `03a3ea2b3ca146dc9a71f7bcfa37e644`
Map of north slope tundra travel regions. This map is displayed on the public tundra travel webpage https://dnr.alaska.gov/mlw/tundra-travel/. Based on soil temperature and snow depth data collected at the 20 monitoring stations the tundra areas will either be open of closed. The color of the polygons for
... [truncated] ...


$ get_layer_schema({"item_id": "f3298e00f4fa40fdb0d443bb61dcfee3"})   [isError=None]

## Schema: Alaska Forestry Roads Public View
**Layer:** Forestry Roads - Public view  |  **Geometry:** esriGeometryPolyline  |  **Max Records:** 2000
**Service URL:** https://services1.arcgis.com/7HDiw78fcUiM2BWn/arcgis/rest/services/Forestry_Roads_-_Public_View/FeatureServer/0

### Fields (16)

| Field Name | Alias | Type |
|---|---|---|
| `OBJECTID` | OBJECTID | OID |
| `forestry_roads_area` | AREA | String |
| `class` | CLASS | String |
| `rd_status` | Road Designation | String |
| `season` | SEASON | String |
| `own_type` | OWN_TYPE | String |
| `manager` | MANAGER | String |
| `mainline` | MAINLINE | String |
| `globalid` | GLOBALID | GlobalID |
| `Region` | Region | String |
| `Resource_Area_Subregion` | Road Network  | String |
| `SegmentLengthMiles` | Segment Length Miles | Double |
| `RoadSegmentLengthFeet` | Road Segment Length Feet | Integer |
| `ROAD_NUMBER` | Road Number | String |
| `RoadSegment` | Road Segment | Integer |
| `road_name` | ROAD_NAME | String |

### Coded Domains
- **d_dofArea**: SSE=Southern South East, NSE=Northern South East, KenKod=Kenai Kodiak , MatSu=MatSu, ValCopRiv=Valdez Copper River , Tok=Tok , DA=Delta, FA=Fairbanks, SW=South West 
- **d_dofrdClass_1**: Primary=Primary, Secondary=Secondary, Spur=Spur, Winter=Winter
- **d_dofrdStatus**: Active=Active, Inactive=Inactive, Closed=Closed, Proposed=Proposed, NonFRPA=Non-FRPA, Conceptual=Conceptual
- **d_dofSeason**: All=All, Summer=Summer, Winter=Winter
- **d_dofOwner**: Federal=Federal, State=State, Private=Private, MuniBoro=Municipal or Borough, AKNative=Alaska Native, MHT=Mental Health Trust, University=University
- **d_dofManager**: AMHT=AMHT, UNI=UNI, USFW=USFW, USFS=USFS, BLM=BLM, BIA=BIA, NPS=NPS, DMLW=DMLW, DFFP=DFFP, DPOR=DPOR, ADFG=ADFG, BORO=BORO, MUN=MUN, ADOA=ADOA, NV=NV ... (+3 more)
- **d_dofrdMainline**: 1=Y, 0=N
- **Forestry Roads_Region_0524032f-ae12-4d9d-8c87-080f30379c65**: 0=Northern, 1=Coastal
- **Forestry Roads_Resource_Area_Subregion_fd3bdf5d-7228-44c8-84de-f057ea77a679**: 0=Nenana Ridge Area, 1=Skinny Dicks Road Area, 2=Bonanza Creek Road Area, 3=Zasada Road Area, 4=Rosie Creek Road Area, 5=Parks Highway Road Area, 6=Standard Creek Road Area, 7=Standard East Road Area, 8=Cache Creek Road Area, 9=Big Bend Road Area, 10=Jenny M Creek Road Area, 11=Two Rivers Road Area, 12=Midway Island Road Area, 13=Mosquito Creek Road Area, 14=Little Delta Road Area ... (+13 more)

---
**NEXT STEPS:** use the field names above in `query_data` -- field names are CASE-SENSITIVE (use the exact `Field Name` column, not the alias). Quote string literals with single quotes. For text searches prefer `LIKE '%substring%'` over `=` (which requires the full exact value).

Example: `query_data(item_id='f3298e00f4fa40fdb0d443bb61dcfee3', where="forestry_roads_area LIKE '%foo%'", limit=10)`

To just COUNT matches, set `limit=1` and read the TOTAL COUNT line in the response.

_Retrieved: 2026-09-15T21:20:49Z_



$ query_data({"item_id": "f3298e00f4fa40fdb0d443bb61dcfee3", "result_record_count": 5, "limit": 5})   [isError=None]

Source: https://services1.arcgis.com/7HDiw78fcUiM2BWn/arcgis/rest/services/Forestry_Roads_-_Public_View/FeatureServer/0
Query: where='1=1', outFields='*', resultRecordCount=5
Retrieved: 2026-09-15T21:20:49Z
**TRUNCATED:** returned 5 of 3,190 matching records (limit=5). The records below are a SAMPLE -- do not generalize counts or percentages from them. Use the TOTAL COUNT line below for 'how many?' questions, or narrow the WHERE clause to get a complete listing.
**LIMITED COVERAGE:** this layer's extent covers ~28% of Alaska. Confirm the question's area of interest falls inside the layer's coverage -- a layer named for a region or map quad does not cover the state.

Returned 5 of 3,190 total record(s) (limit: 5).
TOTAL COUNT (records matching the WHERE clause): 3,190. This is the answer to 'how many?' -- use it directly instead of counting the records below.
**GRAIN NOTE (polyline layer):** the count above is the number of LINE SEGMENTS (geometry features), NOT the number of unique named entities. A single named trail, road, or route is typically stored as multiple connected segments -- so '3,190 records' usually means fewer than 3,190 distinct named features. When answering the user, say e.g. '3,190 trail segments' rather than '3,190 trails'. To count unique named entities, call `get_layer_schema(item_id='f3298e00f4fa40fdb0d443bb61dcfee3')` to find the name/identifier field, then `get_distinct_values` on it to count unique entities.

Record 1:
  OBJECTID: 5
  forestry_roads_area: SSE (Southern South East)
  class: Primary
  rd_status: Active
  season: All
  own_type: State
  manager: DFFP
  mainline: None
  globalid: 9b984524-8358-4987-8c4d-c489786cedd2
  Region: 1 (Coastal)
  Resource_Area_Subregion: None
  SegmentLengthMiles: 0.0011445611761762555
  RoadSegmentLengthFeet: 6
  ROAD_NUMBER: 8000000
  RoadSegment: None
  road_name: Behm Cannal

Record 2:
  OBJECTID: 6
  forestry_roads_area: SSE (Southern South East)
  class: Spur
  rd_status: Inactive
  season: All
  own_type: State
  manager: DFFP
  mainline: None
  globalid: a2a6f1fb-e0f1-4103-a35b-ce99dbf610fd
  Region: 1 (Coastal)
  Resource_Area_Subregion: None
  SegmentLengthMiles: 0.5706414176256941
  RoadSegmentLengthFeet: 3013
  ROAD_NUMBER: None
  RoadSegment: None
  road_name: None

Record 3:
  OBJECTID: 11
  forestry_roads_area: SSE (Southern South East)
  class: Primary
  rd_status: NonFRPA (Non-FRPA)
  season: All
  own_type: State
  manager: USFS
  mainline: None
  globalid: 337a67c4-1009-4f8a-9031-cf9f18ea9d54
  Region: 1 (Coastal)
  Resource_Area_Subregion: None
  SegmentLengthMiles: 2.192019617089837
  RoadSegmentLengthFeet: 11574
  ROAD_NUMBER: 1520000
  RoadSegment: None
  road_name: Edna Bay

Record 4:
  OBJECTID: 13
  forestry_roads_area: SSE (Southern South East)
  class: Primary
  rd_status: Inactive
  season: All
  own_type: State
  manager: USFS
  mainline: None
  globalid: 7edd13d5-532b-4bad-a04d-cc8b866c84a2
  Region: 1 (Coastal)
  Resource_Area_Subregion: None
  SegmentLengthMiles: 0.5306534128365639
  RoadSegmentLengthFeet: 2802
  ROAD_NUMBER: 3
... [truncated] ...


$ spatial_query_point({"item_id": "45072954dcd84d78947a4294ed990657", "lon": -147.72, "lat": 64.84})   [isError=None]

**DATA FRESHNESS:** layer last edited 2025-06-09 (1.3 years ago). Confirm this matches the recency the question needs.
**LIMITED COVERAGE:** this layer's extent covers ~3% of Alaska. Confirm the question's area of interest falls inside the layer's coverage -- a layer named for a region or map quad does not cover the state.

Returned 1 record(s) (limit: 10).

Record 1:
  objectid: 15
  fire_service_area_name: CITY OF FAIRBANKS
  acres: 7811.63183594
  borough: FNSB (Fairbanks North Star)
  globalid: fcf4eb4e-16f7-4b3c-9a37-fde92d6a28d8
  created_user: taruszkowski_for
  created_date: 2020-09-01T19:43:53Z
  last_edited_user: taruszkowski_for
  last_edited_date: 2020-09-01T19:43:53Z
  Shape__Area: 31612552.744293213
  Shape__Length: 55629.51584727947


_Retrieved: 2026-09-15T21:20:50Z_



$ spatial_query_point({"item_id": "458be3d8aafa47cd882af05cee983f6b", "lon": -147.72, "lat": 64.84})   [isError=None]

Returned 1 record(s) (limit: 10).

Record 1:
  OBJECTID: 89280168
  parcel_id: 9999999
  owner: None
  alt_owner: None
  property_type: Roadway
  property_use: None
  land_value: None
  building_value: None
  total_value: None
  local_gov: Fairbanks North Star Borough
  datetime_processed: 2026-09-15T08:40:45.537+00:00
  feature_id: 4738377272017703475
  Shape__Area: 23103.625
  Shape__Length: 1433.9939246126862
  GlobalID: aa68fa8f-8fd5-43dd-99e6-77e4fbaf3e7e


_Retrieved: 2026-09-15T21:20:53Z_



$ browse_gallery({"keyword": "geology", "limit": 5})   [isError=None]

## State of Alaska GIS Gallery -- 'geology' (5 items)

**Erosion exposure assessment of infrastructure in Alaska coastal communities**  _Feature Service_ -- ID: `db176e04b0b54f7894049f55aeefb548`
Alaska communities located along coastlines and tidally influenced rivers are vulnerable to coastal erosion. These communities face advanced planning decisions, such as implementing shore protection or moving infrastructure. This work aims to provide quantitative erosion exposure data to Alaskans that can be combined with local knowledge and evidence for developing hazard mitigation plans and strategies to address erosion.
Tags: environment, geoscientificInformation, planningCadastre, structure, transportation, utilitiesCommunication
https://soa-dnr.maps.arcgis.com/home/item.html?id=db176e04b0b54f7894049f55aeefb548
**Alaska Volcanoes Web Map**  _Web Map_ -- ID: `4f9ad53b45f1463b863a44fc0e31466e`
The purpose of this webmap is to document the location and most recent eruptive events of the historically active volcanoes throughout Alaska.
Tags: Active Volcanoes, Geologic Hazards, Geology, Historic Eruption, Volcanic Eruption, Volcano Hazards
https://soa-dnr.maps.arcgis.com/home/item.html?id=4f9ad53b45f1463b863a44fc0e31466e
**Seismic Shothole Sample data National Petroleum Reserve Alaska (NPRA)**  _Feature Service_ -- ID: `ea3ea5f727c84a168d1cb2204ac36817`
Seismic Shothole Samples with related shotlines in the NPRA. Shothole Samples points include a link to a photo of the drill log card and geologic sample. This photo can be viewed in the popup.
Tags: Aggregate, Archive, Bedrock, Bulk Sample, Clay, Coal
https://soa-dnr.maps.arcgis.com/home/item.html?id=ea3ea5f727c84a168d1cb2204ac36817
**Geologic Map of Alaska**  _Vector Tile Service_ -- ID: `7a6f5ce460304d3c847674eae62fe363`
This data set represents part of a systematic effort to release geologic
map data for the United States in a uniform manner.  Geologic data in
this data set has been compiled from a wide variety of sources,
published and unpublished, ranging from state and regional geologic
map to field mapping.
Tags: geology, Alaska, USGS
https://soa-dnr.maps.arcgis.com/home/item.html?id=7a6f5ce460304d3c847674eae62fe363
**Map Index**  _Feature Service_ -- ID: `f72106ef599d41e7879beaf0ec3b9e0e`
Geologic map outlines of DGGS and USGS geological maps. Excludes geophysical maps.
Tags: geologic maps, DGGS, GERILA, neptune
https://soa-dnr.maps.arcgis.com/home/item.html?id=f72106ef599d41e7879beaf0ec3b9e0e

---
**Only _Feature Service_ / _Map Service_ items above are queryable.** Web Maps, Dashboards, and Apps are VIEWERS and cannot be passed to `query_data` for record counts or filtered lists. If the user asked 'how many?' or 'list X' and no queryable item is listed, call `find_gis_content(topic=...)` to find the underlying Feature Service instead.
_Full gallery: https://gis.data.alaska.gov/search_

_Retrieved: 2026-09-15T21:20:53Z_
```

## 2. `scripts/smoke_prod.py` (19 checks, `SMOKE_URL=http://localhost:8000/mcp`)

```text
[PASS] ping -- {}
[PASS] initialize -- {"serverInfo": {"name": "Alaska Geoportal MCP", "version": "0.1.0"}, "protocolVersion": "2025-03-26"}
[PASS] tools/list -- 14 tools
[PASS] find_gis_content(wildfire) -- 6278 chars
[PASS] search_spatial_layers -- picked f3298e00f4fa40fdb0d443bb61dcfee3
[PASS] get_item_details -- 3131 chars
[PASS] get_layer_schema -- found fire_service_area_name
[PASS] query_data count -- **TRUNCATED:** returned 1 of 32 matching records (limit=1). The records below ar
[PASS] query_data listing (no stale reminder) -- trimmed reminder absent
[PASS] get_distinct_values -- borough codes listed
[PASS] spatial_query_point (Fairbanks) -- **DATA FRESHNESS:** layer last edited 2025-06-09 (1.3 years ago). Confirm this m
[PASS] on-prem DNR layer (arcgis.dnr.alaska.gov) -- **TRUNCATED:** returned 1 of 2,586 matching records (limit=1). The records below
[PASS] error handling (bad field -> recovery hint) -- Field 'Nonexistent_Field' not found in this layer. Call get_layer_schema to see all availa
[PASS] tenant scoping (partner-tenant service rejected) -- service URL host 'services.arcgis.com' (path '/r4A0V7UzH9fcLVvv/arcgis/rest/services/Funct
[PASS] point-layer target via filter_item_id -- **LIMITED COVERAGE:** this layer's extent covers ~23% of Alaska. Confirm the que
[PASS] polygon target via inline geometry -- **DATA FRESHNESS:** layer last edited 2025-06-09 (1.3 years ago). Confirm this m
[PASS] search_layers_by_field -- ## State of Alaska Layers with 'segmentlengthmiles' Fields

Found 1 layer(s) wit
[PASS] polyline source aggregation (road miles by borough) -- buckets=9 unmatched=1058 source=3190
[PASS] statewide parcels count (FNSB) -- **TRUNCATED:** returned 1 of 63,888 matching records (limit=1). The records belo

=== SUMMARY ===
19/19 checks passed
```

## 3. `scripts/smoke_aggregate.py` (direct plugin, no HTTP)

```text
### aggregate_by_polygon (forestry road miles by borough) ###

success= True err= None
## Aggregation: f3298e00f4fa40fdb0d443bb61dcfee3 -> 72868306fe0648d49cd653bcdf22ea0e
**City:** State of Alaska  |  **Group field:** `NAME`
**Source geometry:** esriGeometryPolyline  |  **Centroid mode:** auto  |  **Overlap policy:** first_match  |  **Proximity buffer:** none
**Source features:** 3,190  |  **Buckets:** 9  |  **Unmatched:** 1,058

| Group | Count | SegmentLengthMiles |
|---|---|---|
| Kenai Peninsula Borough | 863 | 577.8109768291323 |
| Petersburg Borough | 485 | 198.2287685833419 |
| Fairbanks North Star Borough | 482 | 442.2107131590311 |
| Matanuska-Susitna Borough | 82 | 50.61627484787648 |
| Haines Borough | 80 | 91.04568870991105 |
| City & Borough of Wrangell | 55 | 38.838663353874274 |
| City & Borough of Yakutat | 39 | 35.32147443602646 |
| Ketchikan Gateway Borough | 36 | 53.19404781829849 |
| Denali Borough | 10 | 5.426745681904263 |

_1,058 source feature(s) fell outside every aggregation polygon. This usually means the aggregation layer does not cover those features (e.g. the Unorganized Borough when bucketing by borough) or stray coordinates._

_Retrieved: 2026-09-15T21:21:19Z_

### filter_by_polygon (forestry bridges in the Mat-Su) ###

success= True err= None
## Filter: e9bfc953765d4b279d3316de7967cc08 inside 72868306fe0648d49cd653bcdf22ea0e where "NAME='Matanuska-Susitna Borough'"
**City:** State of Alaska  |  **Container polygons matched:** 1

Returned 1 record(s) (limit: 5).

Record 1:
  OBJECTID: 14
  AreaOffice: 4 (Matsu)
  survey_waypoint: 173
  Structure_Type: Modular Steel
  Manufacturer: Big R
  Install_yr: 2008
  SurveyDate: 2015-08-25
  Land_owner: Department of Natural Resources
  Location: Willer-Cash
  Road_Segment: WKS0001
  Length: 37
  Width: 16
  Longitude: -149.844
  Latitude: 61.837
  Relief_culvert_on_approach: NA
  One_end_log_anchored: NA
  Bank_protect_from_erosion: 4
  Curbs_filter_fabric_installed: NA
  Min_disturb_bank_stream: 4
  Not_encroach_anadromous_stream: 5
  Anad_res: AWC (Anadromous Waters Catalog)
  comments: Iron Creek, Big R.  Willer-Cash
  Stream_Name: IRON CREEK
  GlobalID: a49bc803-3ef5-4168-9de1-dd321c3021bf
  BRIDGE_NAME: Iron Creek Bridge
  DOT_INSPECTION_NO: None
  DOT_INSPECTION_DATE: None


_Retrieved: 2026-09-15T21:21:20Z_

### filter_by_polygon (typo -> 0-polygon error) ###

success= True err= None
Error: container_where "NAME='Matanuska-Sustina Borough'" matched 0 polygons on container layer `72868306fe0648d49cd653bcdf22ea0e`. Did you misspell a name? Try `search_spatial_layers` or `query_data` to browse valid values for the container field.

_Retrieved: 2026-09-15T21:21:21Z_
```
