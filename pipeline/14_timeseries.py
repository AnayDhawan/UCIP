"""Stage 14 — Multi-year per-ward thermal and vegetation trend (issue #64).

What it does:
    Rebuilds the dry-season LST and NDVI composites for every year in a window
    and reduces each to a per-ward mean, producing a real trend per ward instead
    of the single point-in-time snapshot the index is otherwise built on. Then
    fits a least-squares slope per ward and classifies it.

    "Is this ward hot?" and "is this ward getting hotter?" are different
    questions, and the second is the one a planner allocating a multi-year budget
    actually needs. A ward that is merely warm and stable is a different problem
    from one warming half a degree a decade.

What this is NOT, stated plainly because the issue title invites the stronger reading:

    This is not a multi-year Heat Vulnerability Index, and it deliberately does
    not pretend to be one.

    The index combines seven indicators. Only two of them, LST and NDVI, are
    observed per year: they come from satellite imagery that exists for every
    season. The other five do not vary annually in any data this project has.
    Population density and elderly share come from a single pinned WorldPop
    image; the slum layer is one Datameet snapshot; hospital distance is current
    OpenStreetMap; imperviousness is one WorldCover epoch. Recomputing "the HVI
    per year" while five of its seven inputs are frozen would produce a series
    that looks like a vulnerability trend and is really a thermal trend wearing
    its clothing, with the added dishonesty of an official-looking 0-100 score.

    So this publishes what is actually measured: LST and NDVI per ward per year,
    their trends, and a classification. Extending it to a genuine multi-year index
    needs multi-year socioeconomic data, which is its own project.

Inputs:
    ../data/wards_hvi.geojson   ward geometry and current scores
    Google Earth Engine         Landsat 8 C2 L2 only (needs auth; see
                                season_composite on why Landsat 9 is excluded)

Outputs:
    ../data/ward_timeseries.json          per-ward series, slopes, classification
    frontend/public/ward_timeseries.json  published for the dashboard

Notes:
    Landsat 8 launched in 2013, so the series cannot start earlier without
    switching sensors mid-record. Landsat 5/7 have different thermal bands and
    calibration, and splicing them in without a cross-sensor correction would
    manufacture a trend at the join. START_YEAR reflects that limit rather than
    an arbitrary choice.

    The headline result on Mumbai, as of the 2014-2026 record: NO ward shows a
    statistically significant thermal trend. Slopes run from -0.3 to -1.6 C per
    decade, but the standard error on each is around 0.9 and R squared never
    exceeds 0.23, so every one of them is within about two standard errors of
    zero. Dry-season LST swings 2 to 4 C between consecutive years, which is
    larger than any trend thirteen points could resolve.

    That is a real finding and it is the reason this stage reports significance
    rather than bare slopes. Fitting a line and announcing "24 of 24 wards are
    cooling at 1 C per decade", which is what the first version of this code did,
    would have been a confident, checkable, and completely false claim.

Run:
    .venv\\Scripts\\activate
    python 14_timeseries.py [--city mumbai] [--start 2014] [--end 2026]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import ee
import geopandas as gpd

from _city import load_city
from _gee_auth import init_ee
from _publish import publish

ROOT = Path(__file__).resolve().parent.parent

# Landsat 8 began collecting in 2013; the first full Nov-Feb dry season it covers
# ends in 2014. Earlier years would need Landsat 5/7, whose thermal bands differ
# enough that splicing them in would create a step change at the join and call it
# a trend.
DEFAULT_START_YEAR = 2014

MAX_CLOUD = 20
ST_SCALE, ST_OFFSET = 0.00341802, 149.0
SR_SCALE, SR_OFFSET = 2.75e-05, -0.2

# A ward-year needs at least this many contributing scenes to be trusted. Under
# this the "mean" is a couple of overpasses and a cloud edge can move it a
# degree: the 2016 season, with 4 scenes, came out 2.6 C below its neighbours on
# the first run, which is noise rather than a cold year.
MIN_SCENES_PER_YEAR = 4

# Degrees Celsius per decade below which a ward is called stable rather than
# warming or cooling. Chosen to sit above the year-to-year noise visible in the
# series rather than to produce a pleasing split.
TREND_FLAT_C_PER_DECADE = 0.2
# NDVI is an index on [-1, 1]; a hundredth of an index unit per decade is small
# but real, and below that the classification is not meaningful.
TREND_FLAT_NDVI_PER_DECADE = 0.01


def mask_l2_clouds(img: ee.Image) -> ee.Image:
    qa = img.select("QA_PIXEL")
    mask = qa.bitwiseAnd(1 << 3).eq(0).And(qa.bitwiseAnd(1 << 4).eq(0))
    return img.updateMask(mask)


def season_composite(start: str, end: str, region: ee.Geometry) -> tuple[ee.Image, ee.Number]:
    """Median dry-season LST and NDVI for one season, plus the scene count."""
    # Landsat 8 ONLY, deliberately, even though stage 02 merges Landsat 9 in.
    #
    # Landsat 9 launched in late 2021, so merging it doubles the scene count from
    # 2022 onward (4-7 per season before, 12-14 after). The first version of this
    # stage did merge it, and the result was a -0.63 C step in the city mean
    # exactly at the join, which the least-squares fit then reported as Mumbai
    # cooling at 0.91 C per decade across 23 of 24 wards. That is not a plausible
    # finding for a tropical megacity, and it was an artefact of the sensor change
    # rather than a measurement.
    #
    # A consistent sensor across the whole record matters more here than sample
    # size. Stage 02 is right to merge both: it builds one composite for one
    # season, where more observations is strictly better and there is no join to
    # create. A trend is the case where the join is the whole problem.
    collection = (
        ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
        .filterDate(start, end)
        .filterBounds(region)
        .filter(ee.Filter.lt("CLOUD_COVER", MAX_CLOUD))
        .map(mask_l2_clouds)
    )

    def bands(img: ee.Image) -> ee.Image:
        lst = img.select("ST_B10").multiply(ST_SCALE).add(ST_OFFSET).subtract(273.15).rename("LST_C")
        red = img.select("SR_B4").multiply(SR_SCALE).add(SR_OFFSET)
        nir = img.select("SR_B5").multiply(SR_SCALE).add(SR_OFFSET)
        ndvi = nir.subtract(red).divide(nir.add(red)).rename("NDVI")
        return lst.addBands(ndvi)

    return collection.map(bands).median(), collection.size()


def linear_fit(xs: list[float], ys: list[float]) -> dict:
    """Least-squares slope with its standard error, p-value and R squared.

    The significance testing is the point, not decoration. Dry-season LST over
    Mumbai swings 2 to 4 C between consecutive years: the 2016 season came out at
    31.9 C and 2020 at 36.0 C, against a fitted trend around 1 C per decade. Any
    straight line through data that noisy will have a non-zero slope, and
    reporting that slope as "this ward is cooling" would be inventing a finding
    out of scatter.

    A slope whose confidence interval spans zero is reported as no detected
    trend, which over a 13-season record is frequently the honest answer.
    """
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0 or n < 3:
        return {"slope": 0.0, "stderr": None, "p_value": None, "r_squared": None, "n": n}

    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    intercept = my - slope * mx

    residuals = [y - (intercept + slope * x) for x, y in zip(xs, ys)]
    sse = sum(r * r for r in residuals)
    sst = sum((y - my) ** 2 for y in ys)
    r_squared = 1 - sse / sst if sst > 0 else None

    # Standard error of the slope, and a two-sided t-test against zero.
    if n > 2 and sse > 0:
        stderr = ((sse / (n - 2)) / sxx) ** 0.5
        t_stat = slope / stderr if stderr > 0 else 0.0
        try:
            from scipy import stats

            p_value = float(2 * (1 - stats.t.cdf(abs(t_stat), df=n - 2)))
        except ImportError:  # pragma: no cover
            p_value = None
    else:
        stderr, p_value = 0.0, 0.0

    return {
        "slope": slope,
        "stderr": stderr,
        "p_value": p_value,
        "r_squared": r_squared,
        "n": n,
    }


# A slope must clear this to be called a trend at all. Two sided.
SIGNIFICANCE_ALPHA = 0.05


def classify(lst_fit: dict, ndvi_fit: dict) -> str:
    """A short label for what the ward is doing, or an admission that we cannot tell.

    A direction is only claimed when the slope is both statistically significant
    and larger than the flat band. Otherwise the label says no detected trend,
    which on a 13-season record with this much year-to-year scatter is often the
    correct answer and is far more useful than a confident wrong one.
    """
    lst_slope = lst_fit["slope"] * 10
    ndvi_slope = ndvi_fit["slope"] * 10
    lst_sig = lst_fit["p_value"] is not None and lst_fit["p_value"] < SIGNIFICANCE_ALPHA
    ndvi_sig = ndvi_fit["p_value"] is not None and ndvi_fit["p_value"] < SIGNIFICANCE_ALPHA

    if lst_sig and lst_slope > TREND_FLAT_C_PER_DECADE:
        thermal = "warming"
    elif lst_sig and lst_slope < -TREND_FLAT_C_PER_DECADE:
        thermal = "cooling"
    else:
        thermal = "no detected temperature trend"

    if ndvi_sig and ndvi_slope > TREND_FLAT_NDVI_PER_DECADE:
        green = "greening"
    elif ndvi_sig and ndvi_slope < -TREND_FLAT_NDVI_PER_DECADE:
        green = "losing green"
    else:
        green = "no detected green-cover trend"

    return f"{thermal}, {green}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Per-ward multi-year LST and NDVI trend.")
    parser.add_argument("--city", default=None)
    parser.add_argument("--start", type=int, default=DEFAULT_START_YEAR,
                        help="First season END year, e.g. 2014 means the Nov 2013 - Feb 2014 season.")
    parser.add_argument("--end", type=int, default=None,
                        help="Last season END year. Defaults to the most recent complete season.")
    args = parser.parse_args()

    city = load_city(args.city)
    wards_path = city.out("wards_hvi.geojson")
    if not wards_path.exists():
        print(f"[FAIL] {wards_path} not found — run 05_hvi.py first.")
        return 1

    try:
        init_ee(city.gee_project)
    except Exception as exc:
        print(f"[FAIL] Earth Engine init failed: {exc}")
        return 1

    from datetime import date

    end_year = args.end
    if end_year is None:
        today = date.today()
        end_year = today.year if today.month > 2 else today.year - 1

    years = list(range(args.start, end_year + 1))
    print(f"[..] {city.name}: {len(years)} dry seasons, {years[0]} to {years[-1]}")

    wards = gpd.read_file(wards_path)
    id_col = "ward_id"
    features = [
        ee.Feature(ee.Geometry(json.loads(gpd.GeoSeries([geom]).to_json())["features"][0]["geometry"]),
                   {id_col: wid})
        for wid, geom in zip(wards[id_col], wards.geometry)
    ]
    ward_fc = ee.FeatureCollection(features)
    region = ward_fc.geometry()
    print(f"[ok] loaded {len(features)} wards")

    # ward_id -> year -> {LST_C, NDVI}
    series: dict[str, dict[int, dict]] = {w: {} for w in wards[id_col]}
    scenes_per_year: dict[int, int] = {}
    skipped: list[int] = []

    for year in years:
        start, end = f"{year - 1}-11-01", f"{year}-03-01"
        composite, size = season_composite(start, end, region)
        n_scenes = int(size.getInfo())
        scenes_per_year[year] = n_scenes
        if n_scenes < MIN_SCENES_PER_YEAR:
            print(f"[WARN] {year}: only {n_scenes} usable scenes, skipping this season")
            skipped.append(year)
            continue

        stats = composite.reduceRegions(
            collection=ward_fc, reducer=ee.Reducer.mean(), scale=100
        ).getInfo()

        n_ok = 0
        for feat in stats["features"]:
            p = feat["properties"]
            lst, ndvi = p.get("LST_C"), p.get("NDVI")
            if lst is None or ndvi is None:
                continue
            series[p[id_col]][year] = {"LST_C": round(lst, 3), "NDVI": round(ndvi, 4)}
            n_ok += 1
        print(f"[ok] {year}: {n_scenes} scenes, {n_ok} wards")

    # ------------------------------------------------------------- trends --
    out_wards = []
    for ward_id, by_year in series.items():
        points = sorted(by_year.items())
        if len(points) < 3:
            print(f"[WARN] {ward_id}: only {len(points)} usable years, no trend fitted")
            out_wards.append({
                "ward_id": ward_id,
                "n_years": len(points),
                "series": [{"year": y, **v} for y, v in points],
                "trend": None,
            })
            continue

        xs = [float(y) for y, _ in points]
        lst_fit = linear_fit(xs, [v["LST_C"] for _, v in points])
        ndvi_fit = linear_fit(xs, [v["NDVI"] for _, v in points])
        lst_sig = lst_fit["p_value"] is not None and lst_fit["p_value"] < SIGNIFICANCE_ALPHA

        out_wards.append({
            "ward_id": ward_id,
            "n_years": len(points),
            "series": [{"year": y, **v} for y, v in points],
            "trend": {
                "lst_c_per_decade": round(lst_fit["slope"] * 10, 3),
                "lst_stderr_c_per_decade": round(lst_fit["stderr"] * 10, 3) if lst_fit["stderr"] is not None else None,
                "lst_p_value": round(lst_fit["p_value"], 4) if lst_fit["p_value"] is not None else None,
                "lst_r_squared": round(lst_fit["r_squared"], 3) if lst_fit["r_squared"] is not None else None,
                "lst_significant": lst_sig,
                "ndvi_per_decade": round(ndvi_fit["slope"] * 10, 4),
                "ndvi_p_value": round(ndvi_fit["p_value"], 4) if ndvi_fit["p_value"] is not None else None,
                "ndvi_significant": ndvi_fit["p_value"] is not None and ndvi_fit["p_value"] < SIGNIFICANCE_ALPHA,
                "classification": classify(lst_fit, ndvi_fit),
            },
        })

    fitted = [w for w in out_wards if w["trend"]]
    payload = {
        "city": city.slug,
        "years": years,
        "years_skipped": skipped,
        "scenes_per_year": scenes_per_year,
        "n_wards": len(out_wards),
        "measures": ["LST_C", "NDVI"],
        "what_this_is": (
            "Per-ward dry-season land surface temperature and NDVI, one value per year, with a "
            "least-squares trend per ward."
        ),
        "what_this_is_not": (
            "Not a multi-year Heat Vulnerability Index. Only 2 of the index's 7 indicators are "
            "observed annually; population density, elderly share, the slum layer, hospital "
            "distance and imperviousness each come from a single snapshot. Recomputing the index "
            "per year with five inputs frozen would present a thermal trend as a vulnerability "
            "trend."
        ),
        "limitations": [
            f"Landsat 8 and 9 only, so the record starts at the {DEFAULT_START_YEAR} season. "
            "Landsat 5/7 have different thermal calibration and splicing them would create a step "
            "change at the join.",
            "Dry season only (November to February). Monsoon imagery is unusable for LST, so this "
            "is a dry-season trend, not an annual mean.",
            f"A ward-year needs at least {MIN_SCENES_PER_YEAR} scenes to be included, and a ward "
            "needs 3 usable years before a trend is fitted.",
            "Least-squares slope over a short record. It describes the observed period and is not "
            "a forecast.",
        ],
        "wards": sorted(out_wards, key=lambda w: w["ward_id"]),
    }

    if fitted:
        slopes = [w["trend"]["lst_c_per_decade"] for w in fitted]
        sig = [w for w in fitted if w["trend"]["lst_significant"]]
        sig_slopes = [w["trend"]["lst_c_per_decade"] for w in sig]
        payload["summary"] = {
            "n_wards_fitted": len(fitted),
            "n_wards_significant": len(sig),
            "warming": sum(1 for s in sig_slopes if s > TREND_FLAT_C_PER_DECADE),
            "cooling": sum(1 for s in sig_slopes if s < -TREND_FLAT_C_PER_DECADE),
            "no_detected_trend": len(fitted) - len(sig),
            "median_lst_c_per_decade_all": round(sorted(slopes)[len(slopes) // 2], 3),
        }

    out_path = city.out("ward_timeseries.json")
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[ok] wrote {out_path}")

    if city.publishes_to_frontend:
        publish(out_path, ROOT / "frontend" / "public" / "ward_timeseries.json")

    if fitted:
        s = payload["summary"]
        print(f"\n[ok] {s['n_wards_fitted']} wards fitted; {s['n_wards_significant']} with a "
              f"statistically significant slope: {s['warming']} warming, {s['cooling']} cooling, "
              f"{s['no_detected_trend']} with no detected trend "
              f"(median slope across all wards {s['median_lst_c_per_decade_all']:+.2f} C/decade)")

    ok = len(fitted) >= len(out_wards) * 0.8
    print(f"\n{'GO' if ok else 'CHECK WARNINGS'}: trends fitted for {len(fitted)}/{len(out_wards)} wards.")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
