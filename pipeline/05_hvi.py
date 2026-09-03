"""Stage 05 — Compute the Heat Vulnerability Index. The core of the project.

What it does:
    Standardises the seven indicators to z-scores, orients each one so that
    higher always means more vulnerable (NDVI is inverted; more greenery is less
    vulnerability), then derives the weights from a PCA over the standardised
    cells, following Reid et al. 2009. The weighted sum is rescaled to 0-100 and
    rolled up from cells to the 24 wards, which are then ranked.

    The weights come from the data rather than from judgement. That is the
    single claim this project rests on, and it is why the PCA loadings and
    explained variance are logged to disk for the methodology page instead of
    staying inside the script.

    Per-factor contributions (weight x z-score) are stored per cell and per ward.
    That IS the explainability layer: the index is a transparent linear
    combination, so a ward's score decomposes exactly into its drivers with no
    post-hoc attribution needed. No SHAP, by design, because there is no
    black box to explain.

    If the PCA loadings come out unstable or with signs that contradict the
    literature, the script falls back to published weights verbatim and exits 2
    so the run is flagged rather than silently trusted.

Inputs:
    ../data/cells.geojson       tidy indicator table from stage 04

Outputs:
    ../data/cells_hvi.geojson       per-cell HVI and contrib_* breakdown
    ../data/wards_hvi.geojson       per-ward HVI, rank, n_cells, contributions
    ../data/hvi_pca_log.json        loadings, explained variance, fallback flag
    frontend/public/wards_hvi.geojson   same wards file, published for the site

Notes:
    wards_hvi.geojson is read directly by the browser (useWardData.ts,
    WardChoropleth.tsx) and server-side by page.tsx, so it must land in
    frontend/public/ as well as data/ on every refresh. See _publish.py.

    Every number in the pitch deck and on the methodology page traces back to
    this stage's output. Changing the indicator set, the directions, or the
    rescaling changes all of them at once.

See docs/methodology.md sections 3 to 5 and docs/references.md (Reid et al. 2009).

Run:
    .venv\\Scripts\\activate
    python 05_hvi.py
"""

import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
from sklearn.decomposition import PCA

from _publish import publish

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
IN_PATH = DATA_DIR / "cells.geojson"
OUT_CELLS_PATH = DATA_DIR / "cells_hvi.geojson"
OUT_WARDS_PATH = DATA_DIR / "wards_hvi.geojson"
OUT_METHOD_PATH = DATA_DIR / "hvi_pca_log.json"
# wards_hvi.geojson is what the frontend actually reads at request time (server-side
# in page.tsx via fs, client-side via fetch in useWardData.ts and WardChoropleth.tsx),
# so it has to land in frontend/public/, not just data/, on every refresh -- the same
# "write to data/ AND frontend/public/" pattern 10_ward_profile.py, 11_hero_city.py and
# 12_hero_region.py already use for their own outputs.
OUT_WARDS_PUBLIC_PATH = ROOT / "frontend" / "public" / "wards_hvi.geojson"

# direction: +1 means "higher raw value = more vulnerable", -1 = inverted (methodology.md §3)
INDICATORS = {
    "LST_C": 1,
    "NDVI": -1,
    "pop_density_km2": 1,
    "elderly_pct": 1,
    "slum_pct": 1,
    "hospital_dist_m": 1,
    "impervious_pct": 1,
}

# Explained-variance floor below which PC1 loadings are considered unstable
# for a single-city, single-snapshot sample (documented fallback trigger).
MIN_EXPLAINED_VARIANCE = 0.30

WARDS_PATH = DATA_DIR / "bmc_wards.geojson"


def zscore(series):
    mu, sigma = series.mean(), series.std(ddof=0)
    if sigma == 0 or np.isnan(sigma):
        return series * 0.0
    return (series - mu) / sigma


def rescale_0_100(series):
    lo, hi = series.min(), series.max()
    if hi == lo:
        return series * 0 + 50.0
    return (series - lo) / (hi - lo) * 100.0


