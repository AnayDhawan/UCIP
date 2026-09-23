"""
Generates deck-assets/deck-global-lst-may2026.png: a world land-surface-temperature map
for May 2026, rendered in the UCIP deck's own colours.

This is deliberately the same physical quantity the Mumbai pipeline measures (MODIS/Landsat
land surface temperature), so the world panel on slide 3 and the ward choropleth later in
the deck are one measurement at two zoom levels. That is the reason this is generated here
rather than lifted from a published figure.

Accuracy notes, in the order they matter:
  1. QC-masked, not a plain mean. MOD11A2 ships QC_Day; low-confidence retrievals are
     dropped before compositing, otherwise cloud-edge pixels drag the composite.
  2. Nulls stay null. MODIS LST is land-only and genuinely gappy under persistent cloud.
     Missing pixels render as background, never as zero and never as a cold colour.
  3. Fixed colour scale (VMIN/VMAX below), not auto-scaled, so the legend means something
     and two runs are comparable.
  4. It is one month. May is northern spring, so a warm north and cool south is correct
     for May and misleading if read as an annual picture. The caption has to say May.
  5. LST is not air temperature. Same caveat the deck's limitations slide already carries.
  6. Equirectangular inflates high latitudes; clipped to 84N/60S to limit the worst of it.

Usage: python make_global_map.py   (run from the ucip project root)
"""

import io
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import ee
import numpy as np
import rasterio
import requests
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize

GEE_PROJECT = os.environ.get("GEE_PROJECT", "ucip-mum")

START, END = "2026-05-01", "2026-06-01"
PERIOD_LABEL = "May 2026"

# Deck brand constants, copied from build_deck.py so this file stands alone.
BG = "#0D1017"
MUTED = "#9AA3B2"
TEAL = "#0EA5B3"
AMBER = "#F0A63A"
CRIMSON = "#E4572E"


def _mono_font():
    """The deck sets JetBrains Mono, but matplotlib can only use installed fonts.
    Fall back down a chain of monos rather than silently landing on the sans default."""
    from matplotlib import font_manager as fm
    installed = {f.name for f in fm.fontManager.ttflist}
    for name in ("JetBrains Mono", "Cascadia Mono", "Consolas", "DejaVu Sans Mono"):
        if name in installed:
            return name
    return "monospace"


FONT_MONO = _mono_font()

# Fixed scale. Set from the verified global percentiles, not auto-fitted.
VMIN, VMAX = -20.0, 45.0

# Sentinel for ocean and cloud gaps. Must be far outside any real LST value, because
# 0 C is real land temperature and cannot be used to mean "no data".
NODATA = -9999.0

# 0.5 degree. 720x288 at this clip, comfortably inside the getDownloadURL limit.
SCALE_M = 55660
BOUNDS = [-180, -60, 180, 84]

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))
DECK_ASSETS = r"c:\Users\lenovo\EA\projects\ucip\deck-assets"
OUT_PNG = os.path.join(DECK_ASSETS, "deck-global-lst-may2026.png")


def good_quality_lst(img):
    """Keep only retrievals flagged as good quality.

    QC_Day bits 0-1 are the mandatory QA flag: 0 = produced, good quality;
    1 = produced, check other QA. Anything higher was not produced reliably.
    Bits 6-7 are the LST error flag; 0 means average error <= 1K, 1 means <= 2K.
    Keeping QA <= 1 and error <= 1 drops cloud-edge and low-confidence pixels.
    """
    qc = img.select("QC_Day")
    mandatory = qc.bitwiseAnd(3)
    lst_err = qc.rightShift(6).bitwiseAnd(3)
    mask = mandatory.lte(1).And(lst_err.lte(1))
    return (
        img.select("LST_Day_1km")
        .updateMask(mask)
        .multiply(0.02)
        .subtract(273.15)
        .rename("LST_C")
    )


def brand_cmap():
    """Cool to hot ramp built from the deck's own accents, dark-background safe."""
    return LinearSegmentedColormap.from_list(
        "ucip_heat",
        ["#123A47", TEAL, "#8FBF6A", AMBER, CRIMSON, "#8C1D12"],
        N=256,
    )


