# A Transparent, Literature-Weighted Heat Vulnerability Index for Mumbai's 24 Wards

Anay Dhawan, independent researcher

Technical report for the Urban Climate Intelligence Platform (UCIP)

*Draft status, removed before submission: written for issues #66 and #90 and not yet submitted. What remains to be decided is listed in `docs/preprint/SUBMISSION.md`. Every figure below was read from this repository's committed pipeline output (`data/hvi_pca_log.json`, `data/sensitivity.json`, `data/hvi_uncertainty.json`, `data/weighting_comparison.json`, `data/lst_validation.json`, `data/nbs_recommendations.json`, `data/cells_ndvi_change.geojson`) and not re-derived. The one exception is the account of the removed elderly indicator in section 10, which comes from an evaluation run on the dataset before the indicator was removed and is retrievable at commit `186af70`. The dataset is archived at doi:10.5281/zenodo.22923919.*

---

## Abstract

Heat risk is uneven within a city, and so is the ability to cope with it. This report describes the Heat Vulnerability Index (HVI) that UCIP computes for the 24 Brihanmumbai Municipal Corporation (BMC) wards of Mumbai. The index combines seven indicators on a 1 km grid: dry-season land surface temperature, vegetation, population density, the share of young children, informal-settlement coverage, distance to a hospital, and impervious surface. Weights come from the first principal component of the standardised indicators. A rule-based engine turns each cell's scores into a cooling recommendation, and an ecological filter withholds tree planting where the land cover makes it inappropriate.

Most of the report is about how far the ranking can be trusted. We test it four ways: perturbing the weights, bootstrapping the cells, comparing principal-component weights with equal weights, and rebuilding the whole dataset on a 500 m grid. The median ward's 95% rank interval spans 7 of 24 places, and no ward's rank is certain. The 500 m rebuild reorders thirteen wards, yet every ward's 500 m rank sits inside its own bootstrap interval from the 1 km data. Equal weighting is less forgiving than we expected. It agrees with the principal-component ranking at Kendall's tau 0.75 and shares three of the five most vulnerable wards. Almost all of that disagreement comes from one indicator, the child share, which principal-component weighting gives 2.7% and equal weighting gives 14.3%.

We also report two problems with our own work. An elderly share, taken from WorldPop, had two values across the whole city and followed the revenue district boundary exactly, so it carried district-level information under a ward-level label. We removed it, since no accurate ward-level source exists, and report what removing it changed. And with the ecological filter working as intended, the tree-planting recommendation fires for no cell in Mumbai, because every cell that is both hot and bare is built-up land.

## 1. Introduction

Heat is a public-health hazard in cities, and adaptation planning needs to know where to act. Knowing that a city is warm does not say that. A single citywide temperature says nothing about which neighbourhoods to look at first or what kind of intervention suits them. UCIP tries to answer at the level a municipal planner works: which of the 24 wards to act on first, why, and with what.

The index and the recommendation engine are built so that they can be checked. Weights are derived from the data by a published method instead of being set by judgment, every score breaks down into per-indicator contributions, and the sections below say where the results are weak. The in-app methodology page (`/methodology`) and `docs/methodology.md` describe the same work in outline. This report is the version that can be read and cited without the product.

## 2. Prior art

UCIP was designed after comparing existing heat-vulnerability and urban-cooling work: the Mumbai Climate Action Plan (MCAP 2022), the district-level India HVI of Azhar et al. (2017), IIT Bombay's work on Mumbai's surface urban heat island, the C40 Urban Cooling Toolbox, and the Ahmedabad Heat Action Plan (Knowlton et al. 2014). It differs from that work in three ways. The index weights come from the data. A rule-based engine attaches a recommendation to each score. And an ecological filter can reject afforestation on ecological grounds (section 7).

## 3. Study area and data

Mumbai is analysed on a 1 km grid and rolled up to the 24 BMC wards. `pipeline/01_grid.py` clips a fishnet to the ward boundaries in a metric projection (EPSG:32643, UTM zone 43N) and assigns each cell to the ward that holds its largest fragment, which gives 547 cells. Stage 04 (`pipeline/04_zonal.py`) then removes cells that cannot be scored: any cell missing an indicator, which cannot be standardised, and any cell with zero WorldPop population, which has no residents to be vulnerable. At 1 km that removes 6 of the 547, about 1%, against a pipeline ceiling of 15%. All six have zero population, and four have negative NDVI, which fits open water or bare coast. The remaining 541 cells (`data/cells.geojson`) are the basis for every later stage and every cell count in this report.

