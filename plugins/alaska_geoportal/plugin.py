"""Alaska Geoportal plugin for OpenContext.

Access to the State of Alaska Geoportal -- the Alaska Geospatial
Office's ArcGIS Online catalog, plus the Alaska partner organizations
listed in config -- via the ArcGIS Portal REST API. Everything a GIS
deployment shares (discovery, schema, attribute and spatial queries, the
polygon analytics, upstream resilience, structured output) lives in the
`opencontext-arcgis-hub` package (`arcgis_hub.plugin.ArcGISHubPlugin`).
This module holds only what is specific to Alaska: statewide wording,
the two-box state extent across the antimeridian, Alaska Albers
(EPSG:3338), the partner-org refusal messages, and the explanation of
ArcGIS Server's "Unable to complete operation".

To change shared behaviour, change it in opencontext-arcgis-hub, tag a
release, and move the pin in requirements.txt / pyproject.toml.
"""

import logging
import math
import re
from typing import Any, Dict, List, Optional, Tuple

from arcgis_hub.plugin import (  # noqa: F401  (re-exported for tests)
    RETRY_MIN_REMAINING_S,
    TOOL_CALL_BUDGET_S,
    ArcGISHubPlugin,
    UpstreamTimeoutError,
    _call_deadline,
)
from plugins.alaska_geoportal.config_schema import (
    AlaskaGeoportalPluginConfig,
)

logger = logging.getLogger(__name__)


