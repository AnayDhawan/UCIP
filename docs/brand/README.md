# UCIP Brand Assets

Provenance: generated via a sequence of image prompts run through an external image-generation
tool (composite reference sheet, not individually-exported files), then cropped and adapted here.
Not hand-designed in this repo; see the source file for the original reference.

## Files

| File | What |
|------|------|
| `source-sheet.png` | Original composite reference sheet (all panels), keep for provenance |
| `icon-light.png` | Master logo panel, light background (includes reference label) |
| `icon-dark.png` | Dark-mode variant panel (includes reference label) |
| `icon-mono.png` | Monochrome variant panel (includes reference label) |
| `icon-glyph-square.png` | Tight square crop of the light icon, no label, favicon/icon.png source |
| `icon-glyph-square-dark.png` | Tight square crop of the dark-mode icon, no label |
| `icon-glyph-square-mono.png` | Tight square crop of the monochrome icon, no label |
| `icon-transparent.png` | `icon-glyph-square.png` with white background keyed to transparent, for in-app use (`frontend/public/logo-icon.png` is a copy of this) |
| `wordmark-horizontal.png` | Icon + "UCIP" wordmark, horizontal lockup |
| `lockup-vertical-tagline.png` | Icon + wordmark + "Urban Climate Intelligence Platform" tagline, stacked |
| `og-card-source.png` | Source banner for the Open Graph card (`frontend/public/og-image.png` is the adapted 1200x630 export) |
| `style-guide.png` | Palette + typography + clear-space reference sheet |

## Palette

| Name | Hex |
|------|-----|
| Teal | `#0EA5B3` |
| Emerald Green | `#22C55E` |
| Charcoal | `#111827` |
| White | `#FFFFFF` |

## Typography

Inter SemiBold for the wordmark.

## Notes for future work

- These are raster exports, not vector. If a true scalable SVG is ever needed (e.g. print
  materials at large sizes), it needs a manual vector rebuild, the grid-square leaf shape is
  simple geometry and reproducible exactly from `icon-glyph-square.png` if that's ever needed.
- Don't regenerate from scratch, extend from what's here.
