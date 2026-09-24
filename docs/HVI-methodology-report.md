# A Transparent, Literature-Weighted Heat Vulnerability Index for Mumbai's 24 Wards

Anay Dhawan, independent researcher

Technical report for the Urban Climate Intelligence Platform (UCIP)

*Draft status, removed before submission: written for issues #66 and #90 and not yet submitted. What remains to be decided is listed in `docs/preprint/SUBMISSION.md`. Every figure below was read from this repository's committed pipeline output (`data/hvi_pca_log.json`, `data/sensitivity.json`, `data/hvi_uncertainty.json`, `data/weighting_comparison.json`, `data/lst_validation.json`, `data/elderly_evaluation.json`, `data/nbs_recommendations.json`, `data/cells_ndvi_change.geojson`) and not re-derived. The dataset is archived at doi:10.5281/zenodo.22923919.*

---

## Abstract

Heat risk is uneven within a city, and so is the ability to cope with it. This report describes the Heat Vulnerability Index (HVI) that UCIP computes for the 24 Brihanmumbai Municipal Corporation (BMC) wards of Mumbai. The index combines eight indicators on a 1 km grid: dry-season land surface temperature, vegetation, population density, the share of elderly people, the share of young children, informal-settlement coverage, distance to a hospital, and impervious surface. Weights come from the first principal component of the standardised indicators. A rule-based engine turns each cell's scores into a cooling recommendation, and an ecological filter withholds tree planting where the land cover makes it inappropriate.

Most of the report is about how far the ranking can be trusted. We test it four ways: perturbing the weights, bootstrapping the cells, comparing principal-component weights with equal weights, and rebuilding the whole dataset on a 500 m grid. The median ward's 95% rank interval spans 6 of 24 places, and no ward's rank is certain. The 500 m rebuild reorders nine wards, yet every ward's 500 m rank sits inside its own bootstrap interval from the 1 km data. Equal weighting is less forgiving than we expected. It agrees with the principal-component ranking at Kendall's tau 0.84 and moves ward C from first place to fifth, although the set of five most vulnerable wards is the same under both.

We also report two problems with our own inputs. The elderly share, taken from WorldPop, has two values across the whole city and follows the revenue district boundary exactly, so it carries district-level information under a ward-level label. And with the ecological filter working as intended, the tree-planting recommendation fires for no cell in Mumbai, because every cell that is both hot and bare is built-up land.

## 1. Introduction

Heat is a public-health hazard in cities, and adaptation planning needs to know where to act. Knowing that a city is warm does not say that. A single citywide temperature says nothing about which neighbourhoods to look at first or what kind of intervention suits them. UCIP tries to answer at the level a municipal planner works: which of the 24 wards to act on first, why, and with what.

The index and the recommendation engine are built so that they can be checked. Weights are derived from the data by a published method instead of being set by judgment, every score breaks down into per-indicator contributions, and the sections below say where the results are weak. The in-app methodology page (`/methodology`) and `docs/methodology.md` describe the same work in outline. This report is the version that can be read and cited without the product.

## 2. Prior art

UCIP was designed after comparing existing heat-vulnerability and urban-cooling work: the Mumbai Climate Action Plan (MCAP 2022), the district-level India HVI of Azhar et al. (2017), IIT Bombay's work on Mumbai's surface urban heat island, the C40 Urban Cooling Toolbox, and the Ahmedabad Heat Action Plan (Knowlton et al. 2014). It differs from that work in three ways. The index weights come from the data. A rule-based engine attaches a recommendation to each score. And an ecological filter can reject afforestation on ecological grounds (section 7).

## 3. Study area and data

Mumbai is analysed on a 1 km grid and rolled up to the 24 BMC wards. `pipeline/01_grid.py` clips a fishnet to the ward boundaries in a metric projection (EPSG:32643, UTM zone 43N) and assigns each cell to the ward that holds its largest fragment, which gives 547 cells. Stage 04 (`pipeline/04_zonal.py`) then drops any cell that is missing an indicator, since it cannot be standardised. That removes 6 of the 547, about 1%, against a pipeline ceiling of 15%. The remaining 541 cells (`data/cells.geojson`) are the basis for every later stage and every cell count in this report.

