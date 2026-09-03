"""Stage 01 — Build the Mumbai analysis grid. First stage of a refresh.

What it does:
    Lays a 1 km fishnet over the bounding box of the 24 BMC ward polygons,
    clips it to the ward geometry so no cell sits in the sea, and tags each
    surviving cell with the ward it falls in. Every later stage works one row
    per cell, so this file defines the unit of analysis for the whole pipeline.

    The fishnet is built in UTM 43N (EPSG:32643) rather than lat/lon, because a
    1 km cell has to be 1 km on the ground; building it in degrees would give
    cells that stretch as they move north. Output is reprojected back to WGS84.

Inputs:
    ../data/bmc_wards.geojson   24 BMC ward boundaries (Datameet)

Outputs:
    ../data/grid_1km.geojson    one polygon per cell, with grid_id and ward_id

Notes:
    Resolution is a parameter (CELL_SIZE_M). The locked decision was 1 km first,
    500 m later if time allowed; 500 m has not been run.

    The bounds check near the end is a plausibility guard, not a hard failure:
    it warns if the grid lands outside Mumbai's real extent, which is what a
    wrong boundary file or a CRS mix-up looks like.

See docs/methodology.md for how the grid feeds the index.

Run:
    .venv\\Scripts\\activate
    python 01_grid.py
"""

import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
from shapely.geometry import box

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
WARDS_PATH = DATA_DIR / "bmc_wards.geojson"
OUT_PATH = DATA_DIR / "grid_1km.geojson"

CELL_SIZE_M = 1000  # 1 km; rerun at 500 later if time allows
UTM_CRS = "EPSG:32643"  # UTM zone 43N, covers Mumbai — projected, meters
WGS84 = "EPSG:4326"


def build_fishnet(bounds_m: tuple[float, float, float, float], cell_size: float) -> gpd.GeoSeries:
    minx, miny, maxx, maxy = bounds_m
    xs = np.arange(minx, maxx, cell_size)
    ys = np.arange(miny, maxy, cell_size)
    cells = [box(x, y, x + cell_size, y + cell_size) for x in xs for y in ys]
    return gpd.GeoSeries(cells, crs=UTM_CRS)


def main() -> int:
    if not WARDS_PATH.exists():
        print(f"[FAIL] {WARDS_PATH} not found.")
        return 1

    wards = gpd.read_file(WARDS_PATH)
    if wards.crs is None:
        wards = wards.set_crs(WGS84)
    wards_utm = wards.to_crs(UTM_CRS)
    print(f"[ok] loaded {len(wards_utm)} wards")

    ward_union = wards_utm.union_all()
    fishnet = build_fishnet(ward_union.bounds, CELL_SIZE_M)
    print(f"[ok] built {len(fishnet)} candidate 1km cells over ward bbox")

    cells_gdf = gpd.GeoDataFrame(geometry=fishnet, crs=UTM_CRS)
    clipped = gpd.overlay(
        cells_gdf.reset_index(names="cell_idx"),
        wards_utm[["gid", "name", "geometry"]].rename(columns={"gid": "ward_gid", "name": "ward_id"}),
        how="intersection",
    )
    print(f"[ok] {len(clipped)} cell fragments after clipping to ward boundaries")

    # Some fishnet cells straddle a ward border and split into slivers on clip.
    # Keep the largest fragment per original cell so every cell maps to exactly one ward.
    clipped["area_m2"] = clipped.geometry.area
    clipped = clipped.sort_values("area_m2", ascending=False).drop_duplicates("cell_idx", keep="first")
    clipped["grid_id"] = [f"cell_{i:04d}" for i in range(len(clipped))]

    out = clipped[["grid_id", "ward_id", "ward_gid", "area_m2", "geometry"]].to_crs(WGS84)
    out = out.sort_values("grid_id").reset_index(drop=True)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out.to_file(OUT_PATH, driver="GeoJSON")
    print(f"[ok] wrote {len(out)} grid cells -> {OUT_PATH}")

    # ------------------------------------------------------- sanity checks --
    ok = True
    n_wards_covered = out["ward_id"].nunique()
    if n_wards_covered != len(wards):
        print(f"[WARN] grid covers {n_wards_covered}/{len(wards)} wards — some ward has no cells")
        ok = False
    minx, miny, maxx, maxy = out.total_bounds
    if not (72.7 <= minx and maxx <= 73.0 and 18.8 <= miny and maxy <= 19.3):
        print(f"[WARN] grid bounds {out.total_bounds} outside plausible Mumbai extent")
        ok = False
    print(f"\n{'GO' if ok else 'CHECK WARNINGS'}: {len(out)} cells across {n_wards_covered} wards.")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