def fetch_array():
    ee.Initialize(project=GEE_PROJECT)
    print(f"[ok] Earth Engine initialized (project={GEE_PROJECT})")

    col = ee.ImageCollection("MODIS/061/MOD11A2").filterDate(START, END)
    n = col.size().getInfo()
    if n == 0:
        raise RuntimeError(f"No MOD11A2 scenes in {START}..{END}")
    print(f"[ok] {n} MOD11A2 scenes in {START}..{END}")

    lst = col.map(good_quality_lst).mean().rename("LST_C")
    region = ee.Geometry.Rectangle(BOUNDS, None, False)

    pct = lst.reduceRegion(
        reducer=ee.Reducer.percentile([1, 50, 99]),
        geometry=region, scale=100000, maxPixels=int(1e9), bestEffort=True,
    ).getInfo()
    print("[ok] server-side percentiles (C): "
          + ", ".join(f"{k.split('_')[-1]}={v:.1f}" for k, v in sorted(pct.items()) if v is not None))

    # getDownloadURL writes masked pixels as 0, and 0 C is a legitimate land temperature,
    # so an explicit sentinel is the only way to tell ocean and gaps apart from real cold.
    url = lst.unmask(NODATA).getDownloadURL({
        "format": "GEO_TIFF", "scale": SCALE_M, "region": region, "crs": "EPSG:4326",
    })
    print("[..] downloading GeoTIFF")
    resp = requests.get(url, timeout=300)
    resp.raise_for_status()

    with rasterio.open(io.BytesIO(resp.content)) as src:
        raw = src.read(1)
        bounds = src.bounds
    arr = np.ma.masked_invalid(raw)
    arr = np.ma.masked_where(raw <= NODATA / 2, arr)
    print(f"[ok] raster {arr.shape[1]}x{arr.shape[0]}, bounds {bounds}")
    return arr, bounds


def render(arr, bounds):
    valid = arr.compressed()
    p1, p50, p99 = np.percentile(valid, [1, 50, 99])
    print(f"[ok] rendered array percentiles (C): 1st={p1:.1f}, median={p50:.1f}, 99th={p99:.1f}")
    print(f"[ok] land pixels with data: {valid.size:,} of {arr.size:,} "
          f"({100 * valid.size / arr.size:.1f} %)")

    fig_w = 12.0
    fig_h = fig_w * arr.shape[0] / arr.shape[1] * 1.12  # headroom for the colourbar
    fig = plt.figure(figsize=(fig_w, fig_h), dpi=160)
    fig.patch.set_facecolor(BG)

    ax = fig.add_axes([0.0, 0.10, 1.0, 0.90])
    ax.set_facecolor(BG)
    cmap = brand_cmap()
    cmap.set_bad(alpha=0.0)  # gaps and ocean fall through to the background

    im = ax.imshow(
        arr, cmap=cmap, norm=Normalize(vmin=VMIN, vmax=VMAX),
        extent=[bounds.left, bounds.right, bounds.bottom, bounds.top],
        interpolation="bilinear", origin="upper",
    )
    ax.set_xlim(bounds.left, bounds.right)
    ax.set_ylim(bounds.bottom, bounds.top)
    ax.axis("off")

    cax = fig.add_axes([0.30, 0.065, 0.40, 0.022])
    cb = fig.colorbar(im, cax=cax, orientation="horizontal", extend="both")
    cb.outline.set_visible(False)
    cb.set_ticks([-20, 0, 20, 40])
    cax.tick_params(colors=MUTED, labelsize=7.5, length=0, pad=4)
    for lbl in cax.get_xticklabels():
        lbl.set_fontfamily(FONT_MONO)
    cb.set_label("land surface temperature, \u00b0C", color=MUTED,
                 fontsize=7.5, fontfamily=FONT_MONO, labelpad=5)

    os.makedirs(DECK_ASSETS, exist_ok=True)
    fig.savefig(OUT_PNG, facecolor=BG, edgecolor="none", dpi=160)
    plt.close(fig)
    print(f"[ok] wrote {OUT_PNG}")
    print(f"[ok] size {os.path.getsize(OUT_PNG) / 1024:.0f} KB")


def main():
    arr, bounds = fetch_array()
    render(arr, bounds)
    print(f"\nSanity check before this goes in the deck ({PERIOD_LABEL}):")
    print("  Sahara / Arabia / Thar should be the hottest land on the map.")
    print("  Greenland, Himalaya, high Andes should be the coldest.")
    print("  Southern hemisphere should read cooler than northern (May is northern spring).")


if __name__ == "__main__":
    main()
