"use client";

import { Suspense, useEffect, useState, useSyncExternalStore } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import WardPanel from "../components/WardPanel";
import WardDialog from "../components/WardDialog";
import SiteHeader from "../components/SiteHeader";

const WardChoropleth = dynamic(() => import("../components/WardChoropleth"), {
  ssr: false,
  loading: () => <div className="p-8 text-zinc-500">Loading map…</div>,
});

/** Matches the `md` breakpoint the sidebar is gated on (`hidden md:block`). */
const SIDEBAR_QUERY = "(min-width: 48rem)";

function subscribeSidebar(callback: () => void) {
  const mql = window.matchMedia(SIDEBAR_QUERY);
  mql.addEventListener("change", callback);
  return () => mql.removeEventListener("change", callback);
}

function getSidebarSnapshot() {
  return window.matchMedia(SIDEBAR_QUERY).matches;
}

function getSidebarServerSnapshot() {
  return false;
}

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
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const selectedWardId = searchParams.get("ward");
  const [isFullscreen, setIsFullscreen] = useState(false);
  const sidebarVisible = useSyncExternalStore(
    subscribeSidebar,
    getSidebarSnapshot,
    getSidebarServerSnapshot
  );
  /** The sidebar shows the ward itself whenever it is on screen, so the dialog
   *  is only for the cases where there is no sidebar. */
  const dialogHandlesWard = isFullscreen || !sidebarVisible;

  /**
   * The URL is the source of truth for ward selection, not local state.
   * Selecting a ward pushes a new history entry (so browser Back steps back
   * to the list instead of leaving the dashboard entirely); clearing the
   * selection replaces the current entry instead of adding another one.
   *
   * Uses the History API rather than router.push/replace. This route is
   * statically prerendered, and after a cold load of a URL that already
   * carries `?ward=`, both router methods became silent no-ops: selecting a
   * different ward or closing the panel left the URL, and therefore the
   * selection, stuck on whatever was loaded. Next supports history.pushState
   * and replaceState for search-param updates, and useSearchParams re-renders
   * from them.
   */
  function selectWard(wardId: string | null) {
    const params = new URLSearchParams(searchParams.toString());
    if (wardId) {
      params.set("ward", wardId);
      window.history.pushState(null, "", `${pathname}?${params.toString()}`);
    } else {
      params.delete("ward");
      const qs = params.toString();
      window.history.replaceState(null, "", qs ? `${pathname}?${qs}` : pathname);
    }
  }

  /**
   * Escape exits fullscreen, but only when no ward dialog is open. Radix owns
   * Escape while the dialog is up; without this guard a single press would
   * close the dialog and drop out of fullscreen at the same time.
   */
  useEffect(() => {
    // Only skip when the dialog owns Escape; with the ward in the sidebar there
    // is no dialog to close first, so Escape should still exit fullscreen.
    if (!isFullscreen || (selectedWardId && dialogHandlesWard)) return;
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") setIsFullscreen(false);
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [isFullscreen, selectedWardId, dialogHandlesWard]);

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
          // Narrower than it was: the list is an index into the map, not the
          // main event, and every pixel it gives back goes to the map.
          <aside className="hidden w-72 shrink-0 border-l border-border bg-background md:block lg:w-80">
            <WardPanel selectedWardId={selectedWardId} onSelectWard={selectWard} />
          </aside>
        )}
      </main>
      {/* Outside <main> and outside the fullscreen guards on purpose: this is
          the only ward-detail surface now, so it has to work in fullscreen and
          below the md breakpoint, where the aside above does not exist. */}
      <WardDialog
        selectedWardId={selectedWardId}
        onSelectWard={selectWard}
        enabled={dialogHandlesWard}
      />
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
