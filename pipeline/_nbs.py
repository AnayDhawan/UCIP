"""The NBS decision logic, kept free of geospatial dependencies (issue #98).

06_nbs.py needs geopandas to read layers and Earth Engine to fetch land cover.
Deciding what to recommend for a cell needs neither: it is a function of seven
numbers and a land-cover class. Keeping it here means CI can test it, and CI
installs requirements-dev.txt rather than the full stack.

This is the logic most worth testing in the whole pipeline. A bug in
run_pipeline.py produces a visible failure; a bug here produces a confident,
plausible, wrong recommendation that somebody might act on. In particular the
plantability filter exists to stop the tool recommending afforestation on native
grassland, which is the single most damaging output it could produce, and
nothing was checking that it worked.
"""

from __future__ import annotations

from typing import Any

# ESA WorldCover class codes.
WORLDCOVER_GRASSLAND = 30
WORLDCOVER_NONPLANTABLE = {50, 80, 90, 95}  # built-up, water, wetland, mangrove
WORLDCOVER_WATER_LIKE = {80, 90, 95}

# A cell within this distance of mapped water is treated as flood-exposed. A
# proxy, not a hydrology model, and labelled as such in the citation it emits.
FLOOD_PRONE_DIST_M = 500


# Every WorldCover v200 class code. Used to reject a value that is not one,
# rather than letting an unrecognised code fall through as "plantable".
WORLDCOVER_CLASSES = {10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100}


def normalise_worldcover_class(value: float | int | None) -> int | None:
    """A WorldCover class code as an integer, or None if it is not one.

    This exists because of a real failure in published output. Earth Engine's
    mode reducer returns a float, and floating-point arithmetic means a cell
    whose dominant class is built-up can arrive as 50.00000000000015 or
    49.99999999999996 rather than 50. Both compare False against the integer
    50, so `worldcover_class in WORLDCOVER_NONPLANTABLE` silently failed and
    the cell was treated as having no disqualifying land cover.

    In the committed 541-cell dataset that affected 301 cells, and 175 of the
    337 cells published as plantable should have been refused: 127 built-up,
    30 mangrove, 17 open water and 1 native grassland. Recommending tree
    planting on mangrove is the precise failure this filter exists to prevent.

    Rounds rather than truncates, because the error goes in both directions.
    Returns None for anything that is not a real class code, so an unexpected
    value is refused rather than waved through; see is_plantable, where None
    means not plantable.
    """
    if value is None:
        return None
    try:
        code = round(float(value))
    except (TypeError, ValueError):
        return None
    return code if code in WORLDCOVER_CLASSES else None


def is_plantable(
    worldcover_class: float | None,
    impervious_pct: float | None,
    impervious_threshold: float,
) -> bool:
    """Whether native tree planting is ecologically defensible on this cell.

    Three conditions, and the second is the one that matters:

    - Not built-up, water, wetland or mangrove. Trees do not go there.
    - Not native grassland. WorldCover class 30 is the Bastin/Veldman dispute in
      one number: restoration potential maps count open grassland as plantable,
      and planting it destroys a native ecosystem to bank carbon. UCIP refuses
      it and recommends non-tree cooling there instead.
    - Enough unsealed ground to physically plant in, judged against the local
      impervious distribution rather than an absolute figure, because what
      counts as sealed differs city to city.

    A cell with no land-cover reading is not plantable. Absence of evidence is
    not evidence that planting is safe.
    """
    # Normalised first. Comparing the raw float against integer class codes is
    # what let 175 mangrove, water and built-up cells through; see
    # normalise_worldcover_class.
    code = normalise_worldcover_class(worldcover_class)
    if code is None:
        return False
    if code in WORLDCOVER_NONPLANTABLE:
        return False
    if code == WORLDCOVER_GRASSLAND:
        return False
    if impervious_pct is None:
        return False
    return impervious_pct < impervious_threshold


def fire_rules(row: Any, thresholds: dict[str, float]) -> list[dict[str, Any]]:
    """Every intervention that applies to one cell, with its citation.

    `row` is anything exposing the indicator names as attributes, which is what
    geopandas' itertuples gives the pipeline and what a small stand-in gives the
    tests.

    Priority is the urgency of the intervention, not the order rules are
    checked. Several can fire for one cell, and a cell can carry two priority-1
    recommendations for different reasons.
    """
    recs: list[dict[str, Any]] = []

    hvi_high = row.HVI >= thresholds["hvi_p75"]
    canopy_low = row.NDVI <= thresholds["ndvi_p25"]
    density_high = row.pop_density_km2 >= thresholds["density_p75"]
    open_space_low = row.NDVI <= thresholds["ndvi_p25"]
    elderly_high = row.elderly_pct >= thresholds["elderly_p75"]
    hospital_access_low = row.hospital_dist_m >= thresholds["hospital_p75"]
    impervious_high = row.impervious_pct >= thresholds["impervious_p75"]
    flood_prone = row.dist_to_water_m <= FLOOD_PRONE_DIST_M

    # The plantability branch. Both arms fire on the same vulnerability and
    # canopy test, so a hot, bare, ecologically unsuitable cell still gets a
    # cooling recommendation rather than nothing at all.
    if hvi_high and canopy_low and row.plantable:
        recs.append({
            "intervention": "Native tree planting + green corridors",
            "rationale": "High vulnerability, low canopy, ecologically suitable for restoration",
            "citation": "Bastin et al. 2019, Science",
            "priority": 1,
        })
    elif hvi_high and canopy_low and not row.plantable:
        recs.append({
            "intervention": "Cool roofs + reflective pavements + cooling centres",
            "rationale": "High vulnerability, low canopy, but native-grassland/built-up cell: "
                         "afforestation would backfire ecologically",
            "citation": "Veldman et al. 2019, Science (response to Bastin 2019)",
            "priority": 1,
        })

    if impervious_high and flood_prone:
        recs.append({
            "intervention": "Rain gardens + water-sensitive urban design (WSUD)",
            "rationale": "Highly impervious cell near mapped water/wetland: runoff and heat compound risk",
            "citation": "Methodology proxy: WorldCover water-distance < 500m (no dedicated hydrology layer in P0)",
            "priority": 2,
        })

    if density_high and open_space_low:
        recs.append({
            "intervention": "Pocket parks",
            "rationale": "High population density with little existing green/open space",
            "citation": "C40 Urban Cooling Toolbox",
            "priority": 3,
        })

    if elderly_high and hospital_access_low:
        recs.append({
            "intervention": "Cooling centres, priority siting",
            "rationale": "High elderly share combined with poor hospital access",
            "citation": "Knowlton et al. 2014 (Ahmedabad HAP impact study)",
            "priority": 1,
        })

    return recs
