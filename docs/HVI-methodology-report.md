# A Transparent, Literature-Weighted Heat Vulnerability Index for Mumbai's 24 Wards

**A standalone technical report for the Urban Cooling Intervention Platform (UCIP)**

*Status: internal technical writeup, polished for external publication (e.g. a personal
research page, SSRN, or arXiv's econ/physics-adjacent categories). Not yet submitted
anywhere; this document is the writeup itself, prepared per issue #66. All figures below
are read directly from this repository's committed pipeline output
(`data/hvi_pca_log.json`, `data/sensitivity.json`, `data/nbs_recommendations.json`,
`data/cells_ndvi_change.geojson`) and pipeline source (`pipeline/05_hvi.py`,
`pipeline/06_nbs.py`, `pipeline/08_sensitivity.py`, `pipeline/09_ndvi_change.py`,
`frontend/src/lib/coefficients.ts`) as of this writing, not re-derived or estimated.*

---

## Abstract

Urban heat is not distributed evenly across a city, and neither is the capacity to
adapt to it. This report documents the Heat Vulnerability Index (HVI) computed by the
Urban Cooling Intervention Platform (UCIP) for Mumbai's 24 Brihanmumbai Municipal
Corporation (BMC) wards: a seven-indicator, Principal Component Analysis (PCA)-weighted
index built on dry-season satellite land surface temperature and vegetation data,
WorldPop demographic layers, OpenStreetMap hospital access, and Datameet administrative
and slum-cluster boundaries. We describe the indicator set and its directionality, the
PCA weight-derivation procedure and its published fallback, a one-at-a-time
weight-perturbation sensitivity analysis, the rule-based Nature-Based Solutions (NBS)
recommendation engine, and its ecological plantability filter, which withholds
afforestation recommendations for cells that are ecologically unsuitable for tree
planting rather than recommending trees everywhere heat is high. Every indicator,
weight, and coefficient in this report traces to either a value the pipeline actually
computed from real geospatial data, or a specific cited publication; nothing here is an
invented or illustrative placeholder. We close with the limitations we consider most
important to state openly: land surface temperature is not air temperature, several
demographic layers are proxies rather than ward-level census figures, and the cooling
coefficients used elsewhere in the product are transferred from other cities rather
than Mumbai-calibrated.

## 1. Introduction and Motivation

Heat is increasingly recognized as an urban public-health hazard, and IPCC AR6's
Working Group II urban chapter frames adaptation planning as needing spatial
granularity: a city-wide average temperature says little about which specific
neighborhoods need intervention first, or what kind of intervention fits their
physical and ecological constraints. UCIP's premise is that a heat-vulnerability tool
is only useful to a city planner if it goes past "here is a heat map" to "here is which
of your 24 administrative units to act on first, why, and with what intervention,"
grounded in data the tool actually computed rather than expert judgment or arbitrary
weighting.

This report elevates the project's existing in-app methodology page (`/methodology`)
and its outline-form source (`docs/methodology.md`, `docs/references.md`) into a
self-contained technical document: one that can be read, cited, and checked without
the surrounding product.

## 2. Prior Art

UCIP's design was informed by a comparison against existing heat-vulnerability and
urban-cooling work, including the Mumbai Climate Action Plan (MCAP 2022), the RAND/Azhar
et al. India district-level HVI (Azhar et al. 2017), IIT-Bombay's work on Mumbai's
surface urban heat island, the C40 Urban Cooling Toolbox, and the Ahmedabad Heat Action
Plan (documented via Knowlton et al. 2014). Relative to that prior art, UCIP's stated
point of difference is combining (a) a transparent, literature-weighted index rather
than a static or expert-weighted vulnerability score, (b) a rule-based NBS
recommendation engine tied to that index, and (c) an ecological plantability filter
that can reject afforestation on ecological grounds, described in Section 7.

## 3. Study Area and Data

The study area is Mumbai, analyzed at 1 km grid-cell resolution and rolled up to the
city's 24 BMC administrative wards. The pipeline (`pipeline/01_grid.py`) builds this
grid by clipping a fishnet to ward boundaries in a metric CRS (EPSG:32643, UTM zone
43N) and assigning each cell to the ward containing its largest fragment. As of the
data underlying this report, that raw fishnet produces 547 cells across all 24 wards
(`data/grid_1km.geojson`). A later consolidation step, `pipeline/04_zonal.py`, drops
any cell missing one or more of the seven indicators in Section 4 before the indicators
can be z-standardized; as of this run that drops 6 of the 547 cells (about 1%, well
under the pipeline's own 15% sanity-check ceiling for data loss), leaving the 541-cell
table (`data/cells.geojson`) that every subsequent stage, and every other cell count in
this report, is computed from.

| Layer | Source | Access | Note |
|---|---|---|---|
| Land surface temperature (LST) | Landsat 8/9 Collection 2 Level-2, `ST_B10` | Google Earth Engine | Dry-season median composite, cloud/shadow-masked via `QA_PIXEL` |
| NDVI (current + baseline) | Landsat 8/9 Collection 2 Level-2, `SR_B4`/`SR_B5` | Google Earth Engine | Two dry-season composites roughly nine years apart, for the green-cover-change layer (Section 8) |
| Population density, elderly share | WorldPop age-sex structure, pinned to the `IND_2020` image | Google Earth Engine | **Proxy.** 2020 is the most recent year WorldPop publishes for India in this collection; the pin is explicit in `pipeline/03_vectors.py` rather than left to whichever vintage the API returns first |
| Slum index | Datameet `slumClusters.geojson` (mapped cluster boundaries) | Repository data | **Proxy**, but based on observed cluster polygons rather than a modeled index |
| Hospital access | OpenStreetMap `amenity=hospital` | `osmnx` / Overpass | Per-cell straight-line distance to the nearest hospital centroid |
| Impervious / built-up surface, land-cover class | ESA WorldCover v200 | Google Earth Engine | Also the input to the plantability filter (Section 7) |
| Ward boundaries | Datameet BMC ward boundaries | Repository data | 24 features, validated against Mumbai's known extent |

## 4. Indicators and Directionality

Seven indicators feed the index, each assigned a direction reflecting whether a higher
raw value indicates *more* vulnerability (`+1`) or *less* (`-1`, i.e. inverted before
scoring):

| Indicator | Direction | Unit | Observed range (541 cells) |
|---|---|---|---|
| `LST_C` (land surface temperature) | + | °C (land surface, not air) | 26.24 to 39.95 |
| `NDVI` (vegetation index) | − | unitless index, not a canopy percentage | −0.07 to 0.71 |
| `pop_density_km2` (population density) | + | people / km² | 16 to 115,272 |
| `elderly_pct` (elderly share, 60+) | + | % (0-100), WorldPop 2020 proxy | 4.02 to 5.59 |
| `slum_pct` (slum-cluster coverage) | + | % (0-100), mapped-boundary proxy | 0.00 to 68.55 |
| `hospital_dist_m` (distance to nearest hospital) | + | metres | 3.86 to 6199.03 |
| `impervious_pct` (impervious surface share) | + | % (0-100) | 0.00 to 96.79 |

`elderly_pct` spans only 1.6 percentage points across the entire city in this dataset,
so on its own it separates wards weakly; the PCA weighting in Section 5 reflects this
by assigning it the lowest weight of the seven indicators; the product's own UI copy
does not lean on it as a standalone talking point.

## 5. HVI Computation

**Standardization.** Each indicator is z-standardized across all cells
(`pipeline/05_hvi.py`): for indicator column $x$, $z = (x - \bar{x}) / \sigma_x$
(population standard deviation, i.e. `ddof=0`), and then multiplied by its direction
sign so that, after this step, a higher signed z-score always means "more
vulnerable" for every indicator.

**Weight derivation (PCA, Reid et al. 2009).** A Principal Component Analysis is fit
on the seven signed z-score columns. The first principal component's explained
variance ratio is checked against a floor of 0.30; if it is at or above that floor, the
component's loadings are used to derive weights. The component is first sign-oriented
so that a higher PC1 score means more vulnerable (checked by correlating PC1 scores
against the signed `LST_C` z-score and flipping the sign if that correlation is
negative), and the final weight for indicator $i$ is the absolute loading normalized
across all seven indicators:

$$w_i = \frac{|\ell_i|}{\sum_{j=1}^{7} |\ell_j|}$$

where $\ell_i$ is indicator $i$'s (sign-oriented) PC1 loading. **Fallback.** If PC1's
explained variance ratio is below the 0.30 floor, the pipeline treats the loadings as
unstable for this single-city, single-snapshot sample and falls back to equal
weighting across all seven indicators (the published component-level default per Reid
et al. 2009), logging that the fallback fired and why.

**Current run's values.** As of the pipeline output committed to this repository, PC1
explained 58.0% of variance, comfortably above the 0.30 floor, so the PCA-derived
weights below were used (fallback not triggered):

| Indicator | PC1 loading | Weight |
|---|---:|---:|
| `LST_C` | 0.432 | 0.168 |
| `NDVI` | 0.384 | 0.149 |
| `pop_density_km2` | 0.432 | 0.168 |
| `elderly_pct` | 0.197 | 0.077 |
| `slum_pct` | 0.276 | 0.107 |
| `hospital_dist_m` | −0.383 | 0.149 |
| `impervious_pct` | 0.466 | 0.181 |

These weights are **recomputed from the current run's data on every pipeline refresh**,
not fixed constants; a materially different snapshot of Mumbai's cells could shift
PC1's loadings and therefore these weights. What is fixed, and cited, is the *procedure*
(PCA on signed z-scores, with the stated fallback), not any particular numeric weight.

**HVI score.** Per cell, `HVI_raw` is the weighted sum of signed z-scores
($\sum_i w_i z_i$), and the final `HVI` is `HVI_raw` linearly rescaled to 0-100 across
all cells in the run (min mapped to 0, max to 100). Ward-level HVI is the unweighted
mean of its member cells' scores, and ward rank is `HVI` sorted descending (rank 1 =
most vulnerable). As of this run, the five highest-ranked wards are C, G/N, L, E, and
F/S (HVI 73.6, 69.7, 65.8, 65.0, and 64.8 respectively). Reading each ward's largest
per-factor contribution directly from `data/wards_hvi.geojson`: C, G/N, and E are each
driven primarily by `impervious_pct` (contributions 0.292, 0.217, and 0.233
respectively); L primarily by `LST_C` (0.209); and F/S primarily by `elderly_pct`
(0.170), narrowly ahead of `impervious_pct` (0.140) for that one ward.

**Explainability.** Per-cell, per-indicator contributions (`weight × signed z-score`)
are stored alongside the score and shown as a ranked bar breakdown in the product.
Because the index is a transparent weighted linear sum, this contribution decomposition
*is* the full explanation of any given score; the project deliberately does not use a
post-hoc explainability method (e.g. SHAP) because there is no black-box model to
explain.

## 6. Sensitivity Analysis

A weight-transfer validity question, namely whether these literature-derived weights
actually produce a stable, trustworthy ranking for Mumbai specifically, or whether
small disagreements about the "right" weights would change which wards get
prioritized, is addressed with a one-at-a-time perturbation study (`pipeline/08_sensitivity.py`): each
of the seven weights is perturbed ±20% in turn, the remaining six renormalized to keep
all weights summing to 1, and the ward ranking recomputed. Fourteen perturbation runs
result (7 indicators × 2 directions), each compared to the unperturbed baseline ranking
by Kendall's tau (rank-correlation over all 24 wards) and by top-5 overlap (how many of
the baseline top-5 most-vulnerable wards remain in the perturbed top-5).