| Layer | Source | Access | Note |
|---|---|---|---|
| Land surface temperature (LST) | Landsat 8/9 Collection 2 Level-2, `ST_B10` | Google Earth Engine | Dry-season median composite, cloud and shadow masked with `QA_PIXEL` |
| NDVI (current and baseline) | Landsat 8/9 Collection 2 Level-2, `SR_B4` and `SR_B5` | Google Earth Engine | Two dry-season composites about nine years apart, for the green-cover-change layer (section 8) |
| Population density, elderly share | WorldPop age-sex structure, pinned to the `IND_2020` image | Google Earth Engine | Proxy. 2020 is the latest year WorldPop publishes for India in this collection, and the pin is explicit in `pipeline/03_vectors.py` so a newer vintage cannot be picked up silently. See section 10 for what the elderly layer contains |
| Young-child share | Census of India 2011, Primary Census Abstract at Census-ward level, as republished by OpenCity | Repository data (`data/census2011_ward_age_mumbai.csv`) | Ward level, so every cell in a ward carries its ward's value. Ninety-seven Census wards roll up into the 24 BMC wards. The build checks that the population sums to the Census figure for Greater Mumbai, 12,442,373 |
| Slum index | Datameet `slumClusters.geojson`, mapped cluster boundaries | Repository data | Proxy, though it rests on observed cluster polygons and not on a modelled index |
| Hospital access | OpenStreetMap `amenity=hospital` | `osmnx` and Overpass | Straight-line distance from each cell to the nearest hospital centroid |
| Impervious surface, land-cover class | ESA WorldCover v200 | Google Earth Engine | Also the input to the plantability filter (section 7) |
| Ward boundaries | Datameet BMC ward boundaries | Repository data | 24 features, checked against Mumbai's known extent |

## 4. Indicators and direction

Eight indicators feed the index. Each has a direction: +1 when a higher raw value means more vulnerability, and -1 when it means less, in which case the value is inverted before scoring. NDVI is the only -1.

| Indicator | Direction | Unit | Observed range (541 cells) |
|---|---|---|---|
| `LST_C` (land surface temperature) | + | degrees C, land surface and not air | 26.24 to 39.95 |
| `NDVI` (vegetation index) | - | unitless index, not a canopy percentage | -0.07 to 0.71 |
| `pop_density_km2` (population density) | + | people per km2 | 16 to 115,272 |
| `elderly_pct` (share aged 60 and over) | + | % (0-100), WorldPop 2020 | 4.02 to 5.59 |
| `child_pct` (share aged 0 to 6) | + | % (0-100), Census 2011, by ward | 6.75 to 13.09 |
| `slum_pct` (slum-cluster coverage) | + | % (0-100), mapped boundaries | 0.00 to 68.55 |
| `hospital_dist_m` (distance to nearest hospital) | + | metres | 3.86 to 6199.03 |
| `impervious_pct` (impervious surface share) | + | % (0-100) | 0.00 to 96.79 |

The two age indicators behave very differently. `elderly_pct` spans 1.6 percentage points across the whole city, and section 10 shows why: it is a district-level value spread over a raster. `child_pct` is real ward-level Census data with 24 distinct values from 6.75% to 13.09%.

It measures children under seven and not the elderly, and those are different populations. It is in the index because the ward-level Census tables we could find have no 60+ column, and 0 to 6 is the only age-structure signal in them. Including it is a modelling choice and not a settled one, and as section 5 shows, the weighting method gives it very little influence.

## 5. Computing the HVI

**Standardisation.** Each indicator is z-standardised across all cells (`pipeline/05_hvi.py`). For an indicator column $x$, $z = (x - \bar{x}) / \sigma_x$, using the population standard deviation (`ddof=0`). The result is then multiplied by the indicator's direction sign, so a higher signed z-score always means more vulnerable.

