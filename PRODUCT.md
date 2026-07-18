# PRODUCT.md — UCIP

## What this is

UCIP (Urban Climate Intelligence Platform) is a decision-support tool for Mumbai's urban heat
problem. It computes a Heat Vulnerability Index (HVI) for each of the 24 BMC wards from satellite
and demographic data, explains every score with a transparent per-factor breakdown, and recommends
cited nature-based cooling interventions gated by an ecological plantability filter. Built solo for
the TIS x IHFC "Now or Never Hack 2026" (Domain: PLANET); prototype submission Aug 8, 2026.

## Users, in priority order

1. **Curious residents of Mumbai (general public).** No GIS background, no climate literacy
   assumed. They want to know: is my ward at risk, what does this map mean, who made this. They
   arrive at the landing page, not the dashboard.
2. **City planners / BMC-adjacent professionals.** Comfortable with dashboards. Want the ranked
   ward list, the intervention recommendations, and the reasoning behind them.
3. **Researcher judges (hackathon).** Evaluate methodology rigor: PCA weights, sensitivity check,
   citations, stated limitations. They read /methodology closely.

## Register

- **Brand register:** landing page `/`, `/support`, `/contact`, `/legal`. Design carries identity.
- **Product register:** `/dashboard` and `/methodology`. Design serves the data; clarity beats
  flair. The map's data colors (HVI ramp, plantability, NDVI change) are semantic and untouchable.

## Tone

Credible, plain-language, direct. A trustworthy civic tool, not a consumer eco-app. Numbers are
real (computed by the pipeline, never invented); when something is a proxy or a limitation, it is
said openly. That honesty is a product feature, judges and residents both get the same candor.

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
