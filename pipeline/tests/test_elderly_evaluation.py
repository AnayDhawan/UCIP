"""Checks on the elderly_pct evaluation (issue #95).

elderly_evaluation.py imports pandas and scikit-learn, neither of which CI
installs, for the same reason test_uncertainty.py does not re-run the
bootstrap: pipeline/tests/ deliberately runs without requirements.txt's
geospatial and modelling stack.

So the checks that matter validate the committed report and the committed
dataset using the standard library, which is the right boundary anyway. The
published finding is the claim, and the failure that would actually mislead
someone is that finding silently ceasing to hold on a refresh while
methodology.md §10a still asserts it.

The pure-function tests at the bottom need the real module and skip themselves
when it cannot be imported, so they run locally and anywhere with the full
stack.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
REPORT_PATH = ROOT / "data" / "elderly_evaluation.json"
CELLS_PATH = ROOT / "data" / "cells_hvi.geojson"

# Mumbai is two revenue districts and the 2011 Census publishes age structure
# per district. These are the nine island wards of Mumbai City.
MUMBAI_CITY_WARDS = {"A", "B", "C", "D", "E", "F/N", "F/S", "G/N", "G/S"}

INDICATORS = [
    "LST_C",
    "NDVI",
    "pop_density_km2",
    "elderly_pct",
    "slum_pct",
    "hospital_dist_m",
    "impervious_pct",
]


@pytest.fixture(scope="module")
def report():
    if not REPORT_PATH.exists():
        pytest.skip("elderly_evaluation.json not generated yet")
    return json.loads(REPORT_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def cells():
    if not CELLS_PATH.exists():
        pytest.skip("cells_hvi.geojson not present")
    raw = json.loads(CELLS_PATH.read_text(encoding="utf-8"))
    rows = [f["properties"] for f in raw["features"]]
    return [r for r in rows if all(r.get(k) is not None for k in INDICATORS)]


class TestTheCommittedFinding:
    """The numbers methodology.md §10a and the #95 decision quote."""

    def test_the_report_records_what_it_measured(self, report):
        for key in ("information", "administrative_split", "rank_effect"):
            assert key in report, f"report is missing {key}"
        assert report["n_cells"] > 0

    def test_elderly_pct_is_effectively_two_valued(self, report):
        info = report["information"]
        assert info["most_common_share"] > 0.75
        assert info["top_two_share"] > 0.95

    def test_it_has_the_least_spread_of_the_seven_indicators(self, report):
        assert report["information"]["lowest_cv_indicator"] == "elderly_pct"

    def test_the_split_is_exactly_the_district_boundary(self, report):
        split = report["administrative_split"]
        assert split["distinct_ward_values"] == 2
        assert split["matches_district_boundary_exactly"] is True

    def test_dropping_it_moves_the_published_ranking(self, report):
        # A layer carrying one bit should not be reordering half the table.
        # This is the number §10a quotes, and the reason the finding matters
        # rather than being a curiosity about a weak indicator.
        effect = report["rank_effect"]
        assert effect["wards_changing_rank"] >= 10
        assert effect["largest_move_places"] >= 2


