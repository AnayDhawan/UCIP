"""Stage 03 — Add the population and access layers to the grid.

What it does:
    Adds the three human-exposure indicators the satellite layers cannot see, one
    value per cell:
      - pop_density_km2, from WorldPop's 100 m age-sex rasters via Earth Engine.
      - elderly_pct, the 60+ share of the same WorldPop surface. This is a
        modelled proxy, not a census count, and is named as one in the
        methodology page rather than quietly presented as observed.
      - slum_pct, the share of each cell covered by mapped Datameet slum-cluster
        polygons. These are real observed boundaries, which is why they were
        chosen over the modelled GHS-SMOD proxy originally planned.
      - hospital_dist_m, straight-line distance from the cell centroid to the
        nearest OpenStreetMap hospital, pulled with osmnx.

    Census 2011 ward tables are deliberately not used (decision, 2026-07-11):
    proxy-first, stated openly, rather than mixing vintages and administrative
    units. Issue B5 in the roadmap revisits this.

Inputs:
    ../data/grid_1km_gee.geojson    the grid from stage 02
    ../data/bmc_wards.geojson       ward boundaries
    ../data/slumClusters.geojson    mapped slum-cluster polygons (Datameet)
    Google Earth Engine             WorldPop age-sex rasters (needs auth)
    OpenStreetMap                   hospital locations, via osmnx (network call)

Outputs:
    ../data/grid_1km_vectors.geojson    the grid plus pop_density_km2,
                                        elderly_pct, slum_pct, hospital_dist_m

Notes:
    WORLDPOP_YEAR is pinned rather than left on .first(). An unpinned call would
    silently re-target a different vintage the moment WorldPop publishes a newer
    India image, changing published figures with no code change to notice.

    hospital_dist_m is Euclidean, not network distance. A river or a rail line
    between a cell and its nearest hospital is not accounted for; stated as a
    limitation in the methodology rather than modelled.

See docs/methodology.md sections 3 and 10.

Run:
    .venv\\Scripts\\activate
    python 03_vectors.py
"""

import json
import sys
from pathlib import Path

import ee
import geopandas as gpd
import osmnx as ox

from _gee_auth import init_ee, resolve_project
from _city import load_city

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
GRID_PATH = DATA_DIR / "grid_1km_gee.geojson"
_CITY = load_city()
WARDS_PATH = _CITY.boundaries_path
SLUMS_PATH = DATA_DIR / "slumClusters.geojson"
OUT_PATH = DATA_DIR / "grid_1km_vectors.geojson"

GEE_PROJECT = resolve_project()
UTM_CRS = _CITY.projected_crs
WGS84 = "EPSG:4326"

# Most recent year WorldPop's age-sex collection publishes for India (verified live
# 2026-07-21: only one India image exists, system:index "IND_2020"). Pinned explicitly
# rather than left on .first() — an unpinned call would silently re-target a different
# vintage the moment WorldPop adds a newer India image, with no code change to notice.
WORLDPOP_YEAR = "2020"

# WorldPop age-sex bands 60+ (both sexes) — elderly definition per methodology.
ELDERLY_BANDS = [f"{sex}_{age}" for sex in ("M", "F") for age in ("60", "65", "70", "75", "80")]


def load_grid_fc(path: Path) -> ee.FeatureCollection:
    with open(path, encoding="utf-8") as f:
        gj = json.load(f)
    features = [ee.Feature(ee.Geometry(f["geometry"]), {"grid_id": f["properties"]["grid_id"]}) for f in gj["features"]]
    return ee.FeatureCollection(features)


def pull_worldpop(grid_fc: ee.FeatureCollection) -> dict:
    """Total population + elderly population per cell, via GEE reduceRegions(sum)."""
    img = (
        ee.ImageCollection("WorldPop/GP/100m/pop_age_sex")
        .filterBounds(grid_fc)
        .filter(ee.Filter.eq("system:index", f"IND_{WORLDPOP_YEAR}"))
        .first()
    )
    band_names = img.bandNames().getInfo()

    total_pop = img.select(band_names).reduce(ee.Reducer.sum()).rename("total_pop")
    elderly_present = [b for b in ELDERLY_BANDS if b in band_names]
    if not elderly_present:
        print(f"[WARN] none of {ELDERLY_BANDS} found in image bands {band_names[:10]}...")
        elderly_present = band_names  # fallback: won't happen if WorldPop schema holds
    elderly_pop = img.select(elderly_present).reduce(ee.Reducer.sum()).rename("elderly_pop")

    stack = total_pop.addBands(elderly_pop)
    zonal = stack.reduceRegions(collection=grid_fc, reducer=ee.Reducer.sum(), scale=100)
    result = zonal.getInfo()

    out = {}
    for feat in result["features"]:
        p = feat["properties"]
        out[p["grid_id"]] = {"total_pop": p.get("total_pop"), "elderly_pop": p.get("elderly_pop")}
    return out


