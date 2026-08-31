"""M4 — Nature-Based Solutions rule engine + ecological plantability filter (F3+F4).

Planned (sprint Aug 4):
- Plantability flag per cell/ward: restoration-suitable AND not native
  grassland/savanna (Bastin 2019 potential, Veldman 2019 constraint).
- Rules (each fired rule carries a rationale string + citation):
    HVI high + canopy low + plantable      -> native trees + green corridors [Bastin]
    HVI high + canopy low + NOT plantable  -> cool roofs + reflective pavements + cooling centres [Veldman]
    impervious high + flood-prone          -> rain gardens + WSUD
    density high + open space low          -> pocket parks
    elderly high + hospital access low     -> cooling centres priority
- Output: nbs_recommendations rows per ward (intervention, rationale, citation, priority).
The "ward REJECTED for trees, assigned cool roofs" moment is the headline demo beat.

Threshold notes (documented here since methodology.md keeps them at the outline level):
- "high"/"low" cutoffs use the 75th/25th percentile of that indicator across cells
  in THIS run, not fixed absolute values — several indicators (e.g. elderly_pct)
  have a narrow observed range where an absolute cutoff would be meaningless.
- "flood-prone" has no dedicated hydrology layer in P0; proxied as
  distance-to-nearest-WorldCover-water/wetland < 500m (stated limitation).
- "plantable" = not water/wetland/mangrove/built-up AND not native grassland
  (WorldCover class 30) AND impervious_pct below the 75th percentile (physical
  room to plant).

Run:
    .venv\\Scripts\\activate
    python 06_nbs.py
"""

import json
import os
import sys
from pathlib import Path

import ee
import geopandas as gpd

from _gee_auth import init_ee

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
IN_PATH = DATA_DIR / "cells_hvi.geojson"
OUT_CELLS_PATH = DATA_DIR / "cells_nbs.geojson"
OUT_WARD_RECS_PATH = DATA_DIR / "nbs_recommendations.json"

GEE_PROJECT = os.environ.get("GEE_PROJECT", "ucip-mum")
ZONAL_SCALE = 10  # WorldCover native resolution

WORLDCOVER_GRASSLAND = 30
WORLDCOVER_NONPLANTABLE = {50, 80, 90, 95}  # built-up, water, wetland, mangrove
WORLDCOVER_WATER_LIKE = {80, 90, 95}
FLOOD_PRONE_DIST_M = 500


def load_grid_fc(gdf: gpd.GeoDataFrame) -> ee.FeatureCollection:
    features = [ee.Feature(ee.Geometry(row.geometry.__geo_interface__), {"grid_id": row.grid_id}) for row in gdf.itertuples()]
    return ee.FeatureCollection(features)


def pull_landcover_and_flood_proxy(gdf: gpd.GeoDataFrame) -> dict:
    init_ee(GEE_PROJECT)
    grid_fc = load_grid_fc(gdf)
    worldcover = ee.ImageCollection("ESA/WorldCover/v200").first()

    dominant_class = worldcover.reduceRegions(
        collection=grid_fc, reducer=ee.Reducer.mode(), scale=ZONAL_SCALE
    ).getInfo()

    water_mask = worldcover.remap(list(WORLDCOVER_WATER_LIKE), [1] * len(WORLDCOVER_WATER_LIKE), 0)
    dist_to_water = water_mask.fastDistanceTransform().sqrt().multiply(10).rename("dist_to_water_m")
    flood_proxy = dist_to_water.reduceRegions(
        collection=grid_fc, reducer=ee.Reducer.mean(), scale=ZONAL_SCALE
    ).getInfo()

    landcover_by_id = {f["properties"]["grid_id"]: f["properties"].get("mode") for f in dominant_class["features"]}
    dist_by_id = {f["properties"]["grid_id"]: f["properties"].get("mean") for f in flood_proxy["features"]}
    return landcover_by_id, dist_by_id


