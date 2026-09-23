"""Per-stage provenance, written by stages and collected by the runner (#92).

The problem:
    pipeline_run_log.json recorded which stages ran, their exit codes and their
    durations. Nothing about the data itself. So a published figure could not be
    traced back to the imagery that produced it, and "the LST is from Landsat 8"
    was a claim in a document rather than a fact in the output.

Why a sidecar file per stage:
    The runner invokes each stage as a subprocess, so it cannot see which
    collection a stage queried or how many rows it wrote. Stages record what
    they used into data/provenance/<id>.json, and the runner folds those into
    the run log when the stage finishes. The alternative, parsing stdout, would
    make every log line load-bearing.

Recording must never break a refresh:
    A stage that produces correct data and fails to describe itself is a worse
    outcome if the failure is fatal. Every function here swallows its own
    errors and says so in the log, so provenance is best-effort by design.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

PROVENANCE_DIR = Path(__file__).resolve().parent.parent / "data" / "provenance"


def clear() -> None:
    """Drop everything from a previous run, so a stage that is skipped this
    time cannot leave last run's provenance attached to this one."""
    try:
        shutil.rmtree(PROVENANCE_DIR, ignore_errors=True)
    except Exception as exc:  # pragma: no cover
        print(f"[note] could not clear provenance: {exc}")


def record(stage_id: str, **fields: Any) -> None:
    """Merge fields into this stage's provenance record.

    Called more than once per stage, so a stage can record its inputs early and
    its row counts at the end without holding everything in memory.
    """
    try:
        PROVENANCE_DIR.mkdir(parents=True, exist_ok=True)
        path = PROVENANCE_DIR / f"{stage_id}.json"

        existing: dict[str, Any] = {}
        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8"))

        existing.update({k: v for k, v in fields.items() if v is not None})
        path.write_text(json.dumps(existing, indent=2, default=str), encoding="utf-8")
    except Exception as exc:
        # Best effort. A stage that computed the right numbers should not fail
        # because it could not write a note about them.
        print(f"[note] provenance not recorded for stage {stage_id}: {exc}")


def read(stage_id: str) -> dict[str, Any] | None:
    try:
        path = PROVENANCE_DIR / f"{stage_id}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def collect() -> dict[str, dict[str, Any]]:
    """Every stage's provenance, keyed by stage id."""
    out: dict[str, dict[str, Any]] = {}
    if not PROVENANCE_DIR.exists():
        return out
    for path in sorted(PROVENANCE_DIR.glob("*.json")):
        try:
            out[path.stem] = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
    return out
