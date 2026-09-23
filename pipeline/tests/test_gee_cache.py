"""Tests for the Earth Engine result cache (issue #93).

The dangerous failure here is not a miss, it is a wrong hit. Serving cached
statistics for a different window, a different grid or a different scale would
publish numbers that look current and describe something else. So most of these
check that the key actually changes when the question does.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PIPELINE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PIPELINE_DIR))

import _gee_cache  # noqa: E402


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(_gee_cache, "CACHE_DIR", tmp_path / "gee")
    yield


BASE = {
    "bbox": [[[72.7, 18.8], [73.0, 18.8], [73.0, 19.3], [72.7, 19.3]]],
    "current_window": ["2025-11-01", "2026-02-28"],
    "previous_window": ["2023-11-01", "2024-02-29"],
    "collections": ["LANDSAT/LC08/C02/T1_L2"],
    "scale": 100,
    "max_cloud": 35,
    "grid": "abc123",
}


def test_a_round_trip_returns_what_was_stored():
    key = _gee_cache.cache_key(**BASE)
    _gee_cache.store(key, {"features": [{"grid_id": "cell_0001"}]})
    assert _gee_cache.load(key) == {"features": [{"grid_id": "cell_0001"}]}


def test_the_same_question_produces_the_same_key():
    assert _gee_cache.cache_key(**BASE) == _gee_cache.cache_key(**BASE)


def test_key_order_does_not_matter():
    reordered = dict(reversed(list(BASE.items())))
    assert _gee_cache.cache_key(**reordered) == _gee_cache.cache_key(**BASE)


@pytest.mark.parametrize(
    "field,value",
    [
        ("current_window", ["2026-11-01", "2027-02-28"]),
        ("previous_window", ["2022-11-01", "2023-02-28"]),
        ("collections", ["LANDSAT/LC09/C02/T1_L2"]),
        ("scale", 30),
        ("max_cloud", 20),
        ("grid", "different"),
        ("bbox", [[[80.1, 12.8], [80.3, 12.8], [80.3, 13.2], [80.1, 13.2]]]),
    ],
)
def test_changing_anything_that_affects_the_answer_changes_the_key(field, value):
    """A hit on a changed question would publish numbers describing something
    else, which is worse than no cache at all."""
    changed = {**BASE, field: value}
    assert _gee_cache.cache_key(**changed) != _gee_cache.cache_key(**BASE)


def test_a_missing_entry_is_a_miss_not_an_error():
    assert _gee_cache.load(_gee_cache.cache_key(**BASE)) is None


def test_a_corrupt_entry_is_a_miss_not_a_crash():
    key = _gee_cache.cache_key(**BASE)
    _gee_cache.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _gee_cache.path_for(key).write_text("{ not json", encoding="utf-8")
    assert _gee_cache.load(key) is None


def test_an_entry_from_an_older_payload_shape_is_a_miss():
    key = _gee_cache.cache_key(**BASE)
    _gee_cache.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _gee_cache.path_for(key).write_text(
        json.dumps({"_v": _gee_cache.CACHE_VERSION - 1, "payload": {"old": True}}),
        encoding="utf-8",
    )
    assert _gee_cache.load(key) is None


def test_storing_never_raises_when_the_directory_cannot_be_made(tmp_path, monkeypatch):
    blocked = tmp_path / "blocked"
    blocked.write_text("not a directory", encoding="utf-8")
    monkeypatch.setattr(_gee_cache, "CACHE_DIR", blocked / "gee")
    # A stage that computed the right numbers must not fail because it could
    # not write a copy of them.
    _gee_cache.store("key", {"features": []})


def test_clear_removes_entries_and_reports_how_many():
    for i in range(3):
        _gee_cache.store(f"key{i}", {"n": i})
    assert _gee_cache.clear() == 3
    assert _gee_cache.load("key0") is None


def test_clear_on_an_empty_cache_is_zero_not_an_error():
    assert _gee_cache.clear() == 0


# ------------------------------------------------------ grid fingerprint --

def feature(grid_id: str, x: float = 0.0):
    return {
        "properties": {"grid_id": grid_id},
        "geometry": {"type": "Polygon", "coordinates": [[[x, 0], [x + 1, 0], [x + 1, 1], [x, 1]]]},
    }


def test_the_same_grid_fingerprints_the_same():
    grid = [feature("a"), feature("b", 2)]
    assert _gee_cache.grid_fingerprint(grid) == _gee_cache.grid_fingerprint(grid)


def test_moving_a_cell_changes_the_fingerprint():
    """Ids alone would miss a grid that kept its labels and moved its cells."""
    a = [feature("a", 0)]
    b = [feature("a", 5)]
    assert _gee_cache.grid_fingerprint(a) != _gee_cache.grid_fingerprint(b)


def test_relabelling_a_cell_changes_the_fingerprint():
    """Geometry alone would miss a relabelling that downstream joins use."""
    a = [feature("a", 0)]
    b = [feature("z", 0)]
    assert _gee_cache.grid_fingerprint(a) != _gee_cache.grid_fingerprint(b)


def test_a_larger_grid_changes_the_fingerprint():
    """The 500m option in #96 must not hit a 1km cache entry."""
    coarse = [feature(f"c{i}", i) for i in range(4)]
    fine = [feature(f"c{i}", i * 0.5) for i in range(16)]
    assert _gee_cache.grid_fingerprint(coarse) != _gee_cache.grid_fingerprint(fine)


def test_the_real_grid_fingerprints_without_error():
    grid_path = PIPELINE_DIR.parent / "data" / "grid_1km.geojson"
    if not grid_path.exists():
        pytest.skip("grid_1km.geojson not present")
    grid = json.loads(grid_path.read_text(encoding="utf-8"))
    fingerprint = _gee_cache.grid_fingerprint(grid["features"])
    assert len(fingerprint) == 16
