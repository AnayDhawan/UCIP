"""Tests for the rolling dry-season window in 02_gee_layers.py.

The window was two hardcoded literals until 2026-09-03, which made the monthly
refresh workflow unable to ever produce new data: it re-fetched the same Landsat
scenes and emitted identical output. These tests pin the replacement's behaviour,
including the property that mattered most when making the change, namely that it
returns exactly the old hardcoded window for a run made in 2026.
"""

from __future__ import annotations

import importlib.util
import sys
from datetime import date
from pathlib import Path

import pytest

PIPELINE_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def gee_layers(monkeypatch_session=None):
    """Import 02_gee_layers.py by path; its numeric filename is not a valid module name."""
    sys.path.insert(0, str(PIPELINE_DIR))
    spec = importlib.util.spec_from_file_location(
        "gee_layers", PIPELINE_DIR / "02_gee_layers.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_returns_the_previously_hardcoded_window_for_2026(gee_layers, monkeypatch):
    """The change must not move any published figure.

    Every number in the deck, on the methodology page and in the HVI report comes
    from the 2025-11-01 to 2026-02-28 composite. A run made in 2026 has to keep
    producing exactly that, or the rolling window would silently invalidate all
    of them.
    """
    monkeypatch.delenv("GEE_DRY_SEASON_END_YEAR", raising=False)
    assert gee_layers.most_recent_complete_dry_season(date(2026, 9, 3)) == (
        "2025-11-01",
        "2026-02-28",
    )


def test_does_not_use_a_season_still_in_progress(gee_layers, monkeypatch):
    """A half-finished season averages fewer months and is not comparable to a
    full-season baseline, so mid-season runs keep the last complete window."""
    monkeypatch.delenv("GEE_DRY_SEASON_END_YEAR", raising=False)
    # December, with the 2026-27 season underway.
    assert gee_layers.most_recent_complete_dry_season(date(2026, 12, 20)) == (
        "2025-11-01",
        "2026-02-28",
    )
    # Late February, days from the end, still not complete.
    assert gee_layers.most_recent_complete_dry_season(date(2027, 2, 27)) == (
        "2025-11-01",
        "2026-02-28",
    )


def test_rolls_forward_once_the_season_ends(gee_layers, monkeypatch):
    monkeypatch.delenv("GEE_DRY_SEASON_END_YEAR", raising=False)
    assert gee_layers.most_recent_complete_dry_season(date(2027, 3, 1)) == (
        "2026-11-01",
        "2027-02-28",
    )


def test_handles_february_in_a_leap_year(gee_layers, monkeypatch):
    """End-of-February is computed as "the day before 1 March" rather than a
    hardcoded 28, so a leap year gains its extra day of imagery."""
    monkeypatch.delenv("GEE_DRY_SEASON_END_YEAR", raising=False)
    assert gee_layers.most_recent_complete_dry_season(date(2028, 6, 1)) == (
        "2027-11-01",
        "2028-02-29",
    )


def test_env_override_pins_a_specific_season(gee_layers, monkeypatch):
    """Reproducing a past run has to stay possible, or the published figures
    become unverifiable the moment the window rolls."""
    monkeypatch.setenv("GEE_DRY_SEASON_END_YEAR", "2020")
    assert gee_layers.most_recent_complete_dry_season(date(2030, 1, 1)) == (
        "2019-11-01",
        "2020-02-29",
    )


def test_window_always_spans_the_dry_season_months(gee_layers, monkeypatch):
    """Whatever the run date, the window must start in November and end in
    February of the next year. Monsoon imagery is unusable for LST."""
    monkeypatch.delenv("GEE_DRY_SEASON_END_YEAR", raising=False)
    for year in range(2024, 2032):
        for month in (1, 3, 6, 9, 12):
            start, end = gee_layers.most_recent_complete_dry_season(date(year, month, 15))
            assert start.endswith("-11-01"), start
            assert end[5:7] == "02", end
            assert int(end[:4]) == int(start[:4]) + 1


def test_baseline_sits_a_fixed_gap_before_the_current_window(gee_layers):
    """The NDVI-change layer differences two windows, so they must stay the same
    months a fixed number of years apart or the 'change' includes seasonality."""
    assert gee_layers.PREV_START.endswith("-11-01")
    assert gee_layers.PREV_END[5:7] == "02"
    gap = int(gee_layers.CURR_END[:4]) - int(gee_layers.PREV_END[:4])
    assert gap == gee_layers.BASELINE_GAP_YEARS
