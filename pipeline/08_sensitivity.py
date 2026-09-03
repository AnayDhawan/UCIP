"""Stage 08 — Test whether the ward ranking survives its own weight uncertainty.

What it does:
    Perturbs each indicator's weight by plus and minus 20 percent, renormalising
    the rest so the weights still sum to one, recomputes the ward ranking for
    every perturbation, and measures how much the order actually moves (Kendall
    tau against the baseline, plus raw rank-change counts).

    This exists to answer the hardest question the project can be asked: "you
    derived these weights from one PCA on one city, so why should anyone trust
    the ranking?" A ranking that holds under a 20 percent wobble in every weight
    is a much weaker thing to attack than a ranking presented as exact.

    One-at-a-time rather than Monte Carlo, deliberately: each bar in the output
    chart is attributable to exactly one weight's uncertainty, which is
    readable. Fourteen runs for seven indicators.

Inputs:
    ../data/cells_hvi.geojson       scored cells from stage 05
    ../data/hvi_pca_log.json        the baseline weights

Outputs:
    ../data/sensitivity.json            tau and rank movement per perturbation
    ../data/sensitivity_chart.png       the chart the methodology page shows
    frontend/public/ copies of both

Run:
    .venv\\Scripts\\activate
    python 08_sensitivity.py
"""

import json
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib
import numpy as np
from scipy.stats import kendalltau

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from _publish import publish

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CELLS_PATH = DATA_DIR / "cells.geojson"
PCA_LOG_PATH = DATA_DIR / "hvi_pca_log.json"
OUT_JSON_PATH = DATA_DIR / "sensitivity.json"
OUT_CHART_PATH = DATA_DIR / "sensitivity_chart.png"
# sensitivity.json itself is read server-side straight out of data/ (see
# frontend/src/app/methodology/page.tsx's readJson, which resolves "../data/..." from
# frontend/), so it needs no copy. The chart PNG is different: methodology/page.tsx
# renders it as a plain <img src="/sensitivity_chart.png">, a browser-fetched static
# asset, so it has to land in frontend/public/ on every refresh like the other
# browser-fetched outputs.
OUT_CHART_PUBLIC_PATH = ROOT / "frontend" / "public" / "sensitivity_chart.png"

INDICATORS_DIRECTION = {
    "LST_C": 1, "NDVI": -1, "pop_density_km2": 1, "elderly_pct": 1,
    "slum_pct": 1, "hospital_dist_m": 1, "impervious_pct": 1,
}
PERTURBATION = 0.20
TOP_N = 5


def zscore(series):
    mu, sigma = series.mean(), series.std(ddof=0)
    if sigma == 0 or np.isnan(sigma):
        return series * 0.0
    return (series - mu) / sigma


def ward_ranking(gdf, signed_z, weights) -> tuple:
    hvi_raw = (signed_z * weights).sum(axis=1)
    gdf = gdf.copy()
    gdf["HVI"] = hvi_raw
    ward_hvi = gdf.groupby("ward_id")["HVI"].mean().sort_values(ascending=False)
    ranking = list(ward_hvi.index)
    return ranking, ward_hvi