**Weights (PCA, Reid et al. 2009).** A principal component analysis is fitted to the signed z-score columns. The explained-variance ratio of the first component is compared with a floor of 0.30. If it is at or above the floor, the component's loadings give the weights. The component is first oriented so that a higher score means more vulnerable, by correlating its scores with the signed `LST_C` z-score and flipping the sign if the correlation is negative. The weight for indicator $i$ is its absolute loading divided by the sum of absolute loadings:

$$w_i = \frac{|\ell_i|}{\sum_{j=1}^{p} |\ell_j|}$$

where $\ell_i$ is the oriented PC1 loading and $p$ is the number of indicators. If PC1 falls below the 0.30 floor, the pipeline treats the loadings as unstable for a single-city, single-snapshot sample and falls back to equal weights across all indicators, which is the published component-level default in Reid et al. (2009). It logs that the fallback fired and why.

**Values in the committed run.** PC1 explains 50.9% of the variance, above the floor, so the fallback did not fire.

| Indicator | PC1 loading | Weight |
|---|---:|---:|
| `LST_C` | 0.434 | 0.166 |
| `NDVI` | 0.383 | 0.146 |
| `pop_density_km2` | 0.432 | 0.165 |
| `elderly_pct` | 0.193 | 0.074 |
| `child_pct` | 0.050 | 0.019 |
| `slum_pct` | 0.279 | 0.107 |
| `hospital_dist_m` | -0.381 | 0.146 |
| `impervious_pct` | 0.464 | 0.177 |

The index was first built with seven indicators, and PC1 then explained 58.0%. Adding `child_pct` lowered that to 50.9%. Child share is nearly uncorrelated with the other indicators (its correlation with each is at most 0.22 in absolute value), so it adds variance that PC1 does not capture, and PCA gives it the smallest weight of the eight. The effect on the ranking is small. Ten wards move by one place each, and ward B enters the top five in place of F/S.

The weights are recomputed from the current data on every pipeline run. What is fixed, and cited, is the procedure: PCA on signed z-scores, with the stated fallback. A materially different snapshot of Mumbai could shift the loadings.

**Score.** For each cell, `HVI_raw` is the weighted sum of signed z-scores, $\sum_i w_i z_i$, and `HVI` is `HVI_raw` rescaled linearly to 0-100 across all cells in the run. A ward's HVI is the unweighted mean of its cells' scores, and its rank is `HVI` sorted in descending order, so rank 1 is the most vulnerable. In the committed run the five highest-ranked wards are C, G/N, L, E and B, with HVI of 72.1, 69.5, 66.7, 64.8 and 64.6. The largest single contribution comes from `impervious_pct` for C, G/N and E (0.286, 0.213 and 0.228), from `LST_C` for L (0.206), and from `NDVI` for B (0.207).

**Explanation.** Each cell's contribution from each indicator (weight times signed z-score) is stored with its score and shown as a ranked bar chart in the product. The index is a weighted linear sum, so this breakdown is the complete explanation of any score. There is no black-box model, and so no need for a post-hoc method such as SHAP.

## 6. Sensitivity to the weights

This section asks whether small disagreements about the right weights would change which wards get priority. `pipeline/08_sensitivity.py` perturbs each of the eight weights by +20% and by -20% in turn, renormalises the other seven so the weights still sum to 1, and recomputes the ranking. That gives 16 runs. Each is compared with the unperturbed ranking by Kendall's tau over all 24 wards and by top-5 overlap.

Mean tau across the 16 runs is 0.985, and mean top-5 overlap is 4.88 of 5. In 14 of the 16 runs the top five is exactly the baseline set (C, G/N, L, E, B). In the other two, lowering the NDVI weight by 20% and raising the population-density weight by 20%, ward B drops out and F/S takes its place. Wards C, G/N, L and E are in the top five in every run, and ward C is first in all 16. In four runs B and E swap places.

One indicator barely registers. Perturbing `child_pct` by 20% in either direction leaves every rank unchanged (tau 1.000), which follows from its 1.9% weight.

The run output records only the top five for each perturbation, so this section says nothing about how ranks below fifth move. Section 6a covers the whole table.

## 6a. How precise is a ward's rank? A bootstrap

