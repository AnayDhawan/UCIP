/**
 * The published budget scenario, on the page (issue #157).
 *
 * pipeline/15_optimize.py has been computing a real allocation and publishing
 * it to frontend/public/budget_allocation.json, and nothing read it. #154
 * registered the stage so it runs; this is the half that makes the result
 * reachable by a visitor.
 *
 * The caveats are not a footnote here. An allocation table is the most
 * authoritative-looking output this project can produce, and the one most
 * likely to be screenshotted away from its context, so the objective, the
 * assumptions and the limitations render alongside it rather than behind a
 * disclosure. The stage itself refuses to allocate an intervention with no
 * sourced cost; the page should be equally hard to misread.
 */

import { readFile } from "node:fs/promises";
import { join } from "node:path";

type AllocationRow = {
  ward_id: string;
  rank: number;
  hvi: number;
  population_est: number;
  spend_inr: number;
  share_of_ward_treated: number;
  roof_m2_treated: number;
  benefit_person_degrees: number;
};

type Allocation = {
  intervention: { label: string; cost: number; unit: string; source: string; source_url?: string };
  sourced_cost: boolean;
  illustrative_only: boolean;
  budget_inr: number;
  spent_inr: number;
  unspent_inr: number;
  wards_funded: number;
  total_benefit_person_degrees: number;
  objective: string;
  objective_description: string;
  objective_note: string;
  assumptions: string[];
  limitations: string[];
  citations: Record<string, string>;
  allocation: AllocationRow[];
};

/** Indian digit grouping, because the budget is quoted in crore. */
const inr = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

/**
 * The unit cost keeps its paise.
 *
 * Whole rupees are right for a 1.6 crore ward allocation and wrong for a
 * per-square-metre price: rounding 5.38 to 5 understates the programme by 7%
 * and makes a sourced figure look like a guess.
 */
const inrPrecise = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  minimumFractionDigits: 2,
});

const count = new Intl.NumberFormat("en-IN");

/** 50000000 reads as "5 crore" to the audience this is written for. */
function crore(rupees: number): string {
  return `${(rupees / 10_000_000).toLocaleString("en-IN", { maximumFractionDigits: 2 })} crore`;
}

async function loadAllocation(): Promise<Allocation | null> {
  try {
    const path = join(process.cwd(), "public", "budget_allocation.json");
    return JSON.parse(await readFile(path, "utf8")) as Allocation;
  } catch {
    // The file is written by a pipeline stage. A checkout without one should
    // render the rest of the page rather than 500.
    return null;
  }
}

export default async function BudgetAllocation() {
  const data = await loadAllocation();
  if (!data || !data.allocation?.length) return null;

  return (
    <section aria-labelledby="allocation-heading" className="mt-12">
      <h2 id="allocation-heading" className="text-lg font-semibold text-foreground">
        Where would {crore(data.budget_inr)} go?
      </h2>

      <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
        One worked scenario, not a recommendation and not a funded programme. It spends a
        fixed budget on {data.intervention.label.toLowerCase()} at{" "}
        {inrPrecise.format(data.intervention.cost)}/m², allocating by benefit per rupee.
      </p>

      <dl className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
        {[
          { label: "Budget", value: crore(data.budget_inr) },
          { label: "Wards funded", value: String(data.wards_funded) },
          {
            label: "Person-degrees",
            value: count.format(Math.round(data.total_benefit_person_degrees)),
          },
          { label: "Unspent", value: inr.format(data.unspent_inr) },
        ].map((stat) => (
          <div key={stat.label} className="rounded-lg border border-border bg-card p-3">
            <dt className="text-xs uppercase tracking-wide text-muted-foreground">{stat.label}</dt>
            <dd className="mt-1 text-base font-semibold text-foreground">{stat.value}</dd>
          </div>
        ))}
      </dl>

      <div className="mt-6 overflow-x-auto">
        <table className="w-full min-w-[34rem] border-collapse text-sm">
          <caption className="sr-only">
            Wards funded under the {data.objective} objective, with spend and estimated benefit
          </caption>
          <thead>
            <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-muted-foreground">
              <th scope="col" className="py-2 pr-4 font-medium">Ward</th>
              <th scope="col" className="py-2 pr-4 font-medium">HVI rank</th>
              <th scope="col" className="py-2 pr-4 text-right font-medium">Spend</th>
              <th scope="col" className="py-2 pr-4 text-right font-medium">Roofs treated</th>
              <th scope="col" className="py-2 text-right font-medium">Person-degrees</th>
            </tr>
          </thead>
          <tbody>
            {data.allocation.map((row) => (
              <tr key={row.ward_id} className="border-b border-border/60">
                <th scope="row" className="py-2 pr-4 text-left font-medium text-foreground">
                  {row.ward_id}
                </th>
                <td className="py-2 pr-4 text-muted-foreground">
                  {row.rank} of 24
                </td>
                <td className="py-2 pr-4 text-right tabular-nums text-foreground">
                  {inr.format(row.spend_inr)}
                </td>
                <td className="py-2 pr-4 text-right tabular-nums text-muted-foreground">
                  {/* A ward funded below 100% got a partial allocation, which is
                      the fractional knapsack working rather than a rounding
                      artefact, so the share is shown rather than hidden. */}
                  {(row.share_of_ward_treated * 100).toFixed(0)}%
                </td>
                <td className="py-2 text-right tabular-nums text-muted-foreground">
                  {count.format(Math.round(row.benefit_person_degrees))}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-6 rounded-lg border border-border bg-muted/40 p-4">
        <h3 className="text-sm font-semibold text-foreground">
          The objective changes the answer
        </h3>
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
          {data.objective_description}
        </p>
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
          {data.objective_note}
        </p>
      </div>

      <div className="mt-6 grid gap-6 sm:grid-cols-2">
        <div>
          <h3 className="text-sm font-semibold text-foreground">Assumptions</h3>
          <ul className="mt-2 space-y-2 text-sm leading-relaxed text-muted-foreground">
            {data.assumptions.map((assumption) => (
              <li key={assumption} className="border-l-2 border-border pl-3">
                {assumption}
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h3 className="text-sm font-semibold text-foreground">Limitations</h3>
          <ul className="mt-2 space-y-2 text-sm leading-relaxed text-muted-foreground">
            {data.limitations.map((limitation) => (
              <li key={limitation} className="border-l-2 border-border pl-3">
                {limitation}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="mt-6 text-sm leading-relaxed text-muted-foreground">
        <h3 className="text-sm font-semibold text-foreground">Cost and cooling sources</h3>
        <p className="mt-2">
          Unit cost:{" "}
          {data.intervention.source_url ? (
            <a
              href={data.intervention.source_url}
              className="underline underline-offset-2 hover:text-foreground"
              target="_blank"
              rel="noreferrer"
            >
              {data.intervention.source}
            </a>
          ) : (
            data.intervention.source
          )}
        </p>
        {/* These arrive from the pipeline as formatted reference strings rather
            than ids in lib/citations, so they render as written instead of
            being looked up. */}
        {Object.entries(data.citations).map(([key, value]) => (
          <p key={key} className="mt-1">
            Cooling coefficient: {value}
          </p>
        ))}
        <p className="mt-3">
          {data.sourced_cost
            ? "Every rupee allocated here is priced from a published municipal-programme cost. The stage refuses to allocate budget to an intervention with no sourced cost."
            : "This scenario includes an unsourced cost and is illustrative only."}
        </p>
      </div>
    </section>
  );
}
