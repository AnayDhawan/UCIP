"""Tests for per-stage provenance recording (issue #92).

The property that matters is that recording can never break a refresh. A stage
that computed the right numbers and failed to describe itself should still
publish; the opposite trade would lose real data to protect a note about it.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PIPELINE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PIPELINE_DIR))

import _provenance  # noqa: E402


@pytest.fixture(autouse=True)
def isolated_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(_provenance, "PROVENANCE_DIR", tmp_path / "provenance")
    yield


def test_a_record_round_trips():
    _provenance.record("05", cells_in=541, weight_source="pca_reid2009")
    assert _provenance.read("05") == {"cells_in": 541, "weight_source": "pca_reid2009"}


def test_repeated_calls_merge_rather_than_replace():
    """A stage records its inputs early and its row counts at the end, so the
    second call must not discard the first."""
    _provenance.record("02", collections=["LANDSAT/LC08/C02/T1_L2"])
    _provenance.record("02", scenes_current_window=37)

    record = _provenance.read("02")
    assert record["collections"] == ["LANDSAT/LC08/C02/T1_L2"]
    assert record["scenes_current_window"] == 37


def test_a_later_value_wins_for_the_same_field():
    _provenance.record("04", cells_out=100)
    _provenance.record("04", cells_out=541)
    assert _provenance.read("04")["cells_out"] == 541


def test_none_values_are_dropped_rather_than_recorded_as_null():
    """An optional field a stage could not determine should be absent, not
    present and null, which reads as "asked and got nothing"."""
    _provenance.record("06", cells_in=541, thresholds=None)
    record = _provenance.read("06")
    assert record == {"cells_in": 541}


def test_reading_a_stage_that_recorded_nothing_returns_none():
    assert _provenance.read("99") is None


def test_collect_returns_every_stage_keyed_by_id():
    _provenance.record("01", cells_out=541)
    _provenance.record("05", wards_out=24)

    collected = _provenance.collect()
    assert set(collected) == {"01", "05"}
    assert collected["05"]["wards_out"] == 24


def test_collect_on_an_empty_run_is_empty_not_an_error():
    assert _provenance.collect() == {}


def test_clear_drops_the_previous_run():
    """A stage skipped this time must not leave last run's record attached to
    this run's log."""
    _provenance.record("01", cells_out=541)
    _provenance.clear()
    assert _provenance.read("01") is None
    assert _provenance.collect() == {}


def test_clearing_twice_is_harmless():
    _provenance.clear()
    _provenance.clear()


def test_recording_never_raises_even_when_it_cannot_write(monkeypatch, tmp_path):
    """The whole point. A stage that produced correct data must not fail
    because it could not write a note about it."""
    blocked = tmp_path / "blocked"
    blocked.write_text("not a directory", encoding="utf-8")
    monkeypatch.setattr(_provenance, "PROVENANCE_DIR", blocked / "provenance")

    _provenance.record("05", cells_in=541)  # must not raise
    assert _provenance.read("05") is None


def test_unreadable_json_is_skipped_rather_than_crashing_collect():
    _provenance.record("01", cells_out=541)
    (_provenance.PROVENANCE_DIR / "02.json").write_text("{ not json", encoding="utf-8")

    collected = _provenance.collect()
    assert "01" in collected
    assert "02" not in collected


def test_values_that_are_not_json_serialisable_still_record():
    """Stages pass numpy scalars and Path objects without thinking about it."""
    _provenance.record("01", source=Path("bmc_wards.geojson"))
    record = _provenance.read("01")
    assert "bmc_wards.geojson" in record["source"]


def test_the_written_file_is_readable_json():
    _provenance.record("05", cells_in=541)
    raw = (_provenance.PROVENANCE_DIR / "05.json").read_text(encoding="utf-8")
    assert json.loads(raw)["cells_in"] == 541
