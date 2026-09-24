"""Tests for the ward-level Census table and the shared indicator set (issue #95).

Standard library only, so these run in CI, which has no pandas.

The aggregation is the part with real failure modes. Census wards are smaller
than BMC wards, 97 of them roll up into 24, and a wrong join here would put
plausible-looking wrong numbers into a published index. So the tests cover each
way the join can go wrong, and then check the committed table against facts that
do not come from the code that built it.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

PIPELINE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PIPELINE_DIR))

import build_census_table as census  # noqa: E402
from _indicators import DIRECTIONS, OPTIONAL, REQUIRED, present  # noqa: E402
from _quality import CELL_BOUNDS, check_bounds  # noqa: E402

ROOT = PIPELINE_DIR.parent
TABLE_PATH = ROOT / "data" / "census2011_ward_age_mumbai.csv"
CELLS_PATH = ROOT / "data" / "cells_hvi.geojson"


# ------------------------------------------------------------ the shared set


class TestIndicatorSet:
    def test_ndvi_is_the_only_protective_indicator(self):
        # Higher NDVI means more green cover, which lowers vulnerability. If a
        # second indicator ever gets -1 it should be a deliberate decision, and
        # this is where it would be noticed.
        assert [c for c, d in DIRECTIONS.items() if d == -1] == ["NDVI"]

    def test_every_direction_is_plus_or_minus_one(self):
        assert set(DIRECTIONS.values()) <= {1, -1}

    def test_child_share_is_optional_and_the_rest_are_required(self):
        assert "child_pct" in OPTIONAL
        assert "child_pct" not in REQUIRED
        assert set(REQUIRED) | set(OPTIONAL) == set(DIRECTIONS)

    def test_present_keeps_canonical_order_whatever_the_column_order(self):
        shuffled = ["impervious_pct", "child_pct", "LST_C", "geometry", "ward_id", "NDVI"]
        assert present(shuffled) == ["LST_C", "NDVI", "child_pct", "impervious_pct"]

    def test_a_run_without_a_census_table_gets_the_required_set(self):
        assert present(REQUIRED) == REQUIRED

    def test_present_ignores_columns_that_are_not_indicators(self):
        assert present(["grid_id", "HVI", "contrib_LST_C"]) == []


# ------------------------------------------------------------ the aggregation


def pca(rows):
    """Primary Census Abstract rows, as csv.DictReader would give them."""
    return [
        {"Level": "WARD", "Ward": str(code), "TOT_P": str(pop), "P_06": str(kids)}
        for code, pop, kids in rows
    ]


def ward_map(rows):
    return [
        {"Ward Code": str(code), "Ward Name": name, "Total Population": str(pop)}
        for code, name, pop in rows
    ]


class TestAggregate:
    def test_rolls_census_wards_up_into_bmc_wards(self):
        result = census.aggregate(
            pca([(101, 1000, 100), (102, 3000, 450), (201, 2000, 100)]),
            ward_map([(101, "A", 1000), (102, "A", 3000), (201, "B", 2000)]),
            expected_total=6000,
        )
        by_ward = {r["ward_id"]: r for r in result}
        assert by_ward["A"]["tot_p"] == 4000
        assert by_ward["A"]["p_06"] == 550
        # 550 / 4000, not the mean of 10% and 15%. A ward's share has to be
        # weighted by population, which is the mistake an averaged join makes.
        assert by_ward["A"]["child_pct"] == pytest.approx(13.75)
        assert by_ward["B"]["child_pct"] == pytest.approx(5.0)

    def test_ignores_rows_that_are_not_wards(self):
        rows = pca([(101, 1000, 100)]) + [
            {"Level": "DISTRICT", "Ward": "0", "TOT_P": "999999", "P_06": "999999"},
            {"Level": "TOWN", "Ward": "0", "TOT_P": "999999", "P_06": "999999"},
        ]
        result = census.aggregate(rows, ward_map([(101, "A", 1000)]), expected_total=1000)
        assert [r["tot_p"] for r in result] == [1000]

    def test_refuses_a_census_ward_with_no_bmc_mapping(self):
        with pytest.raises(census.CensusError, match="no BMC ward mapping"):
            census.aggregate(pca([(101, 1000, 100), (999, 500, 50)]), ward_map([(101, "A", 1000)]), None)

    def test_refuses_a_mapped_ward_missing_from_the_census(self):
        with pytest.raises(census.CensusError, match="missing from the Primary Census Abstract"):
            census.aggregate(pca([(101, 1000, 100)]), ward_map([(101, "A", 1000), (102, "A", 500)]), None)

    def test_refuses_when_the_two_source_files_disagree(self):
        # The strongest check available: two independent files describing the
        # same ward must give the same population.
        with pytest.raises(census.CensusError, match="disagree on population"):
            census.aggregate(pca([(101, 1000, 100)]), ward_map([(101, "A", 1001)]), None)

    def test_refuses_a_total_that_is_not_the_censuss_own(self):
        with pytest.raises(census.CensusError, match="sums to"):
            census.aggregate(pca([(101, 1000, 100)]), ward_map([(101, "A", 1000)]), expected_total=12_442_373)

    def test_output_is_sorted_and_labelled_with_its_source(self):
        result = census.aggregate(
            pca([(201, 2000, 100), (101, 1000, 100)]),
            ward_map([(201, "B", 2000), (101, "A", 1000)]),
            expected_total=3000,
        )
        assert [r["ward_id"] for r in result] == ["A", "B"]
        assert {r["source"] for r in result} == {census.SOURCE_LABEL}


# ------------------------------------------------------ the committed table


@pytest.fixture(scope="module")
def table():
    if not TABLE_PATH.exists():
        pytest.skip("census table not built yet")
    with TABLE_PATH.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class TestCommittedTable:
    def test_has_every_bmc_ward(self, table):
        assert len(table) == 24
        assert len({r["ward_id"] for r in table}) == 24

    def test_wards_are_the_ones_the_pipeline_uses(self, table):
        wards_path = ROOT / "data" / "wards_hvi.geojson"
        if not wards_path.exists():
            pytest.skip("wards_hvi.geojson not present")
        published = {
            f["properties"]["ward_id"]
            for f in json.loads(wards_path.read_text(encoding="utf-8"))["features"]
        }
        assert {r["ward_id"] for r in table} == published

    def test_population_sums_to_the_censuss_own_figure(self, table):
        # 12,442,373 is Greater Mumbai's 2011 population, from the Census itself
        # and not from anything this code produced.
        assert sum(int(r["tot_p"]) for r in table) == census.GREATER_MUMBAI_POPULATION_2011

    def test_the_share_is_the_stored_counts_divided_out(self, table):
        for row in table:
            expected = int(row["p_06"]) / int(row["tot_p"]) * 100
            assert float(row["child_pct"]) == pytest.approx(expected, abs=1e-3), row["ward_id"]

    def test_it_is_a_real_ward_level_surface_unlike_elderly_pct(self, table):
        """The reason this indicator exists.

        elderly_pct takes two values across the city. A ward-level Census
        figure should take one per ward, and they should genuinely differ.
        """
        values = {round(float(r["child_pct"]), 4) for r in table}
        assert len(values) == 24
        shares = [float(r["child_pct"]) for r in table]
        assert 5 < min(shares) and max(shares) < 15

    def test_every_row_says_where_it_came_from(self, table):
        assert {r["source"] for r in table} == {census.SOURCE_LABEL}


class TestJoinedIntoTheCells:
    def test_every_cell_carries_its_wards_census_value(self, table):
        if not CELLS_PATH.exists():
            pytest.skip("cells_hvi.geojson not present")
        by_ward = {r["ward_id"]: float(r["child_pct"]) for r in table}
        features = json.loads(CELLS_PATH.read_text(encoding="utf-8"))["features"]
        assert features, "no cells"
        for feature in features:
            props = feature["properties"]
            assert props["child_pct"] == pytest.approx(by_ward[props["ward_id"]]), props["grid_id"]

    def test_the_indicator_reaches_the_index(self):
        # A column that is joined but never scored would pass every test above
        # while doing nothing. It has to appear in the published contributions.
        wards_path = ROOT / "data" / "wards_hvi.geojson"
        if not wards_path.exists():
            pytest.skip("wards_hvi.geojson not present")
        features = json.loads(wards_path.read_text(encoding="utf-8"))["features"]
        assert all("contrib_child_pct" in f["properties"] for f in features)


# --------------------------------------------------- the plausibility bounds


class TestQualityBounds:
    """child_pct is optional: absent is fine, present must be a percentage."""

    def rows(self, **extra):
        return [{"grid_id": "cell_0001", **extra}]

    def only_child_bound(self):
        return {"child_pct": CELL_BOUNDS["child_pct"]}

    def test_a_city_without_a_census_table_does_not_fail_the_gate(self):
        assert check_bounds(self.rows(), self.only_child_bound(), "grid_id", "cells") == []

    def test_a_present_value_in_range_passes(self):
        assert check_bounds(self.rows(child_pct=9.5), self.only_child_bound(), "grid_id", "cells") == []

    @pytest.mark.parametrize("bad", [-0.1, 100.5, 950.0])
    def test_a_present_value_out_of_range_still_fails(self, bad):
        failures = check_bounds(self.rows(child_pct=bad), self.only_child_bound(), "grid_id", "cells")
        assert failures and "child_pct" in failures[0]

    def test_a_required_column_going_missing_is_still_a_failure(self):
        # The optional flag must not have weakened the guard for everything else.
        failures = check_bounds(
            self.rows(), {"LST_C": CELL_BOUNDS["LST_C"]}, "grid_id", "cells"
        )
        assert failures and "missing from every record" in failures[0]
