"""Render data/pipeline_diff.json (diff_snapshots.py's output) as Markdown.

Used by .github/workflows/pipeline-refresh.yml to build the body of the automated
refresh PR — kept as a standalone script rather than an inline shell heredoc so the
workflow YAML stays simple and this is testable/runnable on its own.

Run:
    python format_diff_summary.py ../data/pipeline_diff.json
"""

import json
import sys
from pathlib import Path


def render(diff: dict) -> str:
    lines = ["## What changed since the last refresh", ""]

    if not diff.get("had_baseline"):
        lines.append("No previous run to diff against (first refresh).")
        return "\n".join(lines)

    s = diff["summary"]
    lines.append(f"- HVI rank changes: {s['rank_changes']} ward(s)")
    lines.append(f"- NBS recommendation changes: {s['nbs_changes']} ward(s)")
    lines.append(f"- Green-cover classification flips: {s['green_cover_changes']} ward(s)")
    lines.append("")
    lines.append("Full per-ward diff: `data/pipeline_diff.json` (also attached as a workflow artifact).")
    return "\n".join(lines)


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("../data/pipeline_diff.json")
    if not path.exists():
        print("Diff step did not produce output — see the workflow run log.")
        return 0
    diff = json.loads(path.read_text(encoding="utf-8"))
    print(render(diff))
    return 0


if __name__ == "__main__":
    sys.exit(main())