**Results.** Mean Kendall tau across all 14 runs was 0.978 (1.0 = identical ranking),
and mean top-5 overlap was 4.43 of 5. Overlap was 5 of 5 (the entire top-5 set matched
baseline exactly) in 6 of the 14 runs, and 4 of 5 in the other 8; it never fell below 4
in any run. Reading `data/sensitivity.json`'s per-run rankings directly rather than
summarizing from memory: only the top TWO wards by HVI, C and G/N, were unchanged in
every one of the 14 perturbations. Ward L (baseline rank 3) dropped out of the top 5 in
2 of the 14 runs (`elderly_pct` +20%, `slum_pct` -20%), ward E (baseline rank 4)
dropped out in 2 runs (`hospital_dist_m` +20%, `impervious_pct` -20%), and ward F/S
(baseline rank 5) dropped out in 4 runs (`LST_C` -20%, `NDVI` +20%,
`pop_density_km2` -20%, `impervious_pct` +20%). In every one of these 8 runs, the ward
dropped from the top 5 was replaced by exactly one ward, B, and never by any other
ward. No perturbation altered which ward ranked most vulnerable overall: ward C is
rank 1 in the baseline and in all 14 perturbed rankings. We read this as the top of the
ranking (ranks 1-2) being fully robust to plausible weight disagreement, with
increasing but still bounded sensitivity moving down through ranks 3-5, where ward B is
the one consistent alternative that displaces the baseline's 3rd-5th-ranked wards under
perturbation. This is a more qualified result than "top 5 is stable," and we consider
reporting it exactly as computed more honest than rounding up.

