# UCIP — Methodology (outline)

> Mirrors the in-app `/methodology` page (F5). Filled during the sprint. Stating limitations openly is a credibility win with researcher judges; hiding them is the trap.

## 1. Problem & scope
- Decision-support, not another heat map: which Mumbai wards to cool first, why, what intervention, where the budget goes.
- Mumbai only. Grid compute (1 km), rolled up to 24 BMC wards. Architecture city-agnostic (stated, not built).

## 2. Prior art & how UCIP differs
- Prior-art scan done (pre-sprint item #8): 5 cited studies + "how UCIP differs" in `docs/prior-art.md`. Covers MCAP 2022, RAND/Azhar India HVI, IIT-B Mumbai SUHI, C40 Urban Cooling Toolbox, Ahmedabad HAP (+ IIHS governance, Rathi four-city HVI).
- UCIP's difference: transparent literature-weighted index + NBS engine + ecological plantability filter + budget layer, vs static vulnerability assessments.

## 3. Indicators
- LST (+), NDVI inverted (-), population density (+), elderly % (+), slum index (+), hospital distance (+), impervious % (+).
- Each z-standardized; direction set per the heat-vulnerability literature.

## 4. HVI computation
- Weights via PCA (Reid et al. 2009) on standardized indicators; weights from component loadings.
- Fallback: published HVI weights verbatim if loadings are unstable (trigger documented here if used).
- HVI = weighted sum, rescaled 0-100.
- Explainability = per-factor contribution (weight x z-score), shown as a ranked bar breakdown. Transparent linear index — **no SHAP** (nothing black-box to explain).

## 4b. Ward-level figures (what the ward dialog shows)
- HVI, rank and the seven contributions come straight from `wards_hvi.geojson` (stage 05); the dialog never recomputes them.
- The raw indicator figures are the **unweighted mean of the ward's member cells** (stage 10, `ward_profiles.json`). A ward with 2 cells and a ward with 61 cells are both simple means over their own cells, so small wards are noisier.
- "Hotter than X%" is the ward's HVI percentile among the 24, derived from rank, not a separate statistic.
- "Biggest driver" is the largest positive per-factor contribution, i.e. the same numbers as the bar breakdown, not a separate model.
- Adjacency for the neighbour comparison is polygon touching on the BMC boundaries (stage 12 uses the same source for the landing-page coastline).
- Caveats carried over from section 10: `elderly_pct` varies only about 1.6 points across the whole city, so it separates wards weakly and the copy does not lean on it; NDVI is reported as an index, never as a canopy percentage.

## 4c. How precise is a ward's score, really

`pipeline/uncertainty.py`, output `data/hvi_uncertainty.json`.

A ward gets a single HVI to one decimal place and a rank out of 24, which
implies a precision the method does not have. The weights come from a PCA over
541 cells, and that PCA has sampling uncertainty. So the cells are resampled
with replacement 1000 times and the whole chain is rerun on each resample
(z-scores, PCA, weights, per-cell index, 0-100 rescale, ward rollup, rank),
giving a 95% percentile interval per ward.

Rerunning the whole chain matters. Holding the z-scores and the rescale fixed
and varying only the weights would understate the uncertainty while looking
rigorous.

**The result is a real qualification of the ranking, not a formality:**

| | |
|---|---|
| Median rank interval | **6 places** |
| Widest | 14 places (ward B, ranked 6th, interval 1st to 15th) |
| Wards whose rank is certain | **0 of 24** |

Read the ranking as broad bands rather than an ordering. "C is the most
vulnerable ward" survives (interval 1st to 3rd) and "T and R/C are among the
least" survives, but the difference between 8th and 12th does not: those
intervals overlap almost entirely. A planner choosing between two
mid-table wards should treat them as tied and decide on other grounds.

This captures sampling uncertainty in the cells only. It does not capture
measurement error in the indicators, the choice of indicators, or the decision
to weight by PCA at all, which is quantified separately in §5.

## 5. Sensitivity / validity
- Weights perturbed +/-20%; ward priority ranking shown stable (chart). Addresses weight-transfer validity for Mumbai.
- **PCA weighting vs the published fallback** (`pipeline/compare_weightings.py`, output `data/weighting_comparison.json`). The obvious challenge to a data-derived weighting is "how much does it change the answer versus just using the published weights?", so both are run over the same cells and compared:

  | Measure | Result |
  |---|---|
  | Kendall tau | 0.913 |
  | Spearman rho | 0.977 |
  | Wards with an identical rank | 13 of 24 |
  | Largest single move | ward L, 3 places (3rd to 6th) |
  | Top-5 overlap | 4 of 5 |

  Read this correctly. A high correlation does not show the PCA weighting is right; it shows the ranking is largely insensitive to the choice, which is the more useful claim. The wards at the top are there because of the data rather than because of the weighting. The one disagreement that would matter to a spending decision is L, which the PCA weighting places 3rd and the published weighting 6th.

## 6. NBS recommendation engine
- Rule-based; each fired rule carries a rationale + citation.
- Ecological plantability filter: native trees only where restoration-suitable AND not native grassland/savanna (Bastin 2019 vs Veldman/Friedlingstein 2019); cool roofs / reflective pavements / cooling centres elsewhere.

## 7. Green-cover change (F6)
- NDVI at two dates -> per-cell delta -> gained/stable/lost, overlaid with HVI.

## 8. Simulator (F8, if built) — clearly labelled illustrative
- Published cooling coefficients adjust indicators -> recomputed HVI. "Illustrative first-order estimate, not a validated prediction."

## 9. Budget optimizer (F9, if built)
- Greedy/LP: maximize total HVI reduction subject to spend <= budget. Cost figures cited or assumptions listed.

## 10. Limitations (state these openly)
- Land-surface temperature != air temperature.
- Cooling coefficients transferred from other cities, not Mumbai-calibrated.
- Slum-density and elderly layers are proxies (WorldPop 2020 — most recent year available for
  India — and mapped slum-cluster boundaries, OSM), not ward-level census.
- Simulator is a first-order estimate, not a validated climate model.
- Ecological plantability layer is coarse-resolution.
