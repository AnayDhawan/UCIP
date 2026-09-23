"""Plausibility bounds for pipeline output, and the checks over them (issue #91).

Why a gate exists at all:
    Stages emit warnings and exit 2 for some sanity checks, but nothing checked
    the finished dataset systematically. A refresh that silently produced
    wrong-but-well-formed data looked exactly like a good one, and the automated
    refresh workflow would have opened a PR for it either way. Wrong numbers
    that arrive looking correct are the failure mode this project can least
    afford, given the output is a spending recommendation.

What the bounds are and are not:
    They are physical and definitional limits plus generous envelopes around
    what Mumbai actually looks like. They are deliberately wider than the
    observed data, because the job is to catch a broken run, not to freeze the
    current numbers. A real month-to-month change must pass; a unit error, a
    failed reprojection, an empty composite or a rescale applied twice must not.

    Where a bound is physical (NDVI in -1..1, a percentage in 0..100) it is
    exact. Where it is an envelope (land surface temperature for a tropical
    coastal city in the dry season) it is loose and labelled as such, and the
    reasoning is written beside it rather than left as a magic number.

City-specificity:
    The temperature and density envelopes are Mumbai's. A second city with a
    different climate needs its own, which is why they are data here rather than
    literals scattered through the stages. Until then a non-Mumbai run should
    expect to widen these deliberately, not to have them quietly pass.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Bound:
    low: float
    high: float
    reason: str
    # A physical bound cannot be exceeded by real data, however unusual. An
    # envelope can, in principle, which is why the two are distinguished: one
    # is a bug, the other is worth a second look.
    physical: bool = False


# Observed Mumbai ranges as of the 2026-09 dataset, for context on how much
# room each envelope leaves:
#   LST_C 26.2..40.0, NDVI -0.07..0.71, pop_density 16..115272,
#   elderly_pct 4.0..5.6, slum_pct 0..68.6, hospital_dist_m 3.9..6199,
#   impervious_pct 0..96.8, HVI 0..100
CELL_BOUNDS: dict[str, Bound] = {
    "LST_C": Bound(
        10.0, 65.0,
        "Dry-season land surface temperature for a tropical coastal city. Not "
        "air temperature, and a sunlit roof reads far hotter, hence the high "
        "ceiling. Below 10 means the composite is empty or in Kelvin.",
    ),
    "NDVI": Bound(-1.0, 1.0, "NDVI is a normalised difference index.", physical=True),
    "NDVI_prev": Bound(-1.0, 1.0, "As NDVI.", physical=True),
    "pop_density_km2": Bound(
        0.0, 1_000_000.0,
        "Mumbai's densest wards reach six figures per square kilometre. The "
        "ceiling catches a unit error, such as people per square metre.",
    ),
    "elderly_pct": Bound(0.0, 100.0, "A percentage.", physical=True),
    "slum_pct": Bound(0.0, 100.0, "A percentage.", physical=True),
    "impervious_pct": Bound(0.0, 100.0, "A percentage.", physical=True),
    "hospital_dist_m": Bound(
        0.0, 100_000.0,
        "Straight-line distance in metres within one city. A value in the "
        "hundreds of thousands means metres and kilometres were confused.",
    ),
    "HVI": Bound(0.0, 100.0, "Rescaled to 0-100 by stage 05.", physical=True),
}

WARD_BOUNDS: dict[str, Bound] = {
    "HVI": Bound(0.0, 100.0, "Mean of member cells, so it inherits their range.", physical=True),
    "dominant_share": Bound(
        0.0, 1.0, "A share of total absolute contribution.", physical=True
    ),
}

# How far the cell count may move between refreshes before it is suspicious.
# The grid is derived from ward boundaries that essentially never change, so a
# real refresh should not move it at all; the tolerance exists for a boundary
# correction, not for routine drift.
CELL_COUNT_TOLERANCE = 0.05


def check_bounds(
    rows: list[dict],
    bounds: dict[str, Bound],
    id_field: str,
    label: str,
) -> list[str]:
    """Every value outside its bound, as one message each.

    Reports the offending id and value rather than a count, because the first
    question on a failed gate is always which record and how far out.
    """
    failures: list[str] = []

    for column, bound in bounds.items():
        present = [r for r in rows if r.get(column) is not None]
        if not present:
            # A column that vanished entirely is a worse failure than one out
            # of range, and would otherwise pass silently as "nothing to check".
            if any(column in r for r in rows):
                continue
            failures.append(f"{label}: column '{column}' is missing from every record")
            continue

        for row in present:
            value = row[column]
            if not isinstance(value, (int, float)):
                failures.append(
                    f"{label}: {row.get(id_field)}: {column} is {value!r}, not a number"
                )
                continue
            if value < bound.low or value > bound.high:
                kind = "physically impossible" if bound.physical else "implausible"
                failures.append(
                    f"{label}: {row.get(id_field)}: {column} = {value:g} is {kind}, "
                    f"outside {bound.low:g}..{bound.high:g}. {bound.reason}"
                )

    return failures


def check_nulls(rows: list[dict], columns: list[str], id_field: str, label: str) -> list[str]:
    """Columns that went entirely null, which a bounds check cannot see."""
    failures = []
    for column in columns:
        if rows and all(r.get(column) is None for r in rows):
            failures.append(
                f"{label}: column '{column}' is null for all {len(rows)} records. "
                "A stage produced no data rather than bad data."
            )
    return failures


def check_count(actual: int, expected: int, tolerance: float, label: str) -> list[str]:
    """Record count against the previous run, within a tolerance."""
    if expected <= 0:
        return []
    drift = abs(actual - expected) / expected
    if drift > tolerance:
        return [
            f"{label}: {actual} records against {expected} last time, "
            f"a {drift:.1%} change over the {tolerance:.0%} tolerance. "
            "The grid comes from ward boundaries that essentially never move."
        ]
    return []


def check_rescale(values: list[float], label: str) -> list[str]:
    """A 0-100 rescale should actually reach both ends.

    If it does not, the rescale was skipped, applied twice, or applied to a
    constant series. The values would all still sit inside 0..100 and pass every
    bounds check, which is why this is separate.
    """
    if not values:
        return []
    low, high = min(values), max(values)
    if low > 1e-6 or high < 100 - 1e-6:
        return [
            f"{label}: rescaled values span {low:g}..{high:g} rather than 0..100. "
            "The rescale did not take, so the scores are not comparable to any "
            "previous run."
        ]
    return []
