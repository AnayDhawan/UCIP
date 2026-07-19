import { ExternalLink } from "lucide-react";
import { CITATIONS, CITATION_CATEGORY_LABELS, doiUrl, type CitationCategory } from "@/lib/citations";

const CATEGORY_ORDER: CitationCategory[] = [
  "vulnerability-index",
  "plantability-filter",
  "cooling-coefficients",
];

/**
 * Landing-page credibility section: a grouped, varied-height bibliography list
 * (CSS columns, not a uniform card grid — DESIGN.md bans identical repeated
 * grids) making "we cite everything" a visible design language, not just a
 * methodology-page table.
 */
export default function CitationWall() {
  return (
    <div className="space-y-8">
      {CATEGORY_ORDER.map((cat) => {
        const items = CITATIONS.filter((c) => c.category === cat);
        return (
          <div key={cat}>
            <p className="kicker">{CITATION_CATEGORY_LABELS[cat]}</p>
            <div className="mt-3 columns-1 gap-5 sm:columns-2">
              {items.map((c) => (
                <a
                  key={c.id}
                  href={doiUrl(c.doi)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mb-4 block break-inside-avoid rounded-lg border border-border bg-surface p-4 transition-colors hover:border-brand-teal"
                >
                  <p className="flex items-start justify-between gap-2 text-sm font-medium text-foreground">
                    {c.authors}
                    <ExternalLink
                      className="mt-0.5 h-3.5 w-3.5 shrink-0 text-muted-foreground"
                      aria-hidden
                    />
                  </p>
                  <p className="mt-0.5 font-mono text-xs text-muted-foreground">{c.venue}</p>
                  <p className="mt-1.5 text-xs text-muted-foreground">{c.usage}</p>
                </a>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
