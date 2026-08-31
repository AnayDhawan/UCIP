"""Tests for diff_snapshots.py (issue #61's diff-computation core).

No geospatial dependencies needed: the module reads GeoJSON as plain JSON, so these
tests build tiny fixture files directly rather than depending on geopandas/shapely.

Run:
    pip install -r requirements-dev.txt
    pytest pipeline/tests/test_diff_snapshots.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from diff_snapshots import compute_diff  # noqa: E402


def _write_wards_hvi(dir_path: Path, wards: list[dict]) -> None:
    features = [
        {
            "type": "Feature",
            "properties": {"ward_id": w["ward_id"], "HVI": w["hvi"], "rank": w["rank"]},
            "geometry": None,
        }
        for w in wards
    ]
    (dir_path / "wards_hvi.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": features}), encoding="utf-8"
    )


def _write_nbs_recs(dir_path: Path, recs: list[dict]) -> None:
    (dir_path / "nbs_recommendations.json").write_text(json.dumps(recs), encoding="utf-8")


def _write_ndvi_change(dir_path: Path, cells: list[dict]) -> None:
    features = [
        {
            "type": "Feature",
            "properties": {"ward_id": c["ward_id"], "change_class": c["change_class"]},
            "geometry": None,
        }
        for c in cells
    ]
    (dir_path / "cells_ndvi_change.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": features}), encoding="utf-8"
    )


def test_no_baseline_produces_empty_diff(tmp_path):
    old_dir = tmp_path / "old"
    new_dir = tmp_path / "new"
    old_dir.mkdir()
    new_dir.mkdir()
    _write_wards_hvi(new_dir, [{"ward_id": "A", "hvi": 50.0, "rank": 1}])

    result = compute_diff(old_dir, new_dir)

    assert result.had_baseline is False
    # Nothing to compare against, so nothing is reported as "changed" even though
    # the new run obviously has data — there is no "before" to diff it against.
    assert result.rank_changes == []


def test_rank_shift_detected():
    import tempfile

    with tempfile.TemporaryDirectory() as old_s, tempfile.TemporaryDirectory() as new_s:
        old_dir, new_dir = Path(old_s), Path(new_s)
        _write_wards_hvi(old_dir, [
            {"ward_id": "A", "hvi": 60.0, "rank": 3},
            {"ward_id": "B", "hvi": 70.0, "rank": 1},
        ])
        _write_wards_hvi(new_dir, [
            {"ward_id": "A", "hvi": 75.0, "rank": 1},
            {"ward_id": "B", "hvi": 70.0, "rank": 2},
        ])

        result = compute_diff(old_dir, new_dir)

        assert result.had_baseline is True
        by_ward = {c.ward_id: c for c in result.rank_changes}
        assert set(by_ward) == {"A", "B"}
        assert by_ward["A"].old_rank == 3
        assert by_ward["A"].new_rank == 1
        assert by_ward["A"].delta == 2  # moved 2 places toward rank 1 => more vulnerable
        assert by_ward["B"].delta == -1


def test_unchanged_rank_not_reported():
    import tempfile

    with tempfile.TemporaryDirectory() as old_s, tempfile.TemporaryDirectory() as new_s:
        old_dir, new_dir = Path(old_s), Path(new_s)
        _write_wards_hvi(old_dir, [{"ward_id": "A", "hvi": 60.0, "rank": 3}])
        _write_wards_hvi(new_dir, [{"ward_id": "A", "hvi": 60.0, "rank": 3}])

        result = compute_diff(old_dir, new_dir)
        assert result.rank_changes == []


def test_nbs_recommendation_added_and_removed():
    import tempfile

    with tempfile.TemporaryDirectory() as old_s, tempfile.TemporaryDirectory() as new_s:
        old_dir, new_dir = Path(old_s), Path(new_s)
        _write_nbs_recs(old_dir, [
            {"ward_id": "A", "intervention": "Pocket parks"},
            {"ward_id": "A", "intervention": "Cool roofs + reflective pavements + cooling centres"},
        ])
        _write_nbs_recs(new_dir, [
            {"ward_id": "A", "intervention": "Pocket parks"},
            {"ward_id": "A", "intervention": "Native tree planting + green corridors"},
        ])

        result = compute_diff(old_dir, new_dir)

        assert len(result.nbs_changes) == 1
        change = result.nbs_changes[0]
        assert change.ward_id == "A"
        assert change.added == ["Native tree planting + green corridors"]
        assert change.removed == ["Cool roofs + reflective pavements + cooling centres"]


def test_green_cover_flip_uses_ward_majority_class():
    import tempfile

    with tempfile.TemporaryDirectory() as old_s, tempfile.TemporaryDirectory() as new_s:
        old_dir, new_dir = Path(old_s), Path(new_s)
        # Ward A: majority "stable" before, majority "lost" after.
        _write_ndvi_change(old_dir, [
            {"ward_id": "A", "change_class": "stable"},
            {"ward_id": "A", "change_class": "stable"},
            {"ward_id": "A", "change_class": "gained"},
        ])
        _write_ndvi_change(new_dir, [
            {"ward_id": "A", "change_class": "lost"},
            {"ward_id": "A", "change_class": "lost"},
            {"ward_id": "A", "change_class": "stable"},
        ])

        result = compute_diff(old_dir, new_dir)

        assert len(result.green_cover_changes) == 1
        change = result.green_cover_changes[0]
        assert change.ward_id == "A"
        assert change.old_class == "stable"
        assert change.new_class == "lost"


def test_to_json_roundtrip_is_serializable():
    import tempfile

    with tempfile.TemporaryDirectory() as old_s, tempfile.TemporaryDirectory() as new_s:
        old_dir, new_dir = Path(old_s), Path(new_s)
        _write_wards_hvi(old_dir, [{"ward_id": "A", "hvi": 60.0, "rank": 2}])
        _write_wards_hvi(new_dir, [{"ward_id": "A", "hvi": 60.0, "rank": 1}])

        result = compute_diff(old_dir, new_dir)
        payload = result.to_json()

        # Must not raise — this is exactly what the CLI and the CI workflow do.
        serialized = json.dumps(payload)
        assert "rank_changes" in json.loads(serialized)
