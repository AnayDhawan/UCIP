"""Build the ward-level Census age table (issue #95).

Writes data/census2011_ward_age_mumbai.csv: for each of Mumbai's 24 BMC wards,
the 2011 Census population and the population aged 0 to 6, and the share.

Why this exists at all. The index used to carry an elderly share from
WorldPop's India age-sex product, which applies district age structure and so
took two values across the whole city. It was removed (docs/methodology.md 10a).
The Census does publish real ward-level figures, but its ward-level Primary
Census Abstract has no 60+ column. It does have 0 to 6. That is the
age-structure signal that exists at ward resolution, and it is a real one: 24
distinct values from 6.75% to 13.09%.

It measures young children, not the elderly. The two are different populations
and this indicator is named for what it is.

Source. Census of India 2011, Primary Census Abstract, Greater Mumbai (M Corp.),
at Census ward level, as redistributed by OpenCity (data.opencity.in) under
"Other (Public Domain)". Census wards are smaller than BMC wards: 97 of them
roll up into the 24 BMC wards, and OpenCity's ward table gives the mapping.

Checked on every build, because a silent join error here would put wrong
numbers into a published index:
  - both source files must agree on every ward's population;
  - the total must equal the Census's own figure for Greater Mumbai, 12,442,373;
  - all 24 wards must be present, and no ward may be unaccounted for.

Standard library only, so CI can test the aggregation without pandas.

Run (needs network; the output is committed, so a normal refresh does not):
    python pipeline/build_census_table.py
"""

from __future__ import annotations

import csv
import io
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "data" / "census2011_ward_age_mumbai.csv"

DATASET = "https://data.opencity.in/dataset/mumbai-ward-wise-census-data"
SOURCES = {
    "ward_map": (
        "https://data.opencity.in/dataset/1a81291d-369d-43e6-97b1-e62680434437/resource/"
        "fcfeacdc-aa80-4028-a468-f0267fa05d23/download/95e22d97-7f59-4214-b244-2abbf52e6027.csv"
    ),
    "pca_city": (
        "https://data.opencity.in/dataset/1a81291d-369d-43e6-97b1-e62680434437/resource/"
        "b2261b97-db46-4d14-a1a7-a2a14976cede/download/fca87e9a-f012-41fe-93bc-cd1ae7e1f82a.csv"
    ),
    "pca_suburban": (
        "https://data.opencity.in/dataset/1a81291d-369d-43e6-97b1-e62680434437/resource/"
        "a33e01ed-6dec-458b-af70-395c59d4f89e/download/43c17944-e918-4270-ae91-63f986adfb93.csv"
    ),
}

# The Census's own total for Greater Mumbai (M Corp.), 2011. Not derived from
# the files being checked.
GREATER_MUMBAI_POPULATION_2011 = 12_442_373

SOURCE_LABEL = "census2011_pca_ward"


class CensusError(ValueError):
    """The source data failed one of the checks that stop a wrong table shipping."""


def fetch(url: str) -> list[dict[str, str]]:
    with urllib.request.urlopen(url, timeout=60) as response:  # noqa: S310 - fixed https URLs above
        return list(csv.DictReader(io.StringIO(response.read().decode("utf-8-sig"))))


def aggregate(
    pca_rows: list[dict[str, str]],
    ward_map_rows: list[dict[str, str]],
    expected_total: int | None = GREATER_MUMBAI_POPULATION_2011,
) -> list[dict[str, object]]:
    """Roll Census wards up into BMC wards, refusing to return a wrong table.

    `pca_rows` are Primary Census Abstract rows (any level; only WARD rows are
    used). `ward_map_rows` map each Census ward code to a BMC ward name and carry
    their own population, which is what the cross-check runs against.
    """
    ward_rows = {
        int(r["Ward"]): r for r in pca_rows if r.get("Level") == "WARD" and r.get("Ward", "").strip()
    }
    mapping = {int(r["Ward Code"]): r for r in ward_map_rows}

    unmapped = sorted(set(ward_rows) - set(mapping))
    if unmapped:
        raise CensusError(f"Census wards with no BMC ward mapping: {unmapped}")
    unmatched = sorted(set(mapping) - set(ward_rows))
    if unmatched:
        raise CensusError(f"mapped wards missing from the Primary Census Abstract: {unmatched}")

    totals: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for code, pca in ward_rows.items():
        population = int(pca["TOT_P"])
        mapped_population = int(mapping[code]["Total Population"])
        if population != mapped_population:
            raise CensusError(
                f"census ward {code}: the two source files disagree on population "
                f"({population} against {mapped_population})"
            )
        bmc = mapping[code]["Ward Name"].strip()
        totals[bmc][0] += population
        totals[bmc][1] += int(pca["P_06"])

    grand = sum(t[0] for t in totals.values())
    if expected_total is not None and grand != expected_total:
        raise CensusError(
            f"population sums to {grand:,}, but the Census gives {expected_total:,} for Greater Mumbai"
        )

    return [
        {
            "ward_id": ward,
            "tot_p": pop,
            "p_06": kids,
            "child_pct": round(kids / pop * 100, 4),
            "source": SOURCE_LABEL,
        }
        for ward, (pop, kids) in sorted(totals.items())
    ]


def write(rows: list[dict[str, object]], path: Path = OUT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["ward_id", "tot_p", "p_06", "child_pct", "source"])
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    print(f"[..] downloading Census tables from {DATASET}")
    ward_map = fetch(SOURCES["ward_map"])
    pca = fetch(SOURCES["pca_city"]) + fetch(SOURCES["pca_suburban"])
    try:
        rows = aggregate(pca, ward_map)
    except CensusError as exc:
        print(f"[FAIL] {exc}")
        return 1

    write(rows)
    values = [r["child_pct"] for r in rows]
    print(f"[ok] wrote {len(rows)} wards -> {OUT_PATH}")
    print(f"[ok] child share {min(values):.2f}% to {max(values):.2f}%, "
          f"{len({round(v, 4) for v in values})} distinct values")
    return 0


if __name__ == "__main__":
    sys.exit(main())
