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
    parser = __import__("argparse").ArgumentParser()
    parser.add_argument("--include-spike", action="store_true")
    parser.add_argument("--from", dest="from_stage")
    parser.add_argument("--only")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--keep-going", action="store_true")
    return parser.parse_args(argv)


def test_plain_run_excludes_spike_stage():
    stages = rp.select_stages(_parse([]))
    assert [s.id for s in stages] == [s.id for s in rp.STAGES if s.id != "00"]


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
    assert spike.cadence == "manual"
    assert spike.default is False
    assert grid.cadence == "monthly"
    assert grid.default is True


def test_stage_result_status_derived_from_returncode():
    stage = rp.STAGE_BY_ID["01"]
    assert rp.StageResult(stage, 0, 1.0).status == "ok"
    assert rp.StageResult(stage, 2, 1.0).status == "warn"
    assert rp.StageResult(stage, 1, 1.0).status == "fail"
    assert rp.StageResult(stage, 137, 1.0).status == "fail"
    assert rp.StageResult(stage, None, 0.0).status == "skipped"
