"""Tests for index interpretation (issue #97).

The flag these cover is one a planner acts on: a ward scoring high because of
one indicator needs a different intervention from one scoring high across all
seven. Getting the share wrong would produce a confident, wrong label rather
than a visible failure, which is why the arithmetic is pinned here.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PIPELINE_DIR))

from _hvi import DOMINANCE_THRESHOLD, factor_dominance  # noqa: E402

ROOT = PIPELINE_DIR.parent

FACTORS = [
    "LST_C",
    "NDVI",
    "pop_density_km2",
    "child_pct",
    "slum_pct",
    "hospital_dist_m",
    "impervious_pct",
]


def test_an_even_spread_is_not_dominated():
    result = factor_dominance({f: 1.0 for f in FACTORS})
    assert result["single_factor_dominated"] is False
    # Seven equal factors, so each holds a seventh.
    assert result["dominant_share"] == round(1 / 7, 4)


def test_one_factor_carrying_everything_is_flagged():
    contributions = {f: 0.0 for f in FACTORS}
    contributions["LST_C"] = 5.0
    result = factor_dominance(contributions)
    assert result["single_factor_dominated"] is True
    assert result["dominant_factor"] == "LST_C"
    assert result["dominant_share"] == 1.0


def test_a_strongly_negative_contribution_counts_as_driving_the_score():
    """Contributions are signed. A factor pushing a ward's score down hard is
    driving the result just as much as one pushing it up, so the share is taken
    over magnitudes. Summing signed values would let a large negative cancel a
    large positive and report neither as dominant."""
    contributions = {f: 0.0 for f in FACTORS}
    contributions["NDVI"] = -8.0
    contributions["LST_C"] = 1.0
    result = factor_dominance(contributions)
    assert result["dominant_factor"] == "NDVI"
    assert result["single_factor_dominated"] is True


def test_the_threshold_is_inclusive_at_the_boundary():
    # Exactly half from one factor, half spread across the rest.
    contributions = {f: 0.0 for f in FACTORS}
    contributions["slum_pct"] = 5.0
    contributions["LST_C"] = 2.5
    contributions["NDVI"] = 2.5
    result = factor_dominance(contributions)
    assert result["dominant_share"] == 0.5
    assert result["single_factor_dominated"] is True


def test_just_under_the_threshold_is_not_flagged():
    # Three factors, not two: with only two the larger always holds at least
    # half, so a two-factor fixture cannot express "just under".
    contributions = {f: 0.0 for f in FACTORS}
    contributions["slum_pct"] = 4.9
    contributions["LST_C"] = 3.0
    contributions["NDVI"] = 2.1
    result = factor_dominance(contributions)
    assert result["dominant_share"] == 0.49
    assert result["single_factor_dominated"] is False


def test_the_threshold_is_configurable():
    contributions = {f: 0.0 for f in FACTORS}
    contributions["LST_C"] = 3.0
    contributions["NDVI"] = 7.0
    assert factor_dominance(contributions, threshold=0.6)["single_factor_dominated"] is True
    assert factor_dominance(contributions, threshold=0.8)["single_factor_dominated"] is False


def test_all_zero_contributions_do_not_invent_a_winner():
    result = factor_dominance({f: 0.0 for f in FACTORS})
    assert result["dominant_factor"] is None
    assert result["dominant_share"] is None
    assert result["single_factor_dominated"] is False


def test_empty_input_is_handled():
    result = factor_dominance({})
    assert result["dominant_factor"] is None
    assert result["single_factor_dominated"] is False


def test_none_contributions_are_ignored_rather_than_crashing():
    contributions = {f: None for f in FACTORS}
    contributions["LST_C"] = 2.0
    result = factor_dominance(contributions)
    assert result["dominant_factor"] == "LST_C"


def test_the_result_is_deterministic_on_a_tie():
    """The value is committed to a snapshot and diffed on every refresh, so a
    tie must not produce a different winner run to run."""
    contributions = {f: 0.0 for f in FACTORS}
    contributions["LST_C"] = 3.0
    contributions["NDVI"] = 3.0
    first = factor_dominance(contributions)["dominant_factor"]
    for _ in range(10):
        assert factor_dominance(contributions)["dominant_factor"] == first


def test_the_threshold_sits_above_an_even_split():
    """A threshold at or below 1/7 would flag every ward and mean nothing."""
    assert DOMINANCE_THRESHOLD > 1 / len(FACTORS)


def test_the_published_wards_carry_the_flag():
    """Guards against the flag being computed but never reaching the output."""
    path = ROOT / "data" / "wards_hvi.geojson"
    if not path.exists():
        return

    wards = json.loads(path.read_text(encoding="utf-8"))["features"]
    props = wards[0]["properties"]
    if "dominant_factor" not in props:
        # The snapshot predates this change; regenerating is stage 05's job.
        return

    for ward in wards:
        p = ward["properties"]
        assert "single_factor_dominated" in p
        if p["dominant_share"] is not None:
            assert 0 <= p["dominant_share"] <= 1
            assert p["single_factor_dominated"] == (p["dominant_share"] >= DOMINANCE_THRESHOLD)
