# UCIP — Prior Art Scan

Pre-sprint item #8. Citation-ready; feeds the pitch deck "originality" slide and methodology §2.
Five closest prior tools/studies (one paragraph each), then how UCIP differs. Grounded in the locked
decisions (EA `projects/ucip/README.md`): ward-level HVI + PCA weights cited to Reid 2009 + NBS engine
+ ecological plantability filter + methodology transparency + budget layer.

## Closest prior tools/studies

**1. Mumbai Climate Action Plan 2022 (MCAP) — the one judges likely already know**
Launched March 2022 by the Brihanmumbai Municipal Corporation with WRI India and C40 Cities, MCAP is
Mumbai's first comprehensive climate roadmap. Its heat and "Urban Greening & Biodiversity" pillars
carry a heat-risk assessment and set city-wide targets (raise per-capita open space from 1.8 m² to
6 m², a tree-banking system, streetside-landscape and cool-material guidelines) and name a few
vulnerable wards qualitatively. It is the policy backdrop a domain judge will measure UCIP against. But
it is a strategy document producing city- and zone-level framing, not a reproducible per-ward ranking
methodology, not a per-factor explainability breakdown, and not an interactive tool that says "cool
this ward first, with this intervention, for this budget."
*(BMC, WRI India & C40 Cities, Mumbai Climate Action Plan 2022; mcap.mcgm.gov.in.)*

**2. RAND / Azhar et al. 2017 — India-wide district-level Heat Vulnerability Index**
The flagship quantitative Indian HVI and the closest methodological precedent. RAND researchers built
the first India-wide HVI: a standardized composite over all 640 districts from demographic, social,
economic, health, and environmental indicators, classifying districts by heat-wave vulnerability
(10 very-high, 97 high). This is exactly UCIP's index-construction lineage, and it legitimizes the
approach in India. Its two gaps are the openings UCIP takes: resolution (national/district, far too
coarse to guide intervention inside one city — UCIP works at 24 BMC wards on a 1 km grid), and scope
(it maps vulnerability and stops; no intervention engine, no ecological guardrail, no budget layer).
The surrounding Indian HVI literature reinforces the same gap: Rathi et al. (2021) built a four-city
HVI from household surveys (not remote sensing, not spatially continuous), and IIHS (Singh et al.,
2024) reviewed ten Indian Heat Action Plans and found them largely incremental and weakly targeted at
the most vulnerable, rarely converting identified vulnerability into targeted ward-level action.
*(Azhar et al., IJERPH 14(4):357, 2017, DOI 10.3390/ijerph14040357; RAND RB-9974. Rathi et al., IJERPH
19(1):283, 2021, DOI 10.3390/ijerph19010283. Singh et al., PLOS Climate, 2024, DOI 10.1371/journal.pclm.0000484.)*

**3. IIT Bombay Mumbai surface-urban-heat-island studies (Mehrotra, Bardhan & Ramamritham 2018)**
The closest work on both data and geography. IIT-B's Centre for Studies in Resources Engineering
mapped Mumbai's land-surface-temperature / land-use relationship (2015), finding heat pockets over
barren land, slums, salt pans, and impervious concrete; Mehrotra, Bardhan & Ramamritham (2018)
quantified surface-UHI intensity specifically over Mumbai's informal housing. This is rigorous,
Mumbai-specific remote sensing using exactly the LST/land-cover signals UCIP consumes. But it is
diagnostic: it maps where the city is hot and links that to land cover, then stops at the map. There is
no multi-indicator vulnerability weighting, no per-ward explainability, no intervention-recommendation
engine, no ecological plantability constraint, and no budget layer.
*(Mehrotra, Bardhan & Ramamritham, Environment and Urbanization ASIA 9(2), 2018, DOI 10.1177/0975425318783548.)*

