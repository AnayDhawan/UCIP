import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { CITATIONS } from "@/lib/citations";

const VENUES = ["Science", "PNAS", "IJERPH", "Environ. Health Perspect.", "Environ. Res. Lett.", "Solar Energy"];

/**
 * Condensed credibility strip. The full bibliography lives on /methodology; the
 * landing just signals "everything is cited" without dumping the whole wall on
 * tier-1 residents.
 */
export default function CitationStrip() {
  return (
    <section className="mx-auto max-w-5xl px-6 py-14">
      <div className="rounded-2xl border border-border bg-surface p-8">
        <p className="kicker">Cited research</p>
        <h2 className="mt-2 text-xl font-semibold text-foreground">
          Every weight and coefficient traces to a published paper
        </h2>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-muted-foreground">
          The vulnerability index, the plantability filter, and the cooling estimates are all built
          on peer-reviewed work, {CITATIONS.length} papers in total, each with a verifiable DOI.
        </p>
        <div className="mt-5 flex flex-wrap gap-2">
          {VENUES.map((v) => (
            <span
              key={v}
              className="rounded-full border border-border bg-background px-3 py-1 font-mono text-xs text-muted-foreground"
            >
              {v}
            </span>
          ))}
        </div>
        <Link
          href="/methodology"
          className="mt-6 inline-flex items-center gap-1 text-sm font-medium text-brand-teal hover:underline"
        >
          See the full method and citation list
          <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </section>
  );
}
