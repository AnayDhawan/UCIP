"""Tests for the boundary adapter layer (issue #111).

The contract every stage now relies on: whatever the source, a caller gets
ward_id, ward_gid and geometry in WGS84, with ids unique and non-null.

geopandas is not installed in CI, so these skip there and run locally. The
normalisation is the part worth pinning: it replaced four hand-rolled copies,
one of which had already drifted into renaming a hardcoded "name" column
rather than the configured ward_id_field.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PIPELINE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PIPELINE_DIR))

gpd = pytest.importorskip("geopandas", reason="geopandas is not installed in CI")
from shapely.geometry import Polygon  # noqa: E402

import _boundaries  # noqa: E402
from _boundaries import BoundaryError, load_boundaries, normalise  # noqa: E402

ROOT = PIPELINE_DIR.parent


def square(x: float = 0.0) -> Polygon:
    return Polygon([(x, 0), (x + 1, 0), (x + 1, 1), (x, 1)])


def frame(rows: list[dict], crs: str | None = "EPSG:4326") -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(rows, geometry="geometry", crs=crs)


class FakeCity:
    slug = "testville"
    ward_id_field = "name"
    expected_ward_count = None
    boundaries_adapter = "file"
    boundaries_config: dict = {}
    boundaries_path = Path("does-not-exist.geojson")


# ------------------------------------------------------------ normalise --

def test_it_produces_the_agreed_columns():
    out = normalise(frame([{"name": "A", "geometry": square()}]), "name")
    assert list(out.columns) == ["ward_gid", "ward_id", "geometry"]


def test_it_uses_the_configured_id_field_not_a_hardcoded_one():
    """The bug this module was written to remove. 11_hero_city.py renamed a
    literal "name" column, which worked only because both shipped cities use
    that field and would have produced no ward_id at all for a third."""
    out = normalise(frame([{"ward_no": "7", "geometry": square()}]), "ward_no")
    assert out["ward_id"].tolist() == ["7"]


def test_a_missing_id_field_names_the_columns_that_do_exist():
    with pytest.raises(BoundaryError) as err:
        normalise(frame([{"nope": "A", "geometry": square()}]), "name")
    assert "name" in str(err.value)
    assert "nope" in str(err.value)


def test_it_synthesises_a_gid_when_the_source_has_none():
    out = normalise(frame([{"name": "A", "geometry": square()},
                           {"name": "B", "geometry": square(2)}]), "name")
    assert out["ward_gid"].tolist() == [1, 2]


def test_it_keeps_the_source_gid_when_there_is_one():
    out = normalise(frame([{"gid": 41, "name": "A", "geometry": square()}]), "name")
    assert out["ward_gid"].tolist() == [41]


def test_an_absent_crs_is_assumed_to_be_wgs84():
    out = normalise(frame([{"name": "A", "geometry": square()}], crs=None), "name")
    assert out.crs.to_string() == "EPSG:4326"


def test_a_projected_source_is_reprojected_rather_than_relabelled():
    """Assuming WGS84 for a source that declares metres would put Mumbai off
    the coast of Africa while looking entirely well-formed."""
    projected = frame(
        [{"name": "A", "geometry": Polygon([(200000, 2100000), (200100, 2100000),
                                            (200100, 2100100), (200000, 2100100)])}],
        crs="EPSG:32643",
    )
    out = normalise(projected, "name")
    assert out.crs.to_string() == "EPSG:4326"
    minx, miny, maxx, maxy = out.total_bounds
    assert 60 < minx < 100 and 0 < miny < 40


def test_duplicate_ward_ids_are_refused():
    with pytest.raises(BoundaryError) as err:
        normalise(frame([{"name": "A", "geometry": square()},
                         {"name": "A", "geometry": square(2)}]), "name")
    assert "duplicate" in str(err.value).lower()


def test_a_null_ward_id_is_refused():
    with pytest.raises(BoundaryError) as err:
        normalise(frame([{"name": None, "geometry": square()}]), "name")
    assert "no 'name' value" in str(err.value)


def test_ward_ids_come_back_as_strings():
    """Ward ids reach filenames and API paths. A numeric id that arrives as an
    int and leaves as a string somewhere downstream is a lookup that misses."""
    out = normalise(frame([{"name": 7, "geometry": square()}]), "name")
    assert out["ward_id"].tolist() == ["7"]


# ------------------------------------------------------- load_boundaries --

def test_an_unknown_adapter_is_refused_by_name():
    city = FakeCity()
    city.boundaries_adapter = "carrier-pigeon"
    with pytest.raises(BoundaryError) as err:
        load_boundaries(city)
    assert "carrier-pigeon" in str(err.value)
    assert "file" in str(err.value)


def test_a_missing_boundary_file_says_so_rather_than_raising_from_geopandas():
    with pytest.raises(BoundaryError) as err:
        load_boundaries(FakeCity())
    assert "not found" in str(err.value)


def test_the_expected_ward_count_is_enforced():
    city = FakeCity()
    city.expected_ward_count = 99
    _boundaries.ADAPTERS["fake"] = lambda _c: frame([{"name": "A", "geometry": square()}])
    city.boundaries_adapter = "fake"
    try:
        with pytest.raises(BoundaryError) as err:
            load_boundaries(city)
        assert "99" in str(err.value)
    finally:
        del _boundaries.ADAPTERS["fake"]


def test_the_osm_adapter_refuses_without_a_place():
    city = FakeCity()
    city.boundaries_adapter = "osm"
    city.boundaries_config = {}
    with pytest.raises(BoundaryError) as err:
        load_boundaries(city)
    assert "osm_place" in str(err.value)


def test_the_gadm_adapter_refuses_without_a_country_and_level():
    city = FakeCity()
    city.boundaries_adapter = "gadm"
    city.boundaries_config = {"gadm_country": "KEN"}
    with pytest.raises(BoundaryError) as err:
        load_boundaries(city)
    assert "gadm_level" in str(err.value)


# --------------------------------------------------------- the real city --

def test_mumbai_loads_through_the_adapter_unchanged():
    """The acceptance criterion: the shipped city still works."""
    import _city

    boundaries_file = ROOT / "data" / "bmc_wards.geojson"
    if not boundaries_file.exists():
        pytest.skip("bmc_wards.geojson not present")

    wards = load_boundaries(_city.load_city("mumbai"))
    assert len(wards) == 24
    assert list(wards.columns) == ["ward_gid", "ward_id", "geometry"]
    assert wards["ward_id"].is_unique
    assert wards.crs.to_string() == "EPSG:4326"
