import fs from "fs";
import path from "path";
import Link from "next/link";
import SiteHeader from "./components/SiteHeader";
import SiteFooter from "./components/SiteFooter";
import Reveal from "./components/Reveal";
import Hero from "./components/sections/Hero";
import MapPreview from "./components/sections/MapPreview";
import Mission from "./components/sections/Mission";
import CitationStrip from "./components/sections/CitationStrip";

type WardFeature = {
  properties: {
    ward_id: string;
    HVI: number | null;
    rank: number | null;
  };
};

function topWards(n: number) {
  const p = path.join(process.cwd(), "public", "wards_hvi.geojson");
  const gj = JSON.parse(fs.readFileSync(p, "utf-8")) as { features: WardFeature[] };
  return gj.features
    .map((f) => f.properties)
    .filter((w) => w.rank !== null)
    .sort((a, b) => (a.rank ?? 99) - (b.rank ?? 99))
    .slice(0, n);
}

const LAYERS = [
  {
    color: "#f03b20",
    name: "Heat vulnerability",
    text: "Every ward gets a score from 0 to 100 combining surface heat, green cover, crowding, elderly share, informal housing, and distance to hospitals. Darker red means help is needed sooner.",
  },
  {
    color: "#4ade80",
    name: "Plantability",
    text: "Not every hot spot should get trees. This layer shows where planting makes ecological sense and where reflective cool roofs are the better fix.",
  },
  {
    color: "#d4d4d8",
    name: "Green-cover change",
    text: "Satellite comparison against the 2016-17 dry season showing where the city has gained or lost vegetation.",
  },
];

export default function Home() {
  const wards = topWards(5);

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <SiteHeader />

      <main className="flex-1">
        <Hero />

        <Reveal>
          <MapPreview />
        </Reveal>

        <Reveal>
          <section className="mx-auto max-w-5xl px-6 py-14">
            <h2 className="text-xl font-semibold text-foreground">Three ways to look at the city</h2>
            <div className="mt-6 space-y-6">
              {LAYERS.map((l) => (
                <div key={l.name} className="flex items-start gap-4">
                  <span
                    className="mt-1 h-4 w-4 shrink-0 rounded-sm"
                    style={{ background: l.color }}
                    aria-hidden
                  />
                  <div>
                    <h3 className="font-medium text-foreground">{l.name}</h3>
                    <p className="mt-1 max-w-2xl text-sm leading-relaxed text-muted-foreground">
                      {l.text}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </Reveal>

        <Reveal>
          <section className="border-t border-border bg-surface">
            <div className="mx-auto max-w-5xl px-6 py-14">
              <h2 className="text-xl font-semibold text-foreground">
                The five wards that need cooling most
              </h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Computed from the latest satellite pass, not hand-picked.
              </p>
              <ol className="mt-6 divide-y divide-border">
                {wards.map((w) => (
                  <li key={w.ward_id} className="flex items-baseline justify-between py-3">
                    <span className="flex items-baseline gap-3">
                      <span className="w-6 text-right font-mono text-sm text-muted-foreground">
                        {w.rank}
                      </span>
                      <span className="font-medium text-foreground">Ward {w.ward_id}</span>
                    </span>
                    <span className="font-mono text-sm text-muted-foreground">
                      HVI {w.HVI?.toFixed(1)}
                    </span>
                  </li>
                ))}
              </ol>
              <Link
                href="/dashboard"
                className="mt-6 inline-block text-sm font-medium text-brand-teal hover:underline"
              >
                See all 24 wards on the map
              </Link>
            </div>
          </section>
        </Reveal>

        <Mission />

        <Reveal>
          <CitationStrip />
        </Reveal>

        <Reveal>
          <section className="mx-auto max-w-5xl px-6 py-14">
            <h2 className="text-xl font-semibold text-foreground">Built in the open</h2>
            <p className="mt-2 max-w-2xl text-sm leading-relaxed text-muted-foreground">
              All data sources are free and public: Landsat satellite imagery, WorldPop population
              rasters, OpenStreetMap, and municipal ward boundaries. The method, its weights, and
              its limitations are documented on the{" "}
              <Link href="/methodology" className="text-brand-teal hover:underline">
                methodology
              </Link>{" "}
              page, including the parts that are proxies or estimates. This is a research prototype,
              not an official BMC tool.
            </p>
          </section>
        </Reveal>
      </main>

      <SiteFooter />
    </div>
  );
}
