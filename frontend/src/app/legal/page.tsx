import type { Metadata } from "next";
import SiteHeader from "../components/SiteHeader";
import SiteFooter from "../components/SiteFooter";

export const metadata: Metadata = {
  title: "Legal and data attribution | UCIP",
  description: "License, data sources, and disclaimers for UCIP",
};

const SOURCES = [
  { name: "Landsat 8/9 Collection 2 (USGS)", use: "Land surface temperature and NDVI composites" },
  { name: "WorldPop age-sex rasters", use: "Population density and elderly-share estimates" },
  { name: "ESA WorldCover v200", use: "Land cover, impervious surface, plantability screening" },
  { name: "Google Earth Engine", use: "Satellite data access and zonal statistics" },
  { name: "OpenStreetMap contributors", use: "Hospital locations (ODbL)" },
  { name: "Datameet Municipal Spatial Data", use: "BMC ward boundaries and slum-cluster polygons" },
  { name: "CARTO / OpenStreetMap", use: "Basemap tiles on the dashboard" },
];

export default function LegalPage() {
  return (
    <div className="flex min-h-screen flex-col bg-zinc-50 dark:bg-zinc-950">
      <SiteHeader />
      <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-12">
        <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-50">
          Legal and data attribution
        </h1>

        <h2 className="mt-8 text-lg font-semibold text-zinc-900 dark:text-zinc-50">License</h2>
        <p className="mt-2 text-sm leading-relaxed text-zinc-700 dark:text-zinc-300">
          UCIP&apos;s code is released under the MIT License. You are free to use, modify, and
          redistribute it, including commercially, as long as the license notice is preserved.
        </p>

        <h2 className="mt-8 text-lg font-semibold text-zinc-900 dark:text-zinc-50">Data sources</h2>
        <p className="mt-2 text-sm leading-relaxed text-zinc-700 dark:text-zinc-300">
          Every dataset behind UCIP is free and public. Each carries its own license, which remains
          with the upstream provider:
        </p>
        <table className="mt-4 w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-900/15 text-left dark:border-white/15">
              <th className="py-2 pr-4 font-semibold text-zinc-900 dark:text-zinc-50">Source</th>
              <th className="py-2 font-semibold text-zinc-900 dark:text-zinc-50">Used for</th>
            </tr>
          </thead>
          <tbody>
            {SOURCES.map((s) => (
              <tr key={s.name} className="border-b border-zinc-900/[.07] align-top dark:border-white/[.07]">
                <td className="py-2 pr-4 text-zinc-800 dark:text-zinc-200">{s.name}</td>
                <td className="py-2 text-zinc-600 dark:text-zinc-400">{s.use}</td>
              </tr>
            ))}
          </tbody>
        </table>

        <h2 className="mt-8 text-lg font-semibold text-zinc-900 dark:text-zinc-50">Disclaimers</h2>
        <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-relaxed text-zinc-700 dark:text-zinc-300">
          <li>
            UCIP is a research prototype built for a hackathon. It is not an official tool of the
            Brihanmumbai Municipal Corporation or any government body, and no decision should rest
            on it alone.
          </li>
          <li>
            The heat measure is land surface temperature from satellites, which is not the same as
            the air temperature people feel.
          </li>
          <li>
            Slum density and elderly share are estimated from public proxies, not census records.
            The methodology page lists every proxy openly.
          </li>
          <li>
            Intervention recommendations are literature-based suggestions, not engineering
            assessments of specific sites.
          </li>
        </ul>
      </main>
      <SiteFooter />
    </div>
  );
}