def main() -> int:
    if not IN_PATH.exists():
        print(f"[FAIL] {IN_PATH} not found — run 04_zonal.py first.")
        return 1

    gdf = gpd.read_file(IN_PATH)
    print(f"[ok] loaded {len(gdf)} cells")

    cols = list(INDICATORS.keys())
    z = gdf[cols].apply(zscore)
    signed_z = z * np.array([INDICATORS[c] for c in cols])
    signed_z.columns = [f"z_{c}" for c in cols]

    pca = PCA(n_components=len(cols))
    pca.fit(signed_z.values)
    explained_var_1 = float(pca.explained_variance_ratio_[0])
    loadings_1 = pca.components_[0]

    print(f"[ok] PC1 explained variance = {explained_var_1:.3f}")
    print("[ok] PC1 loadings:", dict(zip(cols, loadings_1.round(3))))

    fallback_used = explained_var_1 < MIN_EXPLAINED_VARIANCE
    if fallback_used:
        print(f"[WARN] PC1 explains {explained_var_1:.1%} < {MIN_EXPLAINED_VARIANCE:.0%} floor — "
              "falling back to published equal-weighting (Reid et al. 2009 component-level default).")
        weights = np.ones(len(cols)) / len(cols)
        weight_source = "fallback_equal_reid2009"
    else:
        # Orient PC1 so higher score = more vulnerable: flip sign if PC1 anti-correlates with LST_C.
        pc1_scores = signed_z.values @ loadings_1
        if np.corrcoef(pc1_scores, signed_z["z_LST_C"])[0, 1] < 0:
            loadings_1 = -loadings_1
        weights = np.abs(loadings_1) / np.abs(loadings_1).sum()
        weight_source = "pca_reid2009"

    weights_by_col = dict(zip(cols, weights))
    print("[ok] final weights:", {k: round(v, 3) for k, v in weights_by_col.items()})

    contributions = signed_z.copy()
    contributions.columns = cols
    for c in cols:
        contributions[c] = signed_z[f"z_{c}"] * weights_by_col[c]

    hvi_raw = contributions.sum(axis=1)
    gdf["HVI"] = rescale_0_100(hvi_raw)
    for c in cols:
        gdf[f"contrib_{c}"] = contributions[c]

    OUT_CELLS_PATH.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(OUT_CELLS_PATH, driver="GeoJSON")
    print(f"[ok] wrote {len(gdf)} cells with HVI -> {OUT_CELLS_PATH}")

    # ------------------------------------------------- ward-level rollup --
    wards = gpd.read_file(WARDS_PATH)[["gid", "name", "geometry"]].rename(columns={"gid": "ward_gid", "name": "ward_id"})
    ward_hvi = gdf.groupby("ward_id").agg(
        HVI=("HVI", "mean"),
        n_cells=("HVI", "size"),
        **{f"contrib_{c}": (f"contrib_{c}", "mean") for c in cols},
    ).reset_index()
    ward_hvi["rank"] = ward_hvi["HVI"].rank(ascending=False, method="min").astype(int)
    ward_hvi = ward_hvi.sort_values("rank")

    wards_out = wards.merge(ward_hvi, on="ward_id", how="left")
    wards_out.to_file(OUT_WARDS_PATH, driver="GeoJSON")
    print(f"[ok] wrote {len(wards_out)} wards with ranked HVI -> {OUT_WARDS_PATH}")

    OUT_METHOD_PATH.write_text(json.dumps({
        "explained_variance_pc1": explained_var_1,
        "loadings_pc1": dict(zip(cols, loadings_1.tolist())),
        "weight_source": weight_source,
        "weights": weights_by_col,
        "fallback_used": fallback_used,
        "fallback_trigger": f"explained_variance_pc1 < {MIN_EXPLAINED_VARIANCE}",
    }, indent=2), encoding="utf-8")
    print(f"[ok] wrote PCA log -> {OUT_METHOD_PATH}")

    # ------------------------------------------------------- sanity checks --
    # Runs BEFORE the frontend/public copy below, on purpose: data/ is always written
    # (it's the pipeline's own working state, and the demo-safe-fallback snapshot logic
    # in 07_load.py already treats data/ as the thing to inspect on a bad run), but the
    # live site must not start serving a run that failed its own sanity check just
    # because the copy happened to run first.
    ok = True
    if not (0 <= gdf["HVI"].min() and gdf["HVI"].max() <= 100.0001):
        print(f"[WARN] HVI range {gdf['HVI'].min()}-{gdf['HVI'].max()} outside 0-100")
        ok = False
    if ward_hvi["ward_id"].nunique() != 24:
        print(f"[WARN] only {ward_hvi['ward_id'].nunique()}/24 wards have HVI")
        ok = False
    print("\nTop 5 most vulnerable wards:")
    print(ward_hvi[["rank", "ward_id", "HVI", "n_cells"]].head(5).to_string(index=False))

    if ok:
        publish(OUT_WARDS_PATH, OUT_WARDS_PUBLIC_PATH)
    else:
        print(f"[WARN] sanity check failed -- NOT copying to {OUT_WARDS_PUBLIC_PATH}; "
              "the live site keeps serving its previous wards_hvi.geojson")

    print("\nGO" if ok else "\nCHECK WARNINGS")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