def fire_rules(row, thresholds) -> list[dict]:
    recs = []
    hvi_high = row.HVI >= thresholds["hvi_p75"]
    canopy_low = row.NDVI <= thresholds["ndvi_p25"]
    density_high = row.pop_density_km2 >= thresholds["density_p75"]
    open_space_low = row.NDVI <= thresholds["ndvi_p25"]
    elderly_high = row.elderly_pct >= thresholds["elderly_p75"]
    hospital_access_low = row.hospital_dist_m >= thresholds["hospital_p75"]
    impervious_high = row.impervious_pct >= thresholds["impervious_p75"]
    flood_prone = row.dist_to_water_m <= FLOOD_PRONE_DIST_M

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


def main() -> int:
    if not IN_PATH.exists():
        print(f"[FAIL] {IN_PATH} not found — run 05_hvi.py first.")
        return 1

    gdf = gpd.read_file(IN_PATH)
    print(f"[ok] loaded {len(gdf)} cells")

    print("[..] pulling WorldCover dominant class + water-distance proxy per cell")
    landcover_by_id, dist_by_id = pull_landcover_and_flood_proxy(gdf)
    gdf["worldcover_class"] = gdf["grid_id"].map(landcover_by_id)
    gdf["dist_to_water_m"] = gdf["grid_id"].map(dist_by_id)

    thresholds = {
        "hvi_p75": gdf["HVI"].quantile(0.75),
        "ndvi_p25": gdf["NDVI"].quantile(0.25),
        "density_p75": gdf["pop_density_km2"].quantile(0.75),
        "elderly_p75": gdf["elderly_pct"].quantile(0.75),
        "hospital_p75": gdf["hospital_dist_m"].quantile(0.75),
        "impervious_p75": gdf["impervious_pct"].quantile(0.75),
    }
    print("[ok] thresholds (75th/25th percentile):", {k: round(v, 2) for k, v in thresholds.items()})

    gdf["plantable"] = (
        ~gdf["worldcover_class"].isin(WORLDCOVER_NONPLANTABLE)
        & (gdf["worldcover_class"] != WORLDCOVER_GRASSLAND)
        & (gdf["impervious_pct"] < thresholds["impervious_p75"])
    )
    n_rejected_grassland = (gdf["worldcover_class"] == WORLDCOVER_GRASSLAND).sum()
    print(f"[ok] {gdf['plantable'].sum()}/{len(gdf)} cells plantable "
          f"({n_rejected_grassland} rejected as native grassland)")

    all_recs = []
    fired_flags = []
    for row in gdf.itertuples():
        recs = fire_rules(row, thresholds)
        fired_flags.append(len(recs) > 0)
        for r in recs:
            all_recs.append({"grid_id": row.grid_id, "ward_id": row.ward_id, **r})

    gdf["nbs_fired"] = fired_flags
    gdf.drop(columns=["geometry"]).to_csv(DATA_DIR / "cells_nbs_debug.csv", index=False)
    gdf.to_file(OUT_CELLS_PATH, driver="GeoJSON")
    print(f"[ok] wrote {len(gdf)} cells with NBS flags -> {OUT_CELLS_PATH}")

    # ------------------------------------------------- ward-level rollup --
    ward_recs = {}
    for r in all_recs:
        key = (r["ward_id"], r["intervention"])
        if key not in ward_recs:
            ward_recs[key] = {
                "ward_id": r["ward_id"],
                "intervention": r["intervention"],
                "rationale": r["rationale"],
                "citation": r["citation"],
                "priority": r["priority"],
                "cell_count": 0,
            }
        ward_recs[key]["cell_count"] += 1

    ward_recs_list = sorted(ward_recs.values(), key=lambda r: (r["ward_id"], r["priority"]))
    OUT_WARD_RECS_PATH.write_text(json.dumps(ward_recs_list, indent=2), encoding="utf-8")
    print(f"[ok] wrote {len(ward_recs_list)} ward-level recommendation rows -> {OUT_WARD_RECS_PATH}")

    # ------------------------------------------------------- sanity checks --
    ok = True
    wards_with_recs = {r["ward_id"] for r in all_recs}
    if len(wards_with_recs) < 15:
        print(f"[WARN] only {len(wards_with_recs)}/24 wards got any recommendation")
        ok = False
    if n_rejected_grassland == 0:
        print("[WARN] plantability filter never rejected a grassland cell — check WorldCover class mapping")
    print(f"\n{len(all_recs)} recommendation rows fired across {len(wards_with_recs)} wards")
    print("GO" if ok else "CHECK WARNINGS")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
