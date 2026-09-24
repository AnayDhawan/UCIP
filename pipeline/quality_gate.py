"""Fail a refresh that produced implausible output (issue #91).

Runs after the pipeline and before anything publishes. Stages emit their own
warnings, but nothing checked the finished dataset as a whole, so a refresh that
silently produced wrong-but-well-formed data looked exactly like a good one and
the automated workflow would have opened a PR for it either way.

The bounds and their reasoning live in _quality.py. They are deliberately wider
than the observed data: the job is to catch a broken run, not to freeze the
current numbers. A real month-to-month change passes. A unit error, an empty
composite, a failed reprojection or a rescale applied twice does not.

Exit codes follow the pipeline's convention:
    0  everything within bounds
    1  at least one failure, do not publish this refresh
    2  inputs missing, so nothing could be checked

Run:
    python quality_gate.py
    python quality_gate.py --baseline-dir ../data-baseline   # compare counts
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PIPELINE_DIR))

from _quality import (  # noqa: E402
    CELL_BOUNDS,
    CELL_COUNT_TOLERANCE,
    WARD_BOUNDS,
    check_bounds,
    check_count,
    check_nulls,
    check_rescale,
)

ROOT = PIPELINE_DIR.parent
DATA_DIR = ROOT / "data"

CELLS_FILE = "cells_nbs.geojson"
WARDS_FILE = "wards_hvi.geojson"

# Columns whose total absence means a stage produced nothing. Checked separately
# from bounds, which cannot see a column that is null everywhere.
REQUIRED_CELL_COLUMNS = [
    "LST_C", "NDVI", "pop_density_km2",
    "slum_pct", "hospital_dist_m", "impervious_pct", "HVI",
]


def properties(path: Path) -> list[dict]:
    return [f.get("properties", {}) for f in json.loads(path.read_text(encoding="utf-8"))["features"]]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir", type=Path, default=DATA_DIR,
        help="Directory holding the refreshed output.",
    )
    parser.add_argument(
        "--baseline-dir", type=Path, default=None,
        help="Previous run's output, for the record-count comparison. Skipped if absent.",
    )
    args = parser.parse_args()

    cells_path = args.data_dir / CELLS_FILE
    wards_path = args.data_dir / WARDS_FILE

    missing = [p for p in (cells_path, wards_path) if not p.exists()]
    if missing:
        for path in missing:
            print(f"[SKIP] {path} not found.")
        print("\nNothing to check. Run the pipeline first.")
        return 2

    cells = properties(cells_path)
    wards = properties(wards_path)
    print(f"[ok] checking {len(cells)} cells and {len(wards)} wards")

    failures: list[str] = []
    failures += check_nulls(cells, REQUIRED_CELL_COLUMNS, "grid_id", "cells")
    failures += check_bounds(cells, CELL_BOUNDS, "grid_id", "cells")
    failures += check_bounds(wards, WARD_BOUNDS, "ward_id", "wards")
    failures += check_rescale([c["HVI"] for c in cells if c.get("HVI") is not None], "cells.HVI")

    if args.baseline_dir:
        baseline_cells = args.baseline_dir / CELLS_FILE
        if baseline_cells.exists():
            failures += check_count(
                len(cells), len(properties(baseline_cells)), CELL_COUNT_TOLERANCE, "cells"
            )
        else:
            print(f"[note] no baseline at {baseline_cells}, skipping the count check")

    if failures:
        print(f"\nFAILED: {len(failures)} check(s).\n")
        for failure in failures:
            print(f"[FAIL] {failure}")
        print(
            "\nThis refresh should not publish. Each line above is output that is "
            "outside what the data can plausibly be, which usually means a stage "
            "failed in a way that still produced a file."
        )
        return 1

    print("\nGO: every value within bounds.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
