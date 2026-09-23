"""Invariant checks on the committed science outputs (issue #98).

Stages 05 and 08 import geopandas, numpy, scikit-learn, scipy and matplotlib,
none of which CI installs, so they cannot be imported in a test. What can be
checked without them is the property that matters to a reader: that the numbers
the project publishes hold together.

These are invariants, not regressions against fixed values. A refresh is meant
to move the numbers; it is not meant to produce an HVI of 140, a rank of 0, or
a top-5 list that disagrees with the ranking it came from.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
DATA = ROOT / "data"

INDICATORS = [
    "LST_C",
    "NDVI",
    "pop_density_km2",
    "elderly_pct",
    "slum_pct",
    "hospital_dist_m",
    "impervious_pct",
]


def load(name: str):
    path = DATA / name
    if not path.exists():
        pytest.skip(f"{name} not generated yet")
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def wards():
    return [f["properties"] for f in load("wards_hvi.geojson")["features"]]


@pytest.fixture(scope="module")
def cells():
    return [f["properties"] for f in load("cells_hvi.geojson")["features"]]


@pytest.fixture(scope="module")
def pca_log():
    return load("hvi_pca_log.json")


@pytest.fixture(scope="module")
def sensitivity():
    return load("sensitivity.json")


# ----------------------------------------------------------- HVI itself --

def test_every_cell_score_is_in_range(cells):
    """05_hvi.py rescales to 0-100. A score outside it means the rescale was
    skipped or applied twice, which would look plausible on a map."""
    for cell in cells:
        assert 0 <= cell["HVI"] <= 100, f"{cell['grid_id']} scored {cell['HVI']}"


def test_the_rescale_actually_spans_the_range(cells):
    scores = [c["HVI"] for c in cells]
    assert min(scores) == pytest.approx(0, abs=1e-6)
    assert max(scores) == pytest.approx(100, abs=1e-6)


def test_every_ward_score_is_in_range(wards):
    for ward in wards:
        assert 0 <= ward["HVI"] <= 100, f"{ward['ward_id']} scored {ward['HVI']}"


def test_ward_ranks_are_a_dense_permutation(wards):
    ranks = sorted(w["rank"] for w in wards)
    assert ranks == list(range(1, len(wards) + 1))


def test_rank_order_matches_score_order(wards):
    """Rank 1 is the most vulnerable. A ward ranked above another with a lower
    score would invert the single claim the dashboard makes."""
    ordered = sorted(wards, key=lambda w: w["rank"])
    scores = [w["HVI"] for w in ordered]
    assert scores == sorted(scores, reverse=True)


def test_every_cell_belongs_to_a_ward(cells, wards):
    ward_ids = {w["ward_id"] for w in wards}
    for cell in cells:
        assert cell["ward_id"] in ward_ids


def test_ward_cell_counts_match_the_cells_that_exist(cells, wards):
    counted: dict[str, int] = {}
    for cell in cells:
        counted[cell["ward_id"]] = counted.get(cell["ward_id"], 0) + 1
    for ward in wards:
        assert ward["n_cells"] == counted.get(ward["ward_id"], 0)


def test_every_cell_carries_a_contribution_for_every_indicator(cells):
    for cell in cells:
        for indicator in INDICATORS:
            assert f"contrib_{indicator}" in cell


def test_ward_contributions_are_the_mean_of_their_cells(cells, wards):
    """The explainability claim is that a ward score decomposes into these. If
    the rollup used a sum, or dropped cells, the breakdown shown in the ward
    dialog would not describe the score above it."""
    by_ward: dict[str, list[dict]] = {}
    for cell in cells:
        by_ward.setdefault(cell["ward_id"], []).append(cell)

    for ward in wards:
        members = by_ward[ward["ward_id"]]
        for indicator in INDICATORS:
            key = f"contrib_{indicator}"
            expected = sum(c[key] for c in members) / len(members)
            assert ward[key] == pytest.approx(expected, abs=1e-9)


# ---------------------------------------------------------- the weights --

def test_the_weights_sum_to_one(pca_log):
    assert sum(pca_log["weights"].values()) == pytest.approx(1.0, abs=1e-9)


def test_every_weight_is_positive(pca_log):
    """Weights are absolute PC1 loadings, renormalised. A negative one would
    mean the sign flip was applied to the wrong thing, and an indicator would
    be reducing vulnerability when it should raise it."""
    for name, weight in pca_log["weights"].items():
        assert weight > 0, f"{name} has weight {weight}"


def test_every_indicator_is_weighted(pca_log):
    assert set(pca_log["weights"]) == set(INDICATORS)


def test_the_fallback_flag_agrees_with_the_explained_variance(pca_log):
    """The fallback trigger is documented as a floor on PC1's explained
    variance. The flag and the number must not disagree, or the methodology
    page describes a decision the code did not make."""
    threshold = float(pca_log["fallback_trigger"].rsplit("<", 1)[1])
    expected = pca_log["explained_variance_pc1"] < threshold
    assert pca_log["fallback_used"] is expected


def test_the_weight_source_matches_the_fallback_flag(pca_log):
    if pca_log["fallback_used"]:
        assert pca_log["weight_source"].startswith("fallback")
    else:
        assert not pca_log["weight_source"].startswith("fallback")


def test_explained_variance_is_a_fraction(pca_log):
    assert 0 <= pca_log["explained_variance_pc1"] <= 1


# ------------------------------------------------- sensitivity analysis --

def test_one_run_per_indicator_per_direction(sensitivity):
    assert sensitivity["n_runs"] == len(sensitivity["runs"])
    assert sensitivity["n_runs"] == len(INDICATORS) * 2


def test_every_indicator_is_perturbed_both_ways(sensitivity):
    seen = {(r["indicator"], r["perturbation"]) for r in sensitivity["runs"]}
    for indicator in INDICATORS:
        assert (indicator, "+20%") in seen
        assert (indicator, "-20%") in seen


def test_each_tau_is_a_correlation(sensitivity):
    for run in sensitivity["runs"]:
        assert -1 <= run["kendall_tau"] <= 1


def test_the_mean_tau_is_the_mean_of_the_runs(sensitivity):
    taus = [r["kendall_tau"] for r in sensitivity["runs"]]
    assert sensitivity["mean_kendall_tau"] == pytest.approx(sum(taus) / len(taus))


def test_the_mean_overlap_is_the_mean_of_the_runs(sensitivity):
    overlaps = [r["top5_overlap"] for r in sensitivity["runs"]]
    assert sensitivity["mean_top5_overlap"] == pytest.approx(sum(overlaps) / len(overlaps))


def test_the_stability_claim_matches_the_runs(sensitivity):
    """all_top5_stable is the headline the methodology page leans on. It has to
    follow from the runs rather than being asserted alongside them."""
    every_run_kept_all_five = all(r["top5_overlap"] == 5 for r in sensitivity["runs"])
    assert sensitivity["all_top5_stable"] is every_run_kept_all_five


def test_each_run_reports_an_overlap_consistent_with_its_ranking(sensitivity):
    baseline = set(sensitivity["baseline_top5"])
    for run in sensitivity["runs"]:
        assert run["top5_overlap"] == len(baseline & set(run["top5_ranking"]))


def test_the_baseline_top5_matches_the_published_ranking(sensitivity, wards):
    ranked = [w["ward_id"] for w in sorted(wards, key=lambda w: w["rank"])]
    assert sensitivity["baseline_top5"] == ranked[:5]
