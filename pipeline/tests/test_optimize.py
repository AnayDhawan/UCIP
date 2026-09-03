"""Tests for the budget allocator (issue #67).

The behaviour that matters most is the refusal: this stage must not allocate
money against a cost nobody sourced. F9 was cut from the original build for
exactly that reason, and an optimiser is the most authoritative-looking output
this project can emit.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

PIPELINE_DIR = Path(__file__).resolve().parent.parent
ROOT = PIPELINE_DIR.parent
sys.path.insert(0, str(PIPELINE_DIR))

def _stub_heavy_imports():
    """Let this module import without the geospatial stack installed.

    The functions under test here are pure arithmetic, but they live in a stage
    module that imports geopandas and ee at the top. CI's pipeline job installs
    requirements-dev.txt only, deliberately, so that a test run does not pull in
    geopandas, rasterio and osmnx to check a least-squares fit.

    Stubbing rather than skipping: the significance testing is exactly the logic
    most worth guarding in CI, since without it this stage published a confident
    and false claim about every ward in Mumbai.
    """
    import types

    for name in ("geopandas", "ee"):
        if name not in sys.modules:
            try:
                __import__(name)
            except ImportError:
                sys.modules[name] = types.ModuleType(name)


_stub_heavy_imports()


COSTS_PATH = ROOT / "config" / "intervention_costs.json"


@pytest.fixture(scope="module")
def opt():
    spec = importlib.util.spec_from_file_location("opt", PIPELINE_DIR / "15_optimize.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def costs():
    return json.loads(COSTS_PATH.read_text(encoding="utf-8"))


class TestCostConfigIntegrity:
    def test_every_sourced_cost_has_a_real_citation(self, costs):
        for key, spec in costs["interventions"].items():
            if not spec.get("sourced"):
                continue
            assert spec.get("cost") is not None, f"{key}: sourced but has no cost"
            assert spec.get("cost", 0) > 0, f"{key}: cost must be positive"
            source = spec.get("source", "")
            assert len(source) > 20, f"{key}: sourced costs need a real citation, got {source!r}"
            assert spec.get("source_url", "").startswith("http"), f"{key}: needs a source URL"

    def test_every_unsourced_cost_explains_itself(self, costs):
        # An unsourced entry is a deliberate record of a gap, not an oversight.
        for key, spec in costs["interventions"].items():
            if spec.get("sourced"):
                continue
            assert spec.get("cost") is None, f"{key}: unsourced entries must not carry a number"
            assert len(spec.get("_why_unsourced", "")) > 40, f"{key}: must say why it is unsourced"

    def test_no_intervention_is_silently_neither(self, costs):
        for key, spec in costs["interventions"].items():
            assert "sourced" in spec, f"{key}: must state whether its cost is sourced"

    def test_cool_roof_costs_are_ordered_by_material(self, costs):
        iv = costs["interventions"]
        assert iv["cool_roof_lime"]["cost"] < iv["cool_roof_coating"]["cost"]
        assert iv["cool_roof_coating"]["cost"] < iv["cool_roof_tiles"]["cost"]

    def test_lime_cost_matches_the_published_figure(self, costs):
        # NRDC: the Ahmedabad pilot paid about Rs 0.5 per sq ft.
        # 0.5 x 10.7639 sq ft/m2 = Rs 5.38/m2.
        assert costs["interventions"]["cool_roof_lime"]["cost"] == pytest.approx(5.38, abs=0.01)


class TestCoolingModel:
    def test_matches_the_cited_santamouris_coefficient(self, opt):
        # 0.6 C per +0.1 albedo, the conservative end of the published range and
        # the same headline the frontend's coefficients.ts uses.
        assert opt.cool_roof_cooling_c(0.1) == pytest.approx(0.6)

    def test_scales_linearly_with_albedo(self, opt):
        assert opt.cool_roof_cooling_c(0.2) == pytest.approx(1.2)
        assert opt.cool_roof_cooling_c(0.4) == pytest.approx(2.4)

    def test_zero_albedo_gain_gives_no_cooling(self, opt):
        assert opt.cool_roof_cooling_c(0.0) == 0.0

    def test_assumed_albedo_gain_is_declared(self, opt):
        # An assumption, not a measurement, and it must be visible as a constant
        # rather than buried in an expression.
        assert 0 < opt.ASSUMED_ALBEDO_GAIN <= 1.0

    def test_roof_share_is_a_fraction_of_impervious_not_all_of_it(self, opt):
        # Impervious surface includes roads and paving, so treating all of it as
        # roof would overstate every ward's treatable area.
        assert 0 < opt.ROOF_SHARE_OF_IMPERVIOUS < 1.0
