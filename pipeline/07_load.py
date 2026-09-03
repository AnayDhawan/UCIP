"""Stage 07 — Publish results to Supabase and write the demo-safe snapshots.

What it does:
    Upserts the finished dataset into the five Supabase tables (wards,
    grid_cells, interventions, nbs_recommendations, methodology_refs), and
    always writes committed GeoJSON snapshots to ../data/ regardless of whether
    that upsert worked.

    The snapshots are the point. The frontend reads static files, not the
    database, so the site keeps working with a dead, paused, or unreachable
    Supabase project. That decision was made for demo-day reliability and has
    since earned itself twice over.

Inputs:
    ../data/cells_nbs.geojson           from stage 06
    ../data/wards_hvi.geojson           from stage 05
    ../data/nbs_recommendations.json    from stage 06
    .env.local                          Supabase URL and service-role key

Outputs:
    ../data/snapshot_cells.geojson              committed fallback copies
    ../data/snapshot_wards.geojson
    ../data/snapshot_nbs_recommendations.json
    Supabase tables                             best-effort upsert

Notes:
    The upsert is deliberately best-effort. If the migrations in
    supabase/migrations/ have not been applied to the live project, this logs the
    failure per table and carries on, because the snapshot write is what the site
    actually depends on.

    Writes use the service-role key, which bypasses row-level security. The anon
    key the browser holds is read-only under
    supabase/migrations/0005_add_rls_policies.sql.

Run:
    .venv\\Scripts\\activate
    python 07_load.py
"""

import json
import os
import sys
from pathlib import Path

import geopandas as gpd
from dotenv import load_dotenv
from supabase import Client, create_client

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CELLS_PATH = DATA_DIR / "cells_nbs.geojson"
WARDS_PATH = DATA_DIR / "wards_hvi.geojson"
REC_PATH = DATA_DIR / "nbs_recommendations.json"

# Demo-safe snapshot names — these are what the frontend + pitch deck reference.
SNAP_CELLS = DATA_DIR / "snapshot_cells.geojson"
SNAP_WARDS = DATA_DIR / "snapshot_wards.geojson"
SNAP_RECS = DATA_DIR / "snapshot_nbs_recommendations.json"

CONTRIB_COLS = ["LST_C", "NDVI", "pop_density_km2", "elderly_pct", "slum_pct", "hospital_dist_m", "impervious_pct"]

INTERVENTIONS = [
    {"name": "Native tree planting + green corridors", "category": "greening",
     "citation": "Bastin et al. 2019, Science", "description": "Restoration-suitable, ecologically appropriate afforestation."},
    {"name": "Cool roofs + reflective pavements + cooling centres", "category": "reflective",
     "citation": "Veldman et al. 2019, Science", "description": "Used where afforestation would be ecologically inappropriate."},
    {"name": "Rain gardens + water-sensitive urban design (WSUD)", "category": "water",
     "citation": "Methodology proxy: WorldCover water-distance < 500m", "description": "Impervious + flood-proxy cells."},
    {"name": "Pocket parks", "category": "greening",
     "citation": "C40 Urban Cooling Toolbox", "description": "Dense, open-space-poor cells."},
    {"name": "Cooling centres, priority siting", "category": "siting",
     "citation": "Knowlton et al. 2014", "description": "High elderly share + poor hospital access."},
]

