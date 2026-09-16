"""Correctness of coverage_by_polygon's area figures and diagnostics.

The percentage was always right -- the distortion cancels in a ratio of
two same-projection areas. The RAW areas were not: ArcGIS Online hosted
layers publish Shape__Area in Web Mercator, which inflates area by
sec^2(lat). Statewide that is ~2.5x at Ketchikan, ~4.3x at Anchorage
and ~10x at Utqiagvik, so a single flat divisor would be wrong almost
everywhere; the correction must use each feature's own latitude.
"""

import math

import pytest

from plugins.alaska_geoportal.config_schema import AlaskaGeoportalPluginConfig
from plugins.alaska_geoportal.plugin import AlaskaGeoportalPlugin


@pytest.fixture
def plugin():
    cfg = {
        "portal_base_url": "https://example.maps.arcgis.com/sharing/rest",
        "gallery_group_ids": ["a5055ea72899425c8cc4e01b32658a45"],
        "org_id": "org123",
        "city_name": "State of Alaska",
        "gallery_url": "https://example.com/gallery",
        "timeout": 20,
    }
    p = AlaskaGeoportalPlugin(cfg)
    p.plugin_config = AlaskaGeoportalPluginConfig(**cfg)
    return p


class TestWebMercatorAreaCorrection:
    def test_matches_assessor_lot_size_on_a_real_parcel(self):
        """Ground truth from the Anchorage fork: a parcel storing
        Shape__Area = 1010 (Web Mercator m2) at 61.2N has an assessor
        lot size of 2,493 sqft."""
        sqft = AlaskaGeoportalPlugin._to_sqft(1010.0, 61.2016, 3857)
        assert sqft is not None
        assert abs(sqft - 2493) / 2493 < 0.05, f"{sqft:,.0f} sqft vs 2,493"

    @pytest.mark.parametrize(
        "place, lat, factor",
        [
            ("Ketchikan", 55.34, 3.09),
            ("Anchorage", 61.22, 4.31),
            ("Fairbanks", 64.84, 5.53),
            ("Utqiagvik", 71.29, 9.71),
        ],
    )
    def test_correction_varies_with_latitude(self, place, lat, factor):
        """Statewide the Web Mercator inflation is sec^2(lat): it more
        than triples between Southeast and the North Slope, so the
        correction must be per feature, never a flat divisor."""
        m2 = AlaskaGeoportalPlugin._true_area_m2(1000.0, lat, 3857)
        assert m2 is not None
        assert abs(1000.0 / m2 - factor) / factor < 0.01, (place, 1000.0 / m2)

    def test_correction_is_per_feature_not_a_flat_divisor(self):
        """A single Anchorage-era constant (~4.26) would be 30% wrong in
        Ketchikan and 2x wrong in Utqiagvik."""
        ketchikan = AlaskaGeoportalPlugin._to_sqft(1000.0, 55.34, 3857)
        utqiagvik = AlaskaGeoportalPlugin._to_sqft(1000.0, 71.29, 3857)
        assert ketchikan > utqiagvik  # less distortion further south
        assert ketchikan / utqiagvik > 3.0

    @pytest.mark.parametrize("wkid", [3857, 102100, 102113])
    def test_recognises_web_mercator_variants(self, wkid):
        assert AlaskaGeoportalPlugin._to_sqft(1000.0, 61.2, wkid) is not None

    @pytest.mark.parametrize("wkid", [3338, 102006])
    def test_alaska_albers_is_equal_area_and_passes_through(self, wkid):
        """The on-prem DNR services (and many hosted state layers) are
        published in EPSG:3338, which is equal-area in metres: the stored
        Shape__Area already IS true area, at any latitude."""
        assert AlaskaGeoportalPlugin._true_area_m2(1000.0, 55.3, wkid) == 1000.0
        assert AlaskaGeoportalPlugin._true_area_m2(1000.0, 71.3, wkid) == 1000.0
        sqft = AlaskaGeoportalPlugin._to_sqft(1000.0, 64.8, wkid)
        assert abs(sqft - 10763.9) < 0.1

    @pytest.mark.parametrize("wkid", [4326, 4269, 26935, 26906, None])
    def test_refuses_to_guess_for_other_projections(self, wkid):
        """Returning a number we cannot justify would be the original bug
        in a new costume."""
        assert AlaskaGeoportalPlugin._to_sqft(1000.0, 61.2, wkid) is None

    def test_percentage_is_unaffected_by_the_projection(self):
        """Why this was silent: the ratio was always correct."""
        lat = 61.2
        raw_ratio = 250.0 / 1000.0
        true_ratio = (
            AlaskaGeoportalPlugin._to_sqft(250.0, lat, 3857)
            / AlaskaGeoportalPlugin._to_sqft(1000.0, lat, 3857)
        )
        assert abs(raw_ratio - true_ratio) < 1e-9

    def test_layer_wkid_reads_latest_then_wkid(self):
        f = AlaskaGeoportalPlugin._layer_wkid
        assert f({"extent": {"spatialReference": {"latestWkid": 3857}}}) == 3857
        assert f({"extent": {"spatialReference": {"wkid": 102100}}}) == 102100
        assert f({}) is None


