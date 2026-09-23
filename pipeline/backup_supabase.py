"""Export every Supabase table to JSON (issue #127).

Why this exists:
    The Supabase project was found deleted on 2026-09-03. Nothing was lost,
    because the frontend reads committed snapshots and the pipeline can
    regenerate the database from scratch. That is a good architecture and it is
    not a backup strategy: it depends on every row being derivable from a
    pipeline run, and the moment the database holds anything that is not,
    losing it means losing it.

    It is also slow. Regenerating means a full Earth Engine run, which costs
    quota and about forty minutes, to recover from something a file could have
    fixed in seconds.

Reads through PostgREST with the anon key rather than pg_dump, deliberately:
    A dump needs a direct Postgres connection and the database password, which
    would mean putting a second, more powerful credential into CI. Everything
    here is already public, readable with the key that ships in the browser
    bundle, so the export needs no privilege the site does not already have.

    The trade is that this captures data, not schema. Schema lives in
    supabase/migrations/ and is already version controlled, so the pair is
    complete: migrations rebuild the shape, this rebuilds the contents.

Run:
    python backup_supabase.py --out-dir ../backups
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Every table the pipeline writes, in dependency order so a restore can replay
# the files in the order it reads them.
TABLES = [
    "wards",
    "grid_cells",
    "interventions",
    "methodology_refs",
    "nbs_recommendations",
]

# PostgREST caps a response; anything larger has to be paged. grid_cells is 541
# rows today and would be roughly 2200 at 500m resolution (issue #96), so this
# pages rather than assuming one request is enough.
PAGE_SIZE = 1000
TIMEOUT_SECONDS = 60


def fetch_page(url: str, key: str, table: str, offset: int) -> list[dict]:
    query = urllib.parse.urlencode({"select": "*", "limit": PAGE_SIZE, "offset": offset})
    request = urllib.request.Request(
        f"{url}/rest/v1/{table}?{query}",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_table(url: str, key: str, table: str) -> list[dict]:
    rows: list[dict] = []
    while True:
        page = fetch_page(url, key, table, len(rows))
        rows.extend(page)
        if len(page) < PAGE_SIZE:
            return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=Path("backups"))
    parser.add_argument(
        "--min-rows", type=int, default=1,
        help="Fail if a table returns fewer rows than this. Guards against "
             "archiving an empty database over a good backup.",
    )
    args = parser.parse_args()

    url = (os.environ.get("NEXT_PUBLIC_SUPABASE_URL") or os.environ.get("SUPABASE_URL") or "").rstrip("/")
    key = os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_ANON_KEY")

    if not url or not key:
        print("[FAIL] Supabase URL and anon key are required.")
        return 1

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    out_dir = args.out_dir / stamp
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, object] = {
        "taken_at": datetime.now(timezone.utc).isoformat(),
        "source": url,
        "note": (
            "Data only. Schema lives in supabase/migrations/. To restore: apply "
            "the migrations, then load these files in the order listed."
        ),
        "tables": {},
    }

    failures: list[str] = []
    for table in TABLES:
        try:
            rows = fetch_table(url, key, table)
        except urllib.error.HTTPError as exc:
            failures.append(f"{table}: HTTP {exc.code} {exc.reason}")
            continue
        except Exception as exc:
            failures.append(f"{table}: {exc}")
            continue

        # An empty table is almost certainly a broken export rather than a real
        # state, and writing it would retire a good backup in favour of nothing.
        if len(rows) < args.min_rows:
            failures.append(f"{table}: {len(rows)} rows, below the --min-rows floor of {args.min_rows}")

        path = out_dir / f"{table}.json.gz"
        with gzip.open(path, "wt", encoding="utf-8") as handle:
            json.dump(rows, handle)

        size = path.stat().st_size
        manifest["tables"][table] = {"rows": len(rows), "bytes": size, "file": path.name}
        print(f"[ok] {table}: {len(rows)} rows -> {path.name} ({size / 1024:.0f} KiB)")

    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    if failures:
        print(f"\nFAILED: {len(failures)} table(s).")
        for failure in failures:
            print(f"[FAIL] {failure}")
        return 1

    total = sum(t["rows"] for t in manifest["tables"].values())  # type: ignore[index]
    print(f"\nGO: {total} rows across {len(TABLES)} tables -> {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
