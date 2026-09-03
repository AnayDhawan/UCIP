"""Stage 13 — Validate satellite LST against ground weather stations (issue #65).

What it does:
    Compares the pipeline's satellite-derived land surface temperature against
    real observations from NOAA Global Summary of the Day weather stations in
    Mumbai, and writes the agreement metrics to disk for the methodology page.

    This is the difference between an index that looks plausible and one that has
    been checked. Every other number in this project is internally consistent by
    construction: the PCA is computed from the indicators, the indicators from
    the composites, the composites from the imagery. Nothing until now compared
    any of it to an independent measurement of the real world.

The central caveat, stated up front because it decides how the result may be read:

    LAND SURFACE TEMPERATURE IS NOT AIR TEMPERATURE.

    LST is the radiometric temperature of the ground as seen from orbit. Station
    temperature is air measured in a shaded screen roughly 1.5 m up. On a sunny
    day a paved surface can read 15 C above the air over it, and the offset
    varies with surface type, wind and time of day. So this stage reports
    CORRELATION, whether the two move together across days, and the systematic
    offset between them. It does not and cannot claim they are the same
    quantity, and a high correlation with a large offset is the expected result,
    not a problem.

    What correlation buys is real: if the satellite composite tracks ground
    observations across a season, the LST layer is measuring Mumbai's thermal
    variation rather than sensor noise or cloud artefacts, and the relative
    ranking the index is built on is defensible.

Validation window:
    NOT the window the published figures use. NOAA GSOD publishes on a lag, and
    on 2026-09-03 its Mumbai records ended 2025-08-24, with zero overlap against
    the pipeline's current 2025-11 to 2026-02 composite. So this validates the
    METHOD on the most recent dry season where both data sources exist
    (2024-11-01 to 2025-02-28), which is what a validation can honestly do here.
    Rerun it against the current window once GSOD catches up; VALIDATION_WINDOW
    below is the only thing to change.

Stations:
    43003099999  Chhatrapati Shivaji Maharaj International (Santacruz), inland
    43057099999  Bombay Colaba, coastal

    Two stations is few. It is also all of them: these are the only long-record
    GSOD stations inside Mumbai. The pair is useful beyond the count, because
    coastal Colaba and inland Santacruz sit in genuinely different thermal
    regimes, so agreement at both is a stronger signal than agreement at either.

Inputs:
    NOAA GSOD CSVs, downloaded and cached under pipeline/cache/gsod/
    Google Earth Engine, Landsat 8/9 C2 L2 (needs auth)

Outputs:
    ../data/lst_validation.json         metrics, per station and pooled
    frontend/public/lst_validation.json published for the methodology page

Run:
    .venv\\Scripts\\activate
    python 13_validate_lst.py
"""

from __future__ import annotations

import csv
import json
import sys
import urllib.request
from pathlib import Path

import ee

from _gee_auth import init_ee
from _publish import publish

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CACHE_DIR = Path(__file__).resolve().parent / "cache" / "gsod"
OUT_PATH = DATA_DIR / "lst_validation.json"
OUT_PUBLIC_PATH = ROOT / "frontend" / "public" / "lst_validation.json"

# The most recent dry season with both satellite and station coverage. See the
# module docstring on why this is not the pipeline's own composite window.
VALIDATION_WINDOW = ("2024-11-01", "2025-02-28")

STATIONS = [
    {
        "id": "43003099999",
        "name": "Santacruz (Chhatrapati Shivaji Maharaj Intl)",
        "setting": "inland",
    },
    {"id": "43057099999", "name": "Colaba", "setting": "coastal"},
]

GSOD_URL = "https://www.ncei.noaa.gov/data/global-summary-of-the-day/access/{year}/{station}.csv"

# GSOD encodes missing temperature as 9999.9, in Fahrenheit.
GSOD_MISSING = "9999.9"

# Landsat pixels are 30 m. Averaging LST in a small disc around the station
# rather than sampling one pixel avoids a single anomalous pixel (a roof, a
# runway) standing in for the site, without smearing across land-cover types.
SAMPLE_RADIUS_M = 500

MAX_CLOUD = 20
ST_SCALE, ST_OFFSET = 0.00341802, 149.0


def fahrenheit_to_celsius(f: float) -> float:
    return (f - 32.0) * 5.0 / 9.0


