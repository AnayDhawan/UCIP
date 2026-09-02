"""Shared "publish to frontend/public/" helper.

Why this exists:
    05_hvi.py, 06_nbs.py, 08_sensitivity.py, and 09_ndvi_change.py each copy their own
    output into frontend/public/ (see pipeline/README.md's "Frontend sync" section) so
    the browser-fetched copy stays in sync with what the pipeline just computed. The
    mkdir + shutil.copyfile + "[ok] copied -> ..." sequence was identical in all five
    call sites across those four files -- the same kind of copy-pasted-per-stage
    duplication _gee_auth.py already deduped for ee.Initialize() calls.

Deliberately NOT responsible for deciding WHEN to publish: each stage still runs its
own sanity check and only calls publish() from the `if ok:` branch (see each script's
"sanity checks" section) -- this function just performs the copy once a caller has
already decided it's safe to.
"""

from __future__ import annotations

import shutil
from pathlib import Path


def publish(src: Path, dest: Path) -> None:
    """Copy `src` (already written under data/) to `dest` (under frontend/public/),
    creating dest's parent directory if needed, and print the confirmation line every
    stage already printed inline before this was extracted.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)
    print(f"[ok] copied -> {dest}")