## 7. Nature-Based Solutions Engine and the Ecological Plantability Filter

Given a cell's HVI and its underlying indicators, `pipeline/06_nbs.py` fires one or
more rule-based recommendations, each carrying a plain-language rationale and a
citation. "High" and "low" thresholds are the 75th/25th percentile of that indicator
**within the current run's cells**, not fixed absolute cutoffs. Several indicators
(notably `elderly_pct`) have too narrow an observed range across Mumbai for an absolute
threshold to be meaningful.

| Condition | Recommendation | Citation |
|---|---|---|
| HVI ≥ p75, NDVI ≤ p25, cell is plantable | Native tree planting + green corridors | Bastin et al. 2019 |
| HVI ≥ p75, NDVI ≤ p25, cell is **not** plantable | Cool roofs + reflective pavements + cooling centres | Veldman et al. 2019 |
| impervious_pct ≥ p75 and within 500 m of mapped water/wetland | Rain gardens + water-sensitive urban design (WSUD) | Methodology proxy (no dedicated hydrology layer) |
| pop_density_km2 ≥ p75 and NDVI ≤ p25 | Pocket parks | C40 Urban Cooling Toolbox |
| elderly_pct ≥ p75 and hospital_dist_m ≥ p75 | Cooling centres, priority siting | Knowlton et al. 2014 |

