"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, X } from "lucide-react";
import Logo from "./Logo";
import ThemeToggle from "./ThemeToggle";

const NAV = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/methodology", label: "Methodology" },
  { href: "/simulate", label: "Simulator" },
  { href: "/mission", label: "Mission" },
  { href: "/contribute", label: "Contribute" },
  { href: "/contact", label: "Contact" },
];

export default function SiteHeader({ compact = false }: { compact?: boolean }) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const closeButton = useRef<HTMLButtonElement>(null);

  /** The panel covers the page, so the page behind it must not scroll under it. */
  useEffect(() => {
    if (!open) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    closeButton.current?.focus();
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    window.addEventListener("keydown", onKeyDown);
    return () => {
      document.body.style.overflow = previous;
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  return (
    <>
    <header className="sticky top-0 z-50 border-b border-border bg-background/95 backdrop-blur-sm">
      <div
        className={`mx-auto flex items-center justify-between gap-4 px-6 ${
          compact ? "py-2" : "max-w-5xl py-3"
        }`}
      >
        <Link href="/" aria-label="UCIP home">
          <Logo />
        </Link>

        <nav className="hidden items-center gap-1 md:flex" aria-label="Main">
          {NAV.map((item) => {
            const active =
              item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={`rounded px-3 py-1.5 text-sm transition-colors ${
                  active
                    ? "font-semibold text-foreground"
                    : "text-muted-foreground hover:bg-surface-hover hover:text-foreground"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="hidden md:block">
          <ThemeToggle />
        </div>

        <button
          className="rounded border border-border p-1.5 text-muted-foreground md:hidden"
          onClick={() => setOpen(true)}
          aria-expanded={open}
          aria-controls="mobile-menu"
          aria-label="Open menu"
        >
          <Menu className="h-5 w-5" />
        </button>
      </div>
    </header>

      {/* Full-page panel sliding in from the right. Rendered rather than mounted
          conditionally so the slide has something to animate from, and made
          inert when closed so its links stay out of the tab order.

          Two positioning constraints, both learned the hard way:
          1. It lives outside <header>, because the header's `backdrop-blur`
             creates a containing block for fixed descendants, which pins the
             panel to the header's box instead of the viewport.
          2. The fixed, overflow-hidden wrapper is load-bearing: parked
             off-canvas the panel sits a full viewport to the right, and without
             something clipping it the page becomes horizontally scrollable.
             Clipping on <body> does not help, since a fixed element's overflow
             is attributed to the viewport rather than to body. */}
      <div
        className={`fixed inset-0 z-[60] overflow-hidden md:hidden ${open ? "" : "pointer-events-none"}`}
      >
        <div
          id="mobile-menu"
          role="dialog"
          aria-modal="true"
          aria-label="Site menu"
          aria-hidden={!open}
          inert={!open}
          className={`absolute inset-y-0 right-0 flex h-full w-full flex-col bg-background transition-transform duration-300 ease-out ${
            open ? "translate-x-0" : "translate-x-full"
          }`}
        >
        <div className="flex items-center justify-between gap-4 border-b border-border px-6 py-3">
          <Link href="/" aria-label="UCIP home" onClick={() => setOpen(false)}>
            <Logo />
          </Link>
          <button
            ref={closeButton}
            className="rounded border border-border p-1.5 text-muted-foreground"
            onClick={() => setOpen(false)}
            aria-label="Close menu"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex flex-1 flex-col gap-1 overflow-y-auto px-6 py-6" aria-label="Main mobile">
          {NAV.map((item) => {
            const active =
              item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={active ? "page" : undefined}
                onClick={() => setOpen(false)}
                className={`rounded-lg px-3 py-3 text-lg transition-colors ${
                  active
                    ? "font-semibold text-foreground"
                    : "text-muted-foreground hover:bg-surface-hover hover:text-foreground"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

          <div className="border-t border-border px-6 py-4">
            <ThemeToggle />
          </div>
        </div>
      </div>
    </>
  );
}
