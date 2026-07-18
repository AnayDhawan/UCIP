"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import WardCards from "../components/WardCards";
import SiteHeader from "../components/SiteHeader";

const WardChoropleth = dynamic(() => import("../components/WardChoropleth"), {
  ssr: false,
  loading: () => <div className="p-8 text-zinc-500">Loading map…</div>,
});

const HINT_KEY = "ucip-dashboard-hint-dismissed";

function FirstVisitHint() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!localStorage.getItem(HINT_KEY)) setVisible(true);
  }, []);

  if (!visible) return null;

  return (
    <div className="flex items-center justify-between gap-4 border-b border-teal-600/20 bg-teal-50 px-6 py-2 text-sm text-teal-950 dark:border-teal-400/20 dark:bg-teal-950/40 dark:text-teal-100">
      <p>
        Colors rank Mumbai&apos;s 24 wards by heat vulnerability. Click any ward for details, switch
        layers top-right, or read{" "}
        <Link href="/methodology" className="font-medium underline">
          how it works
        </Link>
        .
      </p>
      <button
        onClick={() => {
          localStorage.setItem(HINT_KEY, "1");
          setVisible(false);
        }}
        className="shrink-0 rounded px-2 py-0.5 text-xs font-medium hover:bg-teal-600/10 dark:hover:bg-teal-400/10"
        aria-label="Dismiss hint"
      >
        Got it
      </button>
    </div>
  );
}

export default function Dashboard() {
  return (
    <div className="flex h-screen flex-col bg-zinc-50 dark:bg-zinc-950">
      <SiteHeader compact />
      <FirstVisitHint />
      <main className="relative flex flex-1 overflow-hidden">
        <div className="relative flex-1">
          <WardChoropleth />
        </div>
        <aside className="hidden w-96 shrink-0 border-l border-zinc-900/10 bg-zinc-50 md:block dark:border-white/10 dark:bg-zinc-950">
          <WardCards />
        </aside>
      </main>
    </div>
  );
}