| Layer | Source | Access | Note |
|---|---|---|---|
| Land surface temperature (LST) | Landsat 8/9 Collection 2 Level-2, `ST_B10` | Google Earth Engine | Dry-season median composite, cloud and shadow masked with `QA_PIXEL` |
| NDVI (current and baseline) | Landsat 8/9 Collection 2 Level-2, `SR_B4` and `SR_B5` | Google Earth Engine | Two dry-season composites about nine years apart, for the green-cover-change layer (section 8) |
| Population density | WorldPop 100 m population, pinned to the `IND_2020` image | Google Earth Engine | Modelled. 2020 is the latest year WorldPop publishes for India in this collection, and the pin is explicit in `pipeline/03_vectors.py` so a newer vintage cannot be picked up silently. The collection's age structure is not used, see section 10 |
| Young-child share | Census of India 2011, Primary Census Abstract at Census-ward level, as republished by OpenCity | Repository data (`data/census2011_ward_age_mumbai.csv`) | Ward level, so every cell in a ward carries its ward's value. Ninety-seven Census wards roll up into the 24 BMC wards. The build checks that the population sums to the Census figure for Greater Mumbai, 12,442,373 |
| Slum index | Datameet `slumClusters.geojson`, mapped cluster boundaries | Repository data | Proxy, though it rests on observed cluster polygons and not on a modelled index |
| Hospital access | OpenStreetMap `amenity=hospital` | `osmnx` and Overpass | Straight-line distance from each cell to the nearest hospital centroid |
| Impervious surface, land-cover class | ESA WorldCover v200 | Google Earth Engine | Also the input to the plantability filter (section 7) |
| Ward boundaries | Datameet BMC ward boundaries | Repository data | 24 features, checked against Mumbai's known extent |

## 4. Indicators and direction

Seven indicators feed the index. Each has a direction: +1 when a higher raw value means more vulnerability, and -1 when it means less, in which case the value is inverted before scoring. NDVI is the only -1.

| Indicator | Direction | Unit | Observed range (541 cells) |
|---|---|---|---|
| `LST_C` (land surface temperature) | + | degrees C, land surface and not air | 26.24 to 39.95 |
| `NDVI` (vegetation index) | - | unitless index, not a canopy percentage | -0.07 to 0.71 |
| `pop_density_km2` (population density) | + | people per km2 | 16 to 115,272 |
| `child_pct` (share aged 0 to 6) | + | % (0-100), Census 2011, by ward | 6.75 to 13.09 |
| `slum_pct` (slum-cluster coverage) | + | % (0-100), mapped boundaries | 0.00 to 68.55 |
| `hospital_dist_m` (distance to nearest hospital) | + | metres | 3.86 to 6199.03 |
| `impervious_pct` (impervious surface share) | + | % (0-100) | 0.00 to 96.79 |

One indicator describes age. `child_pct` is real ward-level Census data with 24 distinct values from 6.75% to 13.09%. It measures children under seven and not the elderly, and those are different populations. It is in the index because the ward-level Census tables we could find have no 60+ column, and 0 to 6 is the only age-structure signal in them. Including it is a modelling choice and not a settled one. As sections 5 and 6b show, principal-component weighting gives it very little influence and equal weighting gives it a lot. Earlier builds also had an elderly share, which section 10 explains and which is no longer in the index.

## 5. Computing the HVI

**Standardisation.** Each indicator is z-standardised across all cells (`pipeline/05_hvi.py`). For an indicator column $x$, $z = (x - \bar{x}) / \sigma_x$, using the population standard deviation (`ddof=0`). The result is then multiplied by the indicator's direction sign, so a higher signed z-score always means more vulnerable.

**Weights (PCA, Reid et al. 2009).** A principal component analysis is fitted to the signed z-score columns. The explained-variance ratio of the first component is compared with a floor of 0.30. If it is at or above the floor, the component's loadings give the weights. The component is first oriented so that a higher score means more vulnerable, by correlating its scores with the signed `LST_C` z-score and flipping the sign if the correlation is negative. The weight for indicator $i$ is its absolute loading divided by the sum of absolute loadings:

$$w_i = \frac{|\ell_i|}{\sum_{j=1}^{p} |\ell_j|}$$

where $\ell_i$ is the oriented PC1 loading and $p$ is the number of indicators. If PC1 falls below the 0.30 floor, the pipeline treats the loadings as unstable for a single-city, single-snapshot sample and falls back to equal weights across all indicators, which is the published component-level default in Reid et al. (2009). It logs that the fallback fired and why.