class AlaskaGeoportalPlugin(ArcGISHubPlugin):
    """Plugin for accessing State of Alaska Geoportal GIS data."""

    plugin_name = "alaska_geoportal"
    plugin_version = "1.1.0"

    CONFIG_CLASS = AlaskaGeoportalPluginConfig
    DISPLAY_NAME = "Alaska Geoportal"
    REGION_NAME = "Alaska"

    # On-prem State of Alaska hosts we'll proxy without further checks.
    # Partner on-prem hosts are exact matches from partner_orgs[].hosts.
    ONPREM_HOST_SUFFIXES = (".alaska.gov",)

    TEXT = {
        **ArcGISHubPlugin.TEXT,
        "limited_coverage_hint_long": (
            " -- a layer named for a region "
            "(Southeast, Mat-Su, North Slope) or a "
            "map quad does not cover the state"
        ),
        "limited_coverage_hint_short": (
            " -- a layer named for a region "
            "or map quad does not cover the state"
        ),
        "ambiguity_warning": (
            "\n> **AMBIGUITY WARNING:** multiple queryable "
            "layers match this topic. They may be maintained "
            "by different agencies (e.g. DNR vs borough vs "
            "federal) or cover different subsets or REGIONS "
            "(e.g. all trails vs state-park trails only; a "
            "statewide layer vs a Southeast-only one). For 'how "
            "many?' / 'list all' questions, do NOT silently "
            "pick the first one -- either (a) query each "
            "layer with `limit=1` and report a breakdown of "
            "totals, or (b) ask the user which subset they "
            "mean (e.g. 'state-managed', 'a specific "
            "borough', 'all combined'). The titles below "
            "hint at scope (look for agency or region prefixes "
            "like 'ADNR', 'DGGS', 'USFS', 'MatSu', 'SE_').\n\n"
        ),
        "gallery_section_title": "Geoportal catalog -- layers, maps & apps",
        "gallery_section_note": (
            "_Feature/Map Services here are queryable; Web Maps, "
            "Dashboards and Apps are viewers._\n\n"
        ),
        "gallery_footer": (
            "**Only _Feature Service_ / _Map Service_ items above are "
            "queryable.** Web Maps, Dashboards, and Apps are VIEWERS "
            "and cannot be passed to `query_data` for record counts or "
            "filtered lists. If the user asked 'how many?' or 'list X' "
            "and no queryable item is listed, call "
            "`find_gis_content(topic=...)` to find the underlying "
            "Feature Service instead.\n"
        ),
        "where_tip_extra": (
            " A field whose Type is **String** holds TEXT even "
            "when its values look numeric (common on DNR layers: well "
            "depths, acreages, years) -- `field > 0` fails on it. Guard "
            "then cast: `field <> '' AND field NOT LIKE '%[^0-9]%' AND "
            "CAST(field AS INTEGER) > 0`, or compare as text."
        ),
        "unmatched_diagnosis": (
            "This usually means the aggregation layer does "
            "not cover those features (e.g. the Unorganized "
            "Borough when bucketing by borough) or stray "
            "coordinates."
        ),
        "mercator_inflation": (
            "~2.5x at Ketchikan, ~4.3x at Anchorage, ~10x at Utqiagvik"
        ),
        "spanning_example": (
            "should be a parcels layer (e.g. a borough's "
            "parcels) and classification should be a zoning or "
            "land-status layer. Use "
        ),
        "parcel_layer_examples": "(e.g. a borough parcels layer) ",
        "shape_area_note": (
            "NOTE: Shape__Area on ArcGIS Online hosted "
            "layers is WEB MERCATOR, not a real area -- "
            "inflated ~2.5x in Southeast Alaska to ~10x "
            "on the North Slope. The "
        ),
        "hosted_layers": "hosted layers",
    }

    # State layers are often all-lowercase (Forestry Roads uses
    # `road_name`, some parcel layers `parcel_id`), so the shared
    # priority lists gain lowercase twins here.
    NATURAL_ID_FIELD_PRIORITY = (
        # Parcel-style identifiers (most common request shape); some
        # Alaska parcel layers use lowercase `parcel_id`.
        "Parcel_ID", "PARCEL_ID", "ParcelID", "PARCELID", "parcel_id",
        "Parcel_Num", "PARCEL_NUM", "ParcelNum", "PARCELNUM",
        "Parcel_Number", "ParcelNumber",
        "GIS_ParcelNum8Formatted", "GIS_ParcelNum11Formatted",
        "GIS_ParcelNum8", "GIS_ParcelNum11",
        # Polyline-entity name fields -- listed BEFORE generic `Name`
        # so a trails/roads layer with both `Trail_Name` and `Name`
        # picks the more specific one. These also drive the grain
        # warning's follow-up suggestion when query_data hits a
        # polyline layer.
        # State layers are often all-lowercase (e.g. Forestry Roads'
        # `road_name`), so each spelling has a lowercase twin.
        "Trail_Name", "TRAIL_NAME", "TrailName", "trail_name",
        "Road_Name", "ROAD_NAME", "RoadName", "road_name",
        "Street_Name", "STREET_NAME", "StreetName", "street_name",
        "Route_Name", "ROUTE_NAME", "RouteName", "route_name",
        # Generic record-name fields (next-best fallback).
        "Name", "NAME", "name", "FullName", "Full_Name",
        "Site_Name", "SiteName",
        "Site_Address", "Address", "ADDRESS",
        "Title", "TITLE",
        # Common code/identifier fields.
        "Permit_Number", "PermitNumber",
        "Project_Name", "ProjectName",
        "Plat_Number", "PlatNumber",
    )

    PARCEL_INDICATOR_FIELDS = frozenset((
        "Parcel_ID", "PARCEL_ID", "ParcelID", "PARCELID", "parcel_id",
        "Parcel_Num", "PARCEL_NUM", "ParcelNum", "PARCELNUM",
        "Parcel_Number", "ParcelNumber",
        "GIS_ParcelNum8", "GIS_ParcelNum11",
        "GIS_ParcelNum8Formatted", "GIS_ParcelNum11Formatted",
    ))

    # ── Tenant refusals name the partner arrangement ─────────────────────

    def _foreign_org_message(self, item: Dict[str, Any]) -> str:
        # Federal tenants (Census, USGS, NOAA, USFS ...) are catalogued
        # in the Geoportal but deliberately not listed as partners, so
        # their items -- and state-owned item records that merely point
        # at a federal tenant's service -- are refused.
        partners = len(self._partner_orgs)
        org = item.get("orgId")
        owner = (
            f"belongs to org {org!r}"
            if org
            else "belongs to another ArcGIS account"
        )
        return (
            f"Item {item.get('id')!r} {owner}, not the configured org "
            f"{self.plugin_config.org_id!r} or one of its {partners} "
            f"Alaska partner orgs; this MCP only serves "
            f"{self.plugin_config.city_name} and Alaska partner data. "
            f"Federal partner layers are listed in the catalog but "
            f"not queryable here -- name the publishing agency to the "
            f"user rather than retrying."
        )

    def _foreign_tenant_message(
        self, host: str, path: str, org_id: str
    ) -> str:
        return (
            f"service URL host {host!r} (path {path!r}) is not "
            f"scoped to org {org_id!r} or a configured Alaska partner "
            f"org; refusing to proxy other ArcGIS Online tenants "
            f"(federal partner layers are not queryable here)"
        )

    # ── ArcGIS Server's catch-all error ──────────────────────────────────

    @classmethod
    def _explain_unresolved_error(
        cls, full: str, item_arg: str, where_clause: Optional[str]
    ) -> Optional[str]:
        # "Unable to complete operation." is ArcGIS Server's (on-prem,
        # e.g. arcgis.dnr.alaska.gov) catch-all for a WHERE clause that
        # parses but cannot execute. Seen live on the DNR well-log layer:
        # `WellDepth > 0` on a field stored as TEXT. The server names
        # nothing, so name the comparisons ourselves.
        if "Unable to complete operation" not in full or not where_clause:
            return None
        numeric_cmps = re.findall(
            r"\b([A-Za-z_][A-Za-z0-9_]*)\s*(?:>=|<=|<>|!=|>|<|=)"
            r"\s*-?\d+(?:\.\d+)?(?![\w'])",
            where_clause,
        )
        fields = sorted(set(numeric_cmps))
        if fields:
            shown = ", ".join(f"`{f}`" for f in fields)
            return (
                f"{full}\n\nLikely cause: the WHERE clause compares "
                f"{shown} to a NUMBER, but on many state layers "
                f"numeric-looking fields are stored as TEXT "
                f"(type String in `get_layer_schema({item_arg})`), "
                f"and a text field cannot be compared to a bare "
                f"number. Guard and cast it: `{fields[0]} <> '' AND "
                f"{fields[0]} NOT LIKE '%[^0-9]%' AND "
                f"CAST({fields[0]} AS INTEGER) > 0` (verified on the "
                f"DNR ArcGIS Server, whose database is SQL Server; "
                f"an unguarded CAST fails as soon as the scan hits "
                f"a non-numeric value). Or compare as text: "
                f"`{fields[0]} <> ''` / `{fields[0]} = '42'`. Check "
                f"the Type column in the schema first."
            )
        return (
            f"{full}\n\nLikely cause: the WHERE clause is valid SQL "
            f"but cannot run on this layer -- a type mismatch "
            f"(number vs text/date) or a function the server does "
            f"not support. Call `get_layer_schema({item_arg})` and "
            f"check each field's Type; retry with the simplest "
            f"clause that works, then add conditions back one at "
            f"a time."
        )

    # ── Coverage of the state ────────────────────────────────────────────

    # Alaska statewide bbox in WGS84 (xmin, ymin, xmax, ymax). TWO boxes
    # because the Aleutians cross the antimeridian: the mainland /
    # panhandle box east of the dateline and a western-Aleutian sliver
    # from 170E to the dateline. Generous envelopes -- used for the
    # coverage-gap devil's-advocate check, not for filtering. Exact
    # boundary fidelity isn't needed; the goal is to flag clearly
    # partial-coverage layers (e.g. a single-borough or quad-tiled layer).
    ALASKA_BBOXES_WGS84 = (
        (-180.0, 51.0, -129.0, 72.0),
        (170.0, 51.0, 180.0, 53.0),
    )

    # EPSG:3338 (NAD83 / Alaska Albers) parameters: GRS80 ellipsoid,
    # standard parallels 55N and 65N, origin 50N 154W, false easting /
    # northing 0. The on-prem DNR and DGGS servers publish nearly every
    # layer in this projection.
    _ALBERS_A = 6378137.0
    _ALBERS_E2 = 2 * (1 / 298.257222101) - (1 / 298.257222101) ** 2
    _ALBERS_LAT0 = math.radians(50.0)
    _ALBERS_LON0 = math.radians(-154.0)
    _ALBERS_LAT1 = math.radians(55.0)
    _ALBERS_LAT2 = math.radians(65.0)
    _ALASKA_ALBERS_WKIDS = frozenset({3338, 102006})

    @classmethod
    def _albers_q(cls, lat: float) -> float:
        e2 = cls._ALBERS_E2
        e = math.sqrt(e2)
        s = math.sin(lat)
        return (1 - e2) * (
            s / (1 - e2 * s * s)
            - (1 / (2 * e)) * math.log((1 - e * s) / (1 + e * s))
        )

    @classmethod
    def _albers_m(cls, lat: float) -> float:
        return math.cos(lat) / math.sqrt(
            1 - cls._ALBERS_E2 * math.sin(lat) ** 2
        )

    @classmethod
    def _alaska_albers_to_wgs84(
        cls, x: float, y: float
    ) -> Tuple[float, float]:
        """Inverse EPSG:3338 (ellipsoidal Albers, Snyder 1987 ch. 14).

        Returns (lon, lat) in degrees. Longitude is NOT normalized to
        [-180, 180]: a point in the western Aleutians comes back as e.g.
        -187, so a bbox that straddles the antimeridian stays contiguous
        and _split_antimeridian can cut it correctly.
        """
        a, e2 = cls._ALBERS_A, cls._ALBERS_E2
        e = math.sqrt(e2)
        m1 = cls._albers_m(cls._ALBERS_LAT1)
        m2 = cls._albers_m(cls._ALBERS_LAT2)
        q0 = cls._albers_q(cls._ALBERS_LAT0)
        q1 = cls._albers_q(cls._ALBERS_LAT1)
        q2 = cls._albers_q(cls._ALBERS_LAT2)
        n = (m1 * m1 - m2 * m2) / (q2 - q1)
        c = m1 * m1 + n * q1
        rho0 = a * math.sqrt(c - n * q0) / n
        rho = math.hypot(x, rho0 - y)
        theta = math.atan2(x, rho0 - y)
        q = (c - rho * rho * n * n / (a * a)) / n
        # Iterate for latitude (converges in a handful of steps).
        lat = math.asin(max(-1.0, min(1.0, q / 2.0)))
        for _ in range(10):
            s = math.sin(lat)
            denom = 1 - e2 * s * s
            delta = (
                (denom**2) / (2 * math.cos(lat))
                * (
                    q / (1 - e2)
                    - s / denom
                    + (1 / (2 * e)) * math.log((1 - e * s) / (1 + e * s))
                )
            )
            lat += delta
            if abs(delta) < 1e-12:
                break
        lon = cls._ALBERS_LON0 + theta / n
        return math.degrees(lon), math.degrees(lat)

    @staticmethod
    def _split_antimeridian(
        xmin: float, ymin: float, xmax: float, ymax: float
    ) -> List[Tuple[float, float, float, float]]:
        """Cut a lon/lat box into pieces that lie within [-180, 180].

        Accepts un-normalized longitudes (xmin < -180 or xmax > 180, as
        the inverse projections above produce) and the ArcGIS convention
        of xmin > xmax for a WGS84 extent that crosses the dateline.
        """
        if xmin > xmax:
            # ArcGIS dateline-crossing WGS84 extent.
            return [(xmin, ymin, 180.0, ymax), (-180.0, ymin, xmax, ymax)]
        out: List[Tuple[float, float, float, float]] = []
        if xmin < -180.0:
            out.append((xmin + 360.0, ymin, 180.0, ymax))
            xmin = -180.0
        if xmax > 180.0:
            out.append((-180.0, ymin, xmax - 360.0, ymax))
            xmax = 180.0
        out.append((xmin, ymin, xmax, ymax))
        return out

    @classmethod
    def _alaska_coverage_pct(cls, extent: Any) -> Optional[float]:
        # Returns (layer intersect Alaska) / Alaska-area, in [0, ~1+]. >1
        # if the layer is larger than the state (continental data). Used
        # to fire the LIMITED COVERAGE caveat for layers covering <50% of
        # the state. Returns None when we can't honestly compute coverage
        # (unhandled SR, malformed extent) so the caveat is suppressed
        # rather than guessed. Alaska is measured as two WGS84 boxes
        # (see ALASKA_BBOXES_WGS84) and the overlap is summed across both.
        if not isinstance(extent, dict):
            return None
        coords = [extent.get(k) for k in ("xmin", "ymin", "xmax", "ymax")]
        if any(not isinstance(v, (int, float)) for v in coords):
            return None
        xmin, ymin, xmax, ymax = coords
        # Degenerate bbox (single point or zero-width/height) carries no
        # useful coverage signal -- a hospital layer with one point in
        # Fairbanks isn't "non-overlapping Alaska", it just has no
        # area. Return None so the caveat stays silent.
        if xmin == xmax or ymin == ymax:
            return None
        sr = extent.get("spatialReference") or {}
        wkid = sr.get("latestWkid") or sr.get("wkid")
        if wkid in (4326, 4269):
            pass
        elif wkid in (102100, 3857, 102113):
            xmin, ymin = cls._webmerc_to_wgs84(xmin, ymin)
            xmax, ymax = cls._webmerc_to_wgs84(xmax, ymax)
        elif wkid in cls._ALASKA_ALBERS_WKIDS:
            # A conic bbox does not invert to a lon/lat box: sample the
            # corners and edge midpoints and take the envelope.
            xs = (xmin, (xmin + xmax) / 2.0, xmax)
            ys = (ymin, (ymin + ymax) / 2.0, ymax)
            pts = [
                cls._alaska_albers_to_wgs84(px, py)
                for px in xs
                for py in ys
                if not (px == xs[1] and py == ys[1])
            ]
            xmin = min(p[0] for p in pts)
            xmax = max(p[0] for p in pts)
            ymin = min(p[1] for p in pts)
            ymax = max(p[1] for p in pts)
        else:
            return None
        layer_boxes = cls._split_antimeridian(xmin, ymin, xmax, ymax)
        intersection = 0.0
        for lb in layer_boxes:
            for ak in cls.ALASKA_BBOXES_WGS84:
                ix = max(lb[0], ak[0])
                iy = max(lb[1], ak[1])
                ax = min(lb[2], ak[2])
                ay = min(lb[3], ak[3])
                if ix < ax and iy < ay:
                    intersection += (ax - ix) * (ay - iy)
        state_area = sum(
            (b[2] - b[0]) * (b[3] - b[1]) for b in cls.ALASKA_BBOXES_WGS84
        )
        if intersection <= 0.0:
            return 0.0
        return intersection / state_area

    # Alaska Albers is equal-area in metres, so a stored area in it is
    # already true square metres (see ArcGISHubPlugin._true_area_m2).
    EQUAL_AREA_METRE_WKIDS = _ALASKA_ALBERS_WKIDS

    @classmethod
    def _region_coverage_pct(cls, extent: Any) -> Optional[float]:
        return cls._alaska_coverage_pct(extent)
