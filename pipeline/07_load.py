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

    Best-effort means the snapshots never depend on it, not that a failure is
    silent. With credentials configured, a failed database write exits 2 so the
    sync workflow goes red. Rows no longer in the new run (cells dropped when the
    grid changed size) are deleted after the upserts, grid_cells before wards.

    Writes use the service-role key, which bypasses row-level security. The anon
    key the browser holds is read-only under
    supabase/migrations/0005_add_rls_policies.sql.

Run:
    .venv\\Scripts\\activate
    python 07_load.py
"""

from __future__ import annotations

import json
import math
import os
import sys
from typing import TYPE_CHECKING

from _city import load_city
from _indicators import DIRECTIONS
from pathlib import Path

import geopandas as gpd

# supabase and python-dotenv are imported where they are used, so the loading
# logic below can be imported and tested with a fake client and without either
# package installed (issue #203).
if TYPE_CHECKING:
    from supabase import Client

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Output paths come from the city config (issue #96). They were literal
# DATA_DIR paths, so this stage wrote to the default city's directory whatever
# city or resolution it was actually run for. A 500 m run reached stage 05 with
# 500 m inputs and then published 1 km-named output over the committed dataset,
# which is how this was found.
_CITY = load_city()
CELLS_PATH = _CITY.out("cells_nbs.geojson")
WARDS_PATH = _CITY.out("wards_hvi.geojson")
REC_PATH = _CITY.out("nbs_recommendations.json")

# Demo-safe snapshot names — these are what the frontend and the API reference.
SNAP_CELLS = _CITY.out("snapshot_cells.geojson")
SNAP_WARDS = _CITY.out("snapshot_wards.geojson")
SNAP_RECS = _CITY.out("snapshot_nbs_recommendations.json")

# From _indicators.py so the stored contributions cannot drift from the ones
# 05_hvi.py computed. A key is stored only when the run has it (see below), so a
# city without a Census table does not get a null child_pct in its JSON.
CONTRIB_COLS = list(DIRECTIONS)

INTERVENTIONS = [
    {"name": "Native tree planting + green corridors", "category": "greening",
     "citation": "Bastin et al. 2019, Science", "description": "Restoration-suitable, ecologically appropriate afforestation."},
    {"name": "Cool roofs + reflective pavements + cooling centres", "category": "reflective",
     "citation": "Veldman et al. 2019, Science", "description": "Used where afforestation would be ecologically inappropriate."},
    {"name": "Rain gardens + water-sensitive urban design (WSUD)", "category": "water",
     "citation": "Methodology proxy: WorldCover water-distance < 500m", "description": "Impervious + flood-proxy cells."},
    {"name": "Pocket parks", "category": "greening",
     "citation": "C40 Urban Cooling Toolbox", "description": "Dense, open-space-poor cells."},
]

METHODOLOGY_REFS = [
    {"short_name": "reid2009", "citation": "Reid et al. 2009, Environ. Health Perspect. 117(11):1730-1736",
     "doi": "10.1289/ehp.0900683", "usage": "PCA-derived HVI weights", "verified": True},
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


def optional_float(value) -> float | None:
    """A float, or None for a missing value (None or NaN).

    GeoPandas hands back NaN for a null, and float(NaN) would both write a NaN
    the database rejects and claim a measurement that was never made.
    """
    if value is None:
        return None
    number = float(value)
    return None if math.isnan(number) else number


def get_client() -> Client | None:
    from dotenv import load_dotenv
    from supabase import create_client

    load_dotenv(Path(__file__).resolve().parent.parent / ".env.local")
    url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("[WARN] Supabase URL/service-role key not found in .env.local — skipping DB upsert.")
        return None
    return create_client(url, key)


def table_has_column(client: Client, table: str, column: str) -> bool:
    """Whether a migration that adds `column` to `table` has been applied.

    Probed rather than assumed, for the reason wards_has_dominance_columns gives:
    writing a column that does not exist fails the whole upsert, not just the
    field.
    """
    try:
        client.table(table).select(column).limit(1).execute()
        return True
    except Exception:
        return False


def wards_has_dominance_columns(client: Client) -> bool:
    """Whether migration 0007 has been applied to this database.

    The three factor-dominance columns (issue #97) were written to the snapshots
    and the CSV export from the start, but this loader never wrote them to the
    database, and the migration that adds them was not applied. Nothing showed
    it: the API's database path selected them, failed, and fell back to the
    snapshot without saying so.

    Probed rather than assumed, because writing a column that does not exist
    makes the whole `wards` upsert fail, not just skip the field. So a database
    that has not run 0007 keeps syncing as it did, and one that has gets the
    values with no further change here.
    """
    try:
        client.table("wards").select("dominant_factor").limit(1).execute()
        return True
    except Exception:
        return False


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


def _is_missing_function(exc: Exception) -> bool:
    """Whether an rpc error means the function does not exist, not that it failed.

    PostgREST reports an unknown function as PGRST202 or as "Could not find the
    function", depending on the version. Anything else is a real failure inside
    the transaction, which has already been rolled back.
    """
    text = f"{getattr(exc, 'code', '')} {exc}"
    return "PGRST202" in text or "Could not find the function" in text


def replace_table(client: Client, table: str, rows: list[dict]) -> bool:
    """Replace every row of nbs_recommendations without ever leaving it empty.

    nbs_recommendations is keyed by `id bigint generated always as identity`
    (supabase/migrations/0001_init.sql), which the pipeline never supplies
    because the value is generated server-side. That gave upsert() nothing to
    conflict on, so PostgREST turned every load into a plain INSERT and appended
    a complete duplicate set on each run (162 rows found on 2026-09-03 against
    the 81 the pipeline produces). So the table is replaced wholesale: the rows
    are regenerated from each run, never edited, and a rule that stops firing
    should have its row disappear.

    The replacement used to be a delete request followed by an insert request.
    If the insert failed the table was left empty, and the API then answered
    from the database with count 0 instead of falling back to the snapshot
    (issue #203). It now goes through replace_nbs_recommendations() from
    migration 0009, which does both in one transaction, so a failed insert
    leaves the previous rows in place.

    Where that migration has not been applied the fallback keeps the same
    guarantee a different way: insert the new rows first, then delete only the
    rows that existed before. A failed insert changes nothing; a failed delete
    leaves duplicates for the next load to clear rather than an empty table.
    """
    if not rows:
        return True
    try:
        client.rpc("replace_nbs_recommendations", {"rows": rows}).execute()
        print(f"[ok] replaced {table} with {len(rows)} rows (one transaction) -> Supabase.{table}")
        return True
    except Exception as exc:
        if not _is_missing_function(exc):
            print(f"[WARN] Supabase replace of '{table}' failed; previous rows kept: {exc}")
            return False
        print("[note] replace_nbs_recommendations() not found; apply "
              "supabase/migrations/0009_replace_nbs_recommendations.sql for an atomic replace. "
              "Falling back to insert-then-delete.")

    try:
        old = client.table(table).select("id").execute().data or []
        newest_old = max((r["id"] for r in old), default=None)
        client.table(table).insert(rows).execute()
        if newest_old is not None:
            client.table(table).delete().lte("id", newest_old).execute()
        print(f"[ok] replaced {table} with {len(rows)} rows -> Supabase.{table}")
        return True
    except Exception as exc:
        print(f"[WARN] Supabase replace of '{table}' failed (migration likely not applied yet): {exc}")
        return False


def prune_stale(client: Client, table: str, key: str, keep: list, page: int = 1000, chunk: int = 100) -> bool:
    """Delete rows whose `key` is not in `keep`.

    Upserts never remove anything, so after the grid went from 547 to 541 cells
    the six dropped cells stayed in the database and /api/v1/cells kept serving
    them (issue #203). Call this after the upserts, and after
    nbs_recommendations has been replaced, since that table references both
    parents and a stale row could still be pointed at until then.

    Refuses to run with an empty `keep`: that is a load that produced nothing,
    and deleting the whole table on that evidence is the wrong response.
    """
    if not keep:
        print(f"[WARN] not pruning '{table}': the new key set is empty")
        return False
    try:
        # Compared as strings on both sides: an id loaded as a number on one
        # side and text on the other would otherwise make every row look stale.
        keep = [str(k) for k in keep]
        existing: list = []
        start = 0
        while True:
            batch = (
                client.table(table).select(key).range(start, start + page - 1).execute().data or []
            )
            existing.extend(str(r[key]) for r in batch)
            if len(batch) < page:
                break
            start += page

        stale = sorted(set(existing) - set(keep))
        for i in range(0, len(stale), chunk):
            client.table(table).delete().in_(key, stale[i:i + chunk]).execute()
        print(f"[ok] pruned {len(stale)} stale rows from Supabase.{table}"
              + (f": {', '.join(map(str, stale[:10]))}{'...' if len(stale) > 10 else ''}" if stale else ""))
        return True
    except Exception as exc:
        print(f"[WARN] pruning '{table}' failed: {exc}")
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
        with_dominance = wards_has_dominance_columns(client)
        if not with_dominance:
            print("[note] wards has no dominant_* columns; apply "
                  "supabase/migrations/0007_ward_factor_dominance.sql to store them")
        with_worldcover_share = table_has_column(client, "grid_cells", "worldcover_share")
        if not with_worldcover_share:
            print("[note] grid_cells has no worldcover_share column; apply "
                  "supabase/migrations/0010_worldcover_share.sql to store it")
        ward_rows = []
        for _, r in wards.iterrows():
            ward_rows.append({
                "ward_id": r["ward_id"],
                "ward_gid": int(r["ward_gid"]),
                "hvi": float(r["HVI"]) if r["HVI"] is not None else None,
                "rank": int(r["rank"]) if r["rank"] is not None else None,
                "n_cells": int(r["n_cells"]) if r["n_cells"] is not None else None,
                "contrib": {c: r.get(f"contrib_{c}") for c in CONTRIB_COLS if f"contrib_{c}" in r},
                "geom_geojson": json.loads(gpd.GeoSeries([r.geometry]).to_json())["features"][0]["geometry"],
                **(
                    {
                        "dominant_factor": r.get("dominant_factor"),
                        "dominant_share": (
                            float(r["dominant_share"]) if r.get("dominant_share") is not None else None
                        ),
                        "single_factor_dominated": (
                            bool(r["single_factor_dominated"])
                            if r.get("single_factor_dominated") is not None
                            else None
                        ),
                    }
                    if with_dominance
                    else {}
                ),
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
                # Null when the city has no slum layer (issue #201); the column
                # is nullable and 0 would claim a measurement.
                "slum_pct": optional_float(r.get("slum_pct")),
                "hospital_dist_m": float(r["hospital_dist_m"]),
                "impervious_pct": float(r["impervious_pct"]),
                "hvi": float(r["HVI"]),
                "contrib": {c: r.get(f"contrib_{c}") for c in CONTRIB_COLS if f"contrib_{c}" in r},
                "worldcover_class": int(r["worldcover_class"]) if r.get("worldcover_class") is not None else None,
                **(
                    {
                        "worldcover_share": optional_float(r.get("worldcover_share")),
                        "worldcover_mixed": (
                            None if r.get("worldcover_mixed") is None else bool(r["worldcover_mixed"])
                        ),
                    }
                    if with_worldcover_share
                    else {}
                ),
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
        # Only after the children are replaced and only when every write above
        # succeeded: pruning on top of a half-finished load would delete the
        # parents of rows that are still there.
        if db_ok:
            db_ok &= prune_stale(client, "grid_cells", "grid_id", [r["grid_id"] for r in cell_rows])
            db_ok &= prune_stale(client, "wards", "ward_id", [r["ward_id"] for r in ward_rows])
    else:
        db_ok = False

    print(f"\n{'GO (snapshots + Supabase both live)' if db_ok else 'PARTIAL: snapshots written, Supabase upsert incomplete (see warnings above — apply supabase/migrations/0001_init.sql, then rerun)'}")
    # Snapshots are the hard requirement and are already written. With no
    # credentials the database is simply not in use, which is not a failure. But
    # when credentials ARE set and the write failed, exit 2 ("ran but flagged",
    # as in run_pipeline.py) so the twice-weekly sync job goes red instead of
    # reporting success over a database that did not update (issue #203).
    if client is not None and not db_ok:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
