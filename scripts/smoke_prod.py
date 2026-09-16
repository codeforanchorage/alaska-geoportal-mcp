"""Ad-hoc smoke test for the Alaska Geoportal MCP server.

Exercises the JSON-RPC surface and the core tool chain end-to-end
against a running server -- the prod API Gateway by default, or a local
`scripts/local_server.py` via SMOKE_URL=http://localhost:8000/mcp.
Read-only; paces calls to stay under the API Gateway rate limit (5 rps)
and WAF per-IP cap (300/5min).
"""

import json
import os
import re
import sys
import time
import urllib.request

# Prod API Gateway (deployed 2026-09-15). Override with SMOKE_URL, e.g.
# http://localhost:8000/mcp for a local server or the custom domain
# https://alaska-geoportal.codeforanchorage.org/mcp once DNS is live.
URL = os.environ.get(
    "SMOKE_URL", "https://ae6gj7yvfg.execute-api.us-west-2.amazonaws.com/prod/mcp"
)
_id = 0
PASS = "PASS"
FAIL = "FAIL"
results = []


def rpc(method, params=None):
    global _id
    _id += 1
    payload = {"jsonrpc": "2.0", "id": _id, "method": method}
    if params is not None:
        payload["params"] = params
    req = urllib.request.Request(
        URL,
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "MCP-Protocol-Version": "2025-06-18",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        body = json.loads(r.read().decode())
    time.sleep(0.4)  # pace under 5 rps
    return body


def call_tool(name, args):
    return rpc("tools/call", {"name": f"alaska_geoportal__{name}", "arguments": args})


def text_of(resp):
    return resp["result"]["content"][0]["text"]


def check(label, ok, detail=""):
    results.append((label, ok))
    mark = PASS if ok else FAIL
    print(f"[{mark}] {label}" + (f" -- {detail}" if detail else ""))


# Verified 2026-09-15 against the live soa-dnr org (docs/ALASKA_SOURCES.md).
CWPP_AREAS = "9a91ae205d544b53a35842591afcc2a1"        # POLYGON, 12 rows
FIRE_SERVICE_AREAS = "45072954dcd84d78947a4294ed990657"  # POLYGON, 32 rows
BOROUGHS = "72868306fe0648d49cd653bcdf22ea0e"           # CLG_borough_POLY
FORESTRY_ROADS = "f3298e00f4fa40fdb0d443bb61dcfee3"     # POLYLINE, 3,190 rows
FORESTRY_BRIDGES = "e9bfc953765d4b279d3316de7967cc08"   # POINT, 183 rows
AK_PARCELS = "458be3d8aafa47cd882af05cee983f6b"         # POLYGON, ~415k rows
RS2477_TRAILS = "f97ec4306fb14ed59c71b02ee8cf0f47"      # on-prem DNR, EPSG:3338
# A DOT&PF layer catalogued in the Geoportal whose service lives in the
# DOT tenant (services.arcgis.com/r4A0V7UzH9fcLVvv/...). Whether the item
# record is state-owned or not, it must be REJECTED: by the ownership
# check if the orgId differs, else by the service-URL allowlist.
DOT_ROADS_OTHER_TENANT = "bbe5cd90520e41348eef242a8f754172"

# 1. ping
try:
    r = rpc("ping")
    check("ping", r.get("result") == {} and "error" not in r, str(r.get("result")))
except Exception as e:
    check("ping", False, repr(e))

# 2. initialize
try:
    r = rpc(
        "initialize",
        {"protocolVersion": "2025-03-26", "capabilities": {},
         "clientInfo": {"name": "smoke", "version": "1.0"}},
    )
    si = r["result"]["serverInfo"]
    pv = r["result"]["protocolVersion"]
    check(
        "initialize",
        si["name"] == "Alaska Geoportal MCP" and pv == "2025-03-26",
        json.dumps({"serverInfo": si, "protocolVersion": pv}),
    )
except Exception as e:
    check("initialize", False, repr(e))

# 3. tools/list -- 14 generic tools, no MOA parcel tools
try:
    r = rpc("tools/list")
    tools = [t["name"] for t in r["result"]["tools"]]
    check(
        "tools/list",
        len(tools) == 14
        and "alaska_geoportal__find_parcel" not in tools
        and "alaska_geoportal__footprint_for_parcel" not in tools,
        f"{len(tools)} tools",
    )
except Exception as e:
    check("tools/list", False, repr(e))

# 4. find_gis_content (discovery)
try:
    r = call_tool("find_gis_content", {"topic": "wildfire", "limit": 6})
    t = text_of(r)
    check("find_gis_content(wildfire)", "ID:" in t, f"{len(t)} chars")
except Exception as e:
    check("find_gis_content(wildfire)", False, repr(e))

# 5. search_spatial_layers -> grab a Feature Service id
fs_id = None
try:
    r = call_tool(
        "search_spatial_layers",
        {"query": "roads", "layer_type": "layers", "limit": 8},
    )
    t = text_of(r)
    m = re.search(r"_Feature Service_\s*--\s*ID: `([0-9a-f]{32})`", t)
    fs_id = m.group(1) if m else None
    check("search_spatial_layers", fs_id is not None, f"picked {fs_id}")
except Exception as e:
    check("search_spatial_layers", False, repr(e))

# 6. get_item_details
try:
    r = call_tool("get_item_details", {"item_id": FIRE_SERVICE_AREAS})
    t = text_of(r)
    check("get_item_details", "ID:" in t and "Type:" in t, f"{len(t)} chars")
except Exception as e:
    check("get_item_details", False, repr(e))

# 7. get_layer_schema -> known field
try:
    r = call_tool("get_layer_schema", {"item_id": FIRE_SERVICE_AREAS})
    t = text_of(r)
    check("get_layer_schema", "fire_service_area_name" in t, "found fire_service_area_name")
except Exception as e:
    check("get_layer_schema", False, repr(e))

# 8. query_data count (limit=1 -> TOTAL COUNT)
try:
    r = call_tool("query_data", {"item_id": FIRE_SERVICE_AREAS, "limit": 1})
    t = text_of(r)
    check("query_data count", "TOTAL COUNT" in t, t.split("\n")[3][:80] if len(t.split("\n")) > 3 else t[:80])
except Exception as e:
    check("query_data count", False, repr(e))

# 9. query_data listing (limit=3)
try:
    r = call_tool("query_data", {"item_id": FIRE_SERVICE_AREAS, "limit": 3})
    t = text_of(r)
    ok = "Record 1:" in t and "results above are a sample" not in t
    check("query_data listing (no stale reminder)", ok,
          "trimmed reminder absent" if ok else "stale text present")
except Exception as e:
    check("query_data listing (no stale reminder)", False, repr(e))

# 10. get_distinct_values
try:
    r = call_tool("get_distinct_values", {"item_id": FIRE_SERVICE_AREAS, "field": "borough", "limit": 10})
    t = text_of(r)
    check("get_distinct_values", "FNSB" in t, "borough codes listed")
except Exception as e:
    check("get_distinct_values", False, repr(e))

# 11. spatial_query_point on a polygon layer, point in Fairbanks
try:
    r = call_tool(
        "spatial_query_point",
        {"item_id": FIRE_SERVICE_AREAS, "lon": -147.72, "lat": 64.84},
    )
    t = text_of(r)
    check("spatial_query_point (Fairbanks)", "CITY OF FAIRBANKS" in t, t.split("\n")[0][:80])
except Exception as e:
    check("spatial_query_point (Fairbanks)", False, repr(e))

# 12. on-prem DNR ArcGIS Server layer (EPSG:3338) is queryable
try:
    r = call_tool("query_data", {"item_id": RS2477_TRAILS, "limit": 1})
    t = text_of(r)
    check("on-prem DNR layer (arcgis.dnr.alaska.gov)", "TOTAL COUNT" in t, t.split("\n")[3][:80] if len(t.split("\n")) > 3 else t[:80])
except Exception as e:
    check("on-prem DNR layer (arcgis.dnr.alaska.gov)", False, repr(e))

# 13. error handling: bad field -> schema recovery hint
try:
    r = call_tool("query_data", {"item_id": FIRE_SERVICE_AREAS, "where": "Nonexistent_Field='x'"})
    t = text_of(r)
    ok = ("get_layer_schema" in t) or ("does not exist" in t) or ("CASE-SENSITIVE" in t)
    check("error handling (bad field -> recovery hint)", ok, t[:90])
except Exception as e:
    check("error handling (bad field -> recovery hint)", False, repr(e))

# 14. tenant scoping: a partner-tenant service catalogued in the Geoportal is refused
try:
    r = call_tool("query_data", {"item_id": DOT_ROADS_OTHER_TENANT, "limit": 1})
    res = r.get("result", {})
    t = text_of(r) if res.get("content") else json.dumps(res)
    ok = bool(res.get("isError")) and (
        "not the configured org" in t
        or "refusing to proxy other ArcGIS Online tenants" in t
    )
    check("tenant scoping (partner-tenant service rejected)", ok, t[:90])
except Exception as e:
    check("tenant scoping (partner-tenant service rejected)", False, repr(e))

# 15. spatial_query_polygon against a POINT target via filter_item_id
try:
    r = call_tool("spatial_query_polygon", {
        "item_id": FORESTRY_BRIDGES,
        "filter_item_id": BOROUGHS,
        "filter_where": "NAME='Matanuska-Susitna Borough'",
        "limit": 5,
    })
    t = text_of(r)
    ok = not r.get("result", {}).get("isError") and "No features" not in t
    check("point-layer target via filter_item_id", ok, t[:80])
except Exception as e:
    check("point-layer target via filter_item_id", False, repr(e))

# 16. the same, via inline filter_geometry (a separate code path)
try:
    r = call_tool("spatial_query_polygon", {
        "item_id": FIRE_SERVICE_AREAS,
        "filter_geometry": {
            "type": "Polygon",
            "coordinates": [[[-148.0, 64.7], [-148.0, 65.0],
                             [-147.4, 65.0], [-147.4, 64.7],
                             [-148.0, 64.7]]],
        },
        "limit": 5,
    })
    t = text_of(r)
    ok = not r.get("result", {}).get("isError") and "No features" not in t
    check("polygon target via inline geometry", ok, t[:80])
except Exception as e:
    check("polygon target via inline geometry", False, repr(e))

# 17. search_layers_by_field
try:
    r = call_tool("search_layers_by_field", {"field_keyword": "SegmentLengthMiles", "service_keyword": "forestry roads"})
    t = text_of(r)
    check("search_layers_by_field", "Forestry" in t, t[:80])
except Exception as e:
    check("search_layers_by_field", False, repr(e))

# 18. aggregate_by_polygon with a POLYLINE source (road miles per borough)
try:
    r = call_tool("aggregate_by_polygon", {
        "source_item_id": FORESTRY_ROADS,
        "aggregation_item_id": BOROUGHS,
        "group_by_field": "NAME",
        "sum_fields": ["SegmentLengthMiles"],
    })
    sc = r.get("result", {}).get("structuredContent") or {}
    summ = sc.get("summary", {})
    ok = (
        not r.get("result", {}).get("isError")
        and (summ.get("buckets") or 0) >= 1
        and (summ.get("source_features") or 0) > 0
    )
    check("polyline source aggregation (road miles by borough)", ok,
          f"buckets={summ.get('buckets')} unmatched={summ.get('unmatched')} "
          f"source={summ.get('source_features')}")
except Exception as e:
    check("polyline source aggregation (road miles by borough)", False, repr(e))

# 19. statewide parcels: count-only on a 415k-row layer stays fast
try:
    r = call_tool("query_data", {
        "item_id": AK_PARCELS,
        "where": "local_gov='Fairbanks North Star Borough'",
        "limit": 1,
    })
    t = text_of(r)
    check("statewide parcels count (FNSB)", "TOTAL COUNT" in t, t.split("\n")[3][:80] if len(t.split("\n")) > 3 else t[:80])
except Exception as e:
    check("statewide parcels count (FNSB)", False, repr(e))


print("\n=== SUMMARY ===")
n_pass = sum(1 for _, ok in results if ok)
print(f"{n_pass}/{len(results)} checks passed")
sys.exit(0 if n_pass == len(results) else 1)
