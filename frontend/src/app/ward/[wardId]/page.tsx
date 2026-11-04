import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import SiteHeader from "../../components/SiteHeader";
import SiteFooter from "../../components/SiteFooter";
import CoefficientSparkline from "../../components/CoefficientSparkline";
import WardRecommendations from "../../components/WardRecommendations";
import WardWeather from "../../components/WardWeather";
import { ACTIVE_CITY } from "@/lib/city";
import { hviColor } from "@/lib/hvi";
import { indexIntervals, rankRangeLabel, type UncertaintyFile } from "@/lib/rankUncertainty";
import { areasForWard } from "@/lib/wardAreas";
import { describeTopDriver, describeWard, type WardProfileData } from "@/lib/wardProfile";
import { wardPageUrl } from "@/lib/wardShare";
import { readPublicJson, wardFeatures, wardFromSlug } from "@/lib/wardSnapshot";
import { wardSlug } from "@/lib/wardSlug";
import { CONTRIB_BAR_MAX, FACTOR_LABELS, INDICATOR_KEYS, type NbsRec } from "@/lib/wardTypes";

const profiles = readPublicJson<WardProfileData>("ward_profiles.json");
const allRecs = readPublicJson<NbsRec[]>("nbs_recommendations.json") ?? [];
const intervals = indexIntervals(readPublicJson<UncertaintyFile>("hvi_uncertainty.json"));

// Slugs, not raw codes: a code with a slash (F/N) cannot be one path segment.
export function generateStaticParams() {
  return wardFeatures.map(({ properties }) => ({ wardId: wardSlug(properties.ward_id) }));
}

export const dynamicParams = false;

export async function generateMetadata({
  params,
}: {
  params: Promise<{ wardId: string }>;
}): Promise<Metadata> {
  const { wardId } = await params;
  const ward = wardFromSlug(wardId);
  if (!ward) return {};
  const { ward_id } = ward.properties;
  const title = `Ward ${ward_id} heat vulnerability in ${ACTIVE_CITY.name} | UCIP`;
  const description = `Heat vulnerability score and rank for ${ACTIVE_CITY.name} ward ${ward_id}, the factors behind it, and recommended cooling interventions.`;
  const url = wardPageUrl(ward_id);
  return {
    title,
    description,
    alternates: { canonical: url },
    openGraph: { title, description, url, siteName: "UCIP", type: "website" },
    twitter: { card: "summary_large_image", title, description },
  };
}

export default async function WardPage({ params }: { params: Promise<{ wardId: string }> }) {
  const { wardId } = await params;
  const ward = wardFromSlug(wardId);
  if (!ward) notFound();
  const { ward_id, HVI, rank, n_cells } = ward.properties;

  const areas = areasForWard(ward_id);
  const profile = profiles?.wards.find((w) => w.ward_id === ward_id) ?? null;
  const topDriver = profile ? describeTopDriver(profile) : null;
  const recs = allRecs.filter((r) => r.ward_id === ward_id).sort((a, b) => a.priority - b.priority);
  const interval = intervals.get(ward_id);
  // Biggest push towards a high score first.
  const factors = INDICATOR_KEYS.map((key) => ({
    key,
    value: (ward.properties[`contrib_${key}`] as number | null) ?? 0,
  })).sort((a, b) => b.value - a.value);

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <SiteHeader />
      <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-14">
        <p className="kicker">{ACTIVE_CITY.name} ward</p>
        <h1 className="mt-3 text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
          Ward {ward_id}
        </h1>
        {areas.length > 0 && (
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{areas.join(", ")}</p>
        )}

        <div className="mt-6 flex items-center gap-4">
          <span
            className="rounded-lg px-4 py-2 font-mono text-3xl font-semibold text-black/80"
            style={{ background: hviColor(HVI) }}
          >
            {HVI?.toFixed(1) ?? "n/a"}
          </span>
          <div className="text-sm">
            <p className="text-foreground">Heat vulnerability score, 0 to 100</p>
            <p className="text-muted-foreground">
              Priority {rank ?? "n/a"} of {wardFeatures.length} &middot; {n_cells ?? "n/a"} grid cells
            </p>
            {interval && (
              <p className="text-muted-foreground">
                Rank is uncertain: likely {rankRangeLabel(interval)} (95% range, from sampling of
                grid cells only).
              </p>
            )}
          </div>
        </div>

        {profile && profiles && (
          <div className="mt-6 space-y-2">
            {describeWard(profile, profiles.city).map((sentence) => (
              <p key={sentence} className="text-sm leading-relaxed text-muted-foreground">
                {sentence}
              </p>
            ))}
          </div>
        )}

        <section className="mt-10">
          <p className="kicker">What drives the score</p>
          <div className="mt-2.5 space-y-2">
            {factors.map(({ key, value }) => (
              <CoefficientSparkline
                key={key}
                label={FACTOR_LABELS[key]}
                value={value}
                max={CONTRIB_BAR_MAX}
              />
            ))}
          </div>
          <p className="mt-1.5 text-[11px] text-muted-foreground">
            Red pushes this ward&apos;s score up, green pushes it down, compared to the city
            average.
            {topDriver && ` ${topDriver}`}
          </p>
        </section>

        <section className="mt-10">
          <WardWeather wardId={ward_id} />
        </section>

        {recs.length > 0 && (
          <section className="mt-10">
            <WardRecommendations recs={recs} />
          </section>
        )}

        <div className="mt-12 flex flex-wrap gap-3">
          <Link
            href={`/dashboard?ward=${encodeURIComponent(ward_id)}`}
            className="rounded-lg bg-brand-teal px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-brand-teal-hover"
          >
            Open on the dashboard
          </Link>
          <Link
            href="/methodology"
            className="rounded-lg border border-border px-5 py-2.5 text-sm font-semibold text-foreground transition-colors hover:bg-surface-hover"
          >
            Read the method
          </Link>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