METHODOLOGY_REFS = [
    {"short_name": "reid2009", "citation": "Reid et al. 2009, Environ. Health Perspect. 117(11):1730-1736",
     "doi": "10.1289/ehp.0900683", "usage": "PCA-derived HVI weights", "verified": True},
    {"short_name": "knowlton2014", "citation": "Knowlton et al. 2014, IJERPH 11(4):3473-3492",
     "doi": "10.3390/ijerph110403473", "usage": "Ahmedabad HAP impact, local credibility", "verified": True},
    {"short_name": "azhar2017", "citation": "Azhar et al. 2017 (RAND India HVI), IJERPH 14(4):357",
     "doi": "10.3390/ijerph14040357", "usage": "India-wide district HVI precedent", "verified": True},
    {"short_name": "bastin2019", "citation": "Bastin et al. 2019, Science 365(6448):76-79",
     "doi": "10.1126/science.aax0848", "usage": "Tree restoration potential; plantability filter", "verified": True},
    {"short_name": "veldman2019", "citation": "Veldman et al. 2019, Science 366(6463):eaay7976",
     "doi": "10.1126/science.aay7976", "usage": "Don't afforest grasslands/savannas; plantability filter", "verified": True},
    {"short_name": "ziter2019", "citation": "Ziter et al. 2019, PNAS 116(15):7575-7580",
     "doi": "10.1073/pnas.1817561116", "usage": "Canopy % -> LST reduction coefficients", "verified": True},
    {"short_name": "li2014", "citation": "Li, Bou-Zeid & Oppenheimer 2014, Environ. Res. Lett. 9(5):055002",
     "doi": "10.1088/1748-9326/9/5/055002", "usage": "Cool-roof fraction -> UHI reduction", "verified": True},
    {"short_name": "santamouris2014", "citation": "Santamouris 2014, Solar Energy 103:682-703",
     "doi": "10.1016/j.solener.2012.07.003", "usage": "Albedo -> peak-temp coefficient", "verified": True},
]


def get_client() -> Client | None:
    load_dotenv(Path(__file__).resolve().parent.parent / ".env.local")
    url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("[WARN] Supabase URL/service-role key not found in .env.local — skipping DB upsert.")
        return None
    return create_client(url, key)


def upsert_table(client: Client, table: str, rows: list[dict]) -> bool:
    """Upsert rows keyed on the table's own primary key.

    Only safe for the tables whose primary key the pipeline actually supplies:
    wards (ward_id), grid_cells (grid_id), interventions (name) and
    methodology_refs (short_name). For those, re-running a load overwrites in
    place. See replace_table() for the one table where that is not true.
    """
    if not rows:
        return True
    try:
        client.table(table).upsert(rows).execute()
        print(f"[ok] upserted {len(rows)} rows -> Supabase.{table}")
        return True
    except Exception as exc:
        print(f"[WARN] Supabase upsert to '{table}' failed (migration likely not applied yet): {exc}")
        return False


def replace_table(client: Client, table: str, rows: list[dict]) -> bool:
    """Delete every row, then insert. For tables with no natural key to upsert on.

    nbs_recommendations is keyed by `id bigint generated always as identity`
    (supabase/migrations/0001_init.sql), which the pipeline never supplies
    because the value is generated server-side. That gave upsert() nothing to
    conflict on, so PostgREST turned every load into a plain INSERT and appended
    a complete duplicate set on each run.

    That is exactly what happened in production. The table was found holding 162
    rows on 2026-09-03 against the 81 the pipeline produces: two identical sets,
    ids offset by 81, every (ward, intervention, priority) present twice. Left
    alone, the monthly refresh workflow would have added another 81 every month,
    and issue #53 would have rendered every recommendation twice on the live
    dashboard.

    Replace rather than upsert because it matches what the data actually is:
    recommendations are regenerated wholesale from each run, never edited
    incrementally, and a rule that stops firing should have its row disappear
    rather than linger from a previous run. A natural unique key would not work
    cleanly here anyway, since grid_id is nullable and NULLs do not compare equal
    in a unique constraint.

    Safe to delete first: nbs_recommendations is the child in both its foreign
    key relationships (to wards and grid_cells), so nothing references it.
    """
    if not rows:
        return True
    try:
        # PostgREST refuses an unfiltered delete, so match every row explicitly.
        client.table(table).delete().gte("id", 0).execute()
        client.table(table).insert(rows).execute()
        print(f"[ok] replaced {table} with {len(rows)} rows -> Supabase.{table}")
        return True
    except Exception as exc:
        print(f"[WARN] Supabase replace of '{table}' failed (migration likely not applied yet): {exc}")
        return False


