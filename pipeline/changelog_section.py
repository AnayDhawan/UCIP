"""Print one version's section from CHANGELOG.md (issue #129).

Used by .github/workflows/release.yml to build a release body.

The release notes are lifted from the hand-written changelog rather than
generated from commit subjects. The changelog explains what changed and why,
in whole sentences; a list of commit subjects explains what the commits were
called. Generating the second and calling it release notes would be a
downgrade, so the automation publishes what is already written.

Exits 1 when the version has no section, so a tag pushed before the changelog
is updated fails loudly instead of publishing an empty release.

Run:
    python changelog_section.py 1.0.0 [--changelog path]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DEFAULT_CHANGELOG = Path(__file__).resolve().parent.parent / "CHANGELOG.md"


def section_for(text: str, version: str) -> str | None:
    """The body under `## [version]`, up to the next `## [` heading."""
    heading = re.compile(r"^## \[([^\]]+)\]")
    lines = text.splitlines()

    start = None
    for i, line in enumerate(lines):
        match = heading.match(line)
        if match and match.group(1) == version:
            start = i + 1
            break

    if start is None:
        return None

    end = len(lines)
    for i in range(start, len(lines)):
        if heading.match(lines[i]):
            end = i
            break

    return "\n".join(lines[start:end]).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", help="version without a leading v, e.g. 1.0.0")
    parser.add_argument("--changelog", type=Path, default=DEFAULT_CHANGELOG)
    args = parser.parse_args()

    if not args.changelog.exists():
        print(f"[FAIL] no changelog at {args.changelog}", file=sys.stderr)
        return 1

    body = section_for(args.changelog.read_text(encoding="utf-8"), args.version)

    if body is None:
        print(
            f"[FAIL] CHANGELOG.md has no '## [{args.version}]' section. "
            "Write the entry before pushing the tag.",
            file=sys.stderr,
        )
        return 1

    if not body:
        print(f"[FAIL] the '## [{args.version}]' section is empty.", file=sys.stderr)
        return 1

    print(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