The perturbation study varies the weights and holds the sample fixed. It answers whether a different analyst's weights would change the result, and it does not answer whether a different sample would. The second question matters just as much, since the PCA weights are themselves estimated from 541 cells and carry sampling error.

`pipeline/uncertainty.py` resamples the cells with replacement 1000 times (seed 20260923) and reruns the whole chain on each replicate: z-scores, PCA, weights, per-cell index, 0-100 rescale, ward roll-up and rank. Holding the z-scores and the rescale fixed and varying only the weights would understate the uncertainty while looking rigorous, so everything is recomputed. The intervals below are 95% percentile intervals.

The median ward's rank interval spans 6 of 24 places. The widest belongs to ward B, ranked 5th, whose interval runs from 1st to 16th, 15 places. No ward's rank is certain: no interval collapses to a single place.

Some statements about the ranking survive this and some do not. Ward C's interval is 1st to 3rd, so C being among the most vulnerable holds. T and R/C, ranked 24th and 23rd, have intervals of 22nd to 24th and 21st to 24th, so being among the least vulnerable holds too. The 8th-ranked ward (G/S, 6th to 12th) and the 12th (M/W, 7th to 14th) overlap almost completely, and a planner choosing between two mid-table wards should treat them as tied and decide on other grounds.

We report this because publishing a rank as a bare integer invites readers to assume a precision the method does not have.

## 6b. Does the choice of weights change the answer?

Section 5 derives weights from PC1 and documents a fallback to equal weights. `pipeline/compare_weightings.py` computes both rankings on the same data and compares them.

Kendall's tau between the two is 0.841 and Spearman's rho is 0.959. Four of the 24 wards get the same rank under both schemes. The largest shift is 4 places: ward C is first under PCA weights and fifth under equal weights, and ward M/E goes from 16th to 12th. The top-5 set is identical (PCA order C, G/N, L, E, B; equal-weight order G/N, L, B, E, C), but the order inside it is not.

This is weaker agreement than the same comparison gave before `child_pct` was added, when tau was 0.913. Two things account for the drop. Holding the equal-weight scheme at seven indicators, adding `child_pct` to the PCA side alone takes tau from 0.913 to 0.891. Then giving `child_pct` an eighth of the total under equal weights (12.5%, against 1.9% under PCA) takes it the rest of the way, to 0.841.

A high correlation would not have shown that PCA weighting is correct, and nothing here could. What the comparison shows is narrower. Which wards are near the top depends little on the weighting, but their order depends on it. The choice of weights matters more than the perturbation study in section 6 suggests, because that study only moves the PCA weights a little way and never tries a different scheme.

## 6c. Does the grid resolution change the answer?

The checks above resample or reweight a fixed 1 km grid. Rebuilding the dataset at 500 m is an independent test, because it changes the unit of analysis. It produces 1975 published cells instead of 541, about 82 per ward instead of 23, with every stage from the fishnet through the Earth Engine reductions rerun. PC1 explains 49.6% of the variance at this resolution.

Nine of the 24 wards change rank. Ward B moves from 5th to 1st and G/N from 2nd to 5th. The top-five set is the same as at 1 km (B, C, L, E, G/N at 500 m), in a different order.

On its own that looks like instability. Set against section 6a it is close to the opposite. Every ward's 500 m rank falls inside that ward's own 95% bootstrap interval from the 1 km data, 24 out of 24. Ward B's interval was the widest in the table, 1st to 16th, and 1st is inside it. Resampling cells at one resolution and rebuilding the grid at another share no machinery, and they disagree about the order while agreeing about which parts of the order carry information. That is the strongest support this report has for section 6a's conclusion: a rank near the top or bottom is a finding, and a rank in the middle depends on where the grid lines fell.

1 km remains the published resolution. The 500 m dataset can be reproduced with `python pipeline/run_pipeline.py --cell-size 500` and is not published. It is a different dataset and not a better one, and switching would reshuffle the top of the table without making it more correct.

## 6d. Validation against station observations

`pipeline/13_validate_lst.py` compares the satellite composite with NOAA GSOD station air temperature. Per-overpass Landsat 8/9 `ST_B10` LST, cloud masked, is averaged within 500 m of each station and matched to the station's mean for that day.

