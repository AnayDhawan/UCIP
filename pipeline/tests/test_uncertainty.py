"""Consistency checks on the HVI uncertainty bands (issue #87).

uncertainty.py imports geopandas, numpy and scikit-learn, none of which CI
installs, so these validate the committed output rather than re-running the
bootstrap. That is the right boundary: the published intervals are the claim,
and an interval that contradicts its own point estimate is the failure that
would actually mislead a reader.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
RESULT_PATH = ROOT / "data" / "hvi_uncertainty.json"
WARDS_PATH = ROOT / "data" / "wards_hvi.geojson"

pytestmark = pytest.mark.skipif(
    not RESULT_PATH.exists(),
    reason="hvi_uncertainty.json not generated yet",
)


@pytest.fixture(scope="module")
def result():
    return json.loads(RESULT_PATH.read_text(encoding="utf-8"))


def test_the_method_and_its_limits_are_recorded(result):
    """A bare interval invites over-reading. The file has to carry what the
    bootstrap does and does not account for, so the number cannot travel
    without its caveat."""
    assert result["method"].strip()
    assert result["captures"].strip()
    assert result["does_not_capture"].strip()


def test_the_run_is_reproducible(result):
    assert result["replicates"] >= 1000
    assert isinstance(result["seed"], int)
    assert result["confidence"] == 0.95


def test_every_ward_has_an_interval(result):
    assert len(result["per_ward"]) == result["summary"]["n_wards"]
    for row in result["per_ward"]:
        for key in ("hvi", "hvi_ci_low", "hvi_ci_high", "rank", "rank_ci_low", "rank_ci_high"):
            assert key in row, f"{row['ward_id']} missing {key}"


def test_the_point_estimate_sits_inside_its_own_interval(result):
    """The check that catches a bootstrap computed over the wrong axis or a
    percentile taken from the wrong array."""
    for row in result["per_ward"]:
        assert row["hvi_ci_low"] <= row["hvi"] <= row["hvi_ci_high"], row["ward_id"]
        assert row["rank_ci_low"] <= row["rank"] <= row["rank_ci_high"], row["ward_id"]


def test_intervals_are_ordered(result):
    for row in result["per_ward"]:
        assert row["hvi_ci_low"] <= row["hvi_ci_high"]
        assert row["rank_ci_low"] <= row["rank_ci_high"]


def test_scores_stay_on_the_published_scale(result):
    for row in result["per_ward"]:
        assert 0 <= row["hvi_ci_low"] <= 100
        assert 0 <= row["hvi_ci_high"] <= 100


def test_ranks_stay_within_the_number_of_wards(result):
    n = result["summary"]["n_wards"]
    for row in result["per_ward"]:
        assert 1 <= row["rank_ci_low"] <= n
        assert 1 <= row["rank_ci_high"] <= n


def test_the_ranks_are_a_permutation(result):
    ranks = sorted(r["rank"] for r in result["per_ward"])
    assert ranks == list(range(1, len(ranks) + 1))


def test_the_summary_matches_the_rows(result):
    widths = [r["rank_ci_high"] - r["rank_ci_low"] for r in result["per_ward"]]
    assert result["summary"]["widest_rank_interval"] == max(widths)
    assert result["summary"]["wards_whose_rank_is_certain"] == sum(1 for w in widths if w == 0)


def test_the_point_estimates_agree_with_the_published_ranking(result):
    """The bands describe the ranking the site shows. If they were computed
    from a different scoring run they would be describing something nobody
    can see."""
    if not WARDS_PATH.exists():
        pytest.skip("no published wards to compare against")

    published = {
        f["properties"]["ward_id"]: f["properties"]
        for f in json.loads(WARDS_PATH.read_text(encoding="utf-8"))["features"]
    }
    for row in result["per_ward"]:
        assert row["rank"] == published[row["ward_id"]]["rank"], row["ward_id"]
        assert row["hvi"] == pytest.approx(published[row["ward_id"]]["HVI"], abs=0.01)


def test_the_uncertainty_is_actually_reported_rather_than_flattened(result):
    """A bootstrap that produced zero-width intervals everywhere would pass
    every check above while telling the reader nothing. The point of this issue
    is that the ranking is less certain than one decimal place implies."""
    widths = [r["rank_ci_high"] - r["rank_ci_low"] for r in result["per_ward"]]
    assert max(widths) > 0
