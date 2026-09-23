"""Consistency checks on the PCA vs published weighting comparison (issue #88).

compare_weightings.py imports geopandas, which CI does not install, so these
tests validate its committed output rather than re-running it. That is the right
boundary anyway: the claim being defended is the published number, and a result
file that contradicts itself is the failure that would actually mislead someone.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
RESULT_PATH = ROOT / "data" / "weighting_comparison.json"

pytestmark = pytest.mark.skipif(
    not RESULT_PATH.exists(),
    reason="weighting_comparison.json not generated yet",
)


@pytest.fixture(scope="module")
def result():
    return json.loads(RESULT_PATH.read_text(encoding="utf-8"))


def test_both_weightings_are_recorded(result):
    assert set(result["weightings"]) == {"pca", "published"}
    for scheme in result["weightings"].values():
        assert scheme["source"]
        assert scheme["weights"]


def test_each_weighting_sums_to_one(result):
    for name, scheme in result["weightings"].items():
        total = sum(scheme["weights"].values())
        assert total == pytest.approx(1.0, abs=1e-9), f"{name} weights sum to {total}"


def test_both_schemes_score_the_same_indicators(result):
    pca = set(result["weightings"]["pca"]["weights"])
    published = set(result["weightings"]["published"]["weights"])
    assert pca == published


def test_each_ranking_is_a_permutation(result):
    rows = result["per_ward"]
    n = len(rows)
    assert sorted(r["rank_pca"] for r in rows) == list(range(1, n + 1))
    assert sorted(r["rank_published"] for r in rows) == list(range(1, n + 1))


def test_rank_shifts_are_internally_consistent(result):
    for row in result["per_ward"]:
        assert row["rank_shift"] == row["rank_published"] - row["rank_pca"]


def test_rank_shifts_cancel_out(result):
    """Two orderings of the same wards, so the moves have to net to zero. A
    non-zero sum would mean a ward was dropped or counted twice."""
    assert sum(row["rank_shift"] for row in result["per_ward"]) == 0


def test_correlations_are_in_range(result):
    agreement = result["agreement"]
    assert -1 <= agreement["kendall_tau"] <= 1
    assert -1 <= agreement["spearman_rho"] <= 1


def test_the_reported_maximum_shift_is_the_actual_maximum(result):
    rows = result["per_ward"]
    assert result["agreement"]["max_abs_rank_shift"] == max(abs(r["rank_shift"]) for r in rows)


def test_the_identical_rank_count_matches_the_rows(result):
    rows = result["per_ward"]
    counted = sum(1 for r in rows if r["rank_shift"] == 0)
    assert result["agreement"]["wards_with_identical_rank"] == counted
    assert result["agreement"]["n_wards"] == len(rows)


def test_the_top_five_overlap_matches_the_listed_rankings(result):
    agreement = result["agreement"]
    overlap = len(set(agreement["top_5_pca"]) & set(agreement["top_5_published"]))
    assert agreement["top_5_overlap"] == overlap


def test_the_top_five_lists_match_the_per_ward_ranks(result):
    rows = {r["ward_id"]: r for r in result["per_ward"]}
    for ward in result["agreement"]["top_5_pca"]:
        assert rows[ward]["rank_pca"] <= 5
    for ward in result["agreement"]["top_5_published"]:
        assert rows[ward]["rank_published"] <= 5
