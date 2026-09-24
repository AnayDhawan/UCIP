"use client";

import { useSyncExternalStore } from "react";
import { useTheme } from "next-themes";
import { Monitor, Moon, Sun } from "lucide-react";

const MODES = [
  { value: "light", label: "Light", Icon: Sun },
  { value: "dark", label: "Dark", Icon: Moon },
  { value: "system", label: "Auto", Icon: Monitor },
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
  const { theme, setTheme } = useTheme();
  const mounted = useMounted();

  if (!mounted) {
    // Reserve space to avoid layout shift before hydration
    return <div className="h-8 w-[108px]" aria-hidden />;
  }

  return (
    <div
      role="radiogroup"
      aria-label="Color theme"
      className="flex items-center rounded-full border border-border p-0.5"
    >
      {MODES.map(({ value, label, Icon }) => (
        <button
          key={value}
          role="radio"
          aria-checked={theme === value}
          aria-label={label}
          title={label}
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
