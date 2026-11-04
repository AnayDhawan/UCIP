import { Card, CardContent } from "@/components/ui/card";
import Citation from "./Citation";
import { matchCitationFromText } from "@/lib/citations";
import type { NbsRec } from "@/lib/wardTypes";

/** A ward's cited interventions, shared by the dashboard detail view and the ward page. */
export default function WardRecommendations({ recs }: { recs: NbsRec[] }) {
  return (
    <>
      <p className="kicker">Recommended interventions</p>
      <div className="mt-2 space-y-2">
        {recs.map((rec) => {
          const cited = matchCitationFromText(rec.citation);
          return (
            <Card key={rec.intervention + rec.priority} size="sm">
              <CardContent className="text-xs">
                <span className="font-medium text-foreground">{rec.intervention}</span>
                <p className="mt-0.5 text-muted-foreground">{rec.rationale}</p>
                {cited ? (
                  <div className="mt-1.5">
                    <Citation mode="chip" entry={cited} />
                  </div>
                ) : (
                  <p className="mt-0.5 italic text-muted-foreground">{rec.citation}</p>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </>
  );
}
