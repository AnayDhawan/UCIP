# UCIP — Pitch Deck Text Briefs

Deck due **Aug 5** (organizer requirement, confirmed 2026-07-16). Prototype submission **Aug 8**.
One brief per required section (organizer's 6-block structure). Text is deck-ready: copy each
block into a slide, trim to taste. Section 05 screenshots get captured Aug 3-5 during the sprint.

---

## 01 — Project Overview & Participant Details

- **Project title:** UCIP — Urban Climate Intelligence Platform
- **Student name:** Anay Dhawan
- **School name:** [fill in]
- **Grade:** 11 (IBDP Year 1)
- **Selected domain:** PLANET
- **Focus area:** Urban heat resilience / climate adaptation decision-support

One-liner (use as the slide subtitle):
> A decision-support tool that tells Mumbai's city planners which of the 24 BMC wards to cool
> first, why, with what intervention, and where a fixed budget goes.

---

## 02 — Problem Understanding

**What problem are you solving?**
Mumbai is heating unevenly. Heat pockets form over slums, barren land, and impervious concrete,
but the city has no ward-level, evidence-based way to decide *where* to invest cooling
infrastructure first. Current plans set city-wide goals without per-ward targeting.

**Who is affected?**
The most heat-vulnerable residents: slum households (heat-trapping roofs, low cooling access),
the elderly, and wards far from hospitals. Vulnerability is highest exactly where data is
scarcest.

**Why does this problem matter?**
Heat is India's deadliest weather hazard, and Ahmedabad's Heat Action Plan proved targeted city
action saves roughly 1,190 lives a year (Knowlton et al. 2014). Mumbai's own climate plan (MCAP
2022) names heat as a priority pillar but stops at city-level strategy: goals without a
reproducible method for choosing which ward gets cooled first.

**Where does this problem exist?**
Every dense tropical city; UCIP scopes it tightly to Mumbai's 24 BMC wards, where IIT Bombay
remote-sensing studies already show strong surface urban-heat-island effects over informal
housing (Mehrotra, Bardhan & Ramamritham 2018).

---

## 03 — Research & Insights

**Data, facts, observations:**
- Live satellite pipeline over Mumbai (Google Earth Engine): 12 Landsat 8/9 dry-season scenes,
  mean land-surface temperature 33.6 °C, mean NDVI 0.305 — computed, not copied.
- WorldPop age-sex rasters give elderly population per ward (e.g. ~235,000 men aged 60+ across
  the metro bbox); OSM gives hospital locations; GHS-SMOD/OSM proxy the slum index.
- Tree canopy cooling is nonlinear: below ~40% canopy, daytime cooling is negligible; 40→80%
  gives ≈1 °C (Ziter et al. 2019, PNAS). Cool roofs cut peak temperature ~0.6 K per +0.1 albedo,
  conservative end of the published range (Santamouris 2014).

**Existing solutions explored (5 closest):**
1. Mumbai Climate Action Plan 2022 — strategy document, no per-ward ranking method
2. RAND / Azhar et al. 2017 India HVI — district-level (640 districts), too coarse for one city;
   maps vulnerability then stops
3. IIT Bombay Mumbai UHI studies — rigorous heat maps, but diagnostic only
4. C40 Urban Cooling Toolbox — real decision-support, but global/generic, no Mumbai data under it
5. Ahmedabad Heat Action Plan — temporal early-warning (when heat strikes), not spatial
   investment targeting (where to build)

**Gaps / limitations discovered:**
Every prior tool does at most two of five things: ward-level ranking, per-factor explainability,
an intervention engine, an ecological guardrail, a budget layer. None does all five. Also: most
tools overstate certainty; none openly discloses proxy-data limitations.

---

## 04 — Proposed Solution

**The idea:**
UCIP computes a Heat Vulnerability Index (HVI) for each of Mumbai's 24 wards from satellite +
demographic data, with PCA-derived weights following the peer-reviewed Reid et al. 2009
methodology (data-driven, not guessed). Every ward gets a transparent per-factor breakdown
(no black box), and the index is sensitivity-tested (weights perturbed ±20% to show the ranking
holds).

**How it solves the problem:**
The index feeds a rule-based Nature-Based-Solutions engine where every recommendation carries a
citation, gated by an ecological plantability filter: native afforestation only where restoration
is appropriate (Bastin et al. 2019), blocked over native grasslands where planting would backfire
(Veldman et al. 2019), routing those areas to cool roofs instead. Recommendations roll up into
ward cards and a budget-constrained allocation a planner can act on. Not another "plant trees
everywhere" map.

**Who benefits:**
- BMC planners: a defensible, explainable priority list instead of intuition
- Vulnerable residents: cooling investment lands in the highest-need wards first
- Researchers/NGOs: open methodology, open data sources, stated limitations

---

## 05 — Prototype / Solution Design (evidence to capture Aug 3-5)

Screenshot checklist for this slide (capture during sprint, in this order):
- [ ] Leaflet choropleth of the 24-ward HVI ranking (M3, Aug 3)
- [ ] Ward card: rank, per-factor contribution bars, recommended intervention (M4, Aug 4)
- [ ] NBS engine output with plantability filter visibly blocking a grassland cell (M4)
- [ ] Sensitivity chart: ranking stability under ±20% weight perturbation (M5, Aug 5)
- [ ] Methodology page: citations table + limitations section (M5)
- [ ] Pipeline evidence: GEE spike thumbnails (spike_lst.png / spike_ndvi.png — already exist)
- [ ] Architecture diagram: GEE → Python pipeline → Supabase/PostGIS → Next.js + Leaflet

Stack line for the slide: Google Earth Engine (Landsat 8/9, WorldPop, WorldCover) → Python
(geopandas, scikit-learn PCA) → Supabase + PostGIS → Next.js + Leaflet, deployed on Vercel.

---

## 06 — Impact & Future Scope

**Expected impact:**
Turns Mumbai's existing heat diagnosis into an operational bridge: which ward first, why, what
intervention, at what cost. Methodology is reproducible for any Indian city with the same open
data (all sources are free: Landsat, WorldPop, OSM, GHSL). Honesty layer builds trust: proxy
data disclosed, LST ≠ air temperature stated, coefficients marked as transferred, not
Mumbai-calibrated.

**How it can be improved / expanded:**
- Finer grid (1 km → 500 m) and Census-linked demographic data when accessible
- NDVI change detection over time to verify interventions actually green the ward (P1, partly in
  scope for Aug 6)
- What-if simulator: slide canopy % / cool-roof fraction, watch predicted LST fall (stretch)
- Budget optimizer: maximize vulnerability-reduction per rupee across wards (stretch)
- Replication kit: config-driven port to Pune, Ahmedabad, Delhi wards