The pooled within-station Pearson r is 0.716 over 23 matched station-days, computed on anomalies about each station's own mean. The LST-minus-air offset ranges from 3.43 to 13.94 degrees C across stations.

Both numbers need careful reading. Land surface temperature is the radiometric temperature of the ground, and station temperature is shaded air at about 1.5 m, so a large positive offset is expected and is no error. The number that speaks to measurement quality is the correlation, which asks whether the composite follows real day-to-day thermal variation and not sensor noise or cloud artefacts. At 0.716 it does, with the caution that 23 station-days is a small sample.

The spread of the offset is a result too. It depends on what the ground is made of, so no single additive correction turns this LST layer into air temperature. That is why the index treats LST as a relative indicator and the product never shows it as a temperature a person would feel.

## 7. Recommendations and the ecological plantability filter

Given a cell's HVI and its indicators, `pipeline/06_nbs.py` fires one or more rule-based recommendations, each with a plain-language rationale and a citation. "High" and "low" mean the 75th and 25th percentile of that indicator across the current run's cells, and are not fixed cutoffs. A fixed threshold would mean little for indicators with a narrow range across Mumbai.

| Condition | Recommendation | Citation |
|---|---|---|
| HVI at or above p75, NDVI at or below p25, cell plantable | Native tree planting and green corridors | Bastin et al. 2019 |
| HVI at or above p75, NDVI at or below p25, cell not plantable | Cool roofs, reflective pavements and cooling centres | Veldman et al. 2019 |
| `impervious_pct` at or above p75 and within 500 m of mapped water or wetland | Rain gardens and water-sensitive urban design | Methodology proxy (no dedicated hydrology layer) |
| `pop_density_km2` at or above p75 and NDVI at or below p25 | Pocket parks | C40 Urban Cooling Toolbox |
| `elderly_pct` at or above p75 and `hospital_dist_m` at or above p75 | Cooling centres, priority siting | Knowlton et al. 2014 |

The filter is the main design decision in the engine. A cell can receive the tree-planting recommendation only if it is not water, wetland, mangrove or built-up (WorldCover classes 50, 80, 90 and 95), is not native grassland (class 30, following Veldman et al. 2019 on afforesting grassland and savanna), and has impervious cover below the 75th percentile, meaning there is physical room to plant. A cell that clears the vulnerability bar but fails the ecological check gets the non-tree recommendation instead. The tool is built to be able to say that a ward needs cooling and that trees are not the way to get it.

In the committed run 161 of 541 cells (30%) are plantable. The engine fires 70 ward-level recommendation rows: 24 rain-garden, 19 cool-roof, 18 pocket-park and 9 cooling-centre rows. Every ward receives at least one. **The tree-planting recommendation fires nowhere.**

The reason is in the data. Eighty-one cells are both hot (HVI at or above p75) and bare (NDVI at or below p25). All 81 are classified as built-up land, with a median impervious share of 78.4% against a plantable ceiling of 68.4%, so none passes the filter and all are routed to cool roofs. A dense city's hottest, barest 1 km cells are built-up, and the filter is doing what it was designed to do. One caveat applies. Each cell takes the most common WorldCover class within it, and a cell whose most common class is built-up can still contain green pockets. The result says that no whole cell is a planting site at this resolution. It does not say that Mumbai has nowhere to plant a tree.

An earlier build of this filter compared floating-point class codes with integers. Earth Engine's mode reducer returns a float, so a built-up cell could arrive as 50.00000000000015 and fail an equality test against 50. That let 175 of the 337 cells then marked plantable through: 127 built-up, 30 mangrove, 17 open water and 1 native grassland. It was corrected on 2026-09-24, and every figure in this section is for the corrected filter. Dataset releases up to and including 1.0.2 predate the correction and carry the error.

## 8. Green-cover change

`pipeline/09_ndvi_change.py` classifies each cell's NDVI change between the current dry-season composite and an older baseline (`NDVI - NDVI_prev`, roughly nine years apart) as gained (above +0.05), lost (below -0.05) or stable. The threshold is a documented choice and not a value from a specific paper. It is meant to be the size of change we trust as signal and not noise, in the same spirit as the 20% tolerance in section 6. Across the 541 cells, 445 are stable, 84 gained and 12 lost.