def main() -> int:
    if not CELLS_PATH.exists() or not WARDS_PATH.exists() or not REC_PATH.exists():
        print(f"[FAIL] missing input(s) — run 05_hvi.py and 06_nbs.py first.")
        return 1

    cells = gpd.read_file(CELLS_PATH)
    wards = gpd.read_file(WARDS_PATH)
    recs = json.loads(REC_PATH.read_text(encoding="utf-8"))
    print(f"[ok] loaded {len(cells)} cells, {len(wards)} wards, {len(recs)} recommendation rows")

    # ---------------------------------------------------- GeoJSON snapshots --
    # ALWAYS written first — this is the demo-safe fallback, independent of DB status.
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    cells.to_file(SNAP_CELLS, driver="GeoJSON")
    wards.to_file(SNAP_WARDS, driver="GeoJSON")
    SNAP_RECS.write_text(json.dumps(recs, indent=2), encoding="utf-8")
    print(f"[ok] wrote demo-safe snapshots: {SNAP_CELLS.name}, {SNAP_WARDS.name}, {SNAP_RECS.name}")

    # -------------------------------------------------------- Supabase upsert --
    client = get_client()
    db_ok = True
    if client is not None:
        ward_rows = []
        for _, r in wards.iterrows():
            ward_rows.append({
                "ward_id": r["ward_id"],
                "ward_gid": int(r["ward_gid"]),
                "hvi": float(r["HVI"]) if r["HVI"] is not None else None,
                "rank": int(r["rank"]) if r["rank"] is not None else None,
                "n_cells": int(r["n_cells"]) if r["n_cells"] is not None else None,
                "contrib": {c: r.get(f"contrib_{c}") for c in CONTRIB_COLS},
                "geom_geojson": json.loads(gpd.GeoSeries([r.geometry]).to_json())["features"][0]["geometry"],
            })

        cell_rows = []
        for _, r in cells.iterrows():
            cell_rows.append({
                "grid_id": r["grid_id"],
                "ward_id": r["ward_id"],
                "area_m2": float(r["area_m2"]) if r.get("area_m2") is not None else None,
                "lst_c": float(r["LST_C"]),
                "ndvi": float(r["NDVI"]),
                "ndvi_prev": float(r["NDVI_prev"]) if r.get("NDVI_prev") is not None else None,
                "pop_density_km2": float(r["pop_density_km2"]),
                "elderly_pct": float(r["elderly_pct"]),
                "slum_pct": float(r["slum_pct"]),
                "hospital_dist_m": float(r["hospital_dist_m"]),
                "impervious_pct": float(r["impervious_pct"]),
                "hvi": float(r["HVI"]),
                "contrib": {c: r.get(f"contrib_{c}") for c in CONTRIB_COLS},
                "worldcover_class": int(r["worldcover_class"]) if r.get("worldcover_class") is not None else None,
                "dist_to_water_m": float(r["dist_to_water_m"]) if r.get("dist_to_water_m") is not None else None,
                "plantable": bool(r["plantable"]),
                "geom_geojson": json.loads(gpd.GeoSeries([r.geometry]).to_json())["features"][0]["geometry"],
            })

        # Order matters: wards before grid_cells (FK) before nbs_recommendations (FK to both).
        db_ok &= upsert_table(client, "wards", ward_rows)
        db_ok &= upsert_table(client, "interventions", INTERVENTIONS)
        db_ok &= upsert_table(client, "methodology_refs", METHODOLOGY_REFS)
        db_ok &= upsert_table(client, "grid_cells", cell_rows)
        # Replace, not upsert: this table's identity primary key is generated
        # server-side, so an upsert has nothing to conflict on and appends a
        # duplicate set every run. See replace_table().
        db_ok &= replace_table(client, "nbs_recommendations", recs)
    else:
        db_ok = False

    print(f"\n{'GO (snapshots + Supabase both live)' if db_ok else 'PARTIAL: snapshots written, Supabase upsert incomplete (see warnings above — apply supabase/migrations/0001_init.sql, then rerun)'}")
    return 0  # snapshot write succeeding is the hard requirement; DB is best-effort


if __name__ == "__main__":
    sys.exit(main())