**Values in the committed run.** PC1 explains 56.5% of the variance, above the floor, so the fallback did not fire.

| Indicator | PC1 loading | Weight |
|---|---:|---:|
| `LST_C` | 0.446 | 0.179 |
| `NDVI` | 0.376 | 0.151 |
| `pop_density_km2` | 0.442 | 0.178 |
| `child_pct` | 0.068 | 0.027 |
| `slum_pct` | 0.300 | 0.120 |
| `hospital_dist_m` | -0.387 | 0.155 |
| `impervious_pct` | 0.468 | 0.188 |

Child share is nearly uncorrelated with the other indicators (its correlation with each is at most 0.22 in absolute value), so it adds variance that PC1 does not capture, and PCA gives it the smallest weight of the seven. Without it PC1 would explain 65.7% of the variance, which `compare_weightings.py` records.

The weights are recomputed from the current data on every pipeline run. What is fixed, and cited, is the procedure: PCA on signed z-scores, with the stated fallback. A materially different snapshot of Mumbai could shift the loadings.

**Score.** For each cell, `HVI_raw` is the weighted sum of signed z-scores, $\sum_i w_i z_i$, and `HVI` is `HVI_raw` rescaled linearly to 0-100 across all cells in the run. A ward's HVI is the unweighted mean of its cells' scores, and its rank is `HVI` sorted in descending order, so rank 1 is the most vulnerable. In the committed run the five highest-ranked wards are L, C, G/N, H/E and E, with HVI of 66.3, 63.5, 61.6, 56.7 and 56.1. The largest single contribution comes from `LST_C` for L (0.223), from `impervious_pct` for C, G/N and E (0.303, 0.225 and 0.241), and from `pop_density_km2` for H/E (0.196).

**Explanation.** Each cell's contribution from each indicator (weight times signed z-score) is stored with its score and shown as a ranked bar chart in the product. The index is a weighted linear sum, so this breakdown is the complete explanation of any score. There is no black-box model, and so no need for a post-hoc method such as SHAP.

## 6. Sensitivity to the weights

This section asks whether small disagreements about the right weights would change which wards get priority. `pipeline/08_sensitivity.py` perturbs each of the seven weights by +20% and by -20% in turn, renormalises the other six so the weights still sum to 1, and recomputes the ranking. That gives 14 runs. Each is compared with the unperturbed ranking by Kendall's tau over all 24 wards and by top-5 overlap.

Mean tau across the 14 runs is 0.980, and mean top-5 overlap is 4.64 of 5. In 9 of the 14 runs the top five is exactly the baseline set (L, C, G/N, H/E, E). In the other five one ward swaps in for E: ward B when the NDVI weight is raised 20%, the hospital-distance weight is raised 20% or the impervious weight is lowered 20%, and ward K/E when the NDVI weight is lowered 20% or the slum weight is raised 20%. Wards L, C, G/N and H/E are in the top five in every run, and ward L is first in all 14. In two runs, lowering the population-density weight and raising the impervious weight, E and H/E swap places.

One indicator barely registers. Lowering the `child_pct` weight by 20% leaves every rank unchanged (tau 1.000) and raising it by 20% gives tau 0.993, which follows from its 2.7% weight.

The run output records only the top five for each perturbation, so this section says nothing about how ranks below fifth move. Section 6a covers the whole table.

## 6a. How precise is a ward's rank? A bootstrap

The perturbation study varies the weights and holds the sample fixed. It answers whether a different analyst's weights would change the result, and it does not answer whether a different sample would. The second question matters just as much, since the PCA weights are themselves estimated from 541 cells and carry sampling error.

`pipeline/uncertainty.py` resamples the cells with replacement 1000 times (seed 20260923) and reruns the whole chain on each replicate: z-scores, PCA, weights, per-cell index, 0-100 rescale, ward roll-up and rank. Holding the z-scores and the rescale fixed and varying only the weights would understate the uncertainty while looking rigorous, so everything is recomputed. The intervals below are 95% percentile intervals.

The median ward's rank interval spans 7 of 24 places. The widest belongs to ward B, ranked 6th, whose interval runs from 1st to 20th, 19 places. No ward's rank is certain: no interval collapses to a single place.

