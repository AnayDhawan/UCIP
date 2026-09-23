"""Tests for run_pipeline.py's stage-selection logic and derived properties.

No third-party dependencies: this only exercises argument parsing and the STAGES
table, never actually runs a pipeline stage subprocess.

Run:
    pip install -r requirements-dev.txt
    pytest pipeline/tests/test_run_pipeline.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import run_pipeline as rp  # noqa: E402


def _parse(argv: list[str]):
    """Parse with the runner's own parser, not a copy of it.

    This used to hand-roll a second parser listing the same flags. Adding a flag
    to run_pipeline.py then left these tests passing a Namespace the selection
    logic could not read, so the tests failed for a reason that had nothing to do
    with the behaviour under test.
    """
    return rp.build_parser().parse_args(argv)


def test_plain_run_excludes_non_default_stages():
    stages = rp.select_stages(_parse([]))
    assert [s.id for s in stages] == [s.id for s in rp.STAGES if s.default]
    assert "00" not in [s.id for s in stages]
    assert "14" not in [s.id for s in stages]


def test_include_spike_flag_includes_it():
    stages = rp.select_stages(_parse(["--include-spike"]))
    assert stages[0].id == "00"


def test_from_00_without_include_spike_now_includes_it():
    """Regression test: --include-spike used to gate --from but not --only, so
    --from 00 silently dropped stage 00 while --only 00 ran it -- same intent
    (explicitly naming stage 00), opposite outcome, no message either way. Naming 00
    directly via --from is now its own opt-in, consistent with --only.
    """
    stages = rp.select_stages(_parse(["--from", "00"]))
    assert stages[0].id == "00"


def test_only_00_without_include_spike_includes_it():
    """The other half of the same consistency fix: --only 00 already worked this way
    and must keep working this way.
    """
    stages = rp.select_stages(_parse(["--only", "00"]))
    assert [s.id for s in stages] == ["00"]


def test_from_05_without_include_spike_excludes_spike():
    """Naming a later stage must not accidentally pull in 00 -- only an explicit
    reference to "00" itself is treated as opt-in.
    """
    stages = rp.select_stages(_parse(["--from", "05"]))
    assert stages[0].id == "05"
    assert "00" not in [s.id for s in stages]


def test_only_05_without_include_spike_excludes_spike():
    stages = rp.select_stages(_parse(["--only", "05,08"]))
    assert [s.id for s in stages] == ["05", "08"]


def test_stage_default_derived_from_cadence():
    spike = rp.STAGE_BY_ID["00"]
    grid = rp.STAGE_BY_ID["01"]
    timeseries = rp.STAGE_BY_ID["14"]
    assert spike.cadence == "manual"
    assert spike.default is False
    assert grid.cadence == "monthly"
    assert grid.default is True
    assert timeseries.cadence == "annual"
    assert timeseries.default is False


def test_include_annual_flag_includes_the_annual_stage():
    stages = rp.select_stages(_parse(["--include-annual"]))
    assert "14" in [s.id for s in stages]
    assert "00" not in [s.id for s in stages]


def test_only_14_without_the_flag_includes_it():
    """Naming a non-default stage explicitly is its own opt-in, the same rule
    stage 00 already follows."""
    stages = rp.select_stages(_parse(["--only", "14"]))
    assert [s.id for s in stages] == ["14"]


def test_from_13_does_not_sweep_in_the_annual_stage():
    """Stage 14 sits between 13 and 15 in the table. Resuming at 13 must run the
    monthly chain from there without silently adding a stage that costs one GEE
    composite per year of history."""
    stages = rp.select_stages(_parse(["--from", "13"]))
    assert [s.id for s in stages] == ["13", "15"]


def test_optimizer_stage_carries_its_required_budget():
    """15_optimize.py declares --budget required, so an unattended run needs the
    argument supplied by the stage table or the refresh fails on argparse."""
    optimize = rp.STAGE_BY_ID["15"]
    assert optimize.args == ("--budget", "50000000")
    assert rp.STAGE_BY_ID["01"].args == ()


def test_stage_result_status_derived_from_returncode():
    stage = rp.STAGE_BY_ID["01"]
    assert rp.StageResult(stage, 0, 1.0).status == "ok"
    assert rp.StageResult(stage, 2, 1.0).status == "warn"
    assert rp.StageResult(stage, 1, 1.0).status == "fail"
    assert rp.StageResult(stage, 137, 1.0).status == "fail"
    assert rp.StageResult(stage, None, 0.0).status == "skipped"


def test_run_report_serialises_composite_window():
    """The run log records the dry-season window alongside the run's timestamps
    (issue #124), so the site can show "refreshed X from imagery captured
    between A and B" as one statement."""
    report = rp.RunReport(
        started_at="2026-09-03T04:00:00+00:00",
        composite_window={"start": "2025-11-01", "end": "2026-02-28"},
    )
    log = report.to_json()
    assert log["composite_window"] == {"start": "2025-11-01", "end": "2026-02-28"}
    assert log["started_at"] == "2026-09-03T04:00:00+00:00"
    assert log["finished_at"] is None
    assert log["stages"] == []


def test_run_log_window_uses_the_shared_dry_season_helper():
    """run_pipeline must record the same window stage 02 composites, not a copy
    that could drift: the function it calls is the one defined in _dry_season.py."""
    assert rp.most_recent_complete_dry_season.__module__ == "_dry_season"
