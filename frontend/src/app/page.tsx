import fs from "fs";
import path from "path";
import Link from "next/link";
import Image from "next/image";
import SiteHeader from "./components/SiteHeader";
import SiteFooter from "./components/SiteFooter";

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
    <div className="flex min-h-screen flex-col bg-zinc-50 dark:bg-zinc-950">
      <SiteHeader />

      <main className="flex-1">
        <section className="border-b border-zinc-900/10 bg-gradient-to-b from-teal-50 to-zinc-50 dark:border-white/10 dark:from-teal-950/30 dark:to-zinc-950">
          <div className="mx-auto max-w-5xl px-6 py-16 md:py-24">
            <div className="flex flex-col items-start gap-10 md:flex-row md:items-center">
              <div className="max-w-xl">
                <h1 className="text-4xl font-semibold leading-tight tracking-tight text-zinc-900 md:text-5xl dark:text-zinc-50">
                  Which parts of Mumbai need cooling first?
                </h1>
                <p className="mt-4 text-lg leading-relaxed text-zinc-700 dark:text-zinc-300">
                  UCIP maps heat vulnerability across all 24 city wards using satellite and
                  population data, then recommends what to build where: trees, cool roofs, shaded
                  cooling centres. Every number is computed and every claim cites its source.
                </p>
                <div className="mt-8 flex flex-wrap gap-3">
                  <Link
                    href="/dashboard"
                    className="rounded-lg bg-teal-700 px-5 py-2.5 text-sm font-semibold text-teal-50 transition-colors hover:bg-teal-800 dark:bg-teal-500 dark:text-teal-950 dark:hover:bg-teal-400"
                  >
                    Open the dashboard
                  </Link>
                  <Link
                    href="/methodology"
                    className="rounded-lg border border-zinc-900/15 px-5 py-2.5 text-sm font-semibold text-zinc-800 transition-colors hover:bg-zinc-900/[.04] dark:border-white/20 dark:text-zinc-200 dark:hover:bg-white/[.06]"
                  >
                    How it works
                  </Link>
                </div>
              </div>
              <div className="hidden shrink-0 md:block">
                <Image
                  src="/logo-icon.png"
                  alt=""
                  width={200}
                  height={200}
                  priority
                  className="opacity-90"
                />
              </div>
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-5xl px-6 py-14">
          <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50">
            Three ways to look at the city
          </h2>
          <div className="mt-6 space-y-6">
            {LAYERS.map((l) => (
              <div key={l.name} className="flex items-start gap-4">
                <span
                  className="mt-1 h-4 w-4 shrink-0 rounded-sm"
                  style={{ background: l.color }}
                  aria-hidden
                />
                <div>
                  <h3 className="font-medium text-zinc-900 dark:text-zinc-50">{l.name}</h3>
                  <p className="mt-1 max-w-2xl text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
                    {l.text}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="border-t border-zinc-900/10 bg-white dark:border-white/10 dark:bg-zinc-900/40">
          <div className="mx-auto max-w-5xl px-6 py-14">
            <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50">
              The five wards that need cooling most
            </h2>
            <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
              Computed from the latest satellite pass, not hand-picked.
            </p>
            <ol className="mt-6 divide-y divide-zinc-900/10 dark:divide-white/10">
              {wards.map((w) => (
                <li key={w.ward_id} className="flex items-baseline justify-between py-3">
                  <span className="flex items-baseline gap-3">
                    <span className="w-6 text-right font-mono text-sm text-zinc-500">{w.rank}</span>
                    <span className="font-medium text-zinc-900 dark:text-zinc-50">
                      Ward {w.ward_id}
                    </span>
                  </span>
                  <span className="font-mono text-sm text-zinc-600 dark:text-zinc-400">
                    HVI {w.HVI?.toFixed(1)}
                  </span>
                </li>
              ))}
            </ol>
            <Link
              href="/dashboard"
              className="mt-6 inline-block text-sm font-medium text-teal-700 hover:underline dark:text-teal-400"
            >
              See all 24 wards on the map
            </Link>
          </div>
        </section>

        <section className="mx-auto max-w-5xl px-6 py-14">
          <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50">
            Built in the open
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
            All data sources are free and public: Landsat satellite imagery, WorldPop population
            rasters, OpenStreetMap, and municipal ward boundaries. The method, its weights, and its
            limitations are documented on the{" "}
            <Link href="/methodology" className="text-teal-700 hover:underline dark:text-teal-400">
              how it works
            </Link>{" "}
            page, including the parts that are proxies or estimates. This is a research prototype,
            not an official BMC tool.
          </p>
        </section>
      </main>

      <SiteFooter />
    </div>
  );
}
