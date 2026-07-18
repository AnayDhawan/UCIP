"use client";

import { useEffect, useState } from "react";
import { useTheme } from "next-themes";

const MODES = [
  { value: "light", label: "Light" },
  { value: "dark", label: "Dark" },
  { value: "system", label: "Auto" },
] as const;

export default function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  if (!mounted) {
    // Reserve space to avoid layout shift before hydration
    return <div className="h-8 w-[132px]" aria-hidden />;
  }

  return (
    <div
      role="radiogroup"
      aria-label="Color theme"
      className="flex items-center rounded-full border border-zinc-900/10 p-0.5 dark:border-white/15"
    >
      {MODES.map((m) => (
        <button
          key={m.value}
          role="radio"
          aria-checked={theme === m.value}
          onClick={() => setTheme(m.value)}
          className={`rounded-full px-2.5 py-1 text-xs font-medium transition-colors ${
            theme === m.value
              ? "bg-zinc-900 text-zinc-50 dark:bg-zinc-100 dark:text-zinc-900"
              : "text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100"
          }`}
        >
          {m.label}
        </button>
      ))}
    </div>
  );
}
