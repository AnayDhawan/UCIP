"""The Heat Vulnerability Index indicator set, in one place (issue #95).

The direction table used to be copied into five files (05_hvi, 08_sensitivity,
uncertainty, compare_weightings), each with its own idea of
what the seven indicators were. That is tolerable while the list never changes
and a trap the moment it does: adding an indicator meant finding every copy, and
missing one would not raise an error. It would compute a ranking from a
different index than the one the others were describing.

Direction is +1 when a higher value adds to vulnerability and -1 when it
protects. NDVI is the only protective one.

Two tiers:

REQUIRED indicators come from satellite and open geodata that exist for any
city, so a run without them is broken and stage 04 fails.

OPTIONAL indicators need an input a city may not have. `child_pct` comes from a
ward-level Census table, and only Mumbai has one wired in. A city without it
runs on the required set rather than failing, and `present()` is how every
stage finds out which indicators a given run actually has.
"""

from __future__ import annotations

from typing import Iterable

# Order is the canonical display order, and it is the order the frontend lists
# the factors in. It is not the order PCA sees them in, which does not matter.
DIRECTIONS: dict[str, int] = {
    "LST_C": 1,
    "NDVI": -1,
    "pop_density_km2": 1,
    "child_pct": 1,
    "slum_pct": 1,
    "hospital_dist_m": 1,
    "impervious_pct": 1,
}

OPTIONAL: tuple[str, ...] = ("child_pct",)

REQUIRED: list[str] = [c for c in DIRECTIONS if c not in OPTIONAL]


def present(columns: Iterable[str]) -> list[str]:
    """The indicators a dataset actually carries, in canonical order.

    Required indicators are expected to be there; stage 04 enforces that. This
    exists so that the optional ones are picked up when present and skipped
    when not, by one rule rather than one guess per stage.
    """
    available = set(columns)
    return [c for c in DIRECTIONS if c in available]
