"""Bootstrap a confidence interval for every ward's score and rank (issue #87).

The problem:
    Each ward gets a single HVI to one decimal place, which implies a precision
    the method does not have. The weights come from a PCA over 541 cells, and
    that PCA has sampling uncertainty nobody had quantified. A ward ranked 7th
    might be anywhere from 5th to 10th, and presenting "7" alone invites a
    planner to treat the gap between 7th and 8th as real.

The method:
    Resample the 541 cells with replacement, rerun the whole scoring chain on
    each resample (z-scores, PCA, weights, per-cell index, ward rollup, rank),
    and report the percentile interval across replicates.

    The entire chain is rerun rather than just the weights, because the z-scores
    and the 0-100 rescale are also estimated from the sample. Holding those
    fixed and varying only the weights would understate the uncertainty while
    looking rigorous, which is the failure mode worth avoiding in a number whose
    whole purpose is honesty about precision.

What this does and does not capture:
    It captures sampling uncertainty in the cells: how much the answer depends
    on which cells happened to be measured. It does NOT capture measurement
    error in the indicators, the choice of indicators, or the decision to
    weight by PCA at all. The last of those is #88, which compares the PCA
    weighting against the published one directly.

Inputs:
    ../data/cells_hvi.geojson   scored cells from stage 05

Outputs:
    ../data/hvi_uncertainty.json
    frontend/public/hvi_uncertainty.json

Run:
    .venv\\Scripts\\activate
    python uncertainty.py --replicates 1000
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

PIPELINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PIPELINE_DIR))

from _publish import publish  # noqa: E402
from _indicators import DIRECTIONS, REQUIRED, present

ROOT = PIPELINE_DIR.parent
DATA_DIR = ROOT / "data"
CELLS_PATH = DATA_DIR / "cells_hvi.geojson"
OUT_PATH = DATA_DIR / "hvi_uncertainty.json"
OUT_PUBLIC_PATH = ROOT / "frontend" / "public" / "hvi_uncertainty.json"

# The same direction table as stages 05 and 08, from _indicators.py.
INDICATORS_DIRECTION = DIRECTIONS

# Which indicators this run resamples. Starts as the required set and is set
# from the cells actually loaded in main(): child_pct is optional, and a bootstrap
# over a different indicator set than the index it is qualifying would report
# uncertainty for a model nobody published.
COLS: list[str] = list(REQUIRED)

DEFAULT_REPLICATES = 1000
# Fixed so a rerun reproduces the published intervals. A refresh should move
# them because the data moved, not because the random draw differed.
SEED = 20260923
MIN_EXPLAINED_VARIANCE = 0.30


def zscore_matrix(values: np.ndarray) -> np.ndarray:
    mu = values.mean(axis=0)
    sigma = values.std(axis=0, ddof=0)
    sigma = np.where(sigma == 0, 1.0, sigma)
    return (values - mu) / sigma


def weights_for(signed_z: np.ndarray) -> np.ndarray:
    """PCA weights for one sample, mirroring 05_hvi.py including its fallback."""
    pca = PCA(n_components=signed_z.shape[1])
    pca.fit(signed_z)

    if float(pca.explained_variance_ratio_[0]) < MIN_EXPLAINED_VARIANCE:
        return np.ones(signed_z.shape[1]) / signed_z.shape[1]

    loadings = pca.components_[0]
    # Orient so higher means more vulnerable, as stage 05 does.
    scores = signed_z @ loadings
    lst_index = COLS.index("LST_C")
    if np.corrcoef(scores, signed_z[:, lst_index])[0, 1] < 0:
        loadings = -loadings
    return np.abs(loadings) / np.abs(loadings).sum()


def rescale_0_100(values: np.ndarray) -> np.ndarray:
    low, high = values.min(), values.max()
    if high == low:
        return np.full_like(values, 50.0)
    return (values - low) / (high - low) * 100.0


def score_wards(raw: np.ndarray, ward_ids: np.ndarray, wards: list[str]) -> np.ndarray:
    """One replicate: z-score, weight, index, rescale, roll up to wards."""
    signed = zscore_matrix(raw) * np.array([INDICATORS_DIRECTION[c] for c in COLS])
    weights = weights_for(signed)
    cell_hvi = rescale_0_100(signed @ weights)

    frame = pd.DataFrame({"ward_id": ward_ids, "HVI": cell_hvi})
    means = frame.groupby("ward_id")["HVI"].mean()
    # reindex so a ward absent from a resample comes back as NaN rather than
    # silently shifting every other ward's position in the array.
    return means.reindex(wards).to_numpy()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replicates", type=int, default=DEFAULT_REPLICATES)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()

    if not CELLS_PATH.exists():
        print(f"[FAIL] {CELLS_PATH} not found, run 05_hvi.py first.")
        return 1

    gdf = gpd.read_file(CELLS_PATH)
    global COLS
    COLS = present(gdf.columns)
    print(f"[ok] resampling {len(COLS)} indicators: {COLS}")
    raw = gdf[COLS].to_numpy(dtype=float)
    ward_ids = gdf["ward_id"].to_numpy()
    wards = sorted(pd.unique(ward_ids).tolist())
    n_cells = len(gdf)
    print(f"[ok] {n_cells} cells, {len(wards)} wards, {args.replicates} replicates")

    point = score_wards(raw, ward_ids, wards)
    point_rank = pd.Series(point, index=wards).rank(ascending=False, method="min")

    rng = np.random.default_rng(args.seed)
    scores = np.empty((args.replicates, len(wards)))
    ranks = np.empty((args.replicates, len(wards)))

    for i in range(args.replicates):
        draw = rng.integers(0, n_cells, size=n_cells)
        replicate = score_wards(raw[draw], ward_ids[draw], wards)
        scores[i] = replicate
        ranks[i] = pd.Series(replicate, index=wards).rank(ascending=False, method="min").to_numpy()
        if (i + 1) % 200 == 0:
            print(f"     {i + 1}/{args.replicates}")

    per_ward = []
    for j, ward in enumerate(wards):
        ward_scores = scores[:, j][~np.isnan(scores[:, j])]
        ward_ranks = ranks[:, j][~np.isnan(ranks[:, j])]
        per_ward.append({
            "ward_id": ward,
            "hvi": round(float(point[j]), 2),
            "hvi_ci_low": round(float(np.percentile(ward_scores, 2.5)), 2),
            "hvi_ci_high": round(float(np.percentile(ward_scores, 97.5)), 2),
            "rank": int(point_rank[ward]),
            "rank_ci_low": int(np.percentile(ward_ranks, 2.5)),
            "rank_ci_high": int(np.percentile(ward_ranks, 97.5)),
        })

    per_ward.sort(key=lambda r: r["rank"])
    widths = [r["rank_ci_high"] - r["rank_ci_low"] for r in per_ward]

    result = {
        "method": (
            "Non-parametric bootstrap: the 541 cells are resampled with "
            "replacement and the whole scoring chain is rerun on each resample, "
            "including the z-scores, the PCA weights and the 0-100 rescale. "
            "Intervals are 2.5th to 97.5th percentiles across replicates."
        ),
        "captures": (
            "Sampling uncertainty in the cells: how much the answer depends on "
            "which cells happened to be measured."
        ),
        "does_not_capture": (
            "Measurement error in the indicators, the choice of indicators, and "
            "the decision to weight by PCA at all. That last one is quantified "
            "separately in weighting_comparison.json."
        ),
        "replicates": args.replicates,
        "seed": args.seed,
        "confidence": 0.95,
        "summary": {
            "median_rank_interval_width": float(np.median(widths)),
            "widest_rank_interval": max(widths),
            "wards_whose_rank_is_certain": sum(1 for w in widths if w == 0),
            "n_wards": len(per_ward),
        },
        "per_ward": per_ward,
    }

    OUT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"[ok] wrote {OUT_PATH}")
    publish(OUT_PATH, OUT_PUBLIC_PATH)

    print(f"\n     {'ward':<6}{'HVI':>7}{'95% CI':>18}{'rank':>6}{'rank 95% CI':>14}")
    for row in per_ward:
        ci = f"{row['hvi_ci_low']:.1f}-{row['hvi_ci_high']:.1f}"
        rci = f"{row['rank_ci_low']}-{row['rank_ci_high']}"
        print(f"     {row['ward_id']:<6}{row['hvi']:>7.1f}{ci:>18}{row['rank']:>6}{rci:>14}")

    print(f"\n[ok] median rank interval spans {np.median(widths):.0f} places, "
          f"widest {max(widths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
