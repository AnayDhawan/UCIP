"use client";

import dynamic from "next/dynamic";

const WardChoropleth = dynamic(() => import("./components/WardChoropleth"), {
  ssr: false,
  loading: () => <div className="p-8 text-zinc-500">Loading map…</div>,
});

export default function Home() {
  return (
    <div className="flex flex-1 flex-col bg-zinc-50 dark:bg-black">
      <header className="border-b border-black/[.08] bg-white px-6 py-4 dark:border-white/[.145] dark:bg-black">
        <h1 className="text-xl font-semibold text-black dark:text-zinc-50">
          UCIP — Mumbai Ward Heat Vulnerability
        </h1>
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          24 BMC wards ranked by Heat Vulnerability Index (HVI). Darker = higher priority for cooling investment.
        </p>
      </header>
      <main className="relative flex-1">
        <WardChoropleth />
      </main>
    </div>
  );
}
