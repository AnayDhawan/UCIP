import type { Metadata } from "next";
import SiteHeader from "../components/SiteHeader";
import SiteFooter from "../components/SiteFooter";
import { CitationList } from "../components/Citation";
import SimulatePanel from "./SimulatePanel";
import { CITATIONS } from "@/lib/citations";

export const metadata: Metadata = {
  title: "What-if estimator | UCIP",
  description: "Estimate cooling from tree canopy and cool roofs using cited coefficients",
};

const COEFFICIENT_CITATIONS = CITATIONS.filter((c) => c.category === "cooling-coefficients");

export default function SimulatePage() {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <SiteHeader />
      <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-10">
        <h1 className="text-2xl font-semibold text-foreground">What if we cooled a ward?</h1>
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
          Move the sliders to see an illustrative first-order estimate of daytime cooling from
          adding tree canopy or raising roof albedo, using coefficients from published research
          rather than a trained model. Every number below traces to a cited paper.
        </p>

        <div className="mt-8">
          <SimulatePanel />
        </div>

        <div className="mt-10">
          <h2 className="text-lg font-semibold text-foreground">Sources for this estimate</h2>
          <CitationList entries={COEFFICIENT_CITATIONS} />
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
