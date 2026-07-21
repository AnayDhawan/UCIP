# UCIP — Citation Table

Every variable, weight, and design choice cites a paper. DOIs verified 2026-07-12 (pre-sprint item #9) — all ✅ rows resolve to the stated paper.
Pitch discipline: **Veldman = "5x too large + don't afforest grasslands." Friedlingstein = "trees can't replace emission cuts."** Do NOT attribute the 5x number to Friedlingstein.

| Use | Paper | Cite / DOI | Verified? | What it justifies |
|-----|-------|-----------|-----------|-------------------|
| Motivation | IPCC AR6 WGII, urban chapter | — | ☐ (not needed for launch — general motivation only) | Why urban heat adaptation matters (motivation only) |
| Method (satellite heat) | Landsat/MODIS LST + NDVI urban-heat literature | — | ☐ (implicit via GEE dataset docs, no single paper needed) | Use of LST/NDVI as heat + green-cover proxies |
| HVI weighting | Reid et al. 2009, *Environ. Health Perspect.* 117(11):1730-1736 | 10.1289/ehp.0900683 | ✅ verified — resolves at ehp.niehs.nih.gov | PCA-derived HVI weights (data, not guesses) |
| HVI (India relevance) | Ahmedabad Heat Action Plan 2013; peer-reviewed writeup Knowlton et al. 2014, *IJERPH* 11(4):3473-3492 | 10.3390/ijerph110403473 | ✅ verified 2026-07-12 — Knowlton 2014 DOI resolves; cite the paper for a DOI, the plan as institutional report | Local credibility; first HAP in South Asia |
| HVI (India, quantitative) | Azhar et al. 2017 (RAND India HVI), *IJERPH* 14(4):357 | 10.3390/ijerph14040357 | ✅ verified 2026-07-12 (RAND brief RB-9974) | India-wide district HVI precedent; UCIP goes ward-level (see prior-art.md) |
| Tree restoration potential | Bastin et al. 2019, *Science* 365(6448):76-79 | 10.1126/science.aax0848 | ✅ verified — science.org/doi/10.1126/science.aax0848 | ~0.9 Bha canopy potential; where trees CAN go |
| **Critique (key)** | Veldman et al. 2019, *Science* 366(6463):eaay7976 | 10.1126/science.aay7976 | ✅ verified — science.org/doi/10.1126/science.aay7976 | 205 GtC ~5x too large; don't afforest grasslands/savannas — powers the plantability filter |
| Critique (carbon cycle) | Friedlingstein et al. 2019, *Science* 366(6463):eaay8060 | 10.1126/science.aay8060 | ✅ verified (companion comment, same issue as Veldman/Lewis) | Estimate inconsistent w/ carbon-cycle dynamics; trees != substitute for cutting emissions |
| Critique (regrowth) | Lewis et al. 2019, *Science* 366(6463):eaaz0388 | 10.1126/science.aaz0388 | ✅ verified (companion comment, same issue) | Regrowth mostly replaces previously-lost carbon |
| Urban cooling (simulator/NBS coeff) | **Locked in:** Ziter et al. 2019, *PNAS* 116(15):7575-7580, "Scale-dependent interactions between tree canopy cover and impervious surfaces reduce daytime urban heat during summer" | 10.1073/pnas.1817561116 | ✅ verified — pnas.org/doi/10.1073/pnas.1817561116 | Canopy % -> LST reduction coefficients (F8 + NBS impact) |
| Cool-roof effectiveness | Li, Bou-Zeid & Oppenheimer 2014, *Environ. Res. Lett.* 9(5):055002, "The effectiveness of cool and green roofs as urban heat island mitigation strategies" | 10.1088/1748-9326/9/5/055002 | ✅ verified 2026-07-12 — **authorship corrected** (parallel session mis-listed as Santamouris; this DOI is Li et al., ADS 2014ERL....9e5002L). WRF+PUCM, Baltimore-DC; surface UHI drops near-linearly with cool-roof fraction | Cool-roof fraction -> UHI reduction (F8 + NBS impact) |
| Cool-roof coefficient | Santamouris 2014, *Solar Energy* 103:682-703, "Cooling the cities — a review of reflective and green roof mitigation technologies" | 10.1016/j.solener.2012.07.003 | ✅ verified 2026-07-12 | Albedo -> peak-temp coefficient (~0.6-2.3 K per +0.1 albedo) for the NBS impact numbers |
| Pocket-park coefficient | Bowler et al. 2010, *Landscape and Urban Planning* 97:147-155, "Urban greening to cool towns and cities: a systematic review of the empirical evidence" | 10.1016/j.landurbplan.2010.05.006 | ✅ verified 2026-07-21 — resolves via linkinghub.elsevier.com to S0169204610001234 | Park cool-island effect (~0.94°C avg daytime) for the simulator's pocket-park term |

## Cooling coefficients (numbers the NBS impact model / F8 simulator uses)

Both cited so the simulator's "illustrative first-order estimate" carries a source. State the limitation
openly (methodology §10): transferred from other cities, not Mumbai-calibrated.

- **Tree canopy (Ziter et al. 2019, PNAS):** cooling is nonlinear. Canopy below ~40% within a 60-90 m
  radius gives negligible daytime air-temp change; raising cover from 40% to 80% delivers ≈1 °C of
  daytime cooling. Use the ~40% threshold as the plantability-benefit gate in the NBS engine.
- **Cool roofs / high albedo (Santamouris 2014, Solar Energy):** peak ambient temperature falls roughly
  0.57-2.3 K per 0.1 increase in surface albedo (city-scale review range). Use the conservative end
  (~0.6 K per +0.1 albedo) for headline claims and state the full range for the sensitivity chart.
- **Cool-roof city-scale sim (Li, Bou-Zeid & Oppenheimer 2014, ERL):** surface and near-surface UHI
  fall almost linearly as cool-roof fraction rises (WRF+PUCM). Supports a linear cool-roof term in F8.
- **Pocket parks (Bowler et al. 2010, Landscape and Urban Planning):** meta-analysis of park-vs-
  surroundings studies finds parks average ~0.94 °C cooler in the day (the "park cool island"
  effect). The paper doesn't model ward-wide coverage, so the simulator scales this ceiling
  linearly by the share of ward area converted to park — an explicit simplifying assumption, not
  a result from the paper itself.

## Data sources (all open)

| Variable | Source | Access | Note |
|----------|--------|--------|------|
| Land Surface Temp | Landsat 8/9 C2 L2 (USGS) | GEE | Dry-season composite |
| NDVI / green cover | Sentinel-2 or Landsat | GEE | Two dates for F6 |
| Population density | WorldPop / GHS-POP | GEE | |
| Elderly % | WorldPop age-sex structure, 2020 (pinned in `03_vectors.py`; most recent year available for India) | GEE | **PROXY** — stated in methodology |
| Slum index | Datameet `slumClusters.geojson` (mapped cluster boundaries) | `data/slumClusters.geojson` | **PROXY** — stated in methodology |
| Hospitals | OpenStreetMap | osmnx / Overpass | Nearest-hospital distance |
| Impervious / built-up | ESA WorldCover / GHSL | GEE | |
| Ward boundaries | Datameet (`Municipal_Spatial_Data/Mumbai/BMC_Wards.geojson`) | `data/bmc_wards.geojson` | ✅ downloaded + validated 2026-07-12: 24 features, EPSG:4326, valid geometry |