**4. C40 Urban Cooling Toolbox & Heat Resilient Cities Tool (C40 / Ramboll, 2021)**
The closest work on the intervention / decision-support axis. C40's Urban Cooling Toolbox is a
card-based library of cooling measures for planners, and its Heat Resilient Cities Tool estimates the
environmental, health, and economic benefits of interventions (green corridors, parks, water features)
so cities can prioritize and communicate them. This is genuine decision-support, not just mapping, and
it shares UCIP's intent of turning heat into action. But it is global and generic: the toolbox inspires
rather than resolves, the benefit tool runs at city/project scale on user-entered scenarios, it is not
wired to a specific city's ward-resolved vulnerability data, and it applies no ecological plantability
filter to reject unsuitable greening.
*(C40 Cities & Ramboll, Urban Cooling Toolbox, 2021.)*

**5. Ahmedabad Heat Action Plan (Knowlton et al. 2014) — the canonical Indian HAP**
Ahmedabad launched South Asia's first Heat Action Plan in 2013 after the deadly 2010 heatwave; it is
credited with averting roughly 1,190 deaths a year and is the template every later Indian HAP (Mumbai's
included) copies. It proves the life-saving value of city-scale heat action, and UCIP borrows that
credibility. But its axis is temporal and reactive: a color-coded early-warning system, driven by a
7-day forecast, that triggers health-system and public-response protocols on the days heat strikes. It
does not spatially prioritize structural, built-environment investment within a city, and it carries no
vulnerability-weighted map or green-infrastructure targeting engine.
*(Knowlton et al., IJERPH 11(4):3473–3492, 2014, DOI 10.3390/ijerph110403473.)*

## How UCIP differs

Every prior tool found does at most two of five things: (a) a quantitative ward-level vulnerability
ranking, (b) transparent per-factor explainability, (c) an intervention / NBS recommendation engine,
(d) an ecological guardrail on that engine, and (e) a budget-constrained allocation layer. UCIP is the
only one attempting all five in a single interactive tool, scoped tightly to Mumbai's 24 BMC wards.
It computes a literature-cited, **PCA-weighted HVI (Reid et al. 2009)** — data, not guesses, with a
published-weight fallback if loadings are unstable — and exposes it through **per-factor contribution
bars** (a transparent linear index, so no black-box SHAP is needed) that are **sensitivity-tested**
(weights perturbed ±20% to show ranking stability). That index feeds a **rule-based NBS engine** in
which every recommendation carries its own citation, and the engine is **ecologically gated**: native
afforestation only where restoration is appropriate (Bastin et al. 2019), blocked over native
grasslands and savannas where the Veldman / Friedlingstein / Lewis 2019 critiques show it would be
counterproductive — routing those areas to cool roofs and reflective surfaces instead. It is not
another blanket "plant trees everywhere" tool. Recommendations roll up into **ward cards and a
budget-constrained allocation** a planner can act on. The honesty layer is also unusual among city
heat tools, most of which present outputs as more certain than their inputs: UCIP states its
limitations openly (proxy slum/elderly data disclosed, LST ≠ air temperature, cooling coefficients
transferred not Mumbai-calibrated). The result is the operational bridge between the diagnostic
remote-sensing studies (IIT-B: a heatmap), the strategy documents (MCAP: goals without per-ward
targeting), the assessment-only indices (RAND/Rathi/IIHS: vulnerability identified, not converted to
intervention), and the generic global toolboxes (C40: decision-support with no Mumbai data underneath).
Not another heatmap, not a static vulnerability assessment, not a generic toolbox.

## Sources
- Mumbai Climate Action Plan 2022: https://mcap.mcgm.gov.in/ ; WRI India: https://wri-india.org/initiatives/mumbai-climate-action-plan-mcap
- RAND India HVI (RB-9974): https://www.rand.org/pubs/research_briefs/RB9974.html ; Azhar et al. 2017: https://doi.org/10.3390/ijerph14040357
- Rathi et al. 2021 (four-city HVI): https://doi.org/10.3390/ijerph19010283
- IIHS / Singh et al. 2024 (ten HAPs governance): https://doi.org/10.1371/journal.pclm.0000484
- IIT-B Mehrotra, Bardhan & Ramamritham 2018: https://doi.org/10.1177/0975425318783548
- C40 Urban Cooling Toolbox 2021: https://www.c40.org/networks/cool-cities-network/
- Ahmedabad HAP / Knowlton et al. 2014: https://doi.org/10.3390/ijerph110403473
- Reid et al. 2009 (HVI methodology UCIP builds on): https://doi.org/10.1289/ehp.0900683