def download_gsod(station: str, year: int) -> Path:
    """Fetch one station-year of GSOD, caching it so reruns need no network."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"{station}_{year}.csv"
    if path.exists() and path.stat().st_size > 0:
        return path
    url = GSOD_URL.format(year=year, station=station)
    print(f"[..] downloading {url}")
    try:
        with urllib.request.urlopen(url, timeout=120) as resp:
            path.write_bytes(resp.read())
    except Exception as exc:
        print(f"[WARN] could not download {station} {year}: {exc}")
        return path
    return path


def station_daily_temps(station: str) -> dict[str, float]:
    """Daily mean air temperature in Celsius, keyed by ISO date."""
    start, end = VALIDATION_WINDOW
    years = sorted({int(start[:4]), int(end[:4])})
    out: dict[str, float] = {}
    for year in years:
        path = download_gsod(station, year)
        if not path.exists() or path.stat().st_size == 0:
            continue
        with path.open(encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                date = row.get("DATE", "")
                temp = row.get("TEMP", "")
                if not (start <= date <= end):
                    continue
                if temp in ("", GSOD_MISSING):
                    continue
                out[date] = fahrenheit_to_celsius(float(temp))
    return out


def mask_l2_clouds(img: ee.Image) -> ee.Image:
    qa = img.select("QA_PIXEL")
    mask = qa.bitwiseAnd(1 << 3).eq(0).And(qa.bitwiseAnd(1 << 4).eq(0))
    return img.updateMask(mask)


def scene_lst_at(point: ee.Geometry, start: str, end: str) -> list[dict]:
    """Per-scene LST near a point, as [{date, lst_c}], cloud-masked.

    Per scene rather than one composite on purpose: a composite collapses the
    season to a single number and there is nothing left to correlate. Matching
    each overpass to that day's station reading is what makes a correlation
    meaningful.
    """
    collection = (
        ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
        .merge(ee.ImageCollection("LANDSAT/LC09/C02/T1_L2"))
        .filterDate(start, end)
        .filterBounds(point)
        .filter(ee.Filter.lt("CLOUD_COVER", MAX_CLOUD))
        .map(mask_l2_clouds)
    )

    def sample(img: ee.Image) -> ee.Feature:
        lst = (
            img.select("ST_B10")
            .multiply(ST_SCALE)
            .add(ST_OFFSET)
            .subtract(273.15)
            .rename("lst_c")
        )
        value = lst.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=point.buffer(SAMPLE_RADIUS_M),
            scale=30,
            maxPixels=1e9,
        ).get("lst_c")
        return ee.Feature(
            None,
            {"date": img.date().format("YYYY-MM-dd"), "lst_c": value},
        )

    features = collection.map(sample).filter(ee.Filter.notNull(["lst_c"])).getInfo()
    return [f["properties"] for f in features.get("features", [])]


def pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy = sum((y - my) ** 2 for y in ys) ** 0.5
    return num / (dx * dy) if dx and dy else float("nan")


def rmse(xs: list[float], ys: list[float]) -> float:
    return (sum((x - y) ** 2 for x, y in zip(xs, ys)) / len(xs)) ** 0.5


def main() -> int:
    start, end = VALIDATION_WINDOW
    print(f"[..] validating LST against GSOD stations, {start} to {end}")

    try:
        init_ee()
    except Exception as exc:
        print(f"[FAIL] Earth Engine init failed: {exc}")
        return 1

    results = []
    pooled_sat: list[float] = []
    pooled_obs: list[float] = []

    for station in STATIONS:
        obs = station_daily_temps(station["id"])
        if not obs:
            print(f"[WARN] no station data for {station['name']} in window, skipping")
            continue

        # GSOD carries the station's own coordinates; read them from the file
        # rather than hardcoding, so a station relocation is picked up.
        path = CACHE_DIR / f"{station['id']}_{int(start[:4])}.csv"
        with path.open(encoding="utf-8") as fh:
            first = next(csv.DictReader(fh))
        lat, lon = float(first["LATITUDE"]), float(first["LONGITUDE"])
        point = ee.Geometry.Point([lon, lat])

        scenes = scene_lst_at(point, start, end)
        pairs = [(s["lst_c"], obs[s["date"]], s["date"]) for s in scenes if s["date"] in obs]

        if len(pairs) < 3:
            print(f"[WARN] only {len(pairs)} matched overpasses for {station['name']}, skipping")
            continue

        sat = [p[0] for p in pairs]
        air = [p[1] for p in pairs]

        r = pearson(sat, air)
        bias = sum(s - a for s, a in zip(sat, air)) / len(sat)

        # Pool as anomalies about each station's own mean, not as raw values.
        #
        # The two stations have very different LST-to-air offsets (inland
        # Santacruz sits over airport tarmac, coastal Colaba is maritime), which
        # is the physically expected result. Pooling raw values therefore mixes
        # two regimes with different intercepts, and the correlation collapses
        # for a reason that has nothing to do with measurement quality: on this
        # run, per-station r of 0.72 and 0.80 pooled to 0.38.
        #
        # Centring each station first removes the between-station offset and
        # leaves the question actually being asked, which is whether the
        # satellite tracks day-to-day variation at a given place.
        mean_sat = sum(sat) / len(sat)
        mean_air = sum(air) / len(air)
        pooled_sat += [v - mean_sat for v in sat]
        pooled_obs += [v - mean_air for v in air]
        entry = {
            "station_id": station["id"],
            "name": station["name"],
            "setting": station["setting"],
            "lat": lat,
            "lon": lon,
            "n_matched_overpasses": len(pairs),
            "n_station_days": len(obs),
            "pearson_r": round(r, 3),
            "rmse_c": round(rmse(sat, air), 2),
            "mean_bias_c": round(bias, 2),
            "mean_satellite_lst_c": round(sum(sat) / len(sat), 2),
            "mean_station_air_c": round(sum(air) / len(air), 2),
        }
        results.append(entry)
        print(
            f"[ok] {station['name']}: n={entry['n_matched_overpasses']} "
            f"r={entry['pearson_r']} bias={entry['mean_bias_c']} C"
        )

    if not results:
        print("[FAIL] no station produced enough matched overpasses to validate against.")
        return 1

    payload = {
        "window": {"start": start, "end": end},
        "is_pipeline_window": False,
        "method": "Per-overpass Landsat 8/9 ST_B10 LST, cloud-masked, averaged within "
        f"{SAMPLE_RADIUS_M} m of each station, matched to that day's GSOD mean air temperature.",
        "interpretation": (
            "Land surface temperature is not air temperature: LST is the radiometric "
            "temperature of the ground, station temperature is shaded air at roughly 1.5 m. "
            "A large positive bias is expected and is not an error. The figure that matters "
            "is the correlation, which tests whether the satellite composite tracks real "
            "thermal variation rather than sensor noise or cloud artefacts."
        ),
        "limitations": [
            "Two stations, the only long-record GSOD sites in Mumbai.",
            "Validates the method on the most recent dry season with both satellite and "
            "station coverage, not the window the published index is computed from. GSOD "
            "publishes on a lag and had no data overlapping the current composite.",
            "Daily station means are compared against a single mid-morning overpass, so "
            "part of the residual is diurnal rather than error.",
        ],
        "stations": results,
    }

    if len(pooled_sat) >= 3:
        payload["pooled_within_station"] = {
            "n": len(pooled_sat),
            "pearson_r": round(pearson(pooled_sat, pooled_obs), 3),
            "note": (
                "Computed on anomalies about each station's own mean, so the two stations' "
                "different LST-to-air offsets do not contaminate the correlation. This is the "
                "day-to-day tracking skill. Pooling the raw values instead would mix an inland "
                "airport site with a coastal one and report a much lower number for a reason "
                "unrelated to measurement quality."
            ),
        }
        print(
            f"[ok] pooled within-station: n={payload['pooled_within_station']['n']} "
            f"r={payload['pooled_within_station']['pearson_r']}"
        )

    # The spread of per-station bias is itself a result worth publishing: it is
    # the size of the surface-type effect, and it is why a single global
    # LST-to-air correction would be wrong.
    biases = [s["mean_bias_c"] for s in results]
    payload["bias_spread_c"] = {
        "min": min(biases),
        "max": max(biases),
        "note": (
            "Range of the LST-minus-air offset across stations. A wide spread is expected: "
            "the offset depends on what the ground is made of. It also means no single "
            "additive correction converts this LST layer into air temperature, which is "
            "why the index uses LST as a relative indicator rather than as a temperature."
        ),
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[ok] wrote {OUT_PATH}")
    publish(OUT_PATH, OUT_PUBLIC_PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
