"""Index interpretation helpers, kept free of geospatial dependencies.

05_hvi.py needs geopandas to read and write layers. The reasoning about what a
score *means* does not, so it lives here as plain functions over plain numbers.
That keeps it testable in CI, which installs requirements-dev.txt rather than
the full geospatial stack.
"""

from __future__ import annotations

# A ward scoring high because one indicator is doing nearly all the work is a
# different recommendation problem from a ward scoring high across the board,
# and a planner needs to be able to tell them apart (issue #97).
#
# The threshold is a judgement, so it is named rather than buried. With eight
# indicators an even spread gives each 0.125 of the total; half of all the
# signal coming from one of the eight is the point at which describing the ward
# by that one factor stops being a simplification and starts being the
# honest summary.
DOMINANCE_THRESHOLD = 0.5


def factor_dominance(
    contributions: dict[str, float],
    threshold: float = DOMINANCE_THRESHOLD,
) -> dict[str, object]:
    """Which indicator drives a score, and by how much.

    Contributions are signed (weight times z-score), and a strongly negative
    contribution is just as much "this factor is driving the result" as a
    positive one. So the share is computed over absolute values: what fraction
    of the total movement in the index came from this one indicator.

    Returns dominant_factor, dominant_share (0 to 1) and a boolean flag. A ward
    with no contributions at all, which should not happen but would otherwise
    raise, returns nulls and False rather than inventing a winner.
    """
    magnitudes = {
        name: abs(value)
        for name, value in contributions.items()
        if value is not None
    }
    total = sum(magnitudes.values())

    if not magnitudes or total == 0:
        return {
            "dominant_factor": None,
            "dominant_share": None,
            "single_factor_dominated": False,
        }

    # max() on ties returns the first in iteration order, which is the column
    # order the pipeline defines. Deterministic, which matters for a value that
    # gets committed to a snapshot and diffed.
    dominant = max(magnitudes, key=lambda name: magnitudes[name])
    share = magnitudes[dominant] / total

    return {
        "dominant_factor": dominant,
        "dominant_share": round(share, 4),
        "single_factor_dominated": share >= threshold,
    }
