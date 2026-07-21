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

## 5. Sensitivity / validity
- Weights perturbed +/-20%; ward priority ranking shown stable (chart). Addresses weight-transfer validity for Mumbai.

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