class TestGeodesicArea:
    def test_matches_the_analytic_area_of_a_box(self):
        """R^2 * dlon * (sin(lat2) - sin(lat1)) for a lon/lat box."""
        lon1, lat1, lon2, lat2 = -149.90, 61.20, -149.89, 61.21
        box = {
            "type": "Polygon",
            "coordinates": [[[lon1, lat1], [lon1, lat2], [lon2, lat2],
                             [lon2, lat1], [lon1, lat1]]],
        }
        R = AlaskaGeoportalPlugin._EARTH_RADIUS_M
        expected = (
            R * R
            * math.radians(lon2 - lon1)
            * (math.sin(math.radians(lat2)) - math.sin(math.radians(lat1)))
        )
        got = AlaskaGeoportalPlugin._geometry_area_m2(box)
        assert abs(got - abs(expected)) / abs(expected) < 0.001

    def test_subtracts_holes(self):
        outer = [[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]
        hole = [[0.4, 0.4], [0.4, 0.6], [0.6, 0.6], [0.6, 0.4], [0.4, 0.4]]
        solid = AlaskaGeoportalPlugin._geometry_area_m2(
            {"type": "Polygon", "coordinates": [outer]})
        holed = AlaskaGeoportalPlugin._geometry_area_m2(
            {"type": "Polygon", "coordinates": [outer, hole]})
        assert holed < solid
        assert abs((solid - holed) / solid - 0.04) < 0.005  # hole is 4%


class TestDiagnosticThresholds:
    def test_zero_artifact_threshold_matches_the_measured_tiles(self):
        """Eastridge SW1433 measured 128/195 (66%) false zeros; Hillside
        SW2436 measured 0/79. The threshold must split those."""
        t = AlaskaGeoportalPlugin.COVERAGE_ZERO_ARTIFACT_RATIO
        assert (128 / 195) > t, "Eastridge must trigger the warning"
        assert (0 / 79) <= t, "Hillside must not"

    def test_banner_names_the_failure_mode_and_the_escape_hatch(self):
        """A screening tool that doesn't name its failure mode is a trap."""
        import inspect

        src = inspect.getsource(AlaskaGeoportalPlugin._coverage_by_polygon)
        assert "possible_centroid_artifact" in src
        assert "spatial_query_polygon" in src

    def test_polygons_vs_parcels_caveat_exists(self):
        import inspect

        src = inspect.getsource(AlaskaGeoportalPlugin._coverage_by_polygon)
        assert "targets_are_polygons_not_parcels" in src
        assert "one row per parcel" in src


class TestAllNullShortCircuit:
    def test_all_null_page_is_summarised_not_rendered(self, plugin):
        records = [{"OBJECTID": i, "Owner": None, "Land_Use": None}
                   for i in range(30)]
        text, structured = plugin._format_query_results(records, limit=50)
        assert "are NULL on every one of the 30" in text
        assert "Record 1:" not in text
        assert "get_layer_schema" in text
        # the data is still in the structured half
        assert len(structured["rows"]) == 30

    def test_page_with_any_value_renders_normally(self, plugin):
        records = [{"OBJECTID": 1, "Owner": None},
                   {"OBJECTID": 2, "Owner": "SMITH"}]
        text, _ = plugin._format_query_results(records, limit=50)
        assert "are NULL on every one" not in text
        assert "SMITH" in text