## 9. Simulator coefficients

A separate part of the product (`/simulate`, `frontend/src/lib/coefficients.ts`) estimates the cooling effect of a hypothetical intervention, using coefficients from the literature and not fitted to Mumbai. Canopy cooling follows Ziter et al. (2019): negligible below about 40% canopy cover, rising to about 1.0 degree C of daytime cooling at 80%, and capped instead of extrapolated beyond the paper's range. Cool-roof cooling uses 0.6 degrees C per +0.1 albedo as the headline figure, with the 0.57 to 2.3 range from Santamouris (2014) exposed as uncertainty, and Li, Bou-Zeid and Oppenheimer (2014) cited in support of treating the relationship as linear. Pocket-park cooling scales a 0.94 degree C park-cool-island ceiling (Bowler et al. 2010) linearly by the share of ward area converted to park-like green space, which is a simplifying assumption of ours and not a result from that paper. The three terms are added independently, with no attempt to model interactions such as counting a tree that stands inside a park twice.

The simulator is not part of the HVI. It appears here because it draws on the same citations, listed in `docs/references.md`.

## 10. Limitations

**Land surface temperature is not air temperature.** `LST_C` measures the surface and only correlates with the air temperature a person feels. The live-weather widget (`frontend/src/lib/weather.ts`) exists to make the distinction visible, with a real air-temperature reading fetched at the same time.

**The cooling coefficients come from other cities.** They come from studies in eastern North America, city-scale reviews and a Baltimore-Washington simulation, and nobody has validated them in Mumbai.

**`slum_pct` is a mapped proxy.** It comes from Datameet's mapped cluster boundaries and not from a household survey.

**`elderly_pct` is an administrative boundary and not a demographic surface.** WorldPop's India age-sex product is a 100 m raster, which suggests a measured surface at that resolution. It applies district age structure to a population raster instead. Across the 541 cells, 80% share one value and two values cover 95.6%, and the two values split the city exactly along the revenue district line. All nine Mumbai City wards read 5.586 and all fifteen Mumbai Suburban wards read 4.757. Values in between appear only where a 1 km cell straddles the boundary.

The layer is not inert, which is why this is a limitation and not a curiosity. Standardising divides by the standard deviation, and a near-constant variable has a small one, so a gap of 0.83 percentage points between two districts becomes a large z-score. The indicator takes 13.6% of total absolute contribution to ward scores, fourth of the eight, and removing it moves 13 of the 24 wards by up to 4 places. A ward's rank is therefore partly decided by which side of the City and Suburban line it sits on, under a label that reads as demographic (`pipeline/elderly_evaluation.py`).

The same layer feeds a recommendation. The cooling-centre rule requires `elderly_pct` at or above its 75th percentile, and that condition holds for 136 cells: all 94 cells in Mumbai City wards plus 42 suburban cells whose value sits marginally above the district's because of boundary blending. In the current run the rule fires on 18 cells. "High elderly share" is therefore a description of which district a cell is in, and the recommendation should be read that way.

The fix would be ward-level Census age structure at 60 and over, and we could not find it. The ward-level Primary Census Abstract has the 0 to 6 age band only, which is why `child_pct` is in the index. The usual objection to Census data is that 2011 is too old to combine with 2025-26 imagery, and it does not apply here, because WorldPop's age structure is itself derived from the 2011 Census. The choice is between the same census at district resolution and at ward resolution.

**`child_pct` is 2011 data, and it measures children.** It is real and varies by ward, but it describes young children and not the elderly, it is fifteen years old, and it is assigned flat to every cell in a ward because the Census gives nothing finer. Its weight of 1.9% means it changes little in the PCA ranking, and it matters far more under equal weighting (section 6b).

**Tree planting never fires.** Section 7 explains why. It is a result about the 1 km grid and the modal land-cover class, and it should not be read as a claim about individual sites.

