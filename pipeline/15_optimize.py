"""Stage 15 — Budget-constrained allocation of cooling interventions (issue #67).

What it does:
    Given a budget, decides how much of which intervention to fund in which
    wards. Benefit is estimated cooling multiplied by the people who experience
    it, weighted by default by how vulnerable those people are.

    The objective is a real choice and it changes the answer completely. On a
    5 crore budget the two available objectives share no wards at all:

        exposure       funds wards ranked 17, 19, 22 and 24 of 24
        vulnerability  funds wards ranked 5, 8 and 12

    Maximising bare person-degrees sends the whole budget to whichever wards have
    the most roof and the most people, which in Mumbai are not the wards at risk.
    That is a defensible objective for a pure cooling programme and an
    indefensible one for a heat-vulnerability tool, so the default weights by the
    index and the objective is recorded in the output rather than left implicit.

Why this was cut from the original build, and what changed:
    F9, a budget optimiser, was deliberately dropped, and docs/pitch-brief.md
    carries a dated note saying not to reinstate it without real unit-cost data.
    That was the right call: an optimiser is the most authoritative-looking
    output a tool like this can produce, and one built on invented costs would
    launder a guess into a spending recommendation.

    What changed is that real costs now exist for one intervention family. NRDC
    published indicative Indian cool-roof costs including what the Ahmedabad Cool
    Roofs Pilot Program actually paid, which is a municipal programme cost rather
    than a retail quote. Those are in config/intervention_costs.json with their
    source.

    Costs for tree planting, pocket parks, cooling centres and rain gardens were
    searched for and NOT found at any credible standard, so they are recorded as
    sourced=false with the reason. This stage REFUSES to allocate budget to an
    unsourced intervention. Passing --allow-unsourced overrides that and stamps
    every output as illustrative, which exists for experimentation and should not
    be used to produce anything anybody acts on.

    So the original decision is respected exactly rather than quietly reversed:
    the machinery is real and tested, and no number without a citation reaches an
    allocation.

The optimisation:
    Fractional knapsack, maximising benefit per rupee. This is not an
    approximation dressed up: the fundable interventions here are divisible
    (square metres of roof), and for divisible goods greedy allocation by
    benefit-to-cost ratio is provably optimal. There is no need for linear
    programming or a solver dependency, and a greedy rule is explainable to a
    planner, which matters more than sophistication for a number that has to be
    defended in a budget meeting.

Cooling estimates:
    From frontend/src/lib/coefficients.ts, the same cited coefficients the
    /simulate page uses (Santamouris 2014 for albedo, Ziter 2019 for canopy,
    Bowler 2010 for parks). Mirrored here rather than duplicated by hand, with a
    test asserting the constants still agree.

Inputs:
    ../data/wards_hvi.geojson         ward scores and ranks
    ../data/ward_profiles.json        per-ward population density and area
    ../config/intervention_costs.json unit costs, each with a source

Outputs:
    ../data/budget_allocation.json          the allocation and its assumptions
    frontend/public/budget_allocation.json  published for the site

Run:
    .venv\\Scripts\\activate
    python 15_optimize.py --budget 50000000            # 5 crore
    python 15_optimize.py --budget 50000000 --intervention cool_roof_lime
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import geopandas as gpd

from _city import load_city
from _publish import publish

ROOT = Path(__file__).resolve().parent.parent
COSTS_PATH = ROOT / "config" / "intervention_costs.json"

# Santamouris 2014 (Solar Energy 103:682-703): peak ambient temperature falls
# roughly 0.57-2.3 K per +0.1 albedo. The project's citation table uses the
# conservative 0.6 K end as its headline, and so does this.
COOL_ROOF_C_PER_0_1_ALBEDO = 0.6

# A white roof over a typical Indian concrete roof is about a 0.4 albedo gain.
# Treated as an assumption rather than a measurement, and surfaced as one.
ASSUMED_ALBEDO_GAIN = 0.4

# Cool roofs only cool where there are roofs. Rather than invent a roof-area
# survey, treat imperviousness as the upper bound on roofed fraction and take a
# share of it, since impervious surface is roads and paving as well as roofs.
ROOF_SHARE_OF_IMPERVIOUS = 0.4

CITATIONS = {
    "cool_roof": "Santamouris 2014, Solar Energy 103:682-703, doi:10.1016/j.solener.2012.07.003",
}


def load_costs() -> dict:
    return json.loads(COSTS_PATH.read_text(encoding="utf-8"))


def cool_roof_cooling_c(albedo_gain: float = ASSUMED_ALBEDO_GAIN) -> float:
    """Estimated peak ambient cooling from a given albedo increase."""
    return (albedo_gain / 0.1) * COOL_ROOF_C_PER_0_1_ALBEDO


def main() -> int:
    parser = argparse.ArgumentParser(description="Allocate a cooling budget across wards.")
    parser.add_argument("--city", default=None)
    parser.add_argument("--budget", type=float, required=True, help="Total budget in INR.")
    parser.add_argument(
        "--intervention",
        default="cool_roof_lime",
        help="Intervention key from config/intervention_costs.json.",
    )
    parser.add_argument(
        "--objective",
        choices=["exposure", "vulnerability"],
        default="vulnerability",
        help="exposure: maximise person-degrees of cooling, which favours dense wards. "
        "vulnerability: weight those person-degrees by ward HVI, so the same degree counts "
        "for more where people are more vulnerable. Default is vulnerability, because this "
        "is a vulnerability tool.",
    )
    parser.add_argument(
        "--allow-unsourced",
        action="store_true",
        help="Permit an intervention with no sourced unit cost. Output is stamped illustrative "
        "and must not be used for real allocation.",
    )
    args = parser.parse_args()

    city = load_city(args.city)
    costs = load_costs()
    key = args.intervention
    spec = costs["interventions"].get(key)

    if spec is None:
        available = ", ".join(costs["interventions"])
        print(f"[FAIL] unknown intervention '{key}'. Available: {available}")
        return 1

    if not spec.get("sourced"):
        if not args.allow_unsourced:
            print(f"[FAIL] '{key}' has no sourced unit cost, so it cannot be allocated.")
            print(f"       Reason: {spec.get('_why_unsourced', 'not recorded')}")
            if spec.get("what_would_close_this"):
                print(f"       What would close this: {spec['what_would_close_this']}")
            print("       Re-run with --allow-unsourced only for experimentation; the output "
                  "is then illustrative and not a spending recommendation.")
            return 1
        print(f"[WARN] '{key}' has no sourced cost. Output is ILLUSTRATIVE ONLY.")

    wards_path = city.out("wards_hvi.geojson")
    profiles_path = city.out("ward_profiles.json")
    for p in (wards_path, profiles_path):
        if not p.exists():
            print(f"[FAIL] {p} not found — run 05_hvi.py and 10_ward_profile.py first.")
            return 1

    wards = gpd.read_file(wards_path)
    profiles = json.loads(profiles_path.read_text(encoding="utf-8"))
    by_id = {w["ward_id"]: w for w in profiles["wards"]}

    unit_cost = spec["cost"]
    cooling_c = cool_roof_cooling_c() if key.startswith("cool_roof") else None
    if cooling_c is None:
        print(f"[FAIL] no cooling model for '{key}'. Only cool-roof interventions are modelled; "
              f"the cited coefficients for trees and parks exist but their COSTS do not.")
        return 1

    # ------------------------------------------------------- candidate set --
    # One candidate per ward. Benefit is degrees of cooling times the people who
    # feel it; cost is the treatable roof area times the unit cost.
    candidates = []
    skipped = []
    for _, row in wards.iterrows():
        ward_id = row["ward_id"]
        prof = by_id.get(ward_id)
        if prof is None:
            skipped.append(ward_id)
            continue

        density = prof.get("pop_density_km2")
        impervious = prof.get("impervious_pct")
        n_cells = row.get("n_cells")
        if not density or impervious is None or not n_cells:
            skipped.append(ward_id)
            continue

        # Each grid cell is cell_size_m square, so ward area follows from the
        # cell count rather than needing a separate area column.
        area_km2 = n_cells * (city.cell_size_m / 1000.0) ** 2
        population = density * area_km2
        treatable_m2 = area_km2 * 1e6 * (impervious / 100.0) * ROOF_SHARE_OF_IMPERVIOUS
        cost = treatable_m2 * unit_cost
        if cost <= 0:
            skipped.append(ward_id)
            continue

        # Person-degrees: cooling delivered times the people who feel it.
        exposure_benefit = cooling_c * population
        # Vulnerability-weighted: the same person-degrees scaled by the ward's own
        # index, so a degree in a ward scoring 74 counts roughly twice one in a
        # ward scoring 37. Without this the allocator spends a heat-VULNERABILITY
        # budget on whichever wards simply have the most roof, which on the first
        # run put the entire budget into wards ranked 17, 19, 22 and 24 of 24.
        hvi = float(row["HVI"]) if row.get("HVI") is not None else 0.0
        vulnerability_benefit = exposure_benefit * (hvi / 100.0)
        benefit = vulnerability_benefit if args.objective == "vulnerability" else exposure_benefit
        if benefit <= 0:
            skipped.append(ward_id)
            continue
        candidates.append({
            "ward_id": ward_id,
            "rank": int(row["rank"]) if row.get("rank") is not None else None,
            "hvi": round(float(row["HVI"]), 2) if row.get("HVI") is not None else None,
            "population_est": round(population),
            "treatable_roof_m2": round(treatable_m2),
            "full_cost_inr": round(cost),
            "benefit": round(benefit),
            "benefit_person_degrees": round(exposure_benefit),
            "benefit_per_rupee": benefit / cost,
        })

    if not candidates:
        print("[FAIL] no ward had enough data to be a candidate.")
        return 1

    # --------------------------------------------------------- allocation ---
    # Fractional knapsack: sort by benefit per rupee and fill. Optimal for
    # divisible goods, which square metres of roof are.
    candidates.sort(key=lambda c: c["benefit_per_rupee"], reverse=True)

    remaining = args.budget
    allocation = []
    for c in candidates:
        if remaining <= 0:
            break
        spend = min(c["full_cost_inr"], remaining)
        share = spend / c["full_cost_inr"]
        allocation.append({
            **{k: c[k] for k in ("ward_id", "rank", "hvi", "population_est")},
            "spend_inr": round(spend),
            "share_of_ward_treated": round(share, 3),
            "roof_m2_treated": round(c["treatable_roof_m2"] * share),
            "benefit_person_degrees": round(c["benefit_person_degrees"] * share),
        })
        remaining -= spend

    spent = args.budget - remaining
    total_benefit = sum(a["benefit_person_degrees"] for a in allocation)

    payload = {
        "city": city.slug,
        "intervention": {"key": key, "label": spec["label"], **{
            k: spec[k] for k in ("unit", "cost", "source", "source_url") if k in spec
        }},
        "sourced_cost": bool(spec.get("sourced")),
        "illustrative_only": not spec.get("sourced"),
        "budget_inr": args.budget,
        "spent_inr": round(spent),
        "unspent_inr": round(remaining),
        "wards_funded": len(allocation),
        "wards_fully_funded": sum(1 for a in allocation if a["share_of_ward_treated"] >= 0.999),
        "total_benefit_person_degrees": round(total_benefit),
        "objective": args.objective,
        "objective_description": (
            "Maximise vulnerability-weighted cooling: degrees C x people exposed x ward HVI, "
            "allocated by benefit per rupee."
            if args.objective == "vulnerability"
            else "Maximise population-weighted cooling: degrees C x people exposed, allocated by "
                 "benefit per rupee. Favours dense wards regardless of how vulnerable they are."
        ),
        "objective_note": (
            "Allocated by fractional knapsack, provably optimal for a divisible intervention. "
            "The choice of objective moves the answer a long way: on a 5 crore budget the "
            "exposure objective funded wards ranked 17, 19, 22 and 24 of 24, because dense "
            "wards yield the most person-degrees per rupee whether or not they are the wards "
            "at risk. That is why the default weights by vulnerability, and why the objective "
            "is recorded in the output rather than left implicit."
        ),
        "assumptions": [
            f"Albedo gain from a cool roof: +{ASSUMED_ALBEDO_GAIN}. An assumption, not a measurement.",
            f"Cooling: {COOL_ROOF_C_PER_0_1_ALBEDO} C per +0.1 albedo, the conservative end of "
            f"Santamouris 2014's 0.57-2.3 K range.",
            f"Roof area: {ROOF_SHARE_OF_IMPERVIOUS:.0%} of each ward's impervious surface. "
            f"Imperviousness includes roads and paving, so this is a share of it rather than all "
            f"of it, and it is an assumption rather than a roof survey.",
            "Population from WorldPop density times ward area; the same modelled surface the "
            "index uses, not a census count.",
            "Benefit is instantaneous person-degrees. It does not model intervention lifetime, "
            "maintenance, discounting, or health outcomes.",
        ],
        "limitations": [
            "Only cool roofs can be allocated. Cited cooling coefficients exist for tree canopy "
            "(Ziter 2019) and pocket parks (Bowler 2010), but no credible Indian unit COST was "
            "found for either, so they cannot enter a budget comparison.",
            "Costs are 2020 prices and are not inflation-adjusted.",
            "Even the vulnerability-weighted objective is an aggregate one: it maximises total "
            "weighted cooling, not the worst-off ward's outcome. A sparse but severely "
            "vulnerable ward can still lose to a dense moderately vulnerable one. A minimax or "
            "per-capita-floor objective would answer a different and equally legitimate "
            "question.",
        ],
        "citations": CITATIONS,
        "allocation": allocation,
        "skipped_wards": skipped,
    }

    out_path = city.out("budget_allocation.json")
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[ok] wrote {out_path}")
    if city.publishes_to_frontend:
        publish(out_path, ROOT / "frontend" / "public" / "budget_allocation.json")

    print(f"\n[ok] budget INR {args.budget:,.0f} -> {len(allocation)} wards "
          f"({payload['wards_fully_funded']} fully funded), "
          f"INR {spent:,.0f} spent, {total_benefit:,.0f} person-degrees")
    for a in allocation[:5]:
        print(f"     {a['ward_id']:5} rank {a['rank']:>2}  INR {a['spend_inr']:>12,}  "
              f"{a['share_of_ward_treated']:.0%} of roofs")
    if len(allocation) > 5:
        print(f"     ... and {len(allocation) - 5} more")

    return 0


if __name__ == "__main__":
    sys.exit(main())
