"""M1/M2 — Generate the Mumbai analysis grid.

Planned (sprint Aug 1):
- Load BMC 24-ward boundaries from ../data/ (Datameet GeoJSON).
- Build a 1 km fishnet grid over the Mumbai bounding box (geopandas/shapely).
- Clip cells to ward geometry; assign each cell its ward_id.
- Write ../data/grid_1km.geojson.

Resolution is a parameter: rerun at 500 m later if time allows (locked decision #4).

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
