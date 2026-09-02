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

from diff_snapshots import compute_diff, load_green_cover_by_ward, load_nbs_by_ward, main  # noqa: E402


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


def test_green_cover_flags_ward_disappearing_from_new_run(tmp_path):
    """Regression test: diff_rank flags a ward dropping out of the ranking, and
    diff_nbs flags every intervention for a ward as "removed" when the ward
    disappears entirely -- but diff_green_cover used to just `continue` (skip) a ward
    present in old but missing from new, reporting it as zero change instead of the
    same kind of data-quality regression the other two diffs already surface.
    """
    old_dir = tmp_path / "old"
    new_dir = tmp_path / "new"
    old_dir.mkdir()
    new_dir.mkdir()

    _write_ndvi_change(old_dir, [{"ward_id": "A", "change_class": "stable"}])
    # Ward A has no cells at all in the new run.
    _write_ndvi_change(new_dir, [{"ward_id": "B", "change_class": "gained"}])

    result = compute_diff(old_dir, new_dir)

    by_ward = {c.ward_id: c for c in result.green_cover_changes}
    assert "A" in by_ward, "ward A disappearing must be reported, not silently skipped"
    assert by_ward["A"].old_class == "stable"
    assert by_ward["A"].new_class is None


def test_green_cover_flags_ward_newly_appearing_in_new_run(tmp_path):
    """Symmetric case: a ward with no PREVIOUS classification (e.g. a ward that just
    got its first-ever NDVI-change data) is reported too, matching diff_rank's
    "newly ranked" case for consistency.
    """
    old_dir = tmp_path / "old"
    new_dir = tmp_path / "new"
    old_dir.mkdir()
    new_dir.mkdir()

    _write_ndvi_change(old_dir, [{"ward_id": "B", "change_class": "gained"}])
    _write_ndvi_change(new_dir, [
        {"ward_id": "A", "change_class": "lost"},
        {"ward_id": "B", "change_class": "gained"},
    ])

    result = compute_diff(old_dir, new_dir)

    by_ward = {c.ward_id: c for c in result.green_cover_changes}
    assert "A" in by_ward
    assert by_ward["A"].old_class is None
    assert by_ward["A"].new_class == "lost"
    assert "B" not in by_ward  # unchanged, correctly not reported


def test_main_labels_disappeared_ward_in_green_cover_output(tmp_path, monkeypatch, capsys):
    old_dir = tmp_path / "old"
    new_dir = tmp_path / "new"
    old_dir.mkdir()
    new_dir.mkdir()

    _write_ndvi_change(old_dir, [{"ward_id": "A", "change_class": "stable"}])
    _write_ndvi_change(new_dir, [{"ward_id": "B", "change_class": "gained"}])

    monkeypatch.setattr(
        sys, "argv",
        ["diff_snapshots.py", "--old-dir", str(old_dir), "--new-dir", str(new_dir)],
    )
    exit_code = main()
    out = capsys.readouterr().out

    assert exit_code == 0
    assert "A: stable -> MISSING" in out
    assert "data-quality regression" in out


def test_partial_baseline_does_not_produce_false_full_diff(tmp_path):
    """Regression test: an old_dir that has wards_hvi.geojson but NOT
    nbs_recommendations.json used to be treated as "has a baseline" globally (because
    *a* file existed), while load_nbs_by_ward silently treated its own missing file as
    {} -- making every ward in the new run's NBS recs look "added" even though there
    was really no baseline to compare against for that category at all.
    """
    old_dir = tmp_path / "old"
    new_dir = tmp_path / "new"
    old_dir.mkdir()
    new_dir.mkdir()

    # old_dir has a rank baseline but no NBS baseline.
    _write_wards_hvi(old_dir, [{"ward_id": "A", "hvi": 60.0, "rank": 2}])
    _write_wards_hvi(new_dir, [{"ward_id": "A", "hvi": 60.0, "rank": 2}])
    _write_nbs_recs(new_dir, [
        {"ward_id": "A", "intervention": "Pocket parks"},
        {"ward_id": "A", "intervention": "Native tree planting + green corridors"},
    ])

    result = compute_diff(old_dir, new_dir)

    assert result.had_baseline is True  # SOME file existed in old_dir
    assert result.had_rank_baseline is True
    assert result.had_nbs_baseline is False
    # The real fix: no NBS baseline means NBS is not diffed at all, not diffed as
    # "everything just got added."
    assert result.nbs_changes == []
    # The category that DOES have a baseline still gets diffed normally.
    assert result.rank_changes == []  # rank 2 -> 2, unchanged


