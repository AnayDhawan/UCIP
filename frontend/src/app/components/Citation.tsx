import { BadgeCheck, ExternalLink } from "lucide-react";
import { CITATIONS, doiUrl, getCitation, type CitationEntry, type SourceEntry } from "@/lib/citations";

type CitationProps =
  | { mode: "chip"; id?: string; entry?: CitationEntry }
  | { mode: "full"; id?: string; entry?: CitationEntry }
  | { mode: "marker"; id?: string; entry?: CitationEntry; index: number };

function resolve(id?: string, entry?: CitationEntry): CitationEntry | undefined {
  return entry ?? (id ? getCitation(id) : undefined);
}

export default function Citation(props: CitationProps) {
  const entry = resolve(props.id, props.entry);
  if (!entry) return null;

  if (props.mode === "marker") {
    return (
      <a
        href={doiUrl(entry.doi)}
        target="_blank"
        rel="noopener noreferrer"
        className="align-super text-[0.65em] font-mono text-brand-teal hover:underline"
        title={`${entry.authors} — ${entry.venue}`}
      >
        [{props.index}]
      </a>
    );
  }

  if (props.mode === "chip") {
    return (
      <a href={doiUrl(entry.doi)} target="_blank" rel="noopener noreferrer" className="citation-chip">
        <span>{entry.authors}</span>
        <ExternalLink className="h-3 w-3" aria-hidden />
      </a>
    );
  }

  // mode === "full"
  return (
    <li className="py-3">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-foreground">
            {entry.authors}
            {entry.verified && (
              <BadgeCheck
                className="ml-1.5 inline h-3.5 w-3.5 text-brand-emerald"
                aria-label="DOI verified"
              />
            )}
          </p>
          <p className="text-sm text-muted-foreground">{entry.venue}</p>
          <p className="mt-1 text-sm text-muted-foreground">{entry.usage}</p>
        </div>
        <a
          href={doiUrl(entry.doi)}
          target="_blank"
          rel="noopener noreferrer"
          className="citation-chip shrink-0"
        >
          <span>DOI</span>
          <ExternalLink className="h-3 w-3" aria-hidden />
        </a>
      </div>
    </li>
  );
}

/** Full citation list, grouped by category — used by `/methodology` and `CitationWall`. */
export function CitationList({ entries = CITATIONS }: { entries?: CitationEntry[] }) {
  return (
    <ul className="divide-y divide-border">
      {entries.map((c) => (
        <Citation key={c.id} mode="full" entry={c} />
      ))}
    </ul>
  );
}

/** Raw data-provenance table (no DOIs) — `/legal`'s "Data sources" section. */
export function SourceAttribution({ sources }: { sources: SourceEntry[] }) {
  return (
    <table className="mt-4 w-full text-sm">
      <thead>
        <tr className="border-b border-border text-left">
          <th className="py-2 pr-4 font-semibold text-foreground">Source</th>
          <th className="py-2 font-semibold text-foreground">Used for</th>
        </tr>
      </thead>
      <tbody>
        {sources.map((s) => (
          <tr key={s.name} className="border-b border-border/60 align-top">
            <td className="py-2 pr-4 text-foreground">{s.name}</td>
            <td className="py-2 text-muted-foreground">{s.use}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