**The ecological plantability filter** is the headline design decision of this engine:
a cell is only eligible for the tree-planting recommendation if it is *not* water,
wetland, mangrove, or built-up (ESA WorldCover classes 50/80/90/95), *not* native
grassland (WorldCover class 30, per Veldman et al. 2019's caution against afforesting
grassland/savanna ecosystems), and has impervious cover below the 75th percentile
(physical room to plant). A cell that clears the vulnerability bar but fails this
ecological check is routed to the non-tree recommendation (cool roofs / reflective
pavements / cooling centres) instead. The product is deliberately built to be able to
say "this ward needs cooling, but not via tree planting" rather than defaulting to
trees everywhere.

**As of this run:** 337 of 541 cells (62%) were classified plantable. Across all 24
wards, 81 ward-level recommendation rows fired: 24 rain-garden/WSUD, 18 cool-roof, 18
pocket-park, 12 native-tree-planting, and 9 cooling-centre-priority recommendations.
Every ward received at least one recommendation.

## 8. Green Cover Change Classification

`pipeline/09_ndvi_change.py` classifies each cell's NDVI delta between the current
dry-season composite and an older dry-season baseline (`NDVI - NDVI_prev`, roughly a
nine-year gap) as `gained` (delta > +0.05), `lost` (delta < −0.05), or `stable`
(otherwise). The ±0.05 threshold is a deliberate, documented choice, chosen in the
same spirit as the ±20% perturbation tolerance in Section 6, as "the size of change
trusted as real signal rather than noise" for this dataset, not a value taken from a
specific external paper. As of this run, the classification split 445 cells stable, 84
gained, and 12 lost, across the 541-cell grid.

## 9. Illustrative Cooling Coefficients (Simulator)

A separate, clearly-labelled part of the product (`/simulate`,
`frontend/src/lib/coefficients.ts`) lets a user estimate the illustrative cooling effect
of a hypothetical intervention, using coefficients transferred from the cited
literature rather than fit to Mumbai: canopy cooling follows Ziter et al. 2019
(negligible effect below ~40% canopy cover, up to ~1.0°C of daytime cooling by 80%
cover, non-linear and capped rather than extrapolated past the paper's own range);
cool-roof/high-albedo cooling uses a conservative 0.6°C per +0.1 albedo headline figure
with a 0.57-2.3°C per +0.1 range exposed as uncertainty (Santamouris 2014), with Li,
Bou-Zeid & Oppenheimer (2014) cited as structural support for treating the relationship
as linear; pocket-park cooling scales a 0.94°C park-cool-island ceiling (Bowler et al.
2010) linearly by the share of ward area converted to park-like green space, an
explicit simplifying assumption stated as such rather than presented as a result from
the source paper. These three terms are summed independently, with no attempt to model
interaction effects (e.g. double-counting trees that are also inside a park). This
simulator is not part of the HVI computation itself; it is included in this report
because it draws on the same citation discipline and the same cited coefficients
appear in `docs/references.md`.

## 10. Limitations

Stated here in full, matching `docs/methodology.md` section 10:

- **Land surface temperature is not air temperature.** `LST_C` is a satellite-derived
  surface measurement; it correlates with but is not equivalent to the air temperature
  a person actually experiences. The product's live-weather widget
  (`frontend/src/lib/weather.ts`) exists specifically to make this distinction
  tangible with a real, concurrently-fetched air-temperature reading.
- **Cooling coefficients are transferred, not Mumbai-calibrated.** The Section 9
  coefficients come from other cities' studies (Ziter et al. in eastern North America,
  Santamouris's city-scale review, Li/Bou-Zeid/Oppenheimer's Baltimore-DC simulation,
  Bowler et al.'s meta-analysis); no Mumbai-specific field validation of these
  magnitudes has been performed.
- **Slum-density and elderly layers are proxies.** `slum_pct` comes from mapped
  slum-cluster boundaries (Datameet) rather than a household survey, and `elderly_pct`
  comes from WorldPop's 2020 age-sex structure (the most recent year available for
  India in that collection) rather than ward-level census data.
