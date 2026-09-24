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

    It IS responsible for one thing the callers kept getting wrong: whether this
    run is allowed to write to frontend/public/ at all. CityConfig has carried a
    `publishes_to_frontend` property for exactly that, and its docstring says a
    second city's run must not swap the live dashboard's data, but only stages 14
    and 15 ever consulted it. The other seven called publish() unconditionally, so
    a Pune run would have overwritten Mumbai's published snapshots, and a 500 m
    run did overwrite them: stage 05 read 1 km cells, wrote 1 km-named output and
    copied it over the committed files, which is how this was found.

    A guard that every caller has to remember is a guard that one caller will
    forget. It lives here now, at the single chokepoint, so forgetting is not
    possible. Stages 14 and 15 keep their own check, which is harmless and saves
    them the work of writing a file nobody will copy.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from _city import CityConfig, load_city


def publish(src: Path, dest: Path, city: CityConfig | None = None) -> bool:
    """Copy `src` (already written under data/) to `dest` (under frontend/public/),
    creating dest's parent directory if needed, and print the confirmation line every
    stage already printed inline before this was extracted.

    Returns whether the copy happened. A run that is not the published
    configuration skips it and says so, rather than silently doing nothing:
    "why is the dashboard unchanged" is a question the log should answer.
    """
    city = city or load_city()
    if not city.publishes_to_frontend:
        print(
            f"[skip] not publishing {dest.name} to frontend/public: "
            f"{city.slug} at {city.grid_label} is not the published configuration"
        )
        return False

    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)
    print(f"[ok] copied -> {dest}")
    return True


def publish_text(dest: Path, text: str, city: CityConfig | None = None) -> bool:
    """Write `text` to a path under frontend/public/, under the same guard.

    Stages 10, 11 and 12 build their published payload in memory and wrote it
    straight out with `write_text`, so they never went through publish() and
    the guard above did not cover them. A 500 m run therefore still replaced
    frontend/public/ward_profiles.json and hero_city.json after every other
    leak was closed.

    Serialising twice (once for data/, once for public/) is how those stages
    are written, so this takes the text rather than a source path.
    """
    city = city or load_city()
    if not city.publishes_to_frontend:
        print(
            f"[skip] not publishing {dest.name} to frontend/public: "
            f"{city.slug} at {city.grid_label} is not the published configuration"
        )
        return False

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")
    print(f"[ok] copied -> {dest}")
    return True
