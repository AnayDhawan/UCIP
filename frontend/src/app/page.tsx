"use client";

import Link from "next/link";
import dynamic from "next/dynamic";
import WardCards from "./components/WardCards";
import Logo from "./components/Logo";

const WardChoropleth = dynamic(() => import("./components/WardChoropleth"), {
  ssr: false,
  loading: () => <div className="p-8 text-zinc-500">Loading map…</div>,
});

export default function Home() {
  return (
    <div className="flex h-screen flex-col bg-zinc-50 dark:bg-black">
      <header className="flex items-center justify-between border-b border-black/[.08] bg-white px-6 py-4 dark:border-white/[.145] dark:bg-black">
        <div className="flex items-center gap-3">
          <Logo />
          <div className="h-8 w-px bg-black/[.08] dark:bg-white/[.145]" />
          <div>
            <h1 className="text-base font-medium text-black dark:text-zinc-50">
              Mumbai Ward Heat Vulnerability
            </h1>
            <p className="text-sm text-zinc-600 dark:text-zinc-400">
              24 BMC wards ranked by Heat Vulnerability Index (HVI). Darker = higher priority for cooling investment.
            </p>
          </div>
        </div>
        <Link
          href="/methodology"
          className="shrink-0 rounded border border-black/[.08] px-3 py-1.5 text-sm font-medium text-black hover:bg-black/[.04] dark:border-white/[.145] dark:text-zinc-50 dark:hover:bg-white/[.08]"
        >
          Methodology →
        </Link>
      </header>
      <main className="relative flex flex-1 overflow-hidden">
        <div className="relative flex-1">
          <WardChoropleth />
        </div>
        <aside className="w-96 shrink-0 border-l border-black/[.08] bg-white dark:border-white/[.145] dark:bg-black">
          <WardCards />
        </aside>
      </main>
    </div>
  );
}