- **The simulator (Section 9) is a first-order estimate**, explicitly not a validated
  microclimate model, and is labelled as such in its own UI.
- **The ecological plantability layer is coarse-resolution**, driven by ESA WorldCover
  at its native ~10 m pixel size aggregated to 1 km cells, and by a single flood-risk
  proxy (distance to mapped water/wetland) rather than a dedicated hydrology layer.
- **PCA weights are a function of the current snapshot**, as noted in Section 5; they
  are expected to be broadly stable given the Section 6 sensitivity results, but are
  not literally fixed across every possible re-run of the pipeline.

## 11. Reproducibility

Every figure in this report was read from files this repository's own pipeline
produced: `data/hvi_pca_log.json` (Section 5), `data/sensitivity.json` (Section 6),
`data/nbs_recommendations.json` and `data/cells_hvi.geojson` (Section 7),
`data/cells_ndvi_change.geojson` (Section 8). The full pipeline can be re-run end to
end with `python pipeline/run_pipeline.py` (see `pipeline/README.md`), which will
regenerate all of the above from the same source data and procedure described here.

## 12. References

| Use | Citation | DOI |
|---|---|---|
| HVI weighting method | Reid et al. 2009, *Environ. Health Perspect.* 117(11):1730-1736 | 10.1289/ehp.0900683 |
| Local credibility, first South Asian HAP | Knowlton et al. 2014, *IJERPH* 11(4):3473-3492 | 10.3390/ijerph110403473 |
| India-wide district HVI precedent | Azhar et al. 2017 (RAND India HVI), *IJERPH* 14(4):357 | 10.3390/ijerph14040357 |
| Tree restoration potential | Bastin et al. 2019, *Science* 365(6448):76-79 | 10.1126/science.aax0848 |
| Plantability filter (critique of afforestation-everywhere) | Veldman et al. 2019, *Science* 366(6463):eaay7976 | 10.1126/science.aay7976 |
| Carbon-cycle critique companion | Friedlingstein et al. 2019, *Science* 366(6463):eaay8060 | 10.1126/science.aay8060 |
| Regrowth critique companion | Lewis et al. 2019, *Science* 366(6463):eaaz0388 | 10.1126/science.aaz0388 |
| Canopy → LST reduction coefficient | Ziter et al. 2019, *PNAS* 116(15):7575-7580 | 10.1073/pnas.1817561116 |
| Cool-roof city-scale simulation | Li, Bou-Zeid & Oppenheimer 2014, *Environ. Res. Lett.* 9(5):055002 | 10.1088/1748-9326/9/5/055002 |
| Albedo → peak-temperature coefficient | Santamouris 2014, *Solar Energy* 103:682-703 | 10.1016/j.solener.2012.07.003 |
| Pocket-park cooling coefficient | Bowler et al. 2010, *Landscape and Urban Planning* 97:147-155 | 10.1016/j.landurbplan.2010.05.006 |

DOIs above were verified against the publisher resolvers as documented in
`docs/references.md`; this report does not re-verify them independently. For the
complete citation table, including data-source access details not repeated here, see
`docs/references.md`.

---

*This report mirrors and extends `docs/methodology.md`; where the two differ in level
of detail, this document is the more complete one and `docs/methodology.md` should be
treated as the shorter in-app summary of it. Prepared for issue #66. Not submitted to
arXiv, SSRN, or any external venue; that step, if pursued, is a decision for the
project maintainer and is outside what this PR does.*
