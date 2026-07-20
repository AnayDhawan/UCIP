"use client";

import { Suspense, useEffect, useState, useSyncExternalStore } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import WardPanel from "../components/WardPanel";
import SiteHeader from "../components/SiteHeader";

const WardChoropleth = dynamic(() => import("../components/WardChoropleth"), {
  ssr: false,
  loading: () => <div className="p-8 text-zinc-500">Loading map…</div>,
});

const HINT_KEY = "ucip-dashboard-hint-dismissed";
const hintListeners = new Set<() => void>();

function dismissFirstVisitHint() {
  localStorage.setItem(HINT_KEY, "1");
  hintListeners.forEach((listener) => listener());
}

function subscribeFirstVisitHint(callback: () => void) {
  hintListeners.add(callback);
  return () => hintListeners.delete(callback);
}

function getFirstVisitHintSnapshot() {
  return !localStorage.getItem(HINT_KEY);
}

function getFirstVisitHintServerSnapshot() {
  return false;
}

function FirstVisitHint() {
  const visible = useSyncExternalStore(
    subscribeFirstVisitHint,
    getFirstVisitHintSnapshot,
    getFirstVisitHintServerSnapshot
  );

  if (!visible) return null;

  return (
    <div className="flex items-center justify-between gap-4 border-b border-brand-teal/20 bg-brand-teal/10 px-6 py-2 text-sm text-foreground">
      <p>
        Colors rank Mumbai&apos;s 24 wards by heat vulnerability. Click any ward, on the map or in
        the list, to see its breakdown and recommendation. Switch layers top-right, or read the{" "}
        <Link href="/methodology" className="font-medium underline">
          methodology
        </Link>
        .
      </p>
      <button
        onClick={dismissFirstVisitHint}
        className="shrink-0 rounded px-2 py-0.5 text-xs font-medium hover:bg-brand-teal/10"
        aria-label="Dismiss hint"
      >
        Got it
      </button>
    </div>
  );
}

function DashboardContent() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const selectedWardId = searchParams.get("ward");
  const [isFullscreen, setIsFullscreen] = useState(false);

  /**
   * The URL is the source of truth for ward selection, not local state.
   * Selecting a ward pushes a new history entry (so browser Back steps back
   * to the list instead of leaving the dashboard entirely); clearing the
   * selection replaces the current entry instead of adding another one.
   */
  function selectWard(wardId: string | null) {
    const params = new URLSearchParams(searchParams.toString());
    if (wardId) {
      params.set("ward", wardId);
      router.push(`${pathname}?${params.toString()}`, { scroll: false });
    } else {
      params.delete("ward");
      const qs = params.toString();
      router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false });
    }
  }

  useEffect(() => {
    if (!isFullscreen) return;
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") setIsFullscreen(false);
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [isFullscreen]);

  return (
    <div className="flex h-screen flex-col bg-background">
      {!isFullscreen && <SiteHeader compact />}
      {!isFullscreen && <FirstVisitHint />}
      <main className="relative flex flex-1 overflow-hidden">
        <div className="relative flex-1">
          <WardChoropleth
            selectedWardId={selectedWardId}
            onSelectWard={selectWard}
            isFullscreen={isFullscreen}
            onToggleFullscreen={() => setIsFullscreen((v) => !v)}
          />
        </div>
        {!isFullscreen && (
          <aside className="hidden w-96 shrink-0 border-l border-border bg-background md:block">
            <WardPanel selectedWardId={selectedWardId} onSelectWard={selectWard} />
          </aside>
        )}
      </main>
    </div>
  );
}

export default function Dashboard() {
  return (
    <Suspense fallback={<div className="flex h-screen items-center justify-center text-muted-foreground">Loading…</div>}>
      <DashboardContent />
    </Suspense>
  );
}