def compute_slum_pct(grid_gdf: gpd.GeoDataFrame) -> dict:
    if not SLUMS_PATH.exists():
        print(f"[WARN] {SLUMS_PATH} missing — slum_pct will be 0 for all cells.")
        return {gid: 0.0 for gid in grid_gdf["grid_id"]}

    slums = gpd.read_file(SLUMS_PATH)
    if slums.crs is None:
        slums = slums.set_crs(WGS84)
    slums_utm = slums.to_crs(UTM_CRS)
    slums_utm["geometry"] = slums_utm.geometry.buffer(0)  # fix invalid ring topology
    slums_utm = slums_utm[slums_utm.geometry.is_valid & ~slums_utm.geometry.is_empty]

    grid_utm = grid_gdf[["grid_id", "geometry"]].to_crs(UTM_CRS).copy()
    grid_utm["cell_area"] = grid_utm.geometry.area

    inter = gpd.overlay(grid_utm, slums_utm[["geometry"]], how="intersection")
    inter["piece_area"] = inter.geometry.area
    slum_area_by_id = inter.groupby("grid_id")["piece_area"].sum()

    grid_utm["slum_area"] = grid_utm["grid_id"].map(slum_area_by_id).fillna(0.0)
    grid_utm["slum_pct"] = (grid_utm["slum_area"] / grid_utm["cell_area"] * 100).clip(upper=100)
    return dict(zip(grid_utm["grid_id"], grid_utm["slum_pct"]))


def compute_hospital_distance(grid_gdf: gpd.GeoDataFrame, wards_path: Path) -> dict:
    wards = gpd.read_file(wards_path)
    if wards.crs is None:
        wards = wards.set_crs(WGS84)
    ward_union_wgs84 = wards.union_all()

    try:
        hospitals = ox.features_from_polygon(ward_union_wgs84, tags={"amenity": "hospital"})
    except Exception as exc:
        print(f"[WARN] OSM hospital query failed ({exc}); hospital_dist will be null for all cells.")
        return {gid: None for gid in grid_gdf["grid_id"]}

    if hospitals.empty:
        print("[WARN] no OSM hospitals returned; hospital_dist will be null for all cells.")
        return {gid: None for gid in grid_gdf["grid_id"]}

    hospitals_utm = hospitals.set_crs(WGS84, allow_override=True).to_crs(UTM_CRS)
    hospitals_utm = hospitals_utm.set_geometry(hospitals_utm.geometry.centroid)
    hosp_union = hospitals_utm.geometry.union_all()
    print(f"[ok] {len(hospitals_utm)} OSM hospitals found")

    grid_utm = grid_gdf.to_crs(UTM_CRS)
    centroids = grid_utm.geometry.centroid
    dists = centroids.distance(hosp_union)
    return dict(zip(grid_gdf["grid_id"], dists))


def main() -> int:
    if not GRID_PATH.exists():
        print(f"[FAIL] {GRID_PATH} not found — run 02_gee_layers.py first.")
        return 1

    grid_gdf = gpd.read_file(GRID_PATH)
    print(f"[ok] loaded {len(grid_gdf)} grid cells")

    init_ee(GEE_PROJECT)
    print(f"[ok] Earth Engine initialized (project={GEE_PROJECT})")
    grid_fc = load_grid_fc(GRID_PATH)

    print("[..] pulling WorldPop total + elderly population per cell")
    pop_by_id = pull_worldpop(grid_fc)

    print("[..] computing slum_pct from mapped slum-cluster polygons")
    slum_by_id = compute_slum_pct(grid_gdf)

    print("[..] querying OSM hospitals + computing per-cell distance")
    hosp_by_id = compute_hospital_distance(grid_gdf, WARDS_PATH)

    area_km2_by_id = dict(zip(grid_gdf["grid_id"], grid_gdf.to_crs(UTM_CRS).geometry.area / 1_000_000))

    pop_density, elderly_pct, matched = [], [], 0
    for gid in grid_gdf["grid_id"]:
        pop = pop_by_id.get(gid, {})
        total_pop, elderly_pop, area_km2 = pop.get("total_pop"), pop.get("elderly_pop"), area_km2_by_id.get(gid)
        pop_density.append(total_pop / area_km2 if total_pop is not None and area_km2 else None)
        elderly_pct.append((elderly_pop / total_pop * 100) if total_pop and elderly_pop is not None and total_pop > 0 else None)
        if total_pop is not None:
            matched += 1

    grid_gdf["pop_density_km2"] = pop_density
    grid_gdf["elderly_pct"] = elderly_pct
    grid_gdf["slum_pct"] = grid_gdf["grid_id"].map(slum_by_id)
    grid_gdf["hospital_dist_m"] = grid_gdf["grid_id"].map(hosp_by_id)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    grid_gdf.to_file(OUT_PATH, driver="GeoJSON")
    print(f"[ok] wrote {len(grid_gdf)} cells ({matched} with pop data) -> {OUT_PATH}")

    # ------------------------------------------------------- sanity checks --
    ok = True
    if matched < 0.9 * len(grid_gdf):
        print(f"[WARN] only {matched}/{len(grid_gdf)} cells got WorldPop data")
        ok = False
    mean_elderly = grid_gdf["elderly_pct"].dropna().mean()
    if mean_elderly is None or not (0 <= mean_elderly <= 30):
        print(f"[WARN] mean elderly_pct {mean_elderly} outside plausible 0-30% range")
        ok = False
    mean_slum = grid_gdf["slum_pct"].dropna().mean()
    print(f"\nmean elderly_pct={mean_elderly:.2f}, mean slum_pct={mean_slum:.2f}, "
          f"hospital_dist non-null={grid_gdf['hospital_dist_m'].notna().sum()}/{len(grid_gdf)}")
    print("GO" if ok else "CHECK WARNINGS")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
