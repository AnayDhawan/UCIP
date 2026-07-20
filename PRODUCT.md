# PRODUCT.md — UCIP

## What this is

UCIP (Urban Climate Intelligence Platform) is a decision-support tool for Mumbai's urban heat
problem. It computes a Heat Vulnerability Index (HVI) for each of the 24 BMC wards from satellite
and demographic data, explains every score with a transparent per-factor breakdown, and recommends
cited nature-based cooling interventions gated by an ecological plantability filter. Built solo as
an independent research prototype. Code is Apache License 2.0.

## Users, in priority order

1. **Curious residents of Mumbai (general public).** No GIS background, no climate literacy
   assumed. They want to know: is my ward at risk, what does this map mean, who made this. They
   arrive at the landing page, not the dashboard.
2. **City planners / BMC-adjacent professionals.** Comfortable with dashboards. Want the ranked
   ward list, the intervention recommendations, and the reasoning behind them.
3. **Researchers and domain reviewers.** Evaluate methodology rigor: PCA weights, sensitivity check,
   citations, stated limitations. They read /methodology closely.

## Register

- **Brand register:** `/`, `/mission`, `/contribute`, `/contact`, `/legal`. Design carries identity;
  the landing hero runs an animated teal/emerald mesh gradient (@paper-design/shaders-react) with
  real motion, a deliberate exception to the generic-SaaS anti-reference below on the visual-polish
  axis specifically (not the banned patterns, those still hold everywhere).
- **Product register:** `/dashboard`, `/methodology`, `/simulate`. Design serves the data; clarity
  beats flair. The map's data colors (HVI ramp, plantability, NDVI change) are semantic and
  untouchable. The dashboard is master-detail: a compact searchable 24-ward list drives a single
  rich detail panel, synced with map click-to-select and the URL (`?ward=`), not 24 stacked cards.
- **Desktop-only.** No responsive/mobile breakpoint work; the product is not meant to be used on a
  phone.

There is no `/support` page; it was a near-duplicate of `/contribute` and was removed.

## Tone

Credible, plain-language, direct. A trustworthy civic tool, not a consumer eco-app. Numbers are
real (computed by the pipeline, never invented); when something is a proxy or a limitation, it is
said openly. That honesty is a product feature, reviewers and residents both get the same candor.

## Anti-references

- Consumer climate-guilt apps (leafy pastel gradients, carbon-footprint cuteness).
- Generic SaaS dashboard templates (hero metric cards, purple gradients).
- Government portal clutter (dense link farms, seals, marquee banners).

## Strategic principles

- Every claim traceable: to a citation, a computed number, or an open limitation.
- One idea per screen. The dashboard answers "which ward, why, what to do." The landing page
  answers "what is this and why should I care."
- Never overstate: LST is not air temperature, proxies are named as proxies, the prototype is not
  an official BMC tool.

## Writing rules

- No em dashes anywhere (use commas, colons, periods, parentheses).
- No AI-assistance attribution in any user-facing content or commit.
- Sentences a non-expert can read aloud without stumbling.
