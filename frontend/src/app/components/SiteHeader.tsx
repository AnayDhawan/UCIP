"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, X } from "lucide-react";
import Logo from "./Logo";
import ThemeToggle from "./ThemeToggle";
import LanguageSwitcher from "./LanguageSwitcher";
import { useLocale } from "@/lib/i18n/LocaleProvider";

// Keyed into the dictionary rather than carrying its own label, so adding a
// destination means adding it to every language or failing the build (issue
// #122). A `label` string here would have been the one place that quietly
// stayed English.
const NAV = [
  { href: "/dashboard", key: "dashboard" },
  { href: "/cities", key: "cities" },
  { href: "/methodology", key: "methodology" },
  { href: "/simulate", key: "simulator" },
  { href: "/mission", key: "mission" },
  { href: "/contribute", key: "contribute" },
  { href: "/contact", key: "contact" },
] as const;

export default function SiteHeader({ compact = false }: { compact?: boolean }) {
  const pathname = usePathname();
  const { t } = useLocale();
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
        <Link href="/" aria-label={t.nav.homeLabel}>
          <Logo />
        </Link>

        <nav className="hidden items-center gap-1 md:flex" aria-label={t.nav.mainNav}>
          {NAV.map((item) => {
            const active =
              // Widened on purpose. No entry is "/" today, so `as const` makes
              // the comparison provably false and tsc rejects it as dead, but
              // the guard is what stops a future "/" entry matching every
              // route through startsWith.
              (item.href as string) === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href);
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
                {t.nav[item.key]}
              </Link>
            );
          })}
        </nav>

        <div className="hidden md:block">
          <LanguageSwitcher />
          <ThemeToggle />
        </div>

        <button
          className="rounded border border-border p-1.5 text-muted-foreground md:hidden"
          onClick={() => setOpen(true)}
          aria-expanded={open}
          aria-controls="mobile-menu"
          aria-label={t.nav.openMenu}
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
          aria-label={t.nav.siteMenu}
          aria-hidden={!open}
          inert={!open}
          className={`absolute inset-y-0 right-0 flex h-full w-full flex-col bg-background transition-transform duration-300 ease-out ${
            open ? "translate-x-0" : "translate-x-full"
          }`}
        >
        <div className="flex items-center justify-between gap-4 border-b border-border px-6 py-3">
          <Link href="/" aria-label={t.nav.homeLabel} onClick={() => setOpen(false)}>
            <Logo />
          </Link>
          <button
            ref={closeButton}
            className="rounded border border-border p-1.5 text-muted-foreground"
            onClick={() => setOpen(false)}
            aria-label={t.nav.closeMenu}
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex flex-1 flex-col gap-1 overflow-y-auto px-6 py-6" aria-label={t.nav.mobileNav}>
          {NAV.map((item) => {
            const active =
              // Widened on purpose. No entry is "/" today, so `as const` makes
              // the comparison provably false and tsc rejects it as dead, but
              // the guard is what stops a future "/" entry matching every
              // route through startsWith.
              (item.href as string) === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href);
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
                {t.nav[item.key]}
              </Link>
            );
          })}
        </nav>

          <div className="border-t border-border px-6 py-4">
            <LanguageSwitcher />
            <ThemeToggle />
          </div>
        </div>
      </div>
    </>
  );
}
