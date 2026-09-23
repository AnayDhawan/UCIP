"""Cache Earth Engine zonal results between runs (issue #93).

Why this matters more than it used to:
    The expensive part of a refresh is one call: reduceRegions over every grid
    cell, then getInfo() to pull it down. Re-running any GEE stage refetched
    identical imagery and recomputed identical statistics, which burned quota
    for an answer already known.

    The refresh now runs twice a week rather than monthly. Within a dry season
    the composite window is fixed, so most of those runs ask Earth Engine the
    same question and get the same answer. Without a cache that is the same
    cost every time; with one it is paid once per season.

What the key covers:
    Everything that can change the answer. Region bounds, both date windows,
    the collection ids, the reducer scale, and a fingerprint of the grid
    itself. Miss any of those and a cache hit would serve numbers computed for
    a different question, which is worse than no cache: a 500m grid (#96) or a
    rolled window would silently keep returning the old cells.

    The grid fingerprint is why the cell geometry is hashed rather than just
    counted. Two grids can have 541 cells and cover different ground.

Deliberately not TTL-based:
    A time-to-live would either expire a still-valid entry or serve a stale
    one, and neither is necessary: the key already changes when anything that
    affects the result changes. `--no-cache` exists for the case where someone
    wants to force a refetch anyway.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

CACHE_DIR = Path(__file__).resolve().parent / "cache" / "gee"

# Bumped when the cached payload's shape changes, so an old entry is a miss
# rather than something the new code misreads.
CACHE_VERSION = 1


def _canonical(value: Any) -> str:
    """Stable JSON, so an identical request always hashes identically."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def grid_fingerprint(features: list[dict]) -> str:
    """A hash of the grid's identity and shape.

    Both parts matter. Ids alone would miss a grid that kept its ids and moved
    its cells; geometry alone would miss a relabelling that downstream joins
    depend on.
    """
    digest = hashlib.sha256()
    for feature in features:
        props = feature.get("properties", {})
        digest.update(str(props.get("grid_id", "")).encode("utf-8"))
        digest.update(_canonical(feature.get("geometry")).encode("utf-8"))
    return digest.hexdigest()[:16]


def cache_key(**parts: Any) -> str:
    """A key over everything that can change the result."""
    payload = _canonical({"_v": CACHE_VERSION, **parts})
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def path_for(key: str) -> Path:
    return CACHE_DIR / f"{key}.json"


def load(key: str) -> dict | None:
    """The cached payload, or None. Never raises: a broken cache is a miss."""
    path = path_for(key)
    if not path.exists():
        return None
    try:
        entry = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[note] ignoring unreadable cache entry {path.name}: {exc}")
        return None

    if entry.get("_v") != CACHE_VERSION:
        return None
    return entry.get("payload")


def store(key: str, payload: dict, describe: dict | None = None) -> None:
    """Write an entry. A failure here must never fail the run that produced it."""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        entry = {"_v": CACHE_VERSION, "describes": describe or {}, "payload": payload}
        path_for(key).write_text(_canonical(entry), encoding="utf-8")
    except Exception as exc:
        print(f"[note] could not write cache entry: {exc}")


def clear() -> int:
    """Remove every entry. Returns how many were removed."""
    if not CACHE_DIR.exists():
        return 0
    removed = 0
    for path in CACHE_DIR.glob("*.json"):
        try:
            path.unlink()
            removed += 1
        except Exception:
            continue
    return removed
