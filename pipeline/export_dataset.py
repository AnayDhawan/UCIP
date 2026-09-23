"""Flatten the per-cell dataset to CSV for release (issue #85).

Why this exists:
    The computed dataset is only reachable by cloning the repo and knowing
    which files under data/ matter. Researchers and analysts want a download,
    and half of them work in pandas or R rather than in GIS, where a GeoJSON
    of 541 polygons is the wrong shape entirely.

    This writes one flat table: one row per grid cell, every indicator, the
    index, each factor's contribution, the NBS and plantability result, the
    NDVI change class, and the cell centre as plain lon/lat columns so a
    non-GIS user can plot it without touching a geometry library.

    Column meanings, units and known limitations are in docs/DATA-DICTIONARY.md.
    A CSV of unlabelled columns would not be usable, which is why that file was
    a prerequisite for this one.

Inputs:
    ../data/cells_nbs.geojson          every indicator, HVI, contributions,
                                       plantability and the fired NBS rules
    ../data/cells_ndvi_change.geojson  per-cell NDVI delta and its class

Outputs:
    ../data/cells.csv

Run:
    python export_dataset.py
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent
DATA_DIR = PIPELINE_DIR.parent / "data"

CELLS_PATH = DATA_DIR / "cells_nbs.geojson"
CHANGE_PATH = DATA_DIR / "cells_ndvi_change.geojson"
OUT_PATH = DATA_DIR / "cells.csv"

# Only the columns cells_ndvi_change adds. Everything else in that file is a
# duplicate of cells_nbs, and a release asset that carries the same indicator
# under two names invites someone to analyse the wrong one.
CHANGE_COLUMNS = ("ndvi_delta", "change_class")

COLUMNS = [
    "grid_id",
    "ward_id",
    "ward_gid",
    "lon",
    "lat",
    "LST_C",
    "NDVI",
    "NDVI_prev",
    "ndvi_delta",
    "change_class",
    "pop_density_km2",
    "elderly_pct",
    "slum_pct",
    "hospital_dist_m",
    "impervious_pct",
    "worldcover_class",
    "dist_to_water_m",
    "HVI",
    "contrib_LST_C",
    "contrib_NDVI",
    "contrib_pop_density_km2",
    "contrib_elderly_pct",
    "contrib_slum_pct",
    "contrib_hospital_dist_m",
    "contrib_impervious_pct",
    "plantable",
    "nbs_fired",
]


def ring_centre(geometry: dict) -> tuple[float | None, float | None]:
    """Centre of a grid cell, as the mean of its exterior ring vertices.

    The cells are axis-aligned squares built in projected metres and
    reprojected, so for this geometry the vertex mean and the polygon centroid
    are the same point to well under a metre. Doing it this way keeps the
    exporter free of a geometry dependency.
    """
    if not geometry:
        return None, None
    coords = geometry.get("coordinates") or []
    if geometry.get("type") == "MultiPolygon":
        coords = coords[0] if coords else []
    ring = coords[0] if coords else []
    points = [p for p in ring if isinstance(p, (list, tuple)) and len(p) >= 2]
    if not points:
        return None, None
    # A closed ring repeats its first vertex, which would weight that corner twice.
    if len(points) > 1 and points[0] == points[-1]:
        points = points[:-1]
    n = len(points)
    return round(sum(p[0] for p in points) / n, 6), round(sum(p[1] for p in points) / n, 6)


def load_features(path: Path) -> list[dict]:
    if not path.exists():
        sys.exit(f"[FAIL] missing input: {path}. Run the pipeline first.")
    return json.loads(path.read_text(encoding="utf-8")).get("features", [])


def main() -> int:
    cells = load_features(CELLS_PATH)
    change_by_id = {
        f["properties"]["grid_id"]: f["properties"] for f in load_features(CHANGE_PATH)
    }

    missing_change = 0
    rows = []
    for feature in cells:
        props = dict(feature.get("properties", {}))
        extra = change_by_id.get(props.get("grid_id"))
        if extra is None:
            missing_change += 1
        else:
            for column in CHANGE_COLUMNS:
                props[column] = extra.get(column)

        lon, lat = ring_centre(feature.get("geometry"))
        props["lon"], props["lat"] = lon, lat
        rows.append({column: props.get(column) for column in COLUMNS})

    OUT_PATH.write_text("", encoding="utf-8")
    with OUT_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[ok] wrote {OUT_PATH} ({len(rows)} cells, {len(COLUMNS)} columns)")

    if missing_change:
        # Exit 2 is the pipeline's "ran, but check this" code. The file is
        # still written and still usable; two columns are just empty.
        print(f"[WARN] {missing_change} cell(s) had no NDVI-change row, "
              "so ndvi_delta and change_class are blank for them")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
