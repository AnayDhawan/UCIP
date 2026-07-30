/**
 * The HVI colour ramp, in one place.
 *
 * These six hexes are ColorBrewer YlOrRd and are semantic, not decorative:
 * DESIGN.md ("Data colors (semantic, DO NOT restyle)") locks them, and the map
 * legend, the ward list swatches, the landing page and the 3D hero model must
 * all agree exactly or the legend stops meaning anything. Previously duplicated
 * as `colorForHvi` in WardChoropleth.tsx and `hviBandColor` in WardPanel.tsx.
 */

/** Six-bin ColorBrewer YlOrRd ramp, coolest to hottest. */
export const HVI_COLORS = ["#ffffb2", "#fed976", "#feb24c", "#fd8d3c", "#f03b20", "#bd0026"] as const;

/** Rendered where a ward has no score. */
export const HVI_NO_DATA_COLOR = "#cccccc";

/** Upper bound of each bin, aligned 1:1 with HVI_COLORS. */
export const HVI_BIN_MAX = [20, 35, 50, 65, 80, Infinity] as const;

/** Bin an HVI score (0-100) to its ramp colour. Null scores get the no-data gray. */
export function hviColor(hvi: number | null | undefined): string {
  if (hvi === null || hvi === undefined || Number.isNaN(hvi)) return HVI_NO_DATA_COLOR;
  for (let i = 0; i < HVI_BIN_MAX.length; i++) {
    if (hvi < HVI_BIN_MAX[i]) return HVI_COLORS[i];
  }
  return HVI_COLORS[HVI_COLORS.length - 1];
}
