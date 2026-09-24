# UCIP — Methodology (outline)

> Mirrors the in-app `/methodology` page (F5). Filled during the sprint. Stating limitations openly is a credibility win with researcher judges; hiding them is the trap.

## 1. Problem & scope
- Decision-support, not another heat map: which Mumbai wards to cool first, why, what intervention, where the budget goes.
- Mumbai only. Grid compute (1 km default, 500 m runnable and verified, see §4c), rolled up to 24 BMC wards. Architecture city-agnostic.

## 2. Prior art & how UCIP differs
- Prior-art scan done (pre-sprint item #8): 5 cited studies + "how UCIP differs" in `docs/prior-art.md`. Covers MCAP 2022, RAND/Azhar India HVI, IIT-B Mumbai SUHI, C40 Urban Cooling Toolbox, Ahmedabad HAP (+ IIHS governance, Rathi four-city HVI).
- UCIP's difference: transparent literature-weighted index + NBS engine + ecological plantability filter + budget layer, vs static vulnerability assessments.

## 3. Indicators
- LST (+), NDVI inverted (-), population density (+), young-child % (+), slum index (+), hospital distance (+), impervious % (+). Seven in all. `child_pct` is ward-level Census 2011 data and is optional per city; see 10c. There is no elderly indicator: it was removed because no accurate source exists at ward level, see 10a.
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
- Caveats carried over from section 10: `child_pct` is 2011 data and flat within a ward, so the copy does not lean on it; NDVI is reported as an index, never as a canopy percentage.

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
| Median rank interval | **7 places** |
| Widest | 19 places (ward B, ranked 6th, interval 1st to 20th) |
| Wards whose rank is certain | **0 of 24** |

Read the ranking as broad bands rather than an ordering. "L is among the
most vulnerable wards" survives (interval 1st to 4th) and "T and R/C are among
the least" survives (both 22nd to 24th), but the difference between 9th and
12th does not: M/W (4th to 13th) and G/S (8th to 14th) overlap almost
entirely. A planner choosing between two
mid-table wards should treat them as tied and decide on other grounds.

This captures sampling uncertainty in the cells only. It does not capture
measurement error in the indicators, the choice of indicators, or the decision
to weight by PCA at all, which is quantified separately in §5.

### Checked against a different grid

The intervals above come from resampling one 1 km dataset. Rebuilding the
dataset at 500 m is an independent test of the same claim, because it changes
the unit of analysis rather than resampling it: 1975 published cells instead of
541, roughly 82 per ward instead of 23.

Thirteen of the 24 wards change rank. Ward B moves from 6th to 2nd and G/N
from 3rd to 6th, and the top five share 3 wards (L, C, H/E at both
resolutions; G/N and E at 1 km, B and K/E at 500 m).

The agreement is the interesting part. **Every ward's 500 m rank falls inside
that ward's own 95% bootstrap interval from the 1 km data, 24 out of 24.** Ward
B's interval was 1st to 20th, the widest in the table, and 2nd is inside it. The
two methods disagree about the ordering and agree about which parts of the
ordering mean anything, which is what §4c said to expect.

Read together: a rank near the top or the bottom is a finding, and a rank in the
middle is an artefact of where the grid lines fell. 1 km remains the published
resolution, and the 500 m run is reproducible with
`python pipeline/run_pipeline.py --cell-size 500` (see
[`adding-a-city.md`](adding-a-city.md) §4b for what it costs).

## 4d. How much imagery is behind each cell

`lst_clear_obs` per cell, from stage 02 (issue #94).

The dry-season composite is a median over cloud-masked Landsat scenes, and
until now nothing recorded how many observations survived that masking for a
given cell. A cell composited from two clear passes and one composited from
twelve carried identical weight in the index, with no way to tell them apart.
Cloud contamination biases land surface temperature, so that was an unmeasured
exposure rather than a known-small one.

Every cell now carries the mean number of cloud-free observations backing its
LST, and a `lst_obs_sparse` flag.

**The minimum is 3 cloud-free observations.** Below that a cell is flagged.
Three is a floor rather than a comfort level: a four-month dry-season window is
roughly eight to sixteen Landsat 8 and 9 passes, so a cell down at two is
persistently clouded or persistently masked, and a median over two values is
barely a median. Stage 14 already applies the same judgement to a longer
window, requiring four scenes before fitting a ward-year.

Flagged, not dropped. Dropping would change the cell count between runs, and
the downstream stages, the published dataset and the quality gate's count
tolerance all treat the grid size as stable. A consumer who wants to exclude
sparse cells can; the pipeline does not reshape itself silently.

## 5. Sensitivity / validity
- Weights perturbed +/-20%; ward priority ranking shown stable (chart). Addresses weight-transfer validity for Mumbai.
- **PCA weighting vs the published fallback** (`pipeline/compare_weightings.py`, output `data/weighting_comparison.json`). The obvious challenge to a data-derived weighting is "how much does it change the answer versus just using the published weights?", so both are run over the same cells and compared:

  | Measure | Result |
  |---|---|
  | Kendall tau | 0.754 |
  | Spearman rho | 0.891 |
  | Wards with an identical rank | 4 of 24 |
  | Largest single move | ward M/E, 9 places (16th under PCA, 7th under equal weights) |
  | Top-5 overlap | 3 of 5 (PCA: L, C, G/N, H/E, E; equal: L, G/N, H/E, B, M/W) |

  Read this correctly. A high correlation would not show the PCA weighting is right, and this is not a high correlation: the choice of weights matters. Ward C is second under PCA weights and ninth under equal weights.

  Almost all of the disagreement is one indicator. The comparison script drops the lowest-weighted indicator, `child_pct`, refits PCA and equal weights on the other six, and compares again (the `ablation` block in the output). Kendall tau is then 0.957, Spearman rho 0.994, and the top five share 4 of 5. PCA gives `child_pct` 2.7% of the total and equal weighting gives it 14.3%, and that gap is nearly the whole difference between the two schemes.

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
- The slum layer is a proxy (mapped slum-cluster boundaries), and population density is a
  WorldPop 2020 model (the most recent year available for India), not a census count. There is
  no elderly indicator because no accurate source exists at ward level: see §10a.
- Simulator is a first-order estimate, not a validated climate model.
- Ecological plantability layer is coarse-resolution.

### 10b. Correction, 2026-09-24: the plantability filter was failing open

Published plantability was wrong for half its output between the first release
and 2026-09-24, and the correction removed 176 of 337 plantable cells.

Earth Engine's mode reducer returns a float. A cell whose dominant WorldCover
class is built-up therefore arrived as 50.00000000000015 or 49.99999999999996,
never as 50, and `worldcover_class in {50, 80, 90, 95}` is False for both. The
class check silently passed and the cell was treated as having no
disqualifying land cover. 301 of 541 cells carried such a value.

The consequence was the exact failure this filter exists to prevent:

| Land cover | Cells published as plantable | Should have been |
|---|---|---|
| Built-up (50) | 127 | refused |
| **Mangrove (95)** | **30** | **refused** |
| Open water (80) | 17 | refused |
| Native grassland (30) | 1 | refused |
| **Total** | **175 of 337** | **0** |

Recommending tree planting on mangrove is not a rounding error. A mangrove is
already doing the cooling and flood-buffering work, and "planting" it means
replacing it. The documentation in `calibrating-ecology.md` described the filter
as protecting mangroves throughout the period it was not.

Class codes are now normalised to integers at the point they leave Earth Engine
and again inside `is_plantable`, and a value that is not a recognised WorldCover
code is refused rather than passed through. After the fix, 161 of 541 cells are
plantable and none of them carry a disqualifying class.

The lesson generalises past this one comparison: a categorical code arriving as
a float from a numerical reducer will defeat equality checks, and a filter whose
failure mode is to permit rather than refuse will do so silently. The rule the
filter already stated for missing data, that absence of evidence is not evidence
that planting is safe, now applies to unreadable data too.

### 10a. `elderly_pct` was removed

The index no longer has an elderly indicator. It had one, taken from WorldPop,
and it did not measure age. Issue #167 asked what to do about it and the answer
is to remove it, because no accurate ward-level 60+ source exists and a number
that reads as demographic and is not one is worse than no number.

The evidence was produced by `pipeline/elderly_evaluation.py`, since deleted
with the indicator. It stays retrievable: `git show 186af70:data/elderly_evaluation.json`
and `git show 186af70:pipeline/elderly_evaluation.py`.

**What it was.** WorldPop's India age-sex product is a 100 m raster, which
implies a measured surface at that resolution. It applies **district** age
structure to a population raster instead. Across Mumbai's 541 cells:

| | |
|---|---|
| Distinct values | 26, but 80% of cells shared one |
| Two values covered | 95.6% of cells |
| Coefficient of variation | 0.064, the lowest of the eight indicators then in the index |

The two values split the city exactly along the revenue district boundary. All
nine Mumbai City wards carried 5.586 and all fifteen Mumbai Suburban wards
carried 4.757. Only the wards on the line held anything in between, and that was
1 km cells straddling the boundary, not demography. Two wards on the same side
of that line were indistinguishable on the indicator, whatever their real age
structure.

**It was not inert, which is why it could not stay.** Standardisation divides by
the standard deviation, and a near-degenerate variable has a small one, so a
0.83-point gap between two districts became a large z-score. The indicator took
13.6% of total absolute contribution to ward scores, fourth of eight, and
dropping it moved 13 of the 24 wards by up to 4 places. A ward's rank was partly
decided by which side of the City and Suburban line it sat on, under a label
that read as demographic.

**It drove a recommendation, and that rule is removed too.** The cooling-centre
rule fired where `elderly_pct` was at or above its 75th percentile and
`hospital_dist_m` was at or above its 75th. The elderly condition held for 136
cells: all 94 in Mumbai City wards, plus 42 suburban cells whose value sat
marginally above the suburban one because of boundary blending. "High elderly
share" meant which district a cell was in. The rule fired on 18 cells in 9
ward-level rows. It is gone, and so is the Knowlton et al. 2014 citation that
existed only for it. The cool-roof recommendation still names cooling centres as
one of its measures; that is a different rule.

**Why not replace it.** The objection to Census data was never the vintage,
because WorldPop's age structure is itself derived from the 2011 Census. The
choice would have been the same census at ward resolution instead of district
resolution, and that would be a strict improvement, 24 values where there were
two. It does not exist in the open tables. Both files in OpenCity's ward-wise
Census release (Primary Census Abstract for Mumbai City and for Mumbai Suburban,
97 Census wards between them) carry population, sex, SC and ST, literacy and
workers, and the age band 0 to 6. There is no 60+ column. The one age signal
that does exist at ward resolution is in 10c.

An elderly indicator can come back if a ward-level source of 60+ counts turns
up. Until then the index does not claim to know how old the residents are.

**What removal changed.** Ward scores were recomputed and rescaled without it.
Thirteen wards changed rank, by at most 4 places (Kendall tau 0.891 between the
old and new rank tables). The old top five was C, G/N, L, E, B and the new one
is L, C, G/N, H/E, E. Ward C's score fell from 72.1 to 63.5 and it went from
first to second.

The cell set did not change, but it needed a fix to stay the same. Six cells
with zero WorldPop population had been leaving the index by accident, because
the elderly share is undefined at zero population and stage 04 drops any cell
with a missing indicator. Four of the six have negative NDVI, which fits open
water or bare coast. With the share gone they would have entered the index at
zero density, so stage 04 now excludes zero-population cells explicitly, and
says so in its output. The count stays 541.

### 10c. `child_pct`: real ward-level Census data, and why it moves so little

`pipeline/build_census_table.py`, table `data/census2011_ward_age_mumbai.csv`.

Since the Census has no ward-level 60+ figure, the age-structure signal that does
exist at ward resolution is the 0 to 6 share. It is in the index as one of the
seven indicators, named for what it measures: young children, not the elderly.

Census wards are smaller than BMC wards. 97 of them roll up into the 24, using
the mapping OpenCity publishes. The build refuses to write a table unless the
two source files agree on every Census ward's population, every ward is
accounted for, and the total equals the Census's own figure for Greater Mumbai,
12,442,373. It does, exactly.

| | `elderly_pct` (removed, 10a) | `child_pct` |
|---|---|---|
| Distinct values across 24 wards | 2 | 24 |
| Range | 4.76 to 5.59 by district | 6.75% to 13.09% |
| Resolution | district | ward |
| Vintage | WorldPop 2020 (from the 2011 Census) | 2011 |
| Share of ward-score contribution | 13.6% | 2.5% |

Its PCA weight is 0.027 and its PC1 loading 0.068.

**It changes the ranking very little, and that is a finding.** PCA weights an
indicator by how much variance it shares with the others. Child share is nearly
uncorrelated with them (at most 0.22 in absolute value at cell level), so PC1
barely loads on it. Adding it to the other six lowers PC1's explained variance
from 65.7% to 56.5%.

So the index uses real data for every ward, and it is not much better informed
for it. Those are different achievements, and only the first is claimed.

It matters much more under equal weighting, where it gets 14.3% (section 5).
That gap is nearly all of the disagreement between the two weighting schemes.

The value is assigned flat to every cell in a ward, because the Census gives
nothing finer. A city without a ward-level table runs on the six required
indicators instead of failing.

### 10d. With the plantability filter corrected, tree planting fires nowhere

After the 10b correction the tree-planting recommendation fires for no cell in
Mumbai. It fired for 12 ward-level rows before, all on cells that should have
been refused.

The reason is in the data. 75 cells are both hot (HVI at or above the 75th
percentile) and bare (NDVI at or below the 25th). All 75 are built-up
(WorldCover class 50) with a median impervious share of 78.4% against a
plantable ceiling of 68.4%. The ward-level recommendation rows went from 81 to
70 with the correction, and to 61 when the cooling-centre rule left with the
elderly share (10a): 24 rain-garden, 19 cool-roof and 18 pocket-park. Every
ward still has at least one.

The caveat matters. Each cell takes the most common WorldCover class inside it,
and a cell that is mostly built-up can still contain green pockets. This is a
statement about whole 1 km cells, not about whether Mumbai has anywhere to plant
a tree.
