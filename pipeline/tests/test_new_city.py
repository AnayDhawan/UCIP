"""Tests for the new-city scaffolder (issue #108).

The scaffolder exists to stop a new city inheriting Mumbai's values by copying,
so the tests that matter are the ones checking it derives rather than inherits.
A wrong UTM zone distorts every area and distance in the pipeline while
producing output that looks entirely plausible, and an inherited ecology
calibration produces confident planting recommendations for a biome nobody
checked.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PIPELINE_DIR))

import new_city  # noqa: E402

ROOT = PIPELINE_DIR.parent

MUMBAI_BBOX = [72.7, 18.8, 73.0, 19.3]
CHENNAI_BBOX = [80.1, 12.8, 80.35, 13.2]


def scaffold(bbox=None, **overrides):
    kwargs = {
        "slug": "testville",
        "name": "Testville",
        "bbox": bbox or CHENNAI_BBOX,
        "boundaries_file": "testville_wards.geojson",
        "ward_id_field": "ward_no",
        "country": "India",
        "timezone": "Asia/Kolkata",
        "cell_size_m": 1000,
        "expected_ward_count": None,
        "source": None,
        "source_url": None,
        "gee_project": None,
    }
    kwargs.update(overrides)
    return new_city.build_config(**kwargs)


def test_the_output_validates_against_the_schema():
    """The acceptance criterion: usable without hand-editing."""
    assert new_city.validate(scaffold()) == []


def test_a_minimal_invocation_still_validates():
    config = scaffold(country=None, gee_project=None, expected_ward_count=None)
    assert new_city.validate(config) == []


def test_the_utm_zone_is_derived_not_inherited():
    """The whole point. Chennai is in zone 44N; copying Mumbai's config would
    leave it in 43N and quietly distort every area in the pipeline."""
    assert scaffold(bbox=CHENNAI_BBOX)["grid"]["projected_crs"] == "EPSG:32644"
    assert scaffold(bbox=MUMBAI_BBOX)["grid"]["projected_crs"] == "EPSG:32643"


def test_the_map_centre_is_the_bbox_centre():
    config = scaffold(bbox=CHENNAI_BBOX)
    assert config["map"]["center"] == [13.0, 80.225]


def test_the_map_centre_is_lat_lon_not_lon_lat():
    """Leaflet's order is the reverse of the bbox's, which is the single
    easiest thing to get wrong when writing one of these by hand."""
    config = scaffold(bbox=CHENNAI_BBOX)
    lat, lon = config["map"]["center"]
    min_lon, min_lat, max_lon, max_lat = CHENNAI_BBOX
    assert min_lat <= lat <= max_lat
    assert min_lon <= lon <= max_lon


def test_the_centre_falls_inside_the_bbox_for_every_shape():
    for bbox in (MUMBAI_BBOX, CHENNAI_BBOX, [-0.5, 51.3, 0.3, 51.7]):
        lat, lon = scaffold(bbox=bbox)["map"]["center"]
        min_lon, min_lat, max_lon, max_lat = bbox
        assert min_lat <= lat <= max_lat, bbox
        assert min_lon <= lon <= max_lon, bbox


def test_ecology_is_never_scaffolded_as_calibrated():
    """A scaffolder marking a new city calibrated would assert that someone
    reviewed its biome against the restoration literature, which by definition
    nobody has. This is the one field that has to stay a human decision."""
    config = scaffold()
    assert config["ecology"]["calibrated"] is False


def test_the_ecology_note_says_why_and_points_somewhere():
    notes = scaffold()["ecology"]["notes"]
    assert "Veldman" in notes
    assert "docs/adding-a-city.md" in notes


def test_optional_fields_are_omitted_rather_than_left_empty():
    """The schema sets additionalProperties false and these are optional, so
    emitting empty strings would be worse than leaving them out."""
    config = scaffold(country=None, gee_project=None)
    assert "country" not in config
    assert "gee" not in config
    assert "source" not in config["boundaries"]


def test_provided_optional_fields_are_carried_through():
    config = scaffold(
        country="India",
        gee_project="ucip-mum",
        expected_ward_count=15,
        source="Datameet",
        source_url="https://example.org",
    )
    assert config["country"] == "India"
    assert config["gee"]["project"] == "ucip-mum"
    assert config["boundaries"]["expected_ward_count"] == 15
    assert config["boundaries"]["source"] == "Datameet"


def test_the_cell_size_is_configurable():
    assert scaffold(cell_size_m=500)["grid"]["cell_size_m"] == 500


def test_the_scaffold_matches_the_shape_of_the_shipped_configs():
    """A scaffold missing a key the real configs carry would validate and then
    surprise someone later."""
    mumbai = json.loads((ROOT / "config" / "cities" / "mumbai.json").read_text(encoding="utf-8"))
    config = scaffold(country="India", gee_project="ucip-mum")
    for key in ("slug", "name", "timezone", "bbox", "boundaries", "grid", "map", "ecology"):
        assert key in config, key
        assert key in mumbai, key


def test_the_schema_reference_is_relative_and_resolvable():
    config = scaffold()
    referenced = (ROOT / "config" / "cities" / config["$schema"]).resolve()
    assert referenced == (ROOT / "config" / "city.schema.json").resolve()
