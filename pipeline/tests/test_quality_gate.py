"""Tests for the data-quality gate (issue #91).

A gate that passes everything is worse than no gate, because it produces
confidence rather than safety. So these break the data on purpose, one failure
mode at a time, and check the gate notices and says which record and how far
out.

The failure modes are the real ones: a unit error, an empty composite, a stage
that produced nothing, a rescale that did not take, and a grid that changed
size. Each of those has produced a plausible-looking broken dataset in some
pipeline somewhere.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PIPELINE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PIPELINE_DIR))

from _quality import (  # noqa: E402
    CELL_BOUNDS,
    CELL_COUNT_TOLERANCE,
    check_bounds,
    check_count,
    check_nulls,
    check_rescale,
)

ROOT = PIPELINE_DIR.parent

REQUIRED = ["LST_C", "NDVI", "pop_density_km2", "elderly_pct",
            "slum_pct", "hospital_dist_m", "impervious_pct", "HVI"]


def cell(**overrides):
    base = {
        "grid_id": "cell_0001",
        "LST_C": 32.0,
        "NDVI": 0.4,
        "NDVI_prev": 0.38,
        "pop_density_km2": 20000.0,
        "elderly_pct": 5.0,
        "slum_pct": 10.0,
        "hospital_dist_m": 800.0,
        "impervious_pct": 40.0,
        "HVI": 50.0,
    }
    base.update(overrides)
    return base


def test_good_data_passes():
    assert check_bounds([cell()], CELL_BOUNDS, "grid_id", "cells") == []


def test_kelvin_instead_of_celsius_is_caught():
    """The classic temperature unit error. 305 K is a normal Mumbai day and
    would look entirely reasonable in a column labelled LST_C."""
    failures = check_bounds([cell(LST_C=305.0)], CELL_BOUNDS, "grid_id", "cells")
    assert len(failures) == 1
    assert "LST_C" in failures[0]
    assert "cell_0001" in failures[0]


def test_an_empty_composite_reading_zero_is_caught():
    failures = check_bounds([cell(LST_C=0.0)], CELL_BOUNDS, "grid_id", "cells")
    assert any("LST_C" in f for f in failures)


def test_ndvi_outside_its_definition_is_caught():
    for bad in (1.5, -2.0):
        failures = check_bounds([cell(NDVI=bad)], CELL_BOUNDS, "grid_id", "cells")
        assert any("NDVI" in f for f in failures), bad


def test_a_percentage_over_one_hundred_is_caught():
    failures = check_bounds([cell(impervious_pct=140.0)], CELL_BOUNDS, "grid_id", "cells")
    assert any("impervious_pct" in f for f in failures)


def test_metres_confused_with_something_larger_is_caught():
    failures = check_bounds([cell(hospital_dist_m=250_000.0)], CELL_BOUNDS, "grid_id", "cells")
    assert any("hospital_dist_m" in f for f in failures)


def test_a_physical_bound_says_so_and_an_envelope_does_not():
    """The two are different problems. A percentage over 100 is a bug; an
    unusually hot cell is worth a look."""
    physical = check_bounds([cell(slum_pct=150.0)], CELL_BOUNDS, "grid_id", "cells")[0]
    envelope = check_bounds([cell(LST_C=305.0)], CELL_BOUNDS, "grid_id", "cells")[0]
    assert "physically impossible" in physical
    assert "implausible" in envelope


def test_the_message_names_the_record_the_column_and_the_value():
    failure = check_bounds(
        [cell(grid_id="cell_0421", NDVI=9.0)], CELL_BOUNDS, "grid_id", "cells"
    )[0]
    assert "cell_0421" in failure
    assert "NDVI" in failure
    assert "9" in failure


def test_a_non_numeric_value_is_caught_rather_than_crashing():
    failures = check_bounds([cell(LST_C="hot")], CELL_BOUNDS, "grid_id", "cells")
    assert any("not a number" in f for f in failures)


def test_every_bad_record_is_reported_not_just_the_first():
    rows = [cell(grid_id=f"cell_{i:04d}", NDVI=5.0) for i in range(3)]
    assert len(check_bounds(rows, CELL_BOUNDS, "grid_id", "cells")) == 3


def test_a_column_that_went_entirely_null_is_caught():
    """A bounds check alone cannot see this: there are no values to be out of
    range. It means a stage produced no data rather than bad data."""
    rows = [cell(LST_C=None) for _ in range(5)]
    failures = check_nulls(rows, REQUIRED, "grid_id", "cells")
    assert len(failures) == 1
    assert "LST_C" in failures[0]


def test_partially_null_columns_are_not_flagged_as_missing():
    rows = [cell(), cell(LST_C=None)]
    assert check_nulls(rows, REQUIRED, "grid_id", "cells") == []


def test_a_rescale_that_did_not_take_is_caught():
    """Values still inside 0..100, so every bounds check passes. Only the span
    reveals that the rescale was skipped or applied to an already-scaled
    series."""
    assert check_rescale([40.0, 45.0, 50.0], "cells.HVI") != []


def test_a_proper_rescale_passes():
    assert check_rescale([0.0, 50.0, 100.0], "cells.HVI") == []


def test_an_empty_series_does_not_fail_the_rescale_check():
    assert check_rescale([], "cells.HVI") == []


def test_a_grid_that_changed_size_is_caught():
    assert check_count(400, 541, CELL_COUNT_TOLERANCE, "cells") != []


def test_a_stable_grid_passes():
    assert check_count(541, 541, CELL_COUNT_TOLERANCE, "cells") == []


def test_a_small_boundary_correction_is_tolerated():
    within = int(541 * (1 + CELL_COUNT_TOLERANCE / 2))
    assert check_count(within, 541, CELL_COUNT_TOLERANCE, "cells") == []


def test_no_baseline_means_no_count_failure():
    assert check_count(541, 0, CELL_COUNT_TOLERANCE, "cells") == []


def test_every_bound_has_a_reason():
    """These get read when a refresh fails at three in the morning. A bare
    number would not help."""
    for name, bound in CELL_BOUNDS.items():
        assert bound.reason.strip(), name
        assert bound.low < bound.high, name


def test_the_bounds_admit_the_real_data():
    """The envelopes must be wider than what Mumbai actually produces, or the
    gate fails every refresh and gets disabled, which is worse than no gate."""
    path = ROOT / "data" / "cells_nbs.geojson"
    if not path.exists():
        pytest.skip("no committed cells to check against")

    rows = [f["properties"] for f in json.loads(path.read_text(encoding="utf-8"))["features"]]
    assert check_bounds(rows, CELL_BOUNDS, "grid_id", "cells") == []
