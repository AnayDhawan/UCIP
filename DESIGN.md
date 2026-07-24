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
Physical scene: desktop use, either theme, in whatever ambient light the user's own room has;
this is not a mobile product (see PRODUCT.md), so "checked on a phone outdoors" is not the
governing scenario. Light stays the default because it reads as the more neutral/credible choice
for a civic tool, not because of a specific outdoor-glare use case.

## Brand assets

Full inventory and usage rules live in `frontend/public/README.md` (the authoritative source,
generated from the current vector brand kit). Summary:

- `frontend/public/logo.svg` / `logo-dark.svg`: full gradient mark, 492x654 (not square), 48px+
  only.
- `frontend/public/icon-192.png` / `icon-512.png`: square, safely-padded exports of the same mark.
  Use these (not `logo.svg`) anywhere the mark needs to sit in a small square box (nav, footer) —
  the raw mark's aspect ratio distorts if forced square below 48px.
- `frontend/src/app/{favicon.ico,icon.png,apple-icon.png}`: regenerated from `icon-512.png` (not
  from a "logo-small" variant; that asset was retired).
- `frontend/public/og-image.png`, `site.webmanifest`.

## Components inventory

- `Logo.tsx`: icon (`icon-192.png`) + "UCIP" text lockup, used in every header/footer.
- `HeroGradient.tsx`: animated teal/emerald mesh gradient (@paper-design/shaders-react) for the
  landing hero only. Respects `prefers-reduced-motion` and no-WebGL by falling back to a static CSS
  gradient; SSR-safe via `useSyncExternalStore`, no dynamic-import wrapper needed.
- `WardChoropleth.tsx`: Leaflet map, 3-layer switcher (shadcn Tabs), CartoDB Positron tiles,
  click-to-select with a teal selection outline, `fitBounds()` to the ward extent on first load,
  fullscreen mode (hides site chrome, keeps the layer box + legend + exit button, Escape to close),
  and a Leaflet popup shown only in fullscreen (ward summary + top cited intervention + year) since
  fullscreen hides the sidebar detail panel that would otherwise show it.
- `WardPanel.tsx` (replaces the old `WardCards.tsx`): master-detail sidebar, not 24 stacked cards.
  Default view is a compact searchable ranked list (search matches ward code or locality name, via
  `lib/wardAreas.ts`); selecting a ward (list or map) shows a single rich detail panel. Selection is
  synced through the URL (`?ward=`) via `dashboard/page.tsx`'s `useSearchParams`, not local state
  alone, so browser Back steps back through selections instead of leaving the dashboard.
- `Citation.tsx`, `lib/citations.ts`: single source of truth for all citations (from
  `docs/references.md`), three render modes (chip/full/marker) reused across methodology, the
  landing citation wall, and ward-card recommendations.
- `src/components/ui/*`: shadcn/ui primitives (Tabs, Card, Badge, Input, Button, ScrollArea),
  scoped to the dashboard's chrome. **Gotcha:** re-running `npx shadcn add` regenerates
  `globals.css` with shadcn's own generic gray token scheme, overwriting the brand OKLCH tokens
  above (including `--background` going pure white, breaking the never-pure-white rule) and can
  reintroduce Geist as a font import. Always diff and reconcile `globals.css`/`layout.tsx` after.
- Layout gotchas (documented, do not regress): map wrapper needs `absolute inset-0` inside
  `position:relative` parent; page root needs a hard `h-screen` anchor; raw OSM tile server is
  blocked, use CartoDB; Leaflet doesn't notice layout-driven container resizes (e.g. fullscreen
  toggle) without an explicit `map.invalidateSize()` call; don't put `selectedWardId` in a
  `<GeoJSON key={...}>` — remounting the layer on every ward click destroys any popup Leaflet was
  mid-way through opening on that same click, use a `ref` + `.setStyle()` for selection restyling
  instead and reserve `key` for changes that genuinely need `onEachFeature` to rebind (like
  fullscreen toggling, which needs popups bound only in fullscreen).

## Banned (per impeccable + this repo)

Side-stripe borders, gradient text, glassmorphism-by-default, hero-metric template, identical
card grids, modal-first flows, em dashes in copy.
