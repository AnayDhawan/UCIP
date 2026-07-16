# UCIP — Pre-Sprint TODO (Jul 11 → Aug 1)

Official sprint: **Aug 1–7, 2026**. **Pitch deck due Aug 5. Prototype submission Aug 8.** Event **Aug 8–9**.
Full plan + council verdict: EA plan file (`.claude/plans/i-m-building-ucip-heres-velvety-mist.md`) and `C:\Users\lenovo\EA\projects\ucip\README.md`.

## Machine-side (done by Claude, Jul 11)

- [x] Repo folder + git init at `C:\Users\lenovo\ucip` (NOT committed yet, per Anay)
- [x] Skeleton dirs: frontend / pipeline / supabase / data / docs
- [x] Root files: README, LICENSE (MIT), .gitignore, this TODO
- [x] `pipeline/requirements.txt` + venv + geospatial install (see smoke-test result below)
- [x] `pipeline/00_gee_spike.py` ready to run the moment GEE approval lands
- [x] Pipeline stubs 01–08 with docstrings
- [x] Next.js scaffold + leaflet/react-leaflet/supabase-js deps
- [x] docs/references.md + docs/methodology.md outlines

## Anay-side — Day 1 (latency-bound, do first)

- [x] **1. GEE account.** Registered (Individual research/noncommercial, Contributor tier, urban planning use case). Project `ucip-mum` API enabled 2026-07-12 (Cloud Console showed "Earth Engine API is not enabled" once, fixed via Manage → Enable).
- [x] **2. Python geospatial env test.** Fixed 2026-07-12 — earlier install got Ctrl+C'd mid-run. Reinstalled clean: `earthengine-api, geemap, geopandas, rasterio, shapely, scikit-learn, pandas, osmnx, matplotlib, supabase` all import OK in `pipeline/.venv`.
- [x] **3. GEE auth from Python.** 2026-07-12: `earthengine authenticate` → token saved. `python -c "import ee; ee.Initialize(project='ucip-mum'); print(ee.String('gee works').getInfo())"` → printed `gee works`. Live GEE confirmed end-to-end.
- [x] **4. Hackathon logistics.** Resolved 2026-07-16 from organizer material: **Aug 5 = pitch deck** with 6 required sections (01 overview/participant details incl. domain BODY/MACHINE/PLANET + focus area, 02 problem understanding, 03 research & insights, 04 proposed solution, 05 prototype/solution-design evidence: screenshots/mockups/working-model images, 06 impact & future scope). **Aug 8 = prototype submission** (event Aug 8-9). Deck text briefs pre-written at `docs/pitch-brief.md`. Still unconfirmed: post-deadline commit policy, AI-assistance rules — check at event registration.
- [x] **5. Supabase**: account + `ucip` project done — real URL/anon/service keys already in `.env.local`.
- [ ] **6. GitHub repo. Deferred to August.** Create `AnayDhawan/ucip` (public). Local commit exists (`616a4e1`) but no remote added yet:
  ```
  cd C:\Users\lenovo\ucip
  git remote add origin https://github.com/AnayDhawan/ucip.git
  git push -u origin main
  ```

## Anay-side — Day 2 (data + research)

- [x] **7. Ward boundaries.** Done 2026-07-12 → `data/bmc_wards.geojson`, from `datameet/Municipal_Spatial_Data` (Mumbai/BMC_Wards.geojson, not the `maps` repo). Validated: 24 features, all valid geometry, CRS EPSG:4326, bounds match Mumbai (72.78-72.98°E, 18.89-19.27°N), ward names are real BMC split-ward codes (F/N, F/S, G/N, G/S, H/E, H/W, K/E, K/W, M/E, M/W, P/N, P/S, R/C, R/N, R/S + A-E, L, N, S, T). Bonus: same folder has `slumClusters.geojson` — not downloaded yet, but worth pulling later for the slum-index proxy layer instead of GHS-SMOD.
- [x] **8. WorldPop access path.** Done 2026-07-12 → **live GEE, no fallback needed.** `WorldPop/GP/100m/pop_age_sex` has 1 India image, 37 age/sex bands, all 10 elderly brackets present (`M_60..M_80`, `F_60..F_80`). Queried over Mumbai bbox, returned plausible sums (e.g. `M_60` ≈ 235,534). Elderly-% proxy layer is unblocked.
- [x] **9. Prior-art scan.** Done 2026-07-12 → `docs/prior-art.md`. 6 closest tools (RAND/IIHS HVI, WRI India, C40 Cool Cities, IIT-B UHI studies, Ahmedabad HAP, MCAP 2022 heat chapter) + differentiation paragraph.
- [x] **10. Citation collection.** Done 2026-07-12 → `docs/references.md` updated. All 6 core DOIs verified live. Locked Ziter et al. 2019 PNAS for canopy cooling coefficients. Found a cool-roof candidate (Santamouris et al., IOP 2014) — DOI needs final confirm before sprint, flagged in the table.

## Optional, high-value

- [x] **GEE spike run early.** Done 2026-07-12 → **GO**. `pipeline/00_gee_spike.py`: 12 Landsat 8/9 scenes in dry-season window, mean LST 33.6°C, mean NDVI 0.305 — both within plausible urban range, sanity checks passed clean. Thumbnails written (`spike_lst.png`, `spike_ndvi.png`, in `pipeline/`, not committed). Live-GEE pipeline confirmed viable 20 days ahead of the Aug 1 M1 gate — no raster-fallback pivot needed.

## Sprint calendar (Aug 1–7)

| M | Date | Deliverable | Features |
|---|------|-------------|----------|
| M1 | Sat Aug 1 | Setup finalized. **GEE gate already cleared 2026-07-12 (GO)** — M1 becomes buffer/other-infra day | infra |
| M2 | Sun Aug 2 | Full data pipeline → Supabase + GeoJSON snapshot | data |
| M3 | Mon Aug 3 | HVI computed (PCA weights) + Leaflet choropleth. **Capture choropleth screenshot for deck** | F1 |
| M4 | Tue Aug 4 | Factor breakdown, NBS engine + plantability filter, ward rollup + cards. **Capture ward-card + NBS screenshots** | F2 F3 F4 F7 |
| M5 | Wed Aug 5 | 🔴 **PITCH DECK DUE**: assemble deck from `docs/pitch-brief.md` + captured screenshots. Also: Vercel deploy, methodology page, sensitivity chart, README | F5 + deck |
| M6 | Thu Aug 6 | NDVI change (F6), demo-safe static mode + video backup; F8/F9 only if green | F6 (+F8/F9) |
| M7 | Fri Aug 7 | 3-min narrative rehearsed, prototype hardening, deploy freeze | packaging |
| M8 | Sat Aug 8 | 🔴 **PROTOTYPE SUBMISSION** (event day 1) | ship |

**Cut order if late:** F9 → F8 → F6. Never cut F1–F5 or the Aug 5 deck. GEE pivot decision at M1, never later.
**Deck rule:** screenshots for section 05 come from M3/M4 output — anything not built by Aug 4 evening cannot be in the deck; the brief's section-05 checklist is the shot list.
