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

from _city import city_from_argv

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
# Output path resolved per city inside main(); see CityConfig.out().

WGS84 = "EPSG:4326"


def build_fishnet(
    bounds_m: tuple[float, float, float, float], cell_size: float, crs: str
) -> gpd.GeoSeries:
    minx, miny, maxx, maxy = bounds_m
    xs = np.arange(minx, maxx, cell_size)
    ys = np.arange(miny, maxy, cell_size)
    cells = [box(x, y, x + cell_size, y + cell_size) for x in xs for y in ys]
    return gpd.GeoSeries(cells, crs=crs)


def main() -> int:
    city = city_from_argv("Build the analysis grid for a city.")
    wards_path = city.boundaries_path
    utm_crs = city.projected_crs
    cell_size_m = city.cell_size_m
    print(f"[..] city: {city.name} ({city.slug}), {cell_size_m:.0f} m grid in {utm_crs}")

    out_path = city.out("grid_1km.geojson")

    if not wards_path.exists():
        print(f"[FAIL] {wards_path} not found.")
        return 1

    wards = gpd.read_file(wards_path)
    if wards.crs is None:
        wards = wards.set_crs(WGS84)
    wards_utm = wards.to_crs(utm_crs)
    print(f"[ok] loaded {len(wards_utm)} wards")

    ward_union = wards_utm.union_all()
    fishnet = build_fishnet(ward_union.bounds, cell_size_m, utm_crs)
    print(f"[ok] built {len(fishnet)} candidate cells over ward bbox")

    cells_gdf = gpd.GeoDataFrame(geometry=fishnet, crs=utm_crs)
    id_field = city.ward_id_field
    if id_field not in wards_utm.columns:
        print(f"[FAIL] boundary file has no '{id_field}' column; got {list(wards_utm.columns)}.")
        return 1
    # gid is Datameet's own numeric id and is not guaranteed to exist elsewhere,
    # so synthesise one when a city's boundary file lacks it.
    if "gid" not in wards_utm.columns:
        wards_utm = wards_utm.assign(gid=range(1, len(wards_utm) + 1))
    clipped = gpd.overlay(
        cells_gdf.reset_index(names="cell_idx"),
        wards_utm[["gid", id_field, "geometry"]].rename(
            columns={"gid": "ward_gid", id_field: "ward_id"}
        ),
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

    out.to_file(out_path, driver="GeoJSON")
    print(f"[ok] wrote {len(out)} grid cells -> {out_path}")

    # ------------------------------------------------------- sanity checks --
    ok = True
    n_wards_covered = out["ward_id"].nunique()
    if n_wards_covered != len(wards):
        print(f"[WARN] grid covers {n_wards_covered}/{len(wards)} wards — some ward has no cells")
        ok = False
    minx, miny, maxx, maxy = out.total_bounds
    b_minx, b_miny, b_maxx, b_maxy = city.bbox
    if not (b_minx <= minx and maxx <= b_maxx and b_miny <= miny and maxy <= b_maxy):
        print(
            f"[WARN] grid bounds {out.total_bounds} fall outside {city.name}'s configured "
            f"bbox {city.bbox} — check the boundary file and the config."
        )
        ok = False
    print(f"\n{'GO' if ok else 'CHECK WARNINGS'}: {len(out)} cells across {n_wards_covered} wards.")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
