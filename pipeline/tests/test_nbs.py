"""Tests for the NBS rule engine and the plantability filter (issue #98).

This is the logic most worth testing in the pipeline. A bug in run_pipeline.py
produces a visible failure. A bug here produces a confident, plausible, wrong
recommendation that a planner might act on, and nothing downstream would catch
it.

The plantability filter gets the most attention because it encodes a real
scientific dispute: restoration-potential maps count open grassland as
plantable (Bastin 2019), and planting native grassland destroys an ecosystem to
bank carbon (Veldman 2019). UCIP refuses those cells. A regression that
quietly flipped that behaviour would turn the project's most defensible feature
into its most damaging one.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

PIPELINE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PIPELINE_DIR))

from _nbs import (  # noqa: E402
    FLOOD_PRONE_DIST_M,
    WORLDCOVER_GRASSLAND,
    WORLDCOVER_NONPLANTABLE,
    fire_rules,
    is_plantable,
)

THRESHOLDS = {
    "hvi_p75": 60.0,
    "ndvi_p25": 0.25,
    "density_p75": 20000.0,
    "elderly_p75": 6.0,
    "hospital_p75": 2000.0,
    "impervious_p75": 50.0,
}


@dataclass
class Cell:
    """Stands in for a geopandas itertuples row."""
    HVI: float = 30.0
    NDVI: float = 0.5
    pop_density_km2: float = 5000.0
    elderly_pct: float = 3.0
    hospital_dist_m: float = 500.0
    impervious_pct: float = 20.0
    dist_to_water_m: float = 5000.0
    plantable: bool = True


def interventions(recs):
    return [r["intervention"] for r in recs]


# --------------------------------------------------------- plantability --

def test_native_grassland_is_never_plantable():
    """The Bastin/Veldman line. Planting here is the worst output this tool
    could produce, so it is refused regardless of how suitable the cell looks
    on every other measure."""
    assert is_plantable(WORLDCOVER_GRASSLAND, 0.0, 50.0) is False


@pytest.mark.parametrize("cover", sorted(WORLDCOVER_NONPLANTABLE))
def test_built_up_and_water_classes_are_not_plantable(cover):
    assert is_plantable(cover, 0.0, 50.0) is False


def test_a_suitable_cell_is_plantable():
    # Tree cover (10), unsealed ground, below the local impervious threshold.
    assert is_plantable(10, 20.0, 50.0) is True


def test_a_sealed_cell_has_nowhere_to_plant():
    assert is_plantable(10, 80.0, 50.0) is False


def test_the_impervious_test_is_strict_at_the_threshold():
    assert is_plantable(10, 50.0, 50.0) is False
    assert is_plantable(10, 49.9, 50.0) is True


def test_the_impervious_threshold_is_relative_not_absolute():
    """What counts as sealed differs between cities, so the same cell can be
    plantable under one local distribution and not another."""
    assert is_plantable(10, 40.0, 50.0) is True
    assert is_plantable(10, 40.0, 30.0) is False


def test_a_missing_land_cover_reading_is_not_plantable():
    """Absence of evidence is not evidence that planting is safe."""
    assert is_plantable(None, 10.0, 50.0) is False


def test_a_missing_impervious_reading_is_not_plantable():
    assert is_plantable(10, None, 50.0) is False


# ------------------------------------------------------------- the rules --

def test_a_comfortable_cell_gets_no_recommendation():
    assert fire_rules(Cell(), THRESHOLDS) == []


def test_hot_bare_and_suitable_gets_trees():
    recs = fire_rules(Cell(HVI=80, NDVI=0.1, plantable=True), THRESHOLDS)
    assert "Native tree planting + green corridors" in interventions(recs)
    assert recs[0]["citation"].startswith("Bastin")


def test_hot_bare_and_unsuitable_gets_non_tree_cooling_instead():
    """The branch that makes this more than a lookup table: the cell still
    needs cooling, it just must not be trees."""
    recs = fire_rules(Cell(HVI=80, NDVI=0.1, plantable=False), THRESHOLDS)
    names = interventions(recs)
    assert "Cool roofs + reflective pavements + cooling centres" in names
    assert "Native tree planting + green corridors" not in names
    assert recs[0]["citation"].startswith("Veldman")


def test_an_unsuitable_cell_is_never_left_with_nothing():
    """The two plantability arms share their trigger, so refusing trees must
    not mean refusing help."""
    hot_bare = Cell(HVI=80, NDVI=0.1, plantable=False)
    assert len(fire_rules(hot_bare, THRESHOLDS)) >= 1


def test_trees_and_cool_roofs_are_mutually_exclusive():
    for plantable in (True, False):
        names = interventions(fire_rules(Cell(HVI=80, NDVI=0.1, plantable=plantable), THRESHOLDS))
        assert not (
            "Native tree planting + green corridors" in names
            and "Cool roofs + reflective pavements + cooling centres" in names
        )


def test_a_cool_cell_gets_no_canopy_recommendation_however_bare():
    names = interventions(fire_rules(Cell(HVI=10, NDVI=0.01), THRESHOLDS))
    assert "Native tree planting + green corridors" not in names
    assert "Cool roofs + reflective pavements + cooling centres" not in names


def test_impervious_and_near_water_gets_rain_gardens():
    cell = Cell(impervious_pct=90, dist_to_water_m=FLOOD_PRONE_DIST_M - 1)
    assert "Rain gardens + water-sensitive urban design (WSUD)" in interventions(
        fire_rules(cell, THRESHOLDS)
    )


def test_impervious_but_far_from_water_does_not():
    cell = Cell(impervious_pct=90, dist_to_water_m=FLOOD_PRONE_DIST_M + 1)
    assert "Rain gardens + water-sensitive urban design (WSUD)" not in interventions(
        fire_rules(cell, THRESHOLDS)
    )


def test_the_flood_proxy_boundary_is_inclusive():
    cell = Cell(impervious_pct=90, dist_to_water_m=FLOOD_PRONE_DIST_M)
    assert "Rain gardens + water-sensitive urban design (WSUD)" in interventions(
        fire_rules(cell, THRESHOLDS)
    )


def test_dense_with_no_open_space_gets_pocket_parks():
    cell = Cell(pop_density_km2=30000, NDVI=0.1)
    assert "Pocket parks" in interventions(fire_rules(cell, THRESHOLDS))


def test_elderly_with_poor_hospital_access_gets_cooling_centres():
    cell = Cell(elderly_pct=9, hospital_dist_m=5000)
    assert "Cooling centres, priority siting" in interventions(fire_rules(cell, THRESHOLDS))


def test_either_condition_alone_does_not_fire_the_cooling_centre_rule():
    assert "Cooling centres, priority siting" not in interventions(
        fire_rules(Cell(elderly_pct=9, hospital_dist_m=100), THRESHOLDS)
    )
    assert "Cooling centres, priority siting" not in interventions(
        fire_rules(Cell(elderly_pct=1, hospital_dist_m=5000), THRESHOLDS)
    )


def test_several_rules_can_fire_for_one_cell():
    cell = Cell(
        HVI=90, NDVI=0.05, plantable=True,
        pop_density_km2=30000, elderly_pct=9, hospital_dist_m=5000,
        impervious_pct=90, dist_to_water_m=100,
    )
    names = interventions(fire_rules(cell, THRESHOLDS))
    assert len(names) == 4
    assert len(set(names)) == 4


def test_every_recommendation_carries_a_rationale_and_a_citation():
    """The project's claim is that every recommendation is cited. An
    uncited one would break that claim quietly."""
    cell = Cell(
        HVI=90, NDVI=0.05, plantable=False,
        pop_density_km2=30000, elderly_pct=9, hospital_dist_m=5000,
        impervious_pct=90, dist_to_water_m=100,
    )
    for rec in fire_rules(cell, THRESHOLDS):
        assert rec["rationale"].strip()
        assert rec["citation"].strip()
        assert rec["priority"] in (1, 2, 3)


def test_thresholds_are_inclusive_where_the_comparison_says_so():
    """A cell sitting exactly on the 75th percentile counts as high. Worth
    pinning: an off-by-one here silently changes how many cells qualify."""
    on_threshold = Cell(HVI=THRESHOLDS["hvi_p75"], NDVI=THRESHOLDS["ndvi_p25"], plantable=True)
    assert "Native tree planting + green corridors" in interventions(
        fire_rules(on_threshold, THRESHOLDS)
    )

    just_below = Cell(HVI=THRESHOLDS["hvi_p75"] - 0.01, NDVI=THRESHOLDS["ndvi_p25"], plantable=True)
    assert "Native tree planting + green corridors" not in interventions(
        fire_rules(just_below, THRESHOLDS)
    )