Some statements about the ranking survive this and some do not. Ward L's interval is 1st to 4th, so L being among the most vulnerable holds. T and R/C, ranked 24th and 23rd, both have intervals of 22nd to 24th, so being among the least vulnerable holds too. The 9th-ranked ward (M/W, 4th to 13th) and the 12th (G/S, 8th to 14th) overlap almost completely, and a planner choosing between two mid-table wards should treat them as tied and decide on other grounds.

We report this because publishing a rank as a bare integer invites readers to assume a precision the method does not have.

## 6b. Does the choice of weights change the answer?

Section 5 derives weights from PC1 and documents a fallback to equal weights. `pipeline/compare_weightings.py` computes both rankings on the same data and compares them.

Kendall's tau between the two is 0.754 and Spearman's rho is 0.891. Four of the 24 wards get the same rank under both schemes. The largest shift is 9 places: ward M/E is 16th under PCA weights and 7th under equal weights. Wards C and D each move 7 places, C from 2nd to 9th. The two schemes share three of the five most vulnerable wards (PCA order L, C, G/N, H/E, E; equal-weight order L, G/N, H/E, B, M/W).

That is weaker agreement than we expected, and it says the choice of weights matters. A high correlation would not have shown that PCA weighting is correct, and nothing here could. What the comparison does show is where the disagreement comes from. The script drops the lowest-weighted indicator, `child_pct`, refits PCA and equal weights on the other six, and compares again. Tau rises to 0.957, rho to 0.994, and the two top fives share four wards (PCA order C, L, G/N, H/E, E; equal-weight order L, C, G/N, H/E, K/E). Principal-component weighting gives `child_pct` 2.7% of the total and equal weighting gives it 14.3%, and that gap is nearly the whole difference between the schemes.

So the choice between PCA and equal weights is, in practice, a choice about how much a 2011 Census count of young children should count. The perturbation study in section 6 cannot see this, because it only moves the PCA weights a little way and never tries a different scheme.

## 6c. Does the grid resolution change the answer?

The checks above resample or reweight a fixed 1 km grid. Rebuilding the dataset at 500 m is an independent test, because it changes the unit of analysis. It produces 1975 published cells instead of 541, about 82 per ward instead of 23, with every stage from the fishnet through the Earth Engine reductions rerun. PC1 explains 55.2% of the variance at this resolution.

Thirteen of the 24 wards change rank. Ward B moves from 6th to 2nd and G/N from 3rd to 6th. The top five share three wards with the 1 km top five: L, C and H/E at both resolutions, G/N and E at 1 km, B and K/E at 500 m.

On its own that looks like instability. Set against section 6a it is close to the opposite. Every ward's 500 m rank falls inside that ward's own 95% bootstrap interval from the 1 km data, 24 out of 24. Ward B's interval was the widest in the table, 1st to 20th, and 2nd is inside it. Resampling cells at one resolution and rebuilding the grid at another share no machinery, and they disagree about the order while agreeing about which parts of the order carry information. That is the strongest support this report has for section 6a's conclusion: a rank near the top or bottom is a finding, and a rank in the middle depends on where the grid lines fell.

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

The filter is the main design decision in the engine. A cell can receive the tree-planting recommendation only if it is not water, wetland, mangrove or built-up (WorldCover classes 50, 80, 90 and 95), is not native grassland (class 30, following Veldman et al. 2019 on afforesting grassland and savanna), and has impervious cover below the 75th percentile, meaning there is physical room to plant. A cell that clears the vulnerability bar but fails the ecological check gets the non-tree recommendation instead. The tool is built to be able to say that a ward needs cooling and that trees are not the way to get it.

In the committed run 161 of 541 cells (30%) are plantable. The engine fires 61 ward-level recommendation rows: 24 rain-garden, 19 cool-roof and 18 pocket-park rows. Every ward receives at least one. **The tree-planting recommendation fires nowhere.** An earlier build also had a cooling-centre rule keyed on the elderly share, which was removed with that indicator (section 10).

The reason is in the data. Seventy-five cells are both hot (HVI at or above p75) and bare (NDVI at or below p25). All 75 are classified as built-up land, with a median impervious share of 78.4% against a plantable ceiling of 68.4%, so none passes the filter and all are routed to cool roofs. A dense city's hottest, barest 1 km cells are built-up, and the filter is doing what it was designed to do. One caveat applies. Each cell takes the most common WorldCover class within it, and a cell whose most common class is built-up can still contain green pockets. The result says that no whole cell is a planting site at this resolution. It does not say that Mumbai has nowhere to plant a tree.

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