def main() -> int:
    if not CELLS_PATH.exists() or not PCA_LOG_PATH.exists():
        print("[FAIL] missing input(s) — run 04_zonal.py and 05_hvi.py first.")
        return 1

    gdf = gpd.read_file(CELLS_PATH)
    pca_log = json.loads(PCA_LOG_PATH.read_text(encoding="utf-8"))
    base_weights = pca_log["weights"]
    cols = list(base_weights.keys())
    print(f"[ok] loaded {len(gdf)} cells, base weights: {base_weights}")

    z = gdf[cols].apply(zscore)
    signed_z = z * np.array([INDICATORS_DIRECTION[c] for c in cols])
    signed_z.columns = cols

    base_arr = np.array([base_weights[c] for c in cols])
    baseline_ranking, baseline_hvi = ward_ranking(gdf, signed_z, base_arr)
    baseline_top_n = set(baseline_ranking[:TOP_N])
    print(f"[ok] baseline top-{TOP_N}: {baseline_ranking[:TOP_N]}")

    runs = []
    for c in cols:
        for direction, sign in [("+20%", 1), ("-20%", -1)]:
            perturbed = base_arr.copy()
            idx = cols.index(c)
            perturbed[idx] = perturbed[idx] * (1 + sign * PERTURBATION)
            perturbed = perturbed / perturbed.sum()  # renormalize to sum 1

            ranking, _ = ward_ranking(gdf, signed_z, perturbed)
            top_n = set(ranking[:TOP_N])
            overlap = len(top_n & baseline_top_n)

            baseline_rank_map = {w: i for i, w in enumerate(baseline_ranking)}
            perturbed_rank_map = {w: i for i, w in enumerate(ranking)}
            common = list(baseline_rank_map.keys())
            tau, _ = kendalltau(
                [baseline_rank_map[w] for w in common],
                [perturbed_rank_map[w] for w in common],
            )

            runs.append({
                "indicator": c, "perturbation": direction,
                "kendall_tau": float(tau), "top5_overlap": overlap,
                "top5_ranking": ranking[:TOP_N],
            })

    mean_tau = float(np.mean([r["kendall_tau"] for r in runs]))
    mean_overlap = float(np.mean([r["top5_overlap"] for r in runs]))
    all_stable = all(r["top5_overlap"] == TOP_N for r in runs)

    OUT_JSON_PATH.write_text(json.dumps({
        "baseline_top5": baseline_ranking[:TOP_N],
        "perturbation_pct": PERTURBATION,
        "n_runs": len(runs),
        "mean_kendall_tau": mean_tau,
        "mean_top5_overlap": mean_overlap,
        "all_top5_stable": all_stable,
        "runs": runs,
    }, indent=2), encoding="utf-8")
    print(f"[ok] wrote sensitivity results -> {OUT_JSON_PATH}")

    # ------------------------------------------------------------- chart --
    labels = [f"{r['indicator']}\n{r['perturbation']}" for r in runs]
    taus = [r["kendall_tau"] for r in runs]
    fig, ax = plt.subplots(figsize=(11, 4.5))
    bars = ax.bar(labels, taus, color="#3b7dd8")
    ax.axhline(1.0, color="gray", linestyle="--", linewidth=1)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Kendall tau vs. baseline ward ranking")
    ax.set_title(f"HVI ward-ranking stability under ±{int(PERTURBATION*100)}% weight perturbation "
                 f"(mean top-{TOP_N} overlap: {mean_overlap:.1f}/{TOP_N})")
    plt.xticks(rotation=60, ha="right", fontsize=8)
    plt.tight_layout()
    fig.savefig(OUT_CHART_PATH, dpi=150)
    print(f"[ok] wrote chart -> {OUT_CHART_PATH}")

    # ------------------------------------------------------- sanity checks --
    # Runs BEFORE the frontend/public copy below, on purpose -- see 05_hvi.py's
    # matching comment.
    ok = mean_tau > 0.7 and mean_overlap >= TOP_N - 1
    print(f"\nmean Kendall tau={mean_tau:.3f}, mean top-{TOP_N} overlap={mean_overlap:.1f}/{TOP_N}, "
          f"all runs fully stable={all_stable}")

    if ok:
        publish(OUT_CHART_PATH, OUT_CHART_PUBLIC_PATH)
    else:
        print(f"[WARN] sanity check failed -- NOT copying to {OUT_CHART_PUBLIC_PATH}; "
              "the live site keeps serving its previous sensitivity_chart.png")

    print("GO: ranking stable under perturbation." if ok else "CHECK: ranking sensitive to some weight(s) — inspect sensitivity.json.")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
