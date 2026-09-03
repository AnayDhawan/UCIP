"""Mirror the canonical city configs into the frontend bundle (issue #68).

Why a copy exists at all:
    config/cities/*.json is the single source of truth, read by pipeline/_city.py.
    The frontend needs the same values (map centre, zoom, timezone, bbox) but
    lives in its own Next.js root, and Turbopack refuses to import a module from
    outside that root. Reading it at runtime instead would mean the map cannot
    render until a fetch resolves, for data that never changes between deploys.

    So the config is mirrored into frontend/src/lib/cities/ at build time and
    committed. The copy is generated, never hand-edited.

Why this is safe:
    CI runs this with --check, which fails if the mirror has drifted from the
    canonical file. A stale copy is therefore a build failure rather than a
    frontend quietly showing a different map centre from the one the pipeline
    validated its grid against, which is exactly the class of drift this whole
    issue was about.

Run:
    python pipeline/sync_city_config.py            # write the mirror
    python pipeline/sync_city_config.py --check    # verify, used by CI
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = ROOT / "config" / "cities"
MIRROR_DIR = ROOT / "frontend" / "src" / "lib" / "cities"

HEADER_KEY = "_generated"
HEADER_VALUE = "Mirror of config/cities/. Do not edit; run pipeline/sync_city_config.py."


def mirrored_payload(path: Path) -> str:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    # $schema points at a relative path that is wrong from the mirror's location,
    # and the frontend has no use for it.
    cfg.pop("$schema", None)
    out = {HEADER_KEY: HEADER_VALUE, **cfg}
    return json.dumps(out, indent=2) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify without writing.")
    args = parser.parse_args()

    sources = sorted(SOURCE_DIR.glob("*.json"))
    if not sources:
        print(f"[FAIL] no city configs in {SOURCE_DIR}")
        return 1

    MIRROR_DIR.mkdir(parents=True, exist_ok=True)
    stale: list[str] = []

    for src in sources:
        want = mirrored_payload(src)
        dest = MIRROR_DIR / src.name
        have = dest.read_text(encoding="utf-8") if dest.exists() else None
        if have == want:
            print(f"[ok]   {src.stem}")
            continue
        if args.check:
            stale.append(src.stem)
            print(f"[FAIL] {src.stem}: frontend mirror is out of date")
        else:
            dest.write_text(want, encoding="utf-8")
            print(f"[ok]   {src.stem} -> {dest.relative_to(ROOT)}")

    # A mirror with no canonical source behind it would be served to users
    # forever without anything noticing.
    known = {s.name for s in sources}
    for orphan in sorted(p for p in MIRROR_DIR.glob("*.json") if p.name not in known):
        if args.check:
            stale.append(orphan.stem)
            print(f"[FAIL] {orphan.stem}: mirrored but has no config/cities/ source")
        else:
            orphan.unlink()
            print(f"[ok]   removed orphaned mirror {orphan.name}")

    if stale:
        print(f"\nFAILED: run `python pipeline/sync_city_config.py` and commit the result.")
        return 1
    print(f"\nGO: {len(sources)} config(s) mirrored.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
