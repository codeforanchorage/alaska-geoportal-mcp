"""Unit coverage for small plugin helpers that the big tool tests only
reach indirectly: lifecycle, upstream metadata fetches, and the geometry
reductions used to place features in aggregation buckets."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from core.interfaces import ToolInputError
from plugins.alaska_geoportal.config_schema import AlaskaGeoportalPluginConfig
from plugins.alaska_geoportal.plugin import AlaskaGeoportalPlugin

ORG = "7HDiw78fcUiM2BWn"
LAYER = f"https://services1.arcgis.com/{ORG}/arcgis/rest/services/X/FeatureServer/0"


@pytest.fixture
def plugin():
    cfg = {
        "portal_base_url": "https://soa-dnr.maps.arcgis.com/sharing/rest",
        "gallery_group_ids": ["a5055ea72899425c8cc4e01b32658a45"],
        "org_id": ORG,
        "city_name": "State of Alaska",
        "gallery_url": "https://gis.data.alaska.gov/search",
        "timeout": 20,
    }
    p = AlaskaGeoportalPlugin(cfg)
    p.plugin_config = AlaskaGeoportalPluginConfig(**cfg)
    p.client = AsyncMock()
    return p


def _resp(payload, status=200):
    r = Mock()
    r.status_code = status
    r.raise_for_status = Mock()
    r.json.return_value = payload
    return r


class TestLifecycle:
    @pytest.mark.asyncio
    async def test_shutdown_closes_client_and_clears_state(self, plugin):
        client = plugin.client
        plugin._initialized = True
        await plugin.shutdown()
        client.aclose.assert_awaited_once()
        assert plugin.client is None
        assert plugin._initialized is False

    @pytest.mark.asyncio
    async def test_shutdown_without_client_is_a_noop(self, plugin):
        plugin.client = None
        await plugin.shutdown()
        assert plugin._initialized is False

    @pytest.mark.asyncio
    async def test_health_check_true_on_200(self, plugin):
        plugin.client.get = AsyncMock(return_value=_resp({"results": []}))
        assert await plugin.health_check() is True

    @pytest.mark.asyncio
    async def test_health_check_false_on_exception(self, plugin):
        plugin.client.get = AsyncMock(side_effect=RuntimeError("down"))
        assert await plugin.health_check() is False


class TestRecordCount:
    @pytest.mark.asyncio
    async def test_returns_count(self, plugin):
        plugin.client.get = AsyncMock(return_value=_resp({"count": 42}))
        assert await plugin._get_record_count(LAYER, "1=1") == 42
        params = plugin.client.get.await_args.kwargs["params"]
        assert params["returnCountOnly"] == "true"
        assert params["where"] == "1=1"

    @pytest.mark.asyncio
    async def test_none_when_count_missing(self, plugin):
        plugin.client.get = AsyncMock(return_value=_resp({}))
        assert await plugin._get_record_count(LAYER, "1=1") is None

    @pytest.mark.asyncio
    async def test_none_on_upstream_error(self, plugin):
        plugin.client.get = AsyncMock(side_effect=RuntimeError("boom"))
        assert await plugin._get_record_count(LAYER, "1=1") is None

    @pytest.mark.asyncio
    async def test_none_for_disallowed_host_without_calling_upstream(
        self, plugin
    ):
        plugin.client.get = AsyncMock()
        out = await plugin._get_record_count(
            "https://services.arcgis.com/OTHER/FeatureServer/0", "1=1"
        )
        assert out is None
        plugin.client.get.assert_not_awaited()


class TestLayerQuickMeta:
    LAYER_JSON = {
        "geometryType": "esriGeometryPolyline",
        "fields": [
            {"name": "OBJECTID", "type": "esriFieldTypeOID"},
            {"name": "road_name", "type": "esriFieldTypeString"},
            {"name": "SurveyDate", "type": "esriFieldTypeDate"},
            {
                "name": "rd_status",
                "type": "esriFieldTypeString",
                "domain": {
                    "type": "codedValue",
                    "codedValues": [
                        {"code": "Active", "name": "Active"},
                        {"code": "NonFRPA", "name": "Non-FRPA"},
                        {"code": None, "name": "ignored"},
                    ],
                },
            },
            {
                "name": "empty_domain",
                "type": "esriFieldTypeString",
                "domain": {"type": "codedValue", "codedValues": []},
            },
        ],
        "editingInfo": {"dataLastEditDate": 1750000000000},
        "extent": {
            "xmin": -150.0, "ymin": 60.0, "xmax": -147.0, "ymax": 65.0,
            "spatialReference": {"wkid": 4326},
        },
    }

    @pytest.mark.asyncio
    async def test_bundles_dates_domains_geometry_and_caveat_inputs(
        self, plugin
    ):
        plugin.client.get = AsyncMock(return_value=_resp(self.LAYER_JSON))
        meta = await plugin._get_layer_quick_meta(LAYER)
        assert meta["date_fields"] == {"SurveyDate"}
        assert meta["coded_domains"] == {
            "rd_status": {"Active": "Active", "NonFRPA": "Non-FRPA"}
        }
        assert meta["geometry_type"] == "esriGeometryPolyline"
        # road_name is in NATURAL_ID_FIELD_PRIORITY; OBJECTID is not.
        assert meta["name_field"] == "road_name"
        assert meta["field_names"] >= {"OBJECTID", "road_name", "rd_status"}
        assert meta["last_edit_date"] == 1750000000000
        assert meta["coverage_pct"] is not None and 0 < meta["coverage_pct"] < 0.1

    @pytest.mark.asyncio
    async def test_missing_optional_bits_become_none(self, plugin):
        plugin.client.get = AsyncMock(
            return_value=_resp(
                {"fields": [{"name": "A", "type": "esriFieldTypeString"}],
                 "editingInfo": {"dataLastEditDate": "not-a-number"}}
            )
        )
        meta = await plugin._get_layer_quick_meta(LAYER)
        assert meta["date_fields"] is None
        assert meta["coded_domains"] is None
        assert meta["name_field"] is None
        assert meta["last_edit_date"] is None
        assert meta["coverage_pct"] is None

    @pytest.mark.asyncio
    async def test_empty_dict_on_bad_host_or_upstream_failure(self, plugin):
        assert await plugin._get_layer_quick_meta("https://evil.example/x") == {}
        plugin.client.get = AsyncMock(side_effect=RuntimeError("boom"))
        assert await plugin._get_layer_quick_meta(LAYER) == {}

    @pytest.mark.asyncio
    async def test_safe_layer_meta_resolves_item_then_swallows_errors(
        self, plugin
    ):
        with patch.object(
            plugin, "get_dataset",
            AsyncMock(return_value={"url": LAYER.rsplit("/", 1)[0]}),
        ), patch.object(
            plugin, "_get_layer_quick_meta",
            AsyncMock(return_value={"geometry_type": "esriGeometryPoint"}),
        ) as qm:
            out = await plugin._safe_layer_meta("a" * 32)
        assert out == {"geometry_type": "esriGeometryPoint"}
        # _ensure_layer_url appended /0 to the FeatureServer root.
        assert qm.await_args.args[0] == LAYER

        with patch.object(
            plugin, "get_dataset", AsyncMock(side_effect=RuntimeError("x"))
        ):
            assert await plugin._safe_layer_meta("a" * 32) == {}


class TestResolveLayerUrl:
    @pytest.mark.asyncio
    async def test_appends_layer_index_and_validates_host(self, plugin):
        with patch.object(
            plugin, "get_dataset",
            AsyncMock(return_value={
                "url": LAYER.rsplit("/", 1)[0], "type": "Feature Service",
            }),
        ):
            assert await plugin._resolve_layer_url("a" * 32) == LAYER

    @pytest.mark.asyncio
    async def test_rejects_item_without_url(self, plugin):
        with patch.object(
            plugin, "get_dataset",
            AsyncMock(return_value={"url": "", "type": "Feature Service"}),
        ):
            with pytest.raises(ToolInputError, match="no queryable service URL"):
                await plugin._resolve_layer_url("a" * 32)

    @pytest.mark.asyncio
    async def test_rejects_viewer_item_types(self, plugin):
        with patch.object(
            plugin, "get_dataset",
            AsyncMock(return_value={
                "url": "https://soa-dnr.maps.arcgis.com/apps/x", "type": "Web Map",
            }),
        ):
            with pytest.raises(ToolInputError, match="not queryable"):
                await plugin._resolve_layer_url("a" * 32)

    @pytest.mark.asyncio
    async def test_rejects_other_tenant_even_when_state_owned(self, plugin):
        # The Federal Partner groups: state-owned item records whose
        # service URL points at another tenant.
        with patch.object(
            plugin, "get_dataset",
            AsyncMock(return_value={
                "url": "https://services2.arcgis.com/FiaPA4ga0iQKduv3/arcgis/rest/services/X/FeatureServer",
                "type": "Feature Service",
            }),
        ):
            with pytest.raises(ToolInputError, match="other ArcGIS Online tenants"):
                await plugin._resolve_layer_url("a" * 32)

    @pytest.mark.asyncio
    async def test_fetch_layer_meta_surfaces_arcgis_error(self, plugin):
        plugin.client.get = AsyncMock(
            return_value=_resp({"error": {"message": "Invalid layer"}})
        )
        with pytest.raises(RuntimeError, match="Invalid layer"):
            await plugin._fetch_layer_meta(LAYER)

        plugin.client.get = AsyncMock(return_value=_resp({"name": "ok"}))
        assert await plugin._fetch_layer_meta(LAYER) == {"name": "ok"}


class TestGeometryReductions:
    SQ = [[[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]]]
    HOLE = [[0.5, 0.5], [1.5, 0.5], [1.5, 1.5], [0.5, 1.5], [0.5, 0.5]]

    def test_polygon_area_subtracts_holes(self):
        P = AlaskaGeoportalPlugin
        assert P._polygon_area(self.SQ) == pytest.approx(4.0)
        assert P._polygon_area([self.SQ[0], self.HOLE]) == pytest.approx(3.0)
        assert P._polygon_area([]) == 0.0

    def test_geometry_area_dispatches_on_type(self):
        P = AlaskaGeoportalPlugin
        far = [[[10, 10], [14, 10], [14, 14], [10, 14], [10, 10]]]
        assert P._geometry_area({"type": "Polygon", "coordinates": self.SQ}) == pytest.approx(4.0)
        assert P._geometry_area(
            {"type": "MultiPolygon", "coordinates": [self.SQ, far]}
        ) == pytest.approx(20.0)
        assert P._geometry_area({"type": "Point", "coordinates": [0, 0]}) == 0.0
        assert P._geometry_area(None) == 0.0

    def test_multipolygon_centroid_is_area_weighted(self):
        P = AlaskaGeoportalPlugin
        far = [[[10, 10], [14, 10], [14, 14], [10, 14], [10, 10]]]  # 16 sq
        cx, cy = P._geometry_centroid(
            {"type": "MultiPolygon", "coordinates": [self.SQ, far]}
        )
        # (1,1)*4 + (12,12)*16 over 20
        assert cx == pytest.approx((4 + 192) / 20)
        assert cy == pytest.approx((4 + 192) / 20)

    def test_multipolygon_centroid_degenerate_falls_back_to_largest(self):
        P = AlaskaGeoportalPlugin
        line_as_poly = [[[0, 0], [1, 0], [2, 0], [0, 0]]]  # zero area
        out = P._geometry_centroid(
            {"type": "MultiPolygon", "coordinates": [line_as_poly, []]}
        )
        assert out is not None
        assert P._geometry_centroid({"type": "MultiPolygon", "coordinates": []}) is None
        assert P._geometry_centroid({"type": "Polygon", "coordinates": []}) is None
        assert P._geometry_centroid({"type": "Weird", "coordinates": [1]}) is None
        assert P._geometry_centroid({"type": "Polygon"}) is None

    def test_multilinestring_centroid_is_length_weighted(self):
        P = AlaskaGeoportalPlugin
        short = [[0, 0], [1, 0]]          # length 1, centroid (0.5, 0)
        long = [[0, 10], [3, 10]]         # length 3, centroid (1.5, 10)
        cx, cy = P._multilinestring_centroid([short, long])
        assert cx == pytest.approx((0.5 * 1 + 1.5 * 3) / 4)
        assert cy == pytest.approx((0 * 1 + 10 * 3) / 4)

    def test_multilinestring_centroid_zero_length_falls_back_to_first_vertex(self):
        P = AlaskaGeoportalPlugin
        assert P._multilinestring_centroid([[], [[5, 6], [5, 6]]]) == (5.0, 6.0)
        assert P._multilinestring_centroid([[]]) is None
        assert P._multilinestring_centroid([]) is None
