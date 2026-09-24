"""Tests for the city configuration layer (issue #68).

The two properties worth locking down are the ones whose failure is silent:
a wrong UTM zone distorts every area in the pipeline while producing output that
looks fine, and unnamespaced output lets one city overwrite another's data.
"""

from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

import pytest

PIPELINE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PIPELINE_DIR))

import _city  # noqa: E402

ROOT = PIPELINE_DIR.parent


def test_mumbai_config_loads():
    city = _city.load_city("mumbai")
    assert city.slug == "mumbai"
    assert city.ward_id_field == "name"
    assert city.expected_ward_count == 24
    assert city.cell_size_m == 1000
    assert city.projected_crs == "EPSG:32643"


def test_unknown_city_fails_with_a_useful_message():
    with pytest.raises(SystemExit) as exc:
        _city.load_city("atlantis")
    message = str(exc.value)
    assert "atlantis" in message
    # The error should say what IS available, not just what is not.
    assert "mumbai" in message


class TestUtmDerivation:
    """A wrong UTM zone is the most dangerous kind of config error: nothing
    fails, every area and distance is just quietly wrong."""

    def test_mumbai_resolves_to_zone_43_north(self):
        assert _city.utm_crs_for((72.7, 18.8, 73.0, 19.3)) == "EPSG:32643"

    def test_pune_shares_mumbais_zone(self):
        assert _city.utm_crs_for((73.7, 18.4, 74.0, 18.65)) == "EPSG:32643"

    def test_southern_hemisphere_uses_the_327xx_band(self):
        # Rio de Janeiro. Getting the hemisphere wrong shifts northings by
        # 10,000km, so this is worth an explicit case.
        assert _city.utm_crs_for((-43.5, -23.1, -43.1, -22.8)) == "EPSG:32723"

    def test_london_resolves_to_zone_30(self):
        assert _city.utm_crs_for((-0.5, 51.3, 0.3, 51.7)) == "EPSG:32630"

    def test_zone_is_two_digits_for_low_zone_numbers(self):
        # Zone 1 must render as 32601, not 3261.
        code = _city.utm_crs_for((-177.0, 10.0, -176.0, 11.0))
        assert code == "EPSG:32601"
        assert len(code.split(":")[1]) == 5


class TestOutputNamespacing:
    """Before output was namespaced, a Pune run overwrote Mumbai's grid at the
    same filename and nothing complained."""

    def test_default_city_writes_to_the_data_root(self):
        city = _city.load_city("mumbai")
        assert city.data_dir == _city.DATA_DIR

    def test_other_cities_write_to_their_own_directory(self):
        city = _city.load_city("pune")
        assert city.data_dir == _city.DATA_DIR / "pune"

    def test_two_cities_do_not_share_an_output_path(self):
        mumbai = _city.load_city("mumbai")
        pune = _city.load_city("pune")
        assert mumbai.out("grid_1km.geojson") != pune.out("grid_1km.geojson")

    def test_only_the_default_city_publishes_to_the_frontend(self):
        # A second city's run must not swap the live dashboard's data.
        assert _city.load_city("mumbai").publishes_to_frontend is True
        assert _city.load_city("pune").publishes_to_frontend is False


