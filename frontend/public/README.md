# UCIP public assets

Brand mark: a grid-built leaf (ovate silhouette, single vertical vein, short stem), for
nature-based urban cooling intelligence. Teal `#0EA5B3`, Emerald `#22C55E`, Charcoal `#111827`,
Off-white `#FAFAFA`. Teal/emerald/charcoal only, no other hues. Full provenance in
`brand/brand-notes.txt`.

## Logo and brand (root)

| File | Use |
|------|-----|
| `logo.svg` | Full-color gradient mark (light surfaces, 48px and up) |
| `logo-dark.svg` | Same mark, brightened for dark surfaces |
| `logo-mono.svg` | Flat charcoal, one-color contexts |
| `wordmark.svg` | Mark + "UCIP" horizontal lockup |
| `lockup.svg` | Stacked mark + wordmark + tagline |
| `og-image.png` | 1200x630 social card |

## Icons (root)

| File | Use |
|------|-----|
| `favicon.ico` | Multi-resolution favicon (16/32/48) |
| `icon-192.png`, `icon-512.png` | PWA / manifest icons |
| `apple-touch-icon.png` | 180x180 iOS home-screen icon |
| `site.webmanifest` | PWA manifest |

App-router also serves `src/app/{favicon.ico,icon.png,apple-icon.png}` automatically.

## brand/ (reference only, not shipped in the app)

Raster logo ladder (`logo-48..512`, `logo-dark-128/512`), `favicon-16/32`, `style-guide.png`,
and `brand-notes.txt` (the source brand sheet). For docs and large-format use.

## Data (fetched at runtime, do not rename)

`wards_hvi.geojson`, `cells_nbs.geojson`, `cells_ndvi_change.geojson`,
`nbs_recommendations.json`, `hvi_pca_log.json`, `sensitivity.json`, `sensitivity_chart.png`.

Full gradient mark (`logo.svg`/`logo-dark.svg`) is brand-restricted to 48px and up and is not
square (492x654). At nav/footer size, use `icon-192.png`/`icon-512.png` instead: a square,
padded export of the same mark that doesn't distort when boxed to a small square.
