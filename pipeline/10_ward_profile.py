"""M6 — Ward descriptive profiles (feeds the dashboard's ward dialog).

Why this stage exists:
    wards_hvi.geojson carries only HVI, rank, n_cells and the seven contrib_*
    values (weight x z-score). The raw measured indicators live only per 1 km
    cell, so the UI could show a ward's score but never say anything about the
    ward itself. This rolls the cell indicators up to ward level and adds the
    comparison context the dialog needs (city means, percentile, top driver,
    adjacent wards).

Deliberately additive:
    Reads cells_hvi.geojson + wards_hvi.geojson + bmc_wards.geojson, writes only
    ward_profiles.json. It does NOT recompute HVI, PCA weights or ranks; those
    are read straight out of wards_hvi.geojson so the figures already published
    in the pitch deck cannot drift. No Earth Engine calls.

Indicator units, verified against data/cells_hvi.geojson (541 cells):
    LST_C             degrees Celsius     26.24 to 39.95
    NDVI              index, unitless     -0.07 to 0.71   (NOT a canopy percentage)
    pop_density_km2   people per sq km    16 to 115,272
    elderly_pct       percent, 0-100      4.02 to 5.59    (near-flat proxy, see note)
    slum_pct          percent, 0-100      0.00 to 68.55
    hospital_dist_m   metres              3.86 to 6199.03
    impervious_pct    percent, 0-100      0.00 to 96.79

    All *_pct columns are on a 0-100 scale, not 0-1. elderly_pct spans only
    1.6 points across the entire city, so it separates wards very weakly; the
    UI copy should not lean on it. Per methodology.md section 10, the elderly
    and slum layers are proxies (WorldPop 2020, OSM slum-cluster boundaries),
    not ward-level census, and LST is land-surface, not air, temperature.

Run:
    .venv\\Scripts\\activate
    python 10_ward_profile.py
"""

import json
import sys
from pathlib import Path

import geopandas as gpd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
IN_CELLS_PATH = DATA_DIR / "cells_hvi.geojson"
IN_CELLS_FALLBACK = DATA_DIR / "cells_nbs.geojson"
IN_WARDS_PATH = DATA_DIR / "wards_hvi.geojson"
IN_BOUNDARIES_PATH = DATA_DIR / "bmc_wards.geojson"
OUT_PATH = DATA_DIR / "ward_profiles.json"
OUT_PUBLIC_PATH = ROOT / "frontend" / "public" / "ward_profiles.json"

# Same seven indicators as 05_hvi.py INDICATORS, in the same order.
INDICATORS = [
    "LST_C",
    "NDVI",
    "pop_density_km2",
    "elderly_pct",
    "slum_pct",
    "hospital_dist_m",
    "impervious_pct",
]

EXPECTED_WARDS = 24


def neighbours_by_ward(wards: gpd.GeoDataFrame) -> dict[str, list[str]]:
    """Adjacency from the BMC boundary polygons.

    Uses a bounding-box spatial-index query followed by an explicit intersects
    test, rather than sindex.query(predicate=...), so this works across the
    geopandas/shapely versions pinned in the various pipeline venvs. Wards that
    meet only at a corner still count as adjacent, which is what a reader means
    by "next to".
    """
    sindex = wards.sindex
    out: dict[str, list[str]] = {}
    for row in wards.itertuples():
        candidates = sindex.intersection(row.geometry.bounds)
        found = set()
        for i in candidates:
            other = wards.iloc[i]
            if other["ward_id"] == row.ward_id:
                continue
            if row.geometry.intersects(other["geometry"]):
                found.add(other["ward_id"])
        out[row.ward_id] = sorted(found)
    return out


