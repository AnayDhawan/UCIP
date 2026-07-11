# UCIP — Pre-Sprint TODO (Jul 11 → Aug 1)

Official sprint: **Aug 1–7, 2026**. Submission gate **Aug 5**. Event **Aug 8–9**.
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

- [ ] **1. GEE account (~20 min). THE critical one.**
  - `code.earthengine.google.com/register` → Unpaid usage (Academia & Research)
  - Create/link Google Cloud project, e.g. `ucip-mumbai`
  - Success check: GEE Code Editor opens without "unauthorized"
  - Not approved by Aug 1 → M1 starts on pre-downloaded-raster fallback
- [ ] **2. GEE auth from Python (~10 min, after approval).**
  - `pipeline\.venv\Scripts\activate` → `earthengine authenticate`
  - Then: `python -c "import ee; ee.Initialize(project='ucip-mumbai'); print(ee.String('gee works').getInfo())"`
- [ ] **3. Hackathon logistics (~15 min).** What exactly is due Aug 5? Post-deadline commits allowed? AI-assistance rules? Solo entries OK?
- [ ] **4. Supabase**: account + empty `ucip` project (free tier); note project ref + anon/service keys (put in `.env`, never commit).
- [ ] **5. GitHub repo**: create `AnayDhawan/ucip` (public). Then:
  ```
  cd C:\Users\lenovo\ucip
  git remote add origin https://github.com/AnayDhawan/ucip.git
  ```
  (First commit + push whenever you say go.)

## Anay-side — Day 2 (data + research)

- [ ] **6. Ward boundaries (~30 min).** BMC 24-ward GeoJSON: primary Datameet (`github.com/datameet/maps`), fallback BMC portal / OSM. Validate on geojson.io: 24 features, ward codes A–T. Save into `data/`.
- [ ] **7. WorldPop access path (~15 min, needs GEE).** Confirm `WorldPop/GP/100m/pop_age_sex` India assets load in GEE Code Editor (elderly % source). Fallback: direct worldpop.org downloads.
- [ ] **8. Prior-art scan (~2h). Judged-axis derisk.** IIHS heat vulnerability, WRI India urban heat, C40 cool-cities tools, IIT Bombay Mumbai UHI studies, Ahmedabad Heat Action Plan, **Mumbai Climate Action Plan 2022 (heat chapter — judges may know it)**. Deliverable: 3–5 closest prior tools + one paragraph "how UCIP differs" → goes into pitch + methodology.
- [ ] **9. Citation collection (~1–1.5h).** Verify DOIs in `docs/references.md`; pick 1–2 urban-canopy cooling-coefficient papers (e.g. Ziter et al. 2019 PNAS) for NBS impact numbers.

## Optional, high-value

- [ ] If GEE approval lands early: run `pipeline/00_gee_spike.py` in July. Moves the go/no-go gate 2 weeks ahead of the sprint. Pure win.

## Sprint calendar (Aug 1–7)

| M | Date | Deliverable | Features |
|---|------|-------------|----------|
| M1 | Sat Aug 1 | Setup finalized + **GEE gate**: one-ward spike, go/no-go tonight | infra |
| M2 | Sun Aug 2 | Full data pipeline → Supabase + GeoJSON snapshot | data |
| M3 | Mon Aug 3 | HVI computed (PCA weights) + Leaflet choropleth | F1 |
| M4 | Tue Aug 4 | Factor breakdown, NBS engine + plantability filter, ward rollup + cards | F2 F3 F4 F7 |
| M5 | Wed Aug 5 | 🔴 SUBMISSION: Vercel deploy, methodology page, sensitivity chart, README | F5 + ship |
| M6 | Thu Aug 6 | NDVI change (F6), demo-safe static mode + video backup; F8/F9 only if green | F6 (+F8/F9) |
| M7 | Fri Aug 7 | Pitch deck, 3-min narrative rehearsed, deploy freeze | packaging |

**Cut order if late:** F9 → F8 → F6. Never cut F1–F5. GEE pivot decision at M1, never later.
