"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import Logo from "./Logo";
import ThemeToggle from "./ThemeToggle";

const NAV = [
  { href: "/", label: "Home" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/methodology", label: "How it works" },
  { href: "/support", label: "Support" },
  { href: "/contact", label: "Contact" },
];

export default function SiteHeader({ compact = false }: { compact?: boolean }) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <header
      className={`border-b border-zinc-900/10 bg-zinc-50 dark:border-white/10 dark:bg-zinc-950 ${
        compact ? "" : ""
      }`}
    >
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
                    ? "font-semibold text-zinc-900 dark:text-zinc-50"
                    : "text-zinc-600 hover:bg-zinc-900/[.04] hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-white/[.06] dark:hover:text-zinc-100"
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
          className="rounded border border-zinc-900/10 px-3 py-1.5 text-sm text-zinc-700 md:hidden dark:border-white/15 dark:text-zinc-300"
          onClick={() => setOpen(!open)}
          aria-expanded={open}
          aria-label="Toggle menu"
        >
          Menu
        </button>
      </div>

      {open && (
        <div className="border-t border-zinc-900/10 px-6 py-3 md:hidden dark:border-white/10">
          <nav className="flex flex-col gap-1" aria-label="Main mobile">
            {NAV.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setOpen(false)}
                className="rounded px-2 py-2 text-sm text-zinc-700 hover:bg-zinc-900/[.04] dark:text-zinc-300 dark:hover:bg-white/[.06]"
              >
                {item.label}
              </Link>
            ))}
          </nav>
          <div className="mt-3">
            <ThemeToggle />
          </div>
        </div>
      )}
    </header>
  );
}
