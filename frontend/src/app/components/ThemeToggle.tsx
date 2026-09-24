"use client";

import { useSyncExternalStore } from "react";
import { useTheme } from "next-themes";
import { Monitor, Moon, Sun } from "lucide-react";
import { useLocale } from "@/lib/i18n/LocaleProvider";

// `key` looks the label up in the dictionary; the value is what next-themes
// stores, so it stays "system" while the dictionary calls it "auto".
const MODES = [
  { value: "light", key: "light", Icon: Sun },
  { value: "dark", key: "dark", Icon: Moon },
  { value: "system", key: "auto", Icon: Monitor },
] as const;

const noopSubscribe = () => () => {};

/** True once hydrated on the client — avoids a light/dark mismatch flash. */
function useMounted(): boolean {
  return useSyncExternalStore(
    noopSubscribe,
    () => true,
    () => false
  );
}

export default function ThemeToggle() {
  const { t } = useLocale();
  const { theme, setTheme } = useTheme();
  const mounted = useMounted();

  if (!mounted) {
    // Reserve space to avoid layout shift before hydration
    return <div className="h-8 w-[108px]" aria-hidden />;
  }

  return (
    <div
      role="radiogroup"
      aria-label={t.theme.label}
      className="flex items-center rounded-full border border-border p-0.5"
    >
      {MODES.map(({ value, key, Icon }) => (
        <button
          key={value}
          role="radio"
          aria-checked={theme === value}
          aria-label={t.theme[key]}
          title={t.theme[key]}
          onClick={() => setTheme(value)}
          className={`rounded-full p-1.5 transition-colors ${
            theme === value
              ? "bg-brand-teal text-white"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          <Icon className="h-3.5 w-3.5" />
        </button>
      ))}
    </div>
  );
}