def main() -> int:
    cells_path = IN_CELLS_PATH if IN_CELLS_PATH.exists() else IN_CELLS_FALLBACK
    if not cells_path.exists():
        print(f"[FAIL] neither {IN_CELLS_PATH} nor {IN_CELLS_FALLBACK} found — run 05_hvi.py first.")
        return 1
    if not IN_WARDS_PATH.exists():
        print(f"[FAIL] {IN_WARDS_PATH} not found — run 05_hvi.py first.")
        return 1
    if not IN_BOUNDARIES_PATH.exists():
        print(f"[FAIL] {IN_BOUNDARIES_PATH} not found — run 03_vectors.py first.")
        return 1

    cells = gpd.read_file(cells_path)
    print(f"[ok] loaded {len(cells)} cells from {cells_path.name}")

    missing = [c for c in INDICATORS if c not in cells.columns]
    if missing:
        print(f"[FAIL] {cells_path.name} is missing indicator columns: {missing}")
        return 1

    # ------------------------------------------------------- city baseline --
    city = {"hvi_mean": float(cells["HVI"].mean())}
    for c in INDICATORS:
        city[c] = float(cells[c].mean())

    # -------------------------------------------------- ward indicator means --
    ward_means = cells.groupby("ward_id")[INDICATORS].mean()

    # ---------------------------------- HVI, rank, contributions (read, not recomputed) --
    wards_hvi = gpd.read_file(IN_WARDS_PATH).drop(columns="geometry")
    print(f"[ok] loaded {len(wards_hvi)} ward records from {IN_WARDS_PATH.name}")

    boundaries = gpd.read_file(IN_BOUNDARIES_PATH)[["gid", "name", "geometry"]].rename(
        columns={"gid": "ward_gid", "name": "ward_id"}
    )
    neighbours = neighbours_by_ward(boundaries)
    print(f"[ok] built adjacency for {len(neighbours)} wards")

    hvi_by_ward = {
        str(r["ward_id"]): (None if r["HVI"] is None else float(r["HVI"]))
        for _, r in wards_hvi.iterrows()
    }
    n_wards = len(wards_hvi)

    profiles = []
    for _, r in wards_hvi.iterrows():
        ward_id = str(r["ward_id"])
        rank = int(r["rank"]) if r["rank"] is not None else None
        hvi = float(r["HVI"]) if r["HVI"] is not None else None

        entry: dict = {
            "ward_id": ward_id,
            "ward_gid": int(r["ward_gid"]),
            "hvi": hvi,
            "rank": rank,
            "n_cells": int(r["n_cells"]) if r["n_cells"] is not None else None,
        }

        # "Hotter than X% of the city's wards." rank 1 (worst) maps to 100.
        entry["percentile"] = (
            round((n_wards - rank) / (n_wards - 1) * 100, 1) if rank is not None and n_wards > 1 else None
        )

        if ward_id in ward_means.index:
            for c in INDICATORS:
                value = float(ward_means.loc[ward_id, c])
                entry[c] = value
                entry[f"{c}_delta_city"] = value - city[c]

        # Biggest upward driver: most positive per-factor contribution.
        contribs = {
            c: float(r[f"contrib_{c}"])
            for c in INDICATORS
            if f"contrib_{c}" in wards_hvi.columns and r[f"contrib_{c}"] is not None
        }
        if contribs:
            top = max(contribs, key=contribs.get)
            entry["top_driver"] = top
            entry["top_driver_contrib"] = contribs[top]

        ward_neighbours = neighbours.get(ward_id, [])
        entry["neighbours"] = ward_neighbours
        rated = [(n, hvi_by_ward[n]) for n in ward_neighbours if hvi_by_ward.get(n) is not None]
        if rated:
            coolest = min(rated, key=lambda t: t[1])
            hottest = max(rated, key=lambda t: t[1])
            entry["coolest_neighbour"] = {"ward_id": coolest[0], "hvi": coolest[1]}
            entry["hottest_neighbour"] = {"ward_id": hottest[0], "hvi": hottest[1]}

        profiles.append(entry)

    profiles.sort(key=lambda e: (e["rank"] is None, e["rank"]))

    payload = {
        "generated_from": f"data/{cells_path.name}",
        "n_cells": len(cells),
        "n_wards": len(profiles),
        "indicators": INDICATORS,
        "units": {
            "LST_C": "degrees Celsius (land surface, not air)",
            "NDVI": "vegetation index, unitless, not a canopy percentage",
            "pop_density_km2": "people per square kilometre",
            "elderly_pct": "percent (0-100), proxy from WorldPop 2020",
            "slum_pct": "percent (0-100), proxy from mapped slum-cluster boundaries",
            "hospital_dist_m": "metres",
            "impervious_pct": "percent (0-100)",
        },
        "city": city,
        "wards": profiles,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[ok] wrote {len(profiles)} ward profiles -> {OUT_PATH}")

    OUT_PUBLIC_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PUBLIC_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[ok] copied -> {OUT_PUBLIC_PATH}")

    # ------------------------------------------------------- sanity checks --
    ok = True
    if len(profiles) != EXPECTED_WARDS:
        print(f"[WARN] {len(profiles)}/{EXPECTED_WARDS} wards in output")
        ok = False

    no_neighbours = [e["ward_id"] for e in profiles if not e["neighbours"]]
    if no_neighbours:
        print(f"[WARN] wards with no adjacent ward: {no_neighbours}")
        ok = False

    for c in INDICATORS:
        blanks = [e["ward_id"] for e in profiles if e.get(c) is None]
        if blanks:
            print(f"[WARN] {c} missing for: {blanks}")
            ok = False

    missing_profiles = set(hvi_by_ward) - {e["ward_id"] for e in profiles}
    if missing_profiles:
        print(f"[WARN] wards in wards_hvi.geojson with no profile: {sorted(missing_profiles)}")
        ok = False

    cell_total = sum(e["n_cells"] or 0 for e in profiles)
    if cell_total != len(cells):
        print(f"[WARN] ward n_cells sums to {cell_total}, but {len(cells)} cells were loaded")
        ok = False

    print("\nCity means:")
    for c in INDICATORS:
        print(f"  {c:20s} {city[c]:12.4f}")

    print("\nTop 5 most vulnerable wards:")
    print(f"  {'rank':>4}  {'ward':<5} {'HVI':>6} {'LST_C':>7} {'NDVI':>6} {'imperv%':>8}  top driver")
    for e in profiles[:5]:
        print(
            f"  {e['rank']:>4}  {e['ward_id']:<5} {e['hvi']:>6.1f} {e['LST_C']:>7.2f} "
            f"{e['NDVI']:>6.3f} {e['impervious_pct']:>8.1f}  {e.get('top_driver', 'n/a')}"
        )

    print("\nGO" if ok else "\nCHECK WARNINGS")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