class TestAgainstTheDatasetItself:
    """Recomputed from the committed cells, so the report cannot drift from it."""

    def test_two_values_cover_almost_every_cell(self, cells):
        values = Counter(round(c["elderly_pct"], 4) for c in cells)
        total = sum(values.values())
        assert values.most_common(1)[0][1] / total > 0.75
        assert sum(n for _, n in values.most_common(2)) / total > 0.95

    def test_every_ward_carries_its_district_value(self, cells):
        """The finding that reframed issue #95.

        If each ward's value is decided entirely by which revenue district it
        sits in, the layer carries district age structure and nothing below it,
        so it is not the 100 m measured surface the raster's resolution implies.
        """
        by_ward = defaultdict(Counter)
        for cell in cells:
            by_ward[cell["ward_id"]][round(cell["elderly_pct"], 3)] += 1
        # Rounded before taking the most common value. A ward on the district
        # line has cells straddling it, so unrounded it has no repeated value
        # at all and "most common" becomes an artefact of float noise.
        dominant = {w: c.most_common(1)[0][0] for w, c in by_ward.items()}

        city = {w: v for w, v in dominant.items() if w in MUMBAI_CITY_WARDS}
        suburban = {w: v for w, v in dominant.items() if w not in MUMBAI_CITY_WARDS}

        assert len(set(city.values())) == 1, f"Mumbai City wards disagree: {city}"
        assert len(set(suburban.values())) == 1, f"Suburban wards disagree: {suburban}"
        assert set(city.values()).isdisjoint(suburban.values())

    def test_the_blending_is_marginal(self, cells):
        # Only wards on the boundary hold more than one value, so the layer is
        # a district dummy plus edge effects, not a surface.
        distinct = defaultdict(set)
        for cell in cells:
            distinct[cell["ward_id"]].add(round(cell["elderly_pct"], 3))
        single = sum(1 for values in distinct.values() if len(values) == 1)
        assert single >= 16, f"only {single} of {len(distinct)} wards are single-valued"

    def test_it_really_does_have_the_least_spread(self, cells):
        """Recomputed rather than read back, since it is a comparative claim."""

        def cv(key: str) -> float:
            values = [c[key] for c in cells]
            mean = sum(values) / len(values)
            variance = sum((v - mean) ** 2 for v in values) / len(values)
            return (variance**0.5) / abs(mean) if mean else float("inf")

        spreads = {key: cv(key) for key in INDICATORS}
        assert min(spreads, key=spreads.get) == "elderly_pct"


def _load_module():
    """Imports elderly_evaluation.py, which needs pandas and scikit-learn."""
    import importlib.util
    import sys

    pipeline_dir = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(pipeline_dir))
    spec = importlib.util.spec_from_file_location(
        "elderly_evaluation", pipeline_dir / "elderly_evaluation.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestPureFunctions:
    """Runs wherever the full stack exists. Skipped in CI, which has neither dep."""

    @pytest.fixture(scope="class")
    def mod(self):
        # exc_type is explicit because pytest 9.1 makes the default an error:
        # a module that exists but raises ImportError on import is usually a
        # broken install rather than an absent one, and worth failing on. Here
        # it is genuinely absent in CI by design, so ImportError is expected.
        pytest.importorskip("pandas", exc_type=ImportError)
        pytest.importorskip("sklearn", exc_type=ImportError)
        return _load_module()

    def test_zero_variance_z_scores_to_zeros_rather_than_nan(self, mod):
        """The degenerate case, which is the one this indicator is nearest.

        A constant column has to standardise to zeros, not NaN, or a
        near-degenerate indicator poisons every downstream sum.
        """
        import pandas as pd

        assert mod.zscore(pd.Series([4.76] * 10)).tolist() == [0.0] * 10

    def test_rescale_handles_a_flat_series(self, mod):
        import pandas as pd

        assert mod.rescale_0_100(pd.Series([7.0, 7.0, 7.0])).tolist() == [50.0] * 3

    def test_rescale_maps_to_the_full_range(self, mod):
        import pandas as pd

        out = mod.rescale_0_100(pd.Series([1.0, 5.0, 9.0]))
        assert out.iloc[0] == pytest.approx(0.0)
        assert out.iloc[-1] == pytest.approx(100.0)

    def test_ranking_is_a_permutation_of_the_wards(self, mod):
        import pandas as pd

        rows = []
        for w, ward in enumerate("ABCD"):
            for i in range(5):
                rows.append(
                    {
                        "ward_id": ward,
                        "LST_C": 30 + i * 0.7 + w * 1.4,
                        "NDVI": 0.5 - i * 0.05 - w * 0.06,
                        "pop_density_km2": 10000 + i * 900 + w * 4200,
                        "elderly_pct": 4.757 if w < 2 else 5.586,
                        "slum_pct": i * 2.5 + w * 3.1,
                        "hospital_dist_m": 500 + i * 220 + w * 310,
                        "impervious_pct": 20 + i * 8 + w * 5.5,
                    }
                )
        ranks = mod.ward_ranks(pd.DataFrame(rows), mod.INDICATORS)
        assert sorted(ranks.tolist()) == [1, 2, 3, 4]

    def test_the_district_ward_list_is_the_real_one(self, mod):
        # If this drifts, the evaluation reports "matches the district
        # boundary" for a boundary that is not Mumbai's, which is a wrong
        # finding rather than a missing one.
        assert mod.MUMBAI_CITY_WARDS == MUMBAI_CITY_WARDS
