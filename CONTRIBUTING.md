# Contributing to UCIP

Thanks for looking at improving **UCIP**. By participating you agree to the
[Code of Conduct](./CODE_OF_CONDUCT.md).

## Quick setup

Frontend (Next.js):

```bash
git clone https://github.com/AnayDhawan/ucip.git
cd ucip/frontend
npm install
cp ../.env.example .env.local   # fill in Supabase keys if you need live data
npm run dev
```

Pipeline (Python, only needed if you're touching the data layer):

```bash
cd pipeline
python -m venv .venv
.venv\Scripts\activate      # .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
earthengine authenticate     # needs your own Google Earth Engine account
```

The pipeline scripts (`00`–`12`) require a Google Earth Engine project and Supabase
credentials to run end-to-end; the committed GeoJSON snapshots in `data/` let the frontend
run without either. Run the full chain in order with `python pipeline/run_pipeline.py`
rather than invoking each script by hand; see [pipeline/README.md](pipeline/README.md)
for usage, the monthly refresh cadence, and the post-refresh change-diff tool.

## How to contribute

### Reporting bugs

Open an issue using the [bug report template](.github/ISSUE_TEMPLATE/bug_report.yml).
Include steps to reproduce, expected vs actual behavior, and browser/OS.

### Requesting features

Open an issue using the [feature request template](.github/ISSUE_TEMPLATE/feature_request.yml).

### Submitting a PR

1. Fork the repo and create a branch: `git checkout -b feat/your-feature`.
2. Make your change.
3. Verify: `npm run lint && npm run build` (inside `frontend/`) — must pass clean. There's no
   test suite yet; a PR that adds one for a previously-untested area is welcome.
4. Open a PR against `main` using the template.

## Data and methodology changes

UCIP's whole pitch is that every number is computed and every claim is cited. If your PR
changes an HVI weight, an NBS rule, or a data source:

- Update `docs/methodology.md` and `docs/references.md` in the same PR, not a follow-up.
- Cite the paper or dataset (DOI where one exists) in `frontend/src/lib/citations.ts`.
- Don't hardcode a data vintage silently — see `pipeline/03_vectors.py`'s `WORLDPOP_YEAR`
  pin for the pattern (explicit, disclosed, not just "whatever the API returns first").

## Code style

- TypeScript/React: follow the existing ESLint config (`npm run lint`), Tailwind v4
  CSS-first tokens in `globals.css` — don't hand-roll new color values.
- Python: match the existing numbered-script style in `pipeline/` (`01_grid.py`,
  `02_gee_layers.py`, ...); each script does one pipeline stage and is runnable standalone.
- No em dashes in prose (docs, commit messages, UI copy).

## PR guidelines

- One PR per change — keep scope tight.
- PR description explains *why*, not just *what*.
- Map/legend colors (`WardChoropleth.tsx`'s HVI/plantability/NDVI-change palettes) are
  semantic and DO NOT get restyled for aesthetics — see `DESIGN.md`.
- AI-assisted code is welcome, provided you've reviewed and tested the output.

## Commit style

[Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add sensitivity-analysis chart to methodology page
fix: correct ward area lookup for split wards
docs: update citation DOI for cool-roof coefficient
```

Types: `feat | fix | docs | style | refactor | perf | test | ci | chore`
