"""Tests for the elderly_pct evaluation (issue #95).

The evaluation's conclusion is that WorldPop's India age-sex product carries
district age structure rather than a measured surface, so these check that the
script detects that structure when it is present and does not claim it when it
is not. A diagnostic that always reports the same answer is not a diagnostic.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

PIPELINE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PIPELINE_DIR))

import importlib.util  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "elderly_evaluation", PIPELINE_DIR / "elderly_evaluation.py"
)
ee_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ee_mod)


def cells(elderly_by_ward: dict[str, float], per_ward: int = 5, separation: float = 1.0) -> pd.DataFrame:
    """A synthetic grid where only elderly_pct is controlled.

    Each ward gets its own offset `w`, so the six other indicators genuinely
    separate the wards. Without that every ward rolls up to the same mean, the
    ranking is a single tie, and the tests pass or fail for reasons that have
    nothing to do with what they claim to check.

    `separation` scales how far apart the other six indicators put the wards.
    At 1.0 they separate the wards decisively and nothing else can reorder
    them; near 0 the wards are close to tied on everything else, which is the
    situation in which a weak indicator decides the order.
    """
    rows = []
    for w, (ward, elderly) in enumerate(elderly_by_ward.items()):
        off = w * separation
        for i in range(per_ward):
            rows.append(
                {
                    "ward_id": ward,
                    "LST_C": 30 + i * 0.7 + off * 1.4,
                    "NDVI": 0.5 - i * 0.05 - off * 0.06,
                    "pop_density_km2": 10000 + i * 900 + off * 4200,
                    "elderly_pct": elderly,
                    "slum_pct": i * 2.5 + off * 3.1,
                    "hospital_dist_m": 500 + i * 220 + off * 310,
                    "impervious_pct": 20 + i * 8 + off * 5.5,
                }
            )
    return pd.DataFrame(rows)


class TestRankMachinery:
    def test_ranks_every_ward_once_starting_at_one(self):
        df = cells({"A": 5.0, "B": 4.0, "C": 4.5, "D": 5.2})
        ranks = ee_mod.ward_ranks(df, ee_mod.INDICATORS)
        assert sorted(ranks.tolist()) == [1, 2, 3, 4]
        assert set(ranks.index) == {"A", "B", "C", "D"}

    def test_dropping_an_indicator_is_a_smaller_model_not_an_error(self):
        df = cells({"A": 5.0, "B": 4.0, "C": 4.5})
        fewer = {k: v for k, v in ee_mod.INDICATORS.items() if k != "elderly_pct"}
        ranks = ee_mod.ward_ranks(df, fewer)
        assert sorted(ranks.tolist()) == [1, 2, 3]

    def test_a_constant_indicator_cannot_move_the_ranking(self):
        """The degenerate case, which is the one that matters here.

        If every cell carries the same elderly_pct, the indicator holds no
        information and the ranking must be identical with and without it. A
        z-score of a zero-variance column has to come out as zeros rather than
        NaN for that to hold, which is what zscore() guards.
        """
        df = cells({"A": 4.76, "B": 4.76, "C": 4.76, "D": 4.76})
        with_it = ee_mod.ward_ranks(df, ee_mod.INDICATORS)
        without = ee_mod.ward_ranks(df, {k: v for k, v in ee_mod.INDICATORS.items() if k != "elderly_pct"})
        assert with_it.to_dict() == without.to_dict()

    def test_a_two_valued_indicator_is_not_inert(self):
        """It enters the model, unlike a constant one.

        Deliberately not asserting that it reorders the wards. Whether it does
        depends on how close the wards are on the other six indicators, and a
        synthetic grid can be built either way, so such a test would be
        asserting the fixture rather than the behaviour. What is always true is
        the difference from the degenerate case: a two-valued layer has
        non-zero variance and so survives standardisation.

        The real effect, 13 of 24 wards moving by up to 4 places, is measured
        against the real dataset in the integration test below.
        """
        df = cells({"A": 5.586, "B": 5.586, "C": 4.757, "D": 4.757})
        z = ee_mod.zscore(df["elderly_pct"])
        assert z.std(ddof=0) > 0
        assert set(z.round(6)) == {round(z.min(), 6), round(z.max(), 6)}


class TestZscore:
    def test_zero_variance_returns_zeros_rather_than_nan(self):
        out = ee_mod.zscore(pd.Series([4.76] * 10))
        assert out.tolist() == [0.0] * 10

    def test_normal_case_standardises(self):
        out = ee_mod.zscore(pd.Series([1.0, 2.0, 3.0]))
        assert out.mean() == pytest.approx(0.0)
        assert out.iloc[0] < 0 < out.iloc[2]


class TestRescale:
    def test_maps_to_zero_and_one_hundred(self):
        out = ee_mod.rescale_0_100(pd.Series([1.0, 5.0, 9.0]))
        assert out.iloc[0] == pytest.approx(0.0)
        assert out.iloc[-1] == pytest.approx(100.0)

    def test_a_flat_series_becomes_the_midpoint_rather_than_dividing_by_zero(self):
        out = ee_mod.rescale_0_100(pd.Series([7.0, 7.0, 7.0]))
        assert out.tolist() == [50.0, 50.0, 50.0]


def test_the_district_ward_split_is_the_real_one():
    """Guards the list the administrative check is made against.

    If this set drifts, the evaluation would report "matches the district
    boundary" for a boundary that is not Mumbai's, which is a wrong finding
    rather than a missing one.
    """
    assert len(ee_mod.MUMBAI_CITY_WARDS) == 9
    assert "A" in ee_mod.MUMBAI_CITY_WARDS
    assert "G/S" in ee_mod.MUMBAI_CITY_WARDS
    # Suburban wards must not be in it.
    for ward in ("H/E", "K/W", "R/C", "T", "M/E"):
        assert ward not in ee_mod.MUMBAI_CITY_WARDS


class TestAgainstTheRealDataset:
    """Pins the findings the issue-#95 decision rests on.

    Skipped when the dataset is absent, so a fresh clone without a pipeline run
    does not fail, but run everywhere the committed snapshot exists, which is
    CI included.
    """

    @pytest.fixture(scope="class")
    def real(self):
        import json

        path = PIPELINE_DIR.parent / "data" / "cells_hvi.geojson"
        if not path.exists():
            pytest.skip("data/cells_hvi.geojson not present")
        raw = json.loads(path.read_text(encoding="utf-8"))
        df = pd.DataFrame([f["properties"] for f in raw["features"]])
        return df.dropna(subset=list(ee_mod.INDICATORS))

    def test_elderly_pct_is_effectively_two_valued(self, real):
        counts = real["elderly_pct"].round(4).value_counts()
        assert counts.iloc[0] / len(real) > 0.75, "the most common value should cover most cells"
        assert counts.iloc[:2].sum() / len(real) > 0.95, "two values should cover almost everything"

    def test_it_has_the_least_spread_of_the_seven_indicators(self, real):
        cv = {c: real[c].std(ddof=0) / abs(real[c].mean()) for c in ee_mod.INDICATORS}
        assert min(cv, key=cv.get) == "elderly_pct"

    def test_its_pattern_is_the_revenue_district_boundary(self, real):
        """The finding that reframes the issue.

        If each ward's value is determined entirely by which of Mumbai's two
        revenue districts it sits in, the layer carries district age structure
        and no sub-district information, so it is not the 100 m measured
        surface the raster's resolution implies.
        """
        # Round before taking the mode, not after. A ward on the district line
        # has cells that straddle it and so blends the two values; unrounded,
        # such a ward has no repeated value at all and mode() falls back to the
        # minimum, which looks like a third district that does not exist.
        by_ward = real.groupby("ward_id")["elderly_pct"].agg(
            lambda s: s.round(3).mode().iloc[0]
        )
        city = {w: v for w, v in by_ward.items() if w in ee_mod.MUMBAI_CITY_WARDS}
        suburban = {w: v for w, v in by_ward.items() if w not in ee_mod.MUMBAI_CITY_WARDS}

        assert len(set(city.values())) == 1, f"Mumbai City wards disagree: {city}"
        assert len(set(suburban.values())) == 1, f"Suburban wards disagree: {suburban}"
        assert set(city.values()) != set(suburban.values()), "the two districts should differ"
        # And the blending is real but marginal: only the wards on the boundary
        # carry more than one value, so the layer is a district dummy plus edge
        # effects, not a surface.
        distinct = real.assign(e=real["elderly_pct"].round(3)).groupby("ward_id")["e"].nunique()
        single = int((distinct == 1).sum())
        assert single >= 16, f"most wards should carry a single value, got {single} of {len(distinct)}"

    def test_dropping_it_moves_the_published_ranking(self, real):
        with_it = ee_mod.ward_ranks(real, ee_mod.INDICATORS)
        without = ee_mod.ward_ranks(real, {k: v for k, v in ee_mod.INDICATORS.items() if k != "elderly_pct"})
        moved = [w for w in with_it.index if with_it[w] != without[w]]
        # A layer carrying one bit should not be reordering half the table.
        # This is the number the decision in methodology.md quotes.
        assert len(moved) >= 10, f"expected a substantial reshuffle, got {len(moved)}"