def test_missing_ward_id_in_nbs_recs_not_treated_as_phantom_ward(tmp_path):
    """Regression test: str(r.get("ward_id")) used to run before the None-check, so a
    rec with no ward_id became the literal string "None" and slipped through as a
    phantom ward in the loaded map and the diff output.
    """
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _write_nbs_recs(data_dir, [
        {"ward_id": "A", "intervention": "Pocket parks"},
        {"intervention": "Cool roofs + reflective pavements + cooling centres"},  # no ward_id
    ])

    by_ward = load_nbs_by_ward(data_dir)

    assert set(by_ward) == {"A"}
    assert "None" not in by_ward


def test_green_cover_tie_break_is_order_independent(tmp_path):
    """Regression test: Counter.most_common(1) ties-break on GeoJSON feature order,
    which GEE exports don't guarantee stable across runs. A ward with an identical
    count distribution (e.g. 2 "gained" / 2 "lost") must resolve to the SAME class
    regardless of which one appears first in the file, or the reported "majority"
    could flip between two runs with nothing having actually changed.
    """
    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    dir_a.mkdir()
    dir_b.mkdir()

    # Same 2-2 tie for ward A, features listed in opposite order.
    _write_ndvi_change(dir_a, [
        {"ward_id": "A", "change_class": "gained"},
        {"ward_id": "A", "change_class": "gained"},
        {"ward_id": "A", "change_class": "lost"},
        {"ward_id": "A", "change_class": "lost"},
    ])
    _write_ndvi_change(dir_b, [
        {"ward_id": "A", "change_class": "lost"},
        {"ward_id": "A", "change_class": "lost"},
        {"ward_id": "A", "change_class": "gained"},
        {"ward_id": "A", "change_class": "gained"},
    ])

    result_a = load_green_cover_by_ward(dir_a)
    result_b = load_green_cover_by_ward(dir_b)

    assert result_a["A"] == result_b["A"]
    # Deterministic tie-break: alphabetically first among tied classes ("gained" < "lost").
    assert result_a["A"] == "gained"


def test_main_labels_new_and_dropped_ranks_correctly(tmp_path, monkeypatch, capsys):
    """Regression test: main()'s printed direction label collapsed a None delta (a
    ward newly appearing in, or dropped entirely from, the ranking) to 0 and always
    printed "less vulnerable" for those cases, regardless of what actually happened.
    """
    old_dir = tmp_path / "old"
    new_dir = tmp_path / "new"
    old_dir.mkdir()
    new_dir.mkdir()

    # Ward A is newly ranked (no old rank); ward B is dropped (no new rank).
    _write_wards_hvi(old_dir, [{"ward_id": "B", "hvi": 50.0, "rank": 1}])
    _write_wards_hvi(new_dir, [{"ward_id": "A", "hvi": 60.0, "rank": 1}])

    monkeypatch.setattr(
        sys, "argv",
        ["diff_snapshots.py", "--old-dir", str(old_dir), "--new-dir", str(new_dir)],
    )
    exit_code = main()
    out = capsys.readouterr().out

    assert exit_code == 0
    assert "A: rank None -> 1 (newly ranked)" in out
    assert "B: rank 1 -> None (dropped from ranking)" in out
    # The old bug printed "less vulnerable" for both of these instead.
    assert "less vulnerable" not in out


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
