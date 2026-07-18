import Link from "next/link";

export default function SiteFooter() {
  return (
    <footer className="border-t border-zinc-900/10 bg-zinc-50 dark:border-white/10 dark:bg-zinc-950">
      <div className="mx-auto max-w-5xl px-6 py-8 text-sm text-zinc-600 dark:text-zinc-400">
        <p>
          UCIP is a research prototype built for the Now or Never Hack 2026. It is not an official
          tool of the BMC or any government body.
        </p>
        <p className="mt-2">
          Data: Landsat (USGS), WorldPop, ESA WorldCover via Google Earth Engine; OpenStreetMap
          contributors; Datameet ward boundaries. Basemap by CARTO.
        </p>
        <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2">
          <Link href="/legal" className="hover:text-zinc-900 hover:underline dark:hover:text-zinc-100">
            Legal and data attribution
          </Link>
          <Link href="/contact" className="hover:text-zinc-900 hover:underline dark:hover:text-zinc-100">
            Contact
          </Link>
          <Link href="/support" className="hover:text-zinc-900 hover:underline dark:hover:text-zinc-100">
            Support the project
          </Link>
        </div>
      </div>
    </footer>
  );
}