class TestGridResolution:
    """Resolution namespacing (issue #96).

    `cell_size_m` was configurable long before it worked. The grid paths were
    module-level constants spelling "grid_1km" literally, so setting it to 500
    produced 500 m cells inside files named grid_1km, on top of the 1 km ones,
    with only a four-times-larger feature count to give it away.
    """

    def at(self, size, slug="mumbai"):
        return replace(_city.load_city(slug), cell_size_m=float(size))

    @pytest.mark.parametrize(
        "size,label",
        [(1000, "1km"), (500, "500m"), (250, "250m"), (2000, "2km"), (100, "100m")],
    )
    def test_label_reads_as_a_human_would_write_it(self, size, label):
        assert self.at(size).grid_label == label

    def test_the_default_resolution_keeps_every_existing_path(self):
        # The committed Mumbai outputs are named grid_1km*.geojson and the
        # deck, docs and snapshots all reference them. Changing those names
        # would be a breaking change dressed up as a refactor.
        city = _city.load_city("mumbai")
        assert city.data_dir == _city.DATA_DIR
        assert city.grid_path().name == "grid_1km.geojson"
        assert city.grid_path("_gee").name == "grid_1km_gee.geojson"
        assert city.grid_path("_vectors").name == "grid_1km_vectors.geojson"

    def test_a_non_default_resolution_gets_its_own_directory(self):
        assert self.at(500).data_dir == _city.DATA_DIR / "mumbai_500m"
        assert self.at(250).data_dir == _city.DATA_DIR / "mumbai_250m"

    def test_resolution_and_city_namespace_independently(self):
        assert self.at(500, "pune").data_dir == _city.DATA_DIR / "pune_500m"
        assert self.at(1000, "pune").data_dir == _city.DATA_DIR / "pune"

    def test_no_two_resolutions_share_any_output_path(self):
        """The property that matters, checked over every artefact, not just the grid.

        The directory carries the resolution precisely so that files named for
        what they hold rather than how they were built (cells.geojson,
        wards_hvi.geojson) are namespaced too. Those are the ones a
        filename-only scheme would have missed, and they are the inputs to
        every stage from 05 onward.
        """
        km, half = self.at(1000), self.at(500)
        for name in [
            "cells.geojson",
            "wards_hvi.geojson",
            "nbs_recommendations.json",
            "ward_timeseries.json",
            "hvi_pca_log.json",
        ]:
            assert km.out(name) != half.out(name), name
        assert km.grid_path() != half.grid_path()

    def test_a_non_default_resolution_does_not_publish_to_the_frontend(self):
        # The site is built and tested against the 1 km dataset. A 500 m run is
        # an experiment until somebody has looked at what it does to the
        # payload, and it must not silently become what the dashboard serves.
        assert self.at(500).publishes_to_frontend is False
        assert self.at(1000).publishes_to_frontend is True


class TestShippedConfigs:
    """Every config in the repo has to be loadable and internally consistent,
    since CI validates them on every push."""

    @pytest.mark.parametrize(
        "path", sorted((ROOT / "config" / "cities").glob("*.json")), ids=lambda p: p.stem
    )
    def test_config_loads_and_agrees_with_its_filename(self, path):
        city = _city.load_city(path.stem)
        assert city.slug == path.stem

    @pytest.mark.parametrize(
        "path", sorted((ROOT / "config" / "cities").glob("*.json")), ids=lambda p: p.stem
    )
    def test_map_centre_sits_inside_the_bbox(self, path):
        city = _city.load_city(path.stem)
        min_lon, min_lat, max_lon, max_lat = city.bbox
        lat, lon = city.map_center
        # Catches the [lon, lat] vs [lat, lon] swap, which puts the map in the sea.
        assert min_lat <= lat <= max_lat, f"{path.stem}: centre latitude outside bbox"
        assert min_lon <= lon <= max_lon, f"{path.stem}: centre longitude outside bbox"

    @pytest.mark.parametrize(
        "path", sorted((ROOT / "config" / "cities").glob("*.json")), ids=lambda p: p.stem
    )
    def test_ecology_calibration_is_stated_explicitly(self, path):
        # An uncalibrated plantability filter on a new biome is the most harmful
        # mistake this project can make, so silence is not an acceptable answer.
        cfg = json.loads(path.read_text(encoding="utf-8"))
        assert "calibrated" in cfg.get("ecology", {}), (
            f"{path.stem}: ecology.calibrated must say whether the plantability "
            f"filter has been reviewed for this city"
        )


def test_frontend_mirror_matches_the_canonical_configs():
    """The frontend bundles a copy because Turbopack cannot import from outside
    its root. A stale copy would show a different map centre from the one the
    pipeline validated against, so CI checks it and so does this."""
    mirror_dir = ROOT / "frontend" / "src" / "lib" / "cities"
    for src in sorted((ROOT / "config" / "cities").glob("*.json")):
        dest = mirror_dir / src.name
        assert dest.exists(), f"missing frontend mirror for {src.stem}"
        canonical = json.loads(src.read_text(encoding="utf-8"))
        mirrored = json.loads(dest.read_text(encoding="utf-8"))
        canonical.pop("$schema", None)
        mirrored.pop("_generated", None)
        assert canonical == mirrored, (
            f"{src.stem}: frontend mirror is stale. "
            f"Run python pipeline/sync_city_config.py"
        )
