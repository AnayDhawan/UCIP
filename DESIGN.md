# DESIGN.md — UCIP

## Brand palette (from docs/brand/README.md, generated brand sheet)

| Role | Value | Notes |
|------|-------|-------|
| Teal (brand) | `#0EA5B3` | Gradient start of the grid-leaf mark |
| Emerald (brand) | `#22C55E` | Gradient end of the grid-leaf mark |
| Charcoal (ink) | `#111827` | Wordmark / dark ink, use instead of pure black |
| White (paper) | `#FFFFFF` | Reference only; surfaces tint toward brand hue, never pure #fff |

Neutrals: tint toward teal (OKLCH chroma ~0.005-0.01). Never `#000` or `#fff` as rendered surface
or text colors; charcoal `#111827` and near-white tinted paper stand in.

## Data colors (semantic, DO NOT restyle)

- **HVI choropleth (6 bins, ColorBrewer YlOrRd):** `#ffffb2 #fed976 #feb24c #fd8d3c #f03b20 #bd0026`,
  gray `#cccccc` for no-data. Defined in `frontend/src/app/components/WardChoropleth.tsx`.
- **Plantability:** plantable `#4ade80`, not-plantable `#f87171`.
- **Green-cover change:** gained `#4ade80`, stable `#d4d4d8`, lost `#f87171`, unknown `#e5e5e5`.
- Legend colors must match these exactly; they are the map's meaning.

## Typography

- UI: Inter (wired via `next/font` in layout.tsx), the brand-sheet face (SemiBold for headings /
  wordmark). Single body face, do not add a second.
- Mono (JetBrains Mono) for computed figures where separation from prose helps (HVI scores,
  weights, DOIs); matches the sibling studentsuite/portfolio ecosystem.
- Hierarchy by size + weight, scale ratio at least 1.25 between steps.

## Theme

Class-based dark mode (`.dark` on `<html>` via next-themes), three states: light, dark, system.
Physical scene: residents check this on phones outdoors in daylight (light default matters);
planners and judges on desktops, either mode. System default respects both.

## Brand assets

- `frontend/public/logo-icon.png`: transparent grid-leaf icon (in-app header use)
- `docs/brand/wordmark-horizontal.png`: icon + UCIP wordmark (README, large lockups)
- `docs/brand/lockup-vertical-tagline.png`: stacked lockup with tagline
- `frontend/public/og-image.png`: 1200x630 social card
- favicon/icon/apple-icon: served from `frontend/src/app/`

## Components inventory

- `Logo.tsx`: icon + "UCIP" text lockup, used in every header
- `WardChoropleth.tsx`: Leaflet map, 3-layer switcher, CartoDB Positron tiles
- `WardCards.tsx`: ranked 24-ward sidebar with contribution bars
- Layout gotchas (documented, do not regress): map wrapper needs `absolute inset-0` inside
  `position:relative` parent; page root needs a hard `h-screen` anchor; raw OSM tile server is
  blocked, use CartoDB.

## Banned (per impeccable + this repo)

Side-stripe borders, gradient text, glassmorphism-by-default, hero-metric template, identical
card grids, modal-first flows, em dashes in copy.
