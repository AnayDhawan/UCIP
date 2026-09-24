"""Evaluate the elderly_pct indicator against its own source (issue #95).

The question the issue asked was whether to swap WorldPop's modelled age
surface for ward-level Census age structure, weighing a 2011 census vintage
against 2020 modelled data used with 2025-26 imagery.

Measuring the current indicator first changes that question, because the
premise turns out to be wrong in a way worth checking before anyone spends
effort on the swap. This script does the measuring, so the finding is
reproducible rather than a claim in a document.

What it reports:

1. How much information elderly_pct actually carries. Distinct values, the
   share of cells on the most common one, and the coefficient of variation
   against the other six indicators.

2. Whether the spatial pattern is demographic or administrative. If every
   ward in one revenue district carries one value and every ward in the other
   carries another, the layer is a district dummy wearing a demographic label.

3. What it does to the published ranking. The index is recomputed with the
   indicator dropped, and the ward ranks are compared, which is the only
   number that answers "does this matter".

Run:
    python pipeline/elderly_evaluation.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _city import load_city  # noqa: E402

# Mirrors 05_hvi.py. Duplicated deliberately rather than imported: the stage
# modules are numbered and not importable as packages, and a copy that is read
# alongside its original in review is safer here than a sys.path trick.
INDICATORS = {
    "LST_C": 1,
    "NDVI": -1,
    "pop_density_km2": 1,
    "elderly_pct": 1,
    "slum_pct": 1,
    "hospital_dist_m": 1,
    "impervious_pct": 1,
}
MIN_EXPLAINED_VARIANCE = 0.30

# Mumbai is two revenue districts: Mumbai City, the island wards in the south,
# and Mumbai Suburban. The 2011 Census publishes age structure per district.
MUMBAI_CITY_WARDS = {"A", "B", "C", "D", "E", "F/N", "F/S", "G/N", "G/S"}


def zscore(series: pd.Series) -> pd.Series:
    mu, sigma = series.mean(), series.std(ddof=0)
    if sigma == 0 or np.isnan(sigma):
        return series * 0.0
    return (series - mu) / sigma


def rescale_0_100(series: pd.Series) -> pd.Series:
    lo, hi = series.min(), series.max()
    if hi == lo:
        return series * 0 + 50.0
    return (series - lo) / (hi - lo) * 100.0


def ward_ranks(cells: pd.DataFrame, indicators: dict[str, int]) -> pd.Series:
    """Ward ranks from the full index chain over the given indicator set."""
    cols = list(indicators)
    z = cells[cols].apply(zscore)
    signed = z * np.array([indicators[c] for c in cols])

    pca = PCA(n_components=len(cols))
    pca.fit(signed.values)
    explained, loadings = float(pca.explained_variance_ratio_[0]), pca.components_[0]

    if explained < MIN_EXPLAINED_VARIANCE:
        weights = np.ones(len(cols)) / len(cols)
    else:
        scores = signed.values @ loadings
        if np.corrcoef(scores, signed["LST_C"])[0, 1] < 0:
            loadings = -loadings
        weights = np.abs(loadings) / np.abs(loadings).sum()

    hvi = rescale_0_100(pd.Series(signed.values @ weights, index=cells.index))
    ward = hvi.groupby(cells["ward_id"]).mean()
    return ward.rank(ascending=False, method="min").astype(int)


def main() -> int:
    city = load_city()
    path = city.out("cells_hvi.geojson")
    if not path.exists():
        print(f"[FAIL] {path} not found - run 05_hvi.py first.")
        return 1

    raw = json.loads(path.read_text(encoding="utf-8"))
    cells = pd.DataFrame([f["properties"] for f in raw["features"]])
    cells = cells.dropna(subset=list(INDICATORS))
    print(f"[ok] loaded {len(cells)} cells from {path.name}")

    report: dict = {"city": city.slug, "n_cells": int(len(cells))}

    # ---- 1. How much information is in the layer -------------------------
    values = cells["elderly_pct"].round(4)
    counts = Counter(values)
    top_value, top_n = counts.most_common(1)[0]
    two_share = sum(n for _, n in counts.most_common(2)) / len(values)

    print("\n[1] information content")
    print(f"    distinct values            : {len(counts)} across {len(values)} cells")
    print(f"    most common value          : {top_value} on {top_n} cells ({top_n/len(values):.1%})")
    print(f"    top two values cover       : {two_share:.1%} of cells")

    print("\n    coefficient of variation, all seven indicators:")
    cvs = {}
    for col in INDICATORS:
        series = cells[col]
        cv = float(series.std(ddof=0) / abs(series.mean())) if series.mean() else float("nan")
        cvs[col] = cv
    for col, cv in sorted(cvs.items(), key=lambda kv: kv[1]):
        marker = "  <-- lowest" if col == min(cvs, key=cvs.get) else ""
        print(f"      {col:20} {cv:6.3f}{marker}")

    report["information"] = {
        "distinct_values": len(counts),
        "most_common_value": float(top_value),
        "most_common_share": round(top_n / len(values), 4),
        "top_two_share": round(two_share, 4),
        "coefficient_of_variation": {k: round(v, 4) for k, v in cvs.items()},
        "lowest_cv_indicator": min(cvs, key=cvs.get),
    }

    # ---- 2. Demographic, or administrative? ------------------------------
    by_ward = defaultdict(Counter)
    for _, row in cells.iterrows():
        by_ward[row["ward_id"]][round(row["elderly_pct"], 3)] += 1
    dominant = {w: c.most_common(1)[0][0] for w, c in by_ward.items()}

    groups = defaultdict(list)
    for ward, value in dominant.items():
        groups[value].append(ward)

    print("\n[2] is the pattern demographic or administrative?")
    separates = len(groups) == 2
    for value, wards in sorted(groups.items()):
        city_side = sorted(w for w in wards if w in MUMBAI_CITY_WARDS)
        sub_side = sorted(w for w in wards if w not in MUMBAI_CITY_WARDS)
        print(f"    elderly_pct = {value}")
        print(f"      Mumbai City wards     : {city_side or '-'}")
        print(f"      Mumbai Suburban wards : {sub_side or '-'}")
        if city_side and sub_side:
            separates = False

    if separates:
        print("\n    Every ward in each revenue district carries that district's single")
        print("    value, with no exceptions. The layer resolves the district boundary")
        print("    and nothing inside it.")

    report["administrative_split"] = {
        "distinct_ward_values": len(groups),
        "matches_district_boundary_exactly": bool(separates),
        "ward_values": {w: float(v) for w, v in sorted(dominant.items())},
    }

    # ---- 3. What it does to the ranking ----------------------------------
    with_it = ward_ranks(cells, INDICATORS)
    without = ward_ranks(cells, {k: v for k, v in INDICATORS.items() if k != "elderly_pct"})

    moved = [(w, int(with_it[w]), int(without[w])) for w in with_it.index if with_it[w] != without[w]]
    biggest = max((abs(a - b) for _, a, b in moved), default=0)

    print("\n[3] effect on the published ranking, dropping the indicator entirely")
    print(f"    wards changing rank        : {len(moved)} of {len(with_it)}")
    print(f"    largest move               : {biggest} places")
    for ward, a, b in sorted(moved, key=lambda t: -abs(t[1] - t[2]))[:8]:
        print(f"      {ward:>5}  {a:>2} -> {b:>2}  ({b - a:+d})")

    report["rank_effect"] = {
        "wards_changing_rank": len(moved),
        "of_total": int(len(with_it)),
        "largest_move_places": int(biggest),
        "moves": {w: {"with": a, "without": b} for w, a, b in moved},
    }

    out = city.out("elderly_evaluation.json")
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\n[ok] wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
