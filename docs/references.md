# UCIP — Citation Table

Every variable, weight, and design choice cites a paper. DOIs to be verified during pre-sprint item #9.
Pitch discipline: **Veldman = "5x too large + don't afforest grasslands." Friedlingstein = "trees can't replace emission cuts."** Do NOT attribute the 5x number to Friedlingstein.

| Use | Paper | Cite / DOI | Verified? | What it justifies |
|-----|-------|-----------|-----------|-------------------|
| Motivation | IPCC AR6 WGII, urban chapter | — | ☐ | Why urban heat adaptation matters (motivation only) |
| Method (satellite heat) | Landsat/MODIS LST + NDVI urban-heat literature | — | ☐ | Use of LST/NDVI as heat + green-cover proxies |
| HVI weighting | Reid et al. 2009, *Environ. Health Perspect.* 117(11):1730-1736 | 10.1289/ehp.0900683 (confirm) | ☐ | PCA-derived HVI weights (data, not guesses) |
| HVI (India relevance) | Ahmedabad Heat Action Plan, 2013 | — (confirm citable form) | ☐ | Local credibility; first HAP in South Asia |
| Tree restoration potential | Bastin et al. 2019, *Science* 365(6448):76-79 | 10.1126/science.aax0848 | ☐ | ~0.9 Bha canopy potential; where trees CAN go |
| **Critique (key)** | Veldman et al. 2019, *Science* 366(6463):eaay7976 | 10.1126/science.aay7976 | ☐ | 205 GtC ~5x too large; don't afforest grasslands/savannas — powers the plantability filter |
| Critique (carbon cycle) | Friedlingstein et al. 2019, *Science* 366(6463):eaay8060 | 10.1126/science.aay8060 | ☐ | Estimate inconsistent w/ carbon-cycle dynamics; trees != substitute for cutting emissions |
| Critique (regrowth) | Lewis et al. 2019, *Science* 366(6463):eaaz0388 | 10.1126/science.aaz0388 | ☐ | Regrowth mostly replaces previously-lost carbon |
| Urban cooling (simulator/NBS coeff) | TBD — pick 1-2 (e.g. Ziter et al. 2019, *PNAS* 116(15):7575-7580) | 10.1073/pnas.1817561116 (confirm) | ☐ | Canopy % -> LST reduction coefficients (F8 + NBS impact) |
| Cool-roof cooling | TBD — pick 1 albedo/cool-roof paper | — | ☐ | Cool-roof albedo -> LST reduction coefficient |

## Data sources (all open)

| Variable | Source | Access | Note |
|----------|--------|--------|------|
| Land Surface Temp | Landsat 8/9 C2 L2 (USGS) | GEE | Dry-season composite |
| NDVI / green cover | Sentinel-2 or Landsat | GEE | Two dates for F6 |
| Population density | WorldPop / GHS-POP | GEE | |
| Elderly % | WorldPop age-sex structure | GEE | **PROXY** — stated in methodology |
| Slum index | GHS-SMOD + OSM | GEE / Overpass | **PROXY** — stated in methodology |
| Hospitals | OpenStreetMap | osmnx / Overpass | Nearest-hospital distance |
| Impervious / built-up | ESA WorldCover / GHSL | GEE | |
| Ward boundaries | Datameet / BMC / OSM | GeoJSON | 24 BMC wards |