**There is no elderly indicator, and the reason matters.** Earlier builds of the index had one. It came from WorldPop's India age-sex product, a 100 m raster, which suggests a measured surface at that resolution. The product applies district age structure to a population raster instead. Across the 541 cells, 80% shared one value and two values covered 95.6%, and the two values split the city exactly along the revenue district line. All nine Mumbai City wards read 5.586 and all fifteen Mumbai Suburban wards read 4.757. Values in between appeared only where a 1 km cell straddled the boundary.

The layer was not inert, which is why this is a limitation and not a curiosity. Standardising divides by the standard deviation, and a near-constant variable has a small one, so a gap of 0.83 percentage points between two districts became a large z-score. The indicator took 13.6% of total absolute contribution to ward scores, fourth of the eight then in the index, and dropping it moved 13 of the 24 wards by up to 4 places. A ward's rank was partly decided by which side of the City and Suburban line it sat on, under a label that read as demographic. The same layer fed a cooling-centre rule that fired wherever the elderly share was in its top quartile. That held for 136 cells: all 94 cells in Mumbai City wards plus 42 suburban cells whose value sat marginally above the district's because of boundary blending. "High elderly share" described which district a cell was in.

We removed the indicator and the rule, and did not relabel them. The fix would be ward-level Census age structure at 60 and over, and we could not find it. The ward-level Primary Census Abstract has the 0 to 6 age band only, which is why `child_pct` is in the index. The usual objection to Census data is that 2011 is too old to combine with 2025-26 imagery, and it does not apply here, because WorldPop's age structure is itself derived from the 2011 Census. The choice was between the same census at district resolution and at ward resolution, and only the first was available.

Removing it recomputed every score. Thirteen wards changed rank, by at most 4 places (Kendall's tau 0.891 between the old and new rank tables). The old top five was C, G/N, L, E, B and the new one is L, C, G/N, H/E, E, and ward C's score fell from 72.1 to 63.5. The evaluation behind all of this, `pipeline/elderly_evaluation.py` and its output, was deleted with the indicator and is at commit `186af70`.

A consequence for anyone reading the index: it has no measure of the elderly, a group at particular risk in heat. It accounts for young children through `child_pct` and for nothing else about age, and it should not be presented as capturing age vulnerability more broadly.

**`child_pct` is 2011 data, and it measures children.** It is real and varies by ward, but it describes young children and not the elderly, it is fifteen years old, and it is assigned flat to every cell in a ward because the Census gives nothing finer. Its weight of 2.7% means it changes little in the PCA ranking, and it matters far more under equal weighting, where it accounts for nearly all of the disagreement with PCA (section 6b).

**Tree planting never fires.** Section 7 explains why. It is a result about the 1 km grid and the modal land-cover class, and it should not be read as a claim about individual sites.

**The ranking is imprecise.** Section 6a puts the median ward's 95% rank interval at 7 places and finds no certain rank. Any use of the ranking that turns on a difference of a few places is not supported by the data behind it. Equal weights share only three of the five most vulnerable wards with the PCA weights (section 6b).

**Weights depend on the snapshot.** The PCA weights are recomputed from the current cells, as section 5 notes. The sensitivity results suggest they are fairly stable, but they are not fixed across every possible rerun.

**Satellite coverage varies by cell.** Cells are flagged when their dry-season composite rests on fewer than three clear Landsat observations. Across the published grid the count runs from 8.7 to 12.0 per cell, so no cell in the current snapshot is flagged. The flag travels with the data for refreshes and for cities where it will fire.

**Coarse land cover.** WorldCover is 10 m data aggregated to 1 km cells by modal class, and flood risk is a single proxy, distance to mapped water or wetland, and not a hydrology layer.

## 11. Reproducibility

Every figure in this report came from a file the repository's own pipeline produced, listed in the status note at the top. The pipeline runs end to end with `python pipeline/run_pipeline.py` (see `pipeline/README.md`) and regenerates all of them from the same sources and procedure. The ward-level Census table is an input and not an output. It is committed as `data/census2011_ward_age_mumbai.csv` and rebuilt from the OpenCity source with `python pipeline/build_census_table.py`, which stops if the two source files disagree on any ward's population or if the total differs from the Census figure for Greater Mumbai.

The evaluations that this report relies on are each a script in `pipeline/`: `uncertainty.py`, `compare_weightings.py`, `08_sensitivity.py` and `13_validate_lst.py`. The 500 m comparison in section 6c is reproduced with `--cell-size 500`, which writes to its own directory and never overwrites the published 1 km outputs.

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
