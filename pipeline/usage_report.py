"""Report Supabase and Earth Engine consumption against their ceilings (#130).

Both services are free tier and both have limits this project will approach as
the pipeline runs more often and the API takes traffic. Right now the first
sign of exhaustion would be an outage, which is the thing worth fixing.

What is measured, and what is estimated, stated plainly because the difference
matters when someone acts on this:

    Supabase rows       measured exactly, via PostgREST's count=exact.
    Supabase bytes      estimated. The payload PostgREST returns is not what
                        Postgres stores: no TOAST compression, no page
                        overhead, no indexes. Treat it as an order of
                        magnitude, not a figure. Reading the real size needs
                        pg_database_size() exposed through a migration, or the
                        dashboard.
    GEE quota           not readable. Earth Engine publishes no consumption
                        API, so this reports what the pipeline SPENT on its
                        last run instead: which collections it queried, how
                        many scenes came back, and how many GEE-calling stages
                        ran. That comes from the per-stage provenance in the
                        run log (#92) and is the honest proxy.

Thresholds warn on approach rather than on breach, which is the whole point:
a quota alert that fires when you are already out is a postmortem.

Run:
    python usage_report.py
    python usage_report.py --fail-on-warning     # for CI
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent
ROOT = PIPELINE_DIR.parent
RUN_LOG_PATH = ROOT / "data" / "pipeline_run_log.json"

TABLES = ["wards", "grid_cells", "interventions", "methodology_refs", "nbs_recommendations"]

# Supabase free tier, as documented at the time of writing. Named here so a
# change to the plan is a one-line edit rather than a hunt.
FREE_TIER_DB_BYTES = 500 * 1024 * 1024

# Warn at 70%. Far enough out to act, close enough to mean something.
WARN_FRACTION = 0.70

TIMEOUT_SECONDS = 30


def row_count(url: str, key: str, table: str) -> int | None:
    """Exact count, via the header PostgREST answers a ranged request with."""
    query = urllib.parse.urlencode({"select": "*"})
    request = urllib.request.Request(
        f"{url}/rest/v1/{table}?{query}",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Prefer": "count=exact",
            "Range": "0-0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            content_range = response.headers.get("Content-Range", "")
    except Exception as exc:
        print(f"[WARN] could not count {table}: {exc}")
        return None

    # Shaped "0-0/541", or "*/0" for an empty table.
    total = content_range.rsplit("/", 1)[-1] if "/" in content_range else ""
    return int(total) if total.isdigit() else None


def payload_bytes(url: str, key: str, table: str) -> int | None:
    """Size of the table as PostgREST serialises it. An estimate, see module docstring."""
    query = urllib.parse.urlencode({"select": "*"})
    request = urllib.request.Request(
        f"{url}/rest/v1/{table}?{query}",
        headers={"apikey": key, "Authorization": f"Bearer {key}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return len(response.read())
    except Exception:
        return None


def supabase_section(url: str, key: str) -> tuple[list[str], bool]:
    lines: list[str] = ["## Supabase", ""]
    warned = False

    total_rows = 0
    total_bytes = 0
    lines.append("| Table | Rows | Payload |")
    lines.append("|---|---:|---:|")

    for table in TABLES:
        rows = row_count(url, key, table)
        size = payload_bytes(url, key, table)
        if rows is not None:
            total_rows += rows
        if size is not None:
            total_bytes += size
        lines.append(
            f"| `{table}` | {rows if rows is not None else 'unknown'} | "
            f"{f'{size / 1024:.0f} KiB' if size is not None else 'unknown'} |"
        )

    fraction = total_bytes / FREE_TIER_DB_BYTES
    lines.append(f"| **Total** | **{total_rows}** | **{total_bytes / 1024 / 1024:.1f} MiB** |")
    lines.append("")
    lines.append(
        f"Roughly {fraction:.1%} of the {FREE_TIER_DB_BYTES / 1024 / 1024:.0f} MiB "
        "free-tier database allowance, by serialised payload."
    )
    lines.append("")
    lines.append(
        "That percentage is an estimate and reads high: it measures JSON over the "
        "wire, not stored bytes, so it ignores compression and counts geometry as "
        "text. Actual usage is lower. Reading the real figure needs "
        "`pg_database_size()` exposed through a migration, or the dashboard."
    )

    if fraction >= WARN_FRACTION:
        lines.append("")
        lines.append(
            f"**Approaching the ceiling.** Over {WARN_FRACTION:.0%} of the allowance "
            "even by an estimate that reads high. Check the real size before the next refresh."
        )
        warned = True

    return lines, warned


def gee_section() -> tuple[list[str], bool]:
    lines: list[str] = ["## Earth Engine", ""]

    if not RUN_LOG_PATH.exists():
        lines.append("No run log yet, so nothing to report. It appears after the first refresh.")
        return lines, False

    log = json.loads(RUN_LOG_PATH.read_text(encoding="utf-8"))
    stages = log.get("stages", [])

    gee_stages = [
        s for s in stages
        if (s.get("provenance") or {}).get("collections")
    ]

    lines.append(
        "Earth Engine publishes no consumption API, so this is what the last run "
        "*spent* rather than what is left. From the per-stage provenance in the "
        "run log (#92)."
    )
    lines.append("")
    lines.append(f"Last run started {log.get('started_at', 'unknown')}.")
    lines.append("")

    if not gee_stages:
        lines.append(
            "No GEE-backed stage recorded provenance in that run. Either none ran, "
            "or the run predates provenance recording."
        )
        return lines, False

    lines.append("| Stage | Collections | Scenes |")
    lines.append("|---|---|---:|")
    total_scenes = 0
    for stage in gee_stages:
        p = stage["provenance"]
        scenes = (p.get("scenes_current_window") or 0) + (p.get("scenes_previous_window") or 0)
        total_scenes += scenes
        collections = ", ".join(f"`{c}`" for c in p.get("collections", []))
        lines.append(f"| {stage['id']} | {collections} | {scenes or 'n/a'} |")

    lines.append("")
    lines.append(
        f"{len(gee_stages)} GEE-backed stage(s), {total_scenes} scene(s) fetched. "
        "A monthly cadence means roughly twelve of these a year; the composite "
        "cache in #93 is what would cut the repeat cost."
    )
    return lines, False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fail-on-warning", action="store_true")
    parser.add_argument("--out", type=Path, help="Write the report here as well as to stdout.")
    args = parser.parse_args()

    url = (os.environ.get("NEXT_PUBLIC_SUPABASE_URL") or os.environ.get("SUPABASE_URL") or "").rstrip("/")
    key = os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_ANON_KEY")

    report: list[str] = ["# UCIP usage", ""]
    warned = False

    if url and key:
        lines, supabase_warned = supabase_section(url, key)
        report += lines + [""]
        warned |= supabase_warned
    else:
        report += ["## Supabase", "", "No credentials configured, so nothing was read.", ""]

    lines, gee_warned = gee_section()
    report += lines
    warned |= gee_warned

    text = "\n".join(report)
    print(text)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")

    if warned and args.fail_on_warning:
        print("\n[FAIL] at least one ceiling is being approached.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
