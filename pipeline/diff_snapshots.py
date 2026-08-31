"""M7 — Alert-worthy change detection between two pipeline refreshes (issue #61).

What this is:
    A pure diff over two runs' worth of pipeline output: given a "before" directory and
    an "after" directory (each holding `wards_hvi.geojson`, `nbs_recommendations.json`,
    and `cells_ndvi_change.geojson`), report per ward what actually changed:
        - HVI rank shift (old rank -> new rank, and by how many places)
        - NBS recommendations added or removed
        - Green-cover classification flip (the ward's majority gained/stable/lost class)
    This is exactly the signal issue #61 asks for: "a saved ward's HVI rank shifts by N
    places, an NBS recommendation changes, or a green-cover-loss classification flips
    for that ward" — computed once per refresh, independent of any particular viewer.

What this deliberately is NOT (out of scope, see the PR description):
    - No per-user "saved wards" filtering. Issue #59 (Supabase Auth + saved-ward
      profiles) does not exist in this repo yet; when it does, it can filter this
      script's output down to a user's saved wards rather than duplicating the diff
      logic itself.
    - No email sending. This produces a structured diff artifact
      (`data/pipeline_diff.json` by default); wiring it to a mailer is future work that
      depends on #59 for "who gets alerted about which wards."

Design notes:
    Reads only the three GeoJSON/JSON files as plain JSON (stdlib only, no geopandas
    dependency) so this stays cheap to run and to unit test — see pipeline/tests/
    test_diff_snapshots.py, which does not need the geospatial stack installed.

    "Before" and "after" are two directories rather than two fixed filenames because in
    CI (see .github/workflows/pipeline-refresh.yml) "before" is a checkout of the
    previously-committed data/ before the refresh runs, and "after" is data/ once
    run_pipeline.py has regenerated it — the diff needs both on disk at once, which two
    directories give you for free.

Run:
    python diff_snapshots.py --old-dir /path/to/previous/data --new-dir ../data \
        --out ../data/pipeline_diff.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

WARDS_HVI_FILENAME = "wards_hvi.geojson"
NBS_RECS_FILENAME = "nbs_recommendations.json"
NDVI_CHANGE_FILENAME = "cells_ndvi_change.geojson"


def _load_json(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_ward_hvi(data_dir: Path) -> dict[str, dict]:
    """ward_id -> {"hvi": float | None, "rank": int | None}, from wards_hvi.geojson."""
    gj = _load_json(data_dir / WARDS_HVI_FILENAME)
    if gj is None:
        return {}
    out = {}
    for feat in gj.get("features", []):
        props = feat.get("properties", {})
        ward_id = props.get("ward_id")
        if ward_id is None:
            continue
        out[str(ward_id)] = {
            "hvi": props.get("HVI") if props.get("HVI") is not None else props.get("hvi"),
            "rank": props.get("rank"),
        }
    return out


def load_nbs_by_ward(data_dir: Path) -> dict[str, set[str]]:
    """ward_id -> set of intervention names currently recommended, from nbs_recommendations.json."""
    recs = _load_json(data_dir / NBS_RECS_FILENAME)
    if recs is None:
        return {}
    out: dict[str, set[str]] = {}
    for r in recs:
        ward_id = str(r.get("ward_id"))
        intervention = r.get("intervention")
        if not ward_id or not intervention:
            continue
        out.setdefault(ward_id, set()).add(intervention)
    return out


def load_green_cover_by_ward(data_dir: Path) -> dict[str, str]:
    """ward_id -> majority per-cell change_class ("gained"/"stable"/"lost"/"unknown"),
    from cells_ndvi_change.geojson. A ward's cells rarely agree unanimously, so this
    rolls the cell-level classification up to the single class that describes the
    ward overall, the same "majority" logic a reader means by "did this ward gain or
    lose canopy."
    """
    gj = _load_json(data_dir / NDVI_CHANGE_FILENAME)
    if gj is None:
        return {}
    classes_by_ward: dict[str, Counter] = {}
    for feat in gj.get("features", []):
        props = feat.get("properties", {})
        ward_id = props.get("ward_id")
        change_class = props.get("change_class")
        if ward_id is None or change_class is None:
            continue
        classes_by_ward.setdefault(str(ward_id), Counter())[change_class] += 1
    return {ward_id: counter.most_common(1)[0][0] for ward_id, counter in classes_by_ward.items()}


@dataclass
class RankChange:
    ward_id: str
    old_rank: Optional[int]
    new_rank: Optional[int]
    delta: Optional[int]  # positive = became MORE vulnerable (worse rank number is lower, so delta = old - new)
    old_hvi: Optional[float]
    new_hvi: Optional[float]


@dataclass
class NbsChange:
    ward_id: str
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)


@dataclass
class GreenCoverChange:
    ward_id: str
    old_class: Optional[str]
    new_class: str


@dataclass
class DiffResult:
    old_dir: str
    new_dir: str
    rank_changes: list[RankChange]
    nbs_changes: list[NbsChange]
    green_cover_changes: list[GreenCoverChange]
    had_baseline: bool  # False if old_dir had none of the three files (e.g. first-ever run)

    def to_json(self) -> dict:
        return {
            "old_dir": self.old_dir,
            "new_dir": self.new_dir,
            "had_baseline": self.had_baseline,
            "summary": {
                "rank_changes": len(self.rank_changes),
                "nbs_changes": len(self.nbs_changes),
                "green_cover_changes": len(self.green_cover_changes),
            },
            "rank_changes": [
                {
                    "ward_id": c.ward_id, "old_rank": c.old_rank, "new_rank": c.new_rank,
                    "delta": c.delta, "old_hvi": c.old_hvi, "new_hvi": c.new_hvi,
                }
                for c in self.rank_changes
            ],
            "nbs_changes": [
                {"ward_id": c.ward_id, "added": sorted(c.added), "removed": sorted(c.removed)}
                for c in self.nbs_changes
            ],
            "green_cover_changes": [
                {"ward_id": c.ward_id, "old_class": c.old_class, "new_class": c.new_class}
                for c in self.green_cover_changes
            ],
        }


def diff_rank(old: dict[str, dict], new: dict[str, dict]) -> list[RankChange]:
    changes = []
    for ward_id in sorted(set(old) | set(new)):
        o, n = old.get(ward_id, {}), new.get(ward_id, {})
        old_rank, new_rank = o.get("rank"), n.get("rank")
        if old_rank == new_rank:
            continue
        if old_rank is None or new_rank is None:
            delta = None
        else:
            delta = old_rank - new_rank  # positive => moved toward rank 1, i.e. more vulnerable
        changes.append(RankChange(ward_id, old_rank, new_rank, delta, o.get("hvi"), n.get("hvi")))
    return changes


def diff_nbs(old: dict[str, set[str]], new: dict[str, set[str]]) -> list[NbsChange]:
    changes = []
    for ward_id in sorted(set(old) | set(new)):
        o, n = old.get(ward_id, set()), new.get(ward_id, set())
        added, removed = n - o, o - n
        if added or removed:
            changes.append(NbsChange(ward_id, sorted(added), sorted(removed)))
    return changes


def diff_green_cover(old: dict[str, str], new: dict[str, str]) -> list[GreenCoverChange]:
    changes = []
    for ward_id in sorted(set(old) | set(new)):
        o, n = old.get(ward_id), new.get(ward_id)
        if n is None or o == n:
            continue
        changes.append(GreenCoverChange(ward_id, o, n))
    return changes


def compute_diff(old_dir: Path, new_dir: Path) -> DiffResult:
    old_files_present = any(
        (old_dir / name).exists()
        for name in (WARDS_HVI_FILENAME, NBS_RECS_FILENAME, NDVI_CHANGE_FILENAME)
    )

    if not old_files_present:
        # No previous run to compare against (e.g. the very first refresh). Reporting
        # every ward in the new run as a "change" from nothing would just be noise —
        # there is nothing alert-worthy about a baseline appearing for the first time.
        return DiffResult(
            old_dir=str(old_dir), new_dir=str(new_dir),
            rank_changes=[], nbs_changes=[], green_cover_changes=[],
            had_baseline=False,
        )

    old_rank = load_ward_hvi(old_dir)
    new_rank = load_ward_hvi(new_dir)
    old_nbs = load_nbs_by_ward(old_dir)
    new_nbs = load_nbs_by_ward(new_dir)
    old_green = load_green_cover_by_ward(old_dir)
    new_green = load_green_cover_by_ward(new_dir)

    return DiffResult(
        old_dir=str(old_dir),
        new_dir=str(new_dir),
        rank_changes=diff_rank(old_rank, new_rank),
        nbs_changes=diff_nbs(old_nbs, new_nbs),
        green_cover_changes=diff_green_cover(old_green, new_green),
        had_baseline=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--old-dir", required=True, type=Path, help="directory holding the PREVIOUS run's output")
    parser.add_argument("--new-dir", required=True, type=Path, help="directory holding the CURRENT run's output")
    parser.add_argument("--out", type=Path, default=None, help="write the diff JSON here (default: print only)")
    args = parser.parse_args()

    if not args.new_dir.exists():
        print(f"[FAIL] --new-dir {args.new_dir} does not exist.")
        return 1

    result = compute_diff(args.old_dir, args.new_dir)

    if not result.had_baseline:
        print(f"[ok] no previous run found at {args.old_dir} — nothing to diff against (first-ever run?). "
              "Writing an empty diff.")

    payload = result.to_json()
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"[ok] wrote diff -> {args.out}")

    print(f"\n{len(result.rank_changes)} ward(s) with an HVI rank change")
    for c in result.rank_changes:
        direction = "more vulnerable" if (c.delta or 0) > 0 else "less vulnerable"
        print(f"  {c.ward_id}: rank {c.old_rank} -> {c.new_rank} ({direction})")

    print(f"\n{len(result.nbs_changes)} ward(s) with an NBS recommendation change")
    for c in result.nbs_changes:
        if c.added:
            print(f"  {c.ward_id}: + {', '.join(c.added)}")
        if c.removed:
            print(f"  {c.ward_id}: - {', '.join(c.removed)}")

    print(f"\n{len(result.green_cover_changes)} ward(s) with a green-cover classification flip")
    for c in result.green_cover_changes:
        print(f"  {c.ward_id}: {c.old_class} -> {c.new_class}")

    print("\nGO")
    return 0


if __name__ == "__main__":
    sys.exit(main())
