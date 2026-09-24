"""Orchestrated pipeline runner (issue #56).

Before this script, a data refresh meant running 00_gee_spike.py through
12_hero_region.py by hand, in the right order, re-reading each script's docstring to
remember what it needs and what comes next. This wraps that into one command:

    python run_pipeline.py

which runs every stage in dependency order, stops at the first hard failure so a
partially-updated data/ directory is never mistaken for a complete refresh, and prints
a clear summary of what ran, what was skipped, and what (if anything) only warned.

Cadence (issue #57 — see pipeline/README.md's "Refresh cadence" section for the full reasoning):
    Every stage below except 00_gee_spike.py reads or derives from satellite imagery
    (Landsat LST/NDVI), WorldPop demographics, or ESA WorldCover land cover — all of
    which change on a monthly-or-slower real-world cadence. Running this chain more
    often than monthly would re-fetch the same underlying composite and burn GEE quota
    for a cosmetic "last updated" timestamp, not a real data change. The one genuinely
    fast-changing signal in this product, live air temperature, is intentionally NOT a
    pipeline stage: it is fetched client-side per page load in
    frontend/src/lib/weather.ts, which needs no cron at all.

    00_gee_spike.py is a one-time go/no-go development gate (see its own docstring),
    not a stage of the data refresh — it queries a tiny fixed test bbox and writes
    nothing any later stage reads. It is EXCLUDED from the default run; pass
    --include-spike to run it anyway (e.g. to smoke-test GEE connectivity in CI).

    14_timeseries.py is on an annual cadence, not a monthly one (issue #154). It
    rebuilds a dry-season composite for every year in its window, so running it
    monthly costs roughly one GEE composite per year of history on every refresh
    to move a trend line that, by construction, gains one new point a year. It is
    excluded from the default run; pass --include-annual, or name it directly with
    --only 14 / --from 14.

Stopping rule:
    Each stage script already returns a process exit code: 0 = clean pass, 2 = ran but
    flagged a "CHECK WARNINGS" sanity check, 1 = hard failure (missing required input,
    no data returned, etc.). This runner treats 1 as fatal and stops the chain there —
    every later stage's docstring says "run <earlier stage> first" and its own
    precondition check would just fail again on stale or missing input. Exit code 2 is
    logged prominently but does not stop the chain, since a warning (e.g. the PCA
    fallback triggering) still produces usable output for the next stage.

Usage:
    python run_pipeline.py                    # run the full monthly refresh, 01..13 + 15
    python run_pipeline.py --include-spike     # also run 00_gee_spike.py first
    python run_pipeline.py --include-annual    # also run the annual stages (14)
    python run_pipeline.py --from 05           # resume from stage 05 onward
    python run_pipeline.py --only 08,09        # run just these stages
    python run_pipeline.py --dry-run           # print the plan, run nothing
    python run_pipeline.py --keep-going        # don't stop on a hard failure

Every run writes a structured log to data/pipeline_run_log.json (stage, exit code,
duration, timestamp) — this is what issue #61's diff step and the CI workflow (#58)
both read to know what actually happened.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import _provenance
from _dry_season import most_recent_complete_dry_season
from _publish import publish

PIPELINE_DIR = Path(__file__).resolve().parent
DATA_DIR = PIPELINE_DIR.parent / "data"


def run_log_path() -> Path:
    """Where this run's log goes, resolved when the run starts.

    A function rather than a module-level constant because it depends on the
    city and resolution, which main() puts into the environment after parsing
    its arguments. As a constant it was fixed at import time, so a 500 m run
    wrote its log over the 1 km one and then published it.
    """
    from _city import load_city

    return load_city().out("pipeline_run_log.json")

# Mirror for the deployed site, which reads data from frontend/public/ (issue
# #124); see the "Frontend sync" section of pipeline/README.md.
RUN_LOG_PUBLIC_PATH = (
    PIPELINE_DIR.parent / "frontend" / "public" / "pipeline_run_log.json"
)


@dataclass
class Stage:
    id: str  # two-digit stage number, e.g. "01"
    script: str
    # "monthly" (satellite/demographic-driven, the default refresh), "annual"
    # (real data that gains one point a year, too expensive to refetch monthly),
    # or "manual" (dev-only gate).
    cadence: str
    description: str
    # Extra CLI arguments this stage needs to run unattended. Only 15_optimize.py
    # uses this: its --budget is required and the refresh cannot invent a policy
    # number, so the published scenario is pinned here where it is reviewable in
    # a diff, rather than defaulted inside the script where it would look like a
    # technical constant.
    args: tuple[str, ...] = ()

    @property
    def default(self) -> bool:
        """Whether this stage runs in a plain `run_pipeline.py` with no flags.

        Derived from cadence rather than stored as its own field, so there is one
        place a stage's schedule is declared. Only "monthly" runs unprompted:
        "manual" is the dev-only spike and "annual" is a stage whose inputs do not
        move month to month. Each of the other cadences has its own --include-*
        opt-in flag, and naming a stage directly with --only or --from is an opt-in
        on its own.
        """
        return self.cadence == "monthly"


STAGES: list[Stage] = [
    Stage("00", "00_gee_spike.py", "manual",
          "Day-0 GEE go/no-go smoke test. Not part of a real refresh; excluded by default."),
    Stage("01", "01_grid.py", "monthly",
          "Build the 1km grid from BMC ward boundaries. Boundaries essentially never change."),
    Stage("02", "02_gee_layers.py", "monthly",
          "Dry-season Landsat LST/NDVI composite + WorldCover impervious pct via GEE."),
    Stage("03", "03_vectors.py", "monthly",
          "WorldPop population/elderly (pinned annual vintage), slum clusters, OSM hospitals."),
    Stage("04", "04_zonal.py", "monthly",
          "Consolidate raster + vector layers into one tidy per-cell table."),
    Stage("05", "05_hvi.py", "monthly",
          "PCA-weighted Heat Vulnerability Index per cell, rolled up to wards."),
    Stage("06", "06_nbs.py", "monthly",
          "NBS rule engine + ecological plantability filter (WorldCover, via GEE)."),
    Stage("07", "07_load.py", "monthly",
          "Upsert Supabase tables and write the demo-safe GeoJSON snapshots."),
    Stage("08", "08_sensitivity.py", "monthly",
          "Weight-perturbation sensitivity check and chart."),
    Stage("09", "09_ndvi_change.py", "monthly",
          "Classify each cell's NDVI delta as gained/stable/lost."),
    Stage("10", "10_ward_profile.py", "monthly",
          "Ward-level descriptive profiles for the dashboard's ward dialog."),
    Stage("11", "11_hero_city.py", "monthly",
          "Simplified ward geometry for the landing page's 3D hero model."),
    Stage("12", "12_hero_region.py", "monthly",
          "Regional coastline context for the hero model (cached after first fetch)."),
    # Runs last because it validates rather than produces: nothing downstream
    # reads its output, and a validation failure should not stop a refresh that
    # already succeeded. It depends on NOAA GSOD, which publishes on a lag, so
    # it is also the stage most likely to warn for reasons outside this repo.
    Stage("13", "13_validate_lst.py", "monthly",
          "Correlate satellite LST against NOAA GSOD weather stations."),
    # Annual, not monthly: it rebuilds one dry-season composite per year of
    # history on every run. See the cadence section of the module docstring.
    Stage("14", "14_timeseries.py", "annual",
          "Multi-year per-ward LST and NDVI trend, slope and classification."),
    # Runs after 13 because it consumes ward scores (05) and profiles (10), and
    # publishing a fresh allocation against stale scores is the failure mode worth
    # avoiding. --budget is an illustrative 5 crore scenario, flagged as such in
    # the output's own `illustrative_only` field; it is not a funded programme.
    Stage("15", "15_optimize.py", "monthly",
          "Budget-constrained cooling allocation for the published 5 crore scenario.",
          args=("--budget", "50000000")),
]

STAGE_BY_ID = {s.id: s for s in STAGES}


@dataclass
class StageResult:
    stage: Stage
    returncode: int | None
    seconds: float

    @property
    def status(self) -> str:
        """"ok" | "warn" | "fail" | "skipped", derived from returncode rather than
        stored separately: the mapping is a pure function of the exit code a stage's
        script process actually returned (None for a dry-run stage that never ran), so
        keeping it as its own field would just be the same information twice, with the
        two copies free to disagree if one were ever updated without the other.
        """
        if self.returncode is None:
            return "skipped"
        if self.returncode == 0:
            return "ok"
        if self.returncode == 2:
            return "warn"
        return "fail"


@dataclass
class RunReport:
    started_at: str
    finished_at: str | None = None
    # The dry-season Landsat composite window (see _dry_season.py) this run was
    # made from, as {"start": ..., "end": ...} ISO dates. The site shows the
    # refresh date and this window as one statement (issue #124), so the run log
    # is where the window is recorded: the orchestrator and stage 02 share the
    # same calendar function, and a consumer never has to know which stage
    # produced it.
    composite_window: dict[str, str] | None = None
    results: list[StageResult] = field(default_factory=list)

    def to_json(self) -> dict:
        return {
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "composite_window": self.composite_window,
            "stages": [
                {
                    "id": r.stage.id,
                    "script": r.stage.script,
                    "cadence": r.stage.cadence,
                    "status": r.status,
                    "returncode": r.returncode,
                    "seconds": round(r.seconds, 2),
                    # What the stage actually used and produced (issue #92):
                    # source dataset ids, the composite window it really
                    # queried, scene counts, rows in and out. Stages write this
                    # to a sidecar because the runner invokes them as
                    # subprocesses and cannot see inside. Absent for a stage
                    # that records nothing, rather than an empty object, so the
                    # log does not imply a stage was asked and had no answer.
                    **({"provenance": p} if (p := _provenance.read(r.stage.id)) else {}),
                }
                for r in self.results
            ],
        }


def parse_stage_ids(raw: str) -> list[str]:
    ids = [s.strip().zfill(2) for s in raw.split(",") if s.strip()]
    unknown = [i for i in ids if i not in STAGE_BY_ID]
    if unknown:
        raise SystemExit(f"unknown stage id(s): {unknown}. Known: {sorted(STAGE_BY_ID)}")
    return ids


def opted_in_cadences(args: argparse.Namespace) -> set[str]:
    """Non-default cadences the caller has asked for with an --include-* flag."""
    cadences = set()
    if args.include_spike:
        cadences.add("manual")
    if args.include_annual:
        cadences.add("annual")
    return cadences


def select_stages(args: argparse.Namespace) -> list[Stage]:
    """Pick which stages to run.

    --only names stages explicitly, and naming a non-default stage that way IS the
    opt-in: no reason to also require --include-spike when the user just typed "00"
    themselves. --from applies the same rule to the stage it starts at: --from 14
    starts the chain AT 14, which only makes sense if the caller meant to include
    it. Stages the chain merely sweeps past keep their own rule, so --from 13 does
    not silently pull in the annual stage that happens to sit after it.

    Without an explicit name or the matching --include-* flag, a plain
    `run_pipeline.py` runs the monthly refresh and nothing else.
    """
    if args.only:
        ids = parse_stage_ids(args.only)
        return [STAGE_BY_ID[i] for i in ids]

    ids_in_order = [s.id for s in STAGES]
    start = 0
    explicit_id = None
    if args.from_stage:
        start_id = args.from_stage.strip().zfill(2)
        if start_id not in STAGE_BY_ID:
            raise SystemExit(f"unknown --from stage id: {start_id}")
        start = ids_in_order.index(start_id)
        explicit_id = start_id

    cadences = opted_in_cadences(args)
    return [
        s for s in STAGES[start:]
        if s.default or s.cadence in cadences or s.id == explicit_id
    ]


def run_stage(stage: Stage, dry_run: bool, city: str | None = None,
              cell_size: float | None = None) -> StageResult:
    script_path = PIPELINE_DIR / stage.script
    command = [sys.executable, str(script_path), *stage.args]
    print(f"\n{'=' * 70}\n[{stage.id}] {stage.script} ({stage.cadence})\n{stage.description}\n{'=' * 70}")

    # The city travels to the subprocesses as UCIP_CITY rather than as a flag.
    # _city.load_city() already resolves in that order (explicit argument, then
    # the environment, then Mumbai) and its docstring has always described this
    # as the mechanism the runner uses; the runner simply never set it, so
    # `run_pipeline.py --city pune` was an unrecognised argument even though
    # docs/adding-a-city.md documents that exact command. Passing it in the
    # environment means a stage that parses no arguments of its own still
    # honours it.
    overrides = {}
    if city:
        overrides["UCIP_CITY"] = city
    if cell_size:
        overrides["UCIP_CELL_SIZE_M"] = str(cell_size)
    env = {**os.environ, **overrides} if overrides else None

    if dry_run:
        suffix = "".join(f"   ({k}={v})" for k, v in overrides.items())
        print("[dry-run] would execute: " + " ".join(command) + suffix)
        return StageResult(stage, None, 0.0)

    start = time.monotonic()
    proc = subprocess.run(command, cwd=PIPELINE_DIR, env=env)
    elapsed = time.monotonic() - start

    result = StageResult(stage, proc.returncode, elapsed)
    print(f"[{stage.id}] {stage.script} finished in {elapsed:.1f}s -> exit {proc.returncode} ({result.status})")
    return result


def build_parser() -> argparse.ArgumentParser:
    """The CLI, as its own function so tests exercise the real flags.

    The stage-selection tests used to hand-roll a second parser with the same
    flags, which is a copy that drifts: adding --include-annual here left those
    tests parsing a Namespace the selection logic no longer recognised.
    """
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--city", default=None, metavar="SLUG",
                         help="city slug to run (default: mumbai, or $UCIP_CITY)")
    parser.add_argument("--cell-size", default=None, type=float, metavar="METRES",
                         help="grid resolution override, e.g. 500 (default: the city config's "
                              "grid.cell_size_m). A non-default resolution writes to its own "
                              "data/<city>_<res>/ directory and never to frontend/public.")
    parser.add_argument("--include-spike", action="store_true",
                         help="also run 00_gee_spike.py (excluded by default, see module docstring)")
    parser.add_argument("--include-annual", action="store_true",
                         help="also run the annual-cadence stages (14_timeseries.py)")
    parser.add_argument("--from", dest="from_stage", metavar="STAGE_ID",
                         help="resume the chain starting at this stage id (e.g. 05)")
    parser.add_argument("--only", metavar="STAGE_IDS",
                         help="comma-separated stage ids to run instead of the full chain (e.g. 08,09)")
    parser.add_argument("--dry-run", action="store_true", help="print the execution plan without running anything")
    parser.add_argument("--keep-going", action="store_true",
                         help="don't stop the chain on a hard failure (exit code 1)")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    # The runner is part of the run, not an observer of it. Its own publish of
    # the run log goes through the same guard as every stage, and that guard
    # reads this process's environment, so the overrides have to be set here
    # too and not only in the subprocess environment. Without this the parent
    # resolved to Mumbai at 1 km and published a 500 m run's log over the
    # committed one.
    if args.city:
        os.environ["UCIP_CITY"] = args.city
    if args.cell_size:
        os.environ["UCIP_CELL_SIZE_M"] = str(args.cell_size)

    stages = select_stages(args)
    if not stages:
        print("[FAIL] no stages selected.")
        return 1

    # A stage that is not run this time must not leave its previous record
    # attached to this run's log (issue #92).
    if not args.dry_run:
        _provenance.clear()

    print("Pipeline plan:")
    for s in stages:
        print(f"  [{s.id}] {s.script:<20s} ({s.cadence})")

    # Same function stage 02 calls when it builds its composites, so the window
    # recorded here always matches the window the run actually used.
    window_start, window_end = most_recent_complete_dry_season()
    report = RunReport(
        started_at=datetime.now(timezone.utc).isoformat(),
        composite_window={"start": window_start, "end": window_end},
    )
    exit_code = 0
    for stage in stages:
        result = run_stage(stage, args.dry_run, args.city, args.cell_size)
        report.results.append(result)
        if result.status == "fail" and not args.dry_run:
            exit_code = 1
            if not args.keep_going:
                print(f"\n[FAIL] stage {stage.id} ({stage.script}) failed — stopping the chain. "
                      f"Fix the failure and resume with: python run_pipeline.py --from {stage.id}")
                break

    report.finished_at = datetime.now(timezone.utc).isoformat()

    if not args.dry_run:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        run_log_path().write_text(json.dumps(report.to_json(), indent=2), encoding="utf-8")
        print(f"\n[ok] wrote run log -> {run_log_path()}")
        # Mirror the log where the deployed site reads data from
        # (frontend/public/, issue #124): /api/v1/meta and the dashboard footer
        # serve it from there, exactly like the stage outputs in the "Frontend
        # sync" table in pipeline/README.md. The methodology page reads the
        # data/ copy server-side instead, like sensitivity.json and
        # hvi_pca_log.json.
        publish(run_log_path(), RUN_LOG_PUBLIC_PATH)

    print("\n" + "-" * 70)
    print("Summary:")
    for r in report.results:
        marker = {"ok": "OK", "warn": "WARN", "fail": "FAIL", "skipped": "SKIP"}[r.status]
        print(f"  [{marker:>4}] {r.stage.id} {r.stage.script}")
    print("-" * 70)

    if exit_code == 0:
        any_warn = any(r.status == "warn" for r in report.results)
        print("GO: pipeline refresh complete." if not any_warn else
              "GO WITH WARNINGS: pipeline refresh complete, some stages flagged CHECK WARNINGS above.")
    else:
        print("FAILED: pipeline refresh did not complete. See the failing stage's output above.")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