**The ranking is imprecise.** Section 6a puts the median ward's 95% rank interval at 6 places and finds no certain rank. Any use of the ranking that turns on a difference of a few places is not supported by the data behind it. Equal weights change the order inside the top five (section 6b).

**Weights depend on the snapshot.** The PCA weights are recomputed from the current cells, as section 5 notes. The sensitivity results suggest they are fairly stable, but they are not fixed across every possible rerun.

**Satellite coverage varies by cell.** Cells are flagged when their dry-season composite rests on fewer than three clear Landsat observations. Across the published grid the count runs from 8.7 to 12.0 per cell, so no cell in the current snapshot is flagged. The flag travels with the data for refreshes and for cities where it will fire.

**Coarse land cover.** WorldCover is 10 m data aggregated to 1 km cells by modal class, and flood risk is a single proxy, distance to mapped water or wetland, and not a hydrology layer.

## 11. Reproducibility

Every figure in this report came from a file the repository's own pipeline produced, listed in the status note at the top. The pipeline runs end to end with `python pipeline/run_pipeline.py` (see `pipeline/README.md`) and regenerates all of them from the same sources and procedure. The ward-level Census table is an input and not an output. It is committed as `data/census2011_ward_age_mumbai.csv` and rebuilt from the OpenCity source with `python pipeline/build_census_table.py`, which stops if the two source files disagree on any ward's population or if the total differs from the Census figure for Greater Mumbai.

The evaluations that this report relies on are each a script in `pipeline/`: `uncertainty.py`, `compare_weightings.py`, `elderly_evaluation.py`, `08_sensitivity.py` and `13_validate_lst.py`. The 500 m comparison in section 6c is reproduced with `--cell-size 500`, which writes to its own directory and never overwrites the published 1 km outputs.

The dataset is archived on Zenodo with the concept DOI 10.5281/zenodo.22923919, which resolves to the latest release. As section 7 notes, releases up to 1.0.2 predate a correction to the plantability filter, so cite a later one.

## 12. References

| Use | Citation | DOI |
|---|---|---|
| HVI weighting method | Reid et al. 2009, *Environ. Health Perspect.* 117(11):1730-1736 | 10.1289/ehp.0900683 |
| First South Asian heat action plan | Knowlton et al. 2014, *IJERPH* 11(4):3473-3492 | 10.3390/ijerph110403473 |
| India-wide district HVI | Azhar et al. 2017 (RAND India HVI), *IJERPH* 14(4):357 | 10.3390/ijerph14040357 |
| Tree restoration potential | Bastin et al. 2019, *Science* 365(6448):76-79 | 10.1126/science.aax0848 |
| Critique of afforestation everywhere (plantability filter) | Veldman et al. 2019, *Science* 366(6463):eaay7976 | 10.1126/science.aay7976 |
| Carbon-cycle critique, companion | Friedlingstein et al. 2019, *Science* 366(6463):eaay8060 | 10.1126/science.aay8060 |
| Regrowth critique, companion | Lewis et al. 2019, *Science* 366(6463):eaaz0388 | 10.1126/science.aaz0388 |
| Canopy and LST reduction | Ziter et al. 2019, *PNAS* 116(15):7575-7580 | 10.1073/pnas.1817561116 |
| City-scale cool-roof simulation | Li, Bou-Zeid and Oppenheimer 2014, *Environ. Res. Lett.* 9(5):055002 | 10.1088/1748-9326/9/5/055002 |
| Albedo and peak temperature | Santamouris 2014, *Solar Energy* 103:682-703 | 10.1016/j.solener.2012.07.003 |
| Pocket-park cooling | Bowler et al. 2010, *Landscape and Urban Planning* 97:147-155 | 10.1016/j.landurbplan.2010.05.006 |
| Ward-level age data | Census of India 2011, Primary Census Abstract, Greater Mumbai (M Corp.), Census-ward level, republished by OpenCity (public domain) | Dataset: data.opencity.in/dataset/mumbai-ward-wise-census-data |

The DOIs were checked against publisher resolvers as recorded in `docs/references.md`, and this report does not check them again. That file also holds the data-source access details not repeated here.
