"""Smoke test the aggregate_by_polygon / filter_by_polygon tools
against the real State of Alaska Geoportal (soa-dnr) org. Read-only."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from plugins.alaska_geoportal.plugin import AlaskaGeoportalPlugin  # noqa: E402


CONFIG = {
    "portal_base_url": "https://soa-dnr.maps.arcgis.com/sharing/rest",
    "gallery_group_ids": [
        "a5055ea72899425c8cc4e01b32658a45",
        "18028130a7a14132bd922bcd830f27c6",
    ],
    "org_id": "7HDiw78fcUiM2BWn",
    "city_name": "State of Alaska",
    "gallery_url": "https://gis.data.alaska.gov/search",
    "timeout": 30,
}

# Verified 2026-09-15 (see docs/ALASKA_SOURCES.md for the probe).
FORESTRY_ROADS = "f3298e00f4fa40fdb0d443bb61dcfee3"   # POLYLINE, 3,190 rows
FORESTRY_BRIDGES = "e9bfc953765d4b279d3316de7967cc08"  # POINT, 183 rows
BOROUGHS = "72868306fe0648d49cd653bcdf22ea0e"          # CLG_borough_POLY


async def main() -> None:
    plugin = AlaskaGeoportalPlugin(CONFIG)
    ok = await plugin.initialize()
    assert ok, "plugin failed to initialize"
    try:
        print("\n### aggregate_by_polygon (forestry road miles by borough) ###\n")
        r = await plugin.execute_tool(
            "aggregate_by_polygon",
            {
                "source_item_id": FORESTRY_ROADS,
                "aggregation_item_id": BOROUGHS,
                "group_by_field": "NAME",
                "sum_fields": ["SegmentLengthMiles"],
            },
        )
        print("success=", r.success, "err=", r.error_message)
        print(r.content[0]["text"] if r.content else "(no content)")

        print("\n### filter_by_polygon (forestry bridges in the Mat-Su) ###\n")
        r2 = await plugin.execute_tool(
            "filter_by_polygon",
            {
                "source_item_id": FORESTRY_BRIDGES,
                "container_item_id": BOROUGHS,
                "container_where": "NAME='Matanuska-Susitna Borough'",
                "limit": 5,
            },
        )
        print("success=", r2.success, "err=", r2.error_message)
        print(r2.content[0]["text"] if r2.content else "(no content)")

        print("\n### filter_by_polygon (typo -> 0-polygon error) ###\n")
        r3 = await plugin.execute_tool(
            "filter_by_polygon",
            {
                "source_item_id": FORESTRY_BRIDGES,
                "container_item_id": BOROUGHS,
                "container_where": "NAME='Matanuska-Sustina Borough'",
                "limit": 5,
            },
        )
        print("success=", r3.success, "err=", r3.error_message)
        print(r3.content[0]["text"] if r3.content else "(no content)")
    finally:
        await plugin.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
