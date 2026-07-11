"""M3 — Heat Vulnerability Index (locked decision #3: PCA, published fallback).

Planned (sprint Aug 3):
- Standardize indicators to z-scores; set directions (LST +, NDVI -, density +,
  elderly +, slum +, hospital_dist +, impervious +).
- PCA (scikit-learn) per Reid et al. 2009; derive weights from component loadings.
  Log explained variance + loadings for the methodology page.
- FALLBACK (if loadings unstable/nonsensical): adopt published HVI weights
  verbatim with citation; document the trigger.
- HVI = weighted sum -> rescaled 0-100.
- Store per-factor contributions (weight x z-score) per cell — this IS the
  explainability layer (F2). No SHAP, by design.
"""

raise NotImplementedError("Sprint M3 (Aug 3) — see docstring.")
