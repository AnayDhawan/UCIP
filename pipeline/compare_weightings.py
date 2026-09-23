"""Compare the PCA-derived weighting against the published fallback (issue #88).

The question this answers:
    05_hvi.py derives its weights by PCA, and documents a fallback to published
    equal weighting (Reid et al. 2009's component-level default) for when PC1
    explains too little variance to trust. The two schemes had never been run
    side by side, so the obvious challenge, "how much does your data-derived
    weighting actually change the answer versus just using the published
    weights?", had no answer in the repo.

    It is the cheapest possible attack on the method and it deserved a number
    rather than a paragraph.

What it measures:
    Both weightings applied to the same z-scored cells, rolled up to wards the
    same way, then compared on rank correlation, how far any single ward moves,
    and whether the top five survive. The top five is the part that would
    actually change a spending decision, so it is reported separately from the
    correlation over all 24.

Read the output honestly:
    A high correlation is not proof the PCA weighting is right. It means the
    ranking is not very sensitive to this choice, which is a different and more
    useful claim: the wards at the top are there because of the data, not
    because of the weighting.

Inputs:
    ../data/cells_hvi.geojson   scored cells from stage 05
    ../data/hvi_pca_log.json    the PCA weights actually used

Outputs:
    ../data/weighting_comparison.json
    frontend/public/weighting_comparison.json

Run:
    .venv\\Scripts\\activate
    python compare_weightings.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
from scipy.stats import kendalltau, spearmanr

PIPELINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PIPELINE_DIR))

from _publish import publish  # noqa: E402

ROOT = PIPELINE_DIR.parent
DATA_DIR = ROOT / "data"
CELLS_PATH = DATA_DIR / "cells_hvi.geojson"
PCA_LOG_PATH = DATA_DIR / "hvi_pca_log.json"
OUT_PATH = DATA_DIR / "weighting_comparison.json"
OUT_PUBLIC_PATH = ROOT / "frontend" / "public" / "weighting_comparison.json"

# Same direction convention as stages 05 and 08: NDVI is protective, the rest
# add to vulnerability.
INDICATORS_DIRECTION = {
    "LST_C": 1, "NDVI": -1, "pop_density_km2": 1, "elderly_pct": 1,
    "slum_pct": 1, "hospital_dist_m": 1, "impervious_pct": 1,
}
TOP_N = 5


def zscore(series):
    mu, sigma = series.mean(), series.std(ddof=0)
    if sigma == 0 or np.isnan(sigma):
        return series * 0.0
    return (series - mu) / sigma


def ward_ranking(gdf, signed_z, weights) -> list[str]:
    scored = gdf.copy()
    scored["HVI"] = (signed_z * weights).sum(axis=1)
    return list(scored.groupby("ward_id")["HVI"].mean().sort_values(ascending=False).index)


def main() -> int:
    if not CELLS_PATH.exists() or not PCA_LOG_PATH.exists():
        print("[FAIL] missing input(s), run 04_zonal.py and 05_hvi.py first.")
        return 1

    gdf = gpd.read_file(CELLS_PATH)
    pca_log = json.loads(PCA_LOG_PATH.read_text(encoding="utf-8"))
    pca_weights = pca_log["weights"]
    cols = list(pca_weights.keys())

    z = gdf[cols].apply(zscore)
    signed_z = z * np.array([INDICATORS_DIRECTION[c] for c in cols])
    signed_z.columns = cols

    pca_arr = np.array([pca_weights[c] for c in cols])
    equal_arr = np.ones(len(cols)) / len(cols)

    pca_ranking = ward_ranking(gdf, signed_z, pca_arr)
    equal_ranking = ward_ranking(gdf, signed_z, equal_arr)

    pca_pos = {w: i + 1 for i, w in enumerate(pca_ranking)}
    equal_pos = {w: i + 1 for i, w in enumerate(equal_ranking)}

    wards = pca_ranking
    tau, _ = kendalltau([pca_pos[w] for w in wards], [equal_pos[w] for w in wards])
    rho, _ = spearmanr([pca_pos[w] for w in wards], [equal_pos[w] for w in wards])

    shifts = {w: equal_pos[w] - pca_pos[w] for w in wards}
    max_shift_ward = max(shifts, key=lambda w: abs(shifts[w]))

    top_overlap = len(set(pca_ranking[:TOP_N]) & set(equal_ranking[:TOP_N]))

    per_ward = [
        {
            "ward_id": w,
            "rank_pca": pca_pos[w],
            "rank_published": equal_pos[w],
            "rank_shift": shifts[w],
        }
        for w in wards
    ]

    result = {
        "question": (
            "How much does the PCA-derived weighting change the ward ranking "
            "compared with the published equal weighting it falls back to?"
        ),
        "weightings": {
            "pca": {
                "source": pca_log.get("weight_source"),
                "weights": pca_weights,
                "explained_variance_pc1": pca_log.get("explained_variance_pc1"),
            },
            "published": {
                "source": "Reid et al. 2009 component-level default, equal weighting",
                "weights": {c: 1 / len(cols) for c in cols},
            },
        },
        "agreement": {
            "kendall_tau": round(float(tau), 4),
            "spearman_rho": round(float(rho), 4),
            "wards_with_identical_rank": sum(1 for w in wards if shifts[w] == 0),
            "n_wards": len(wards),
            "max_abs_rank_shift": abs(shifts[max_shift_ward]),
            "max_shift_ward": max_shift_ward,
            f"top_{TOP_N}_overlap": top_overlap,
            f"top_{TOP_N}_pca": pca_ranking[:TOP_N],
            f"top_{TOP_N}_published": equal_ranking[:TOP_N],
        },
        "interpretation": (
            "A high correlation does not show the PCA weighting is correct. It "
            "shows the ranking is insensitive to the choice, which is the more "
            "useful claim: wards near the top are there because of the data "
            "rather than because of the weighting."
        ),
        "per_ward": per_ward,
    }

    OUT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"[ok] wrote {OUT_PATH}")
    publish(OUT_PATH, OUT_PUBLIC_PATH)

    print(f"\n[ok] Kendall tau {tau:.3f}, Spearman rho {rho:.3f}")
    print(f"[ok] top-{TOP_N} overlap: {top_overlap}/{TOP_N}")
    print(f"[ok] identical rank: {result['agreement']['wards_with_identical_rank']}/{len(wards)} wards")
    print(f"[ok] largest move: {max_shift_ward} shifts {shifts[max_shift_ward]:+d} places")
    print(f"\n     {'ward':<6} {'PCA':>5} {'published':>10} {'shift':>7}")
    for row in per_ward:
        print(f"     {row['ward_id']:<6} {row['rank_pca']:>5} "
              f"{row['rank_published']:>10} {row['rank_shift']:>+7d}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
