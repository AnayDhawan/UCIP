"use client";

/**
 * Language picker (issue #122).
 *
 * Each language is written in its own script, never transliterated: someone
 * looking for Marathi is looking for "मराठी", and "Marathi" in Latin script is
 * a label for people who already read English. That is the opposite of who
 * this control is for.
 *
 * A plain `<select>` rather than a styled dropdown. It is one of the few
 * controls where the native widget is strictly better: it is keyboard
 * accessible without any work, it is announced correctly by screen readers, it
 * renders Devanagari with the system font that actually has the glyphs, and on
 * a phone it opens the platform picker instead of a list that has to be
 * scrolled inside a map page.
 */

import { LOCALES, LOCALE_META, type Locale } from "@/lib/i18n";
import { useLocale } from "@/lib/i18n/LocaleProvider";

export default function LanguageSwitcher({ className = "" }: { className?: string }) {
  const { locale, setLocale, t } = useLocale();

  return (
    <label className={`inline-flex items-center gap-2 text-sm ${className}`}>
      <span className="sr-only">{t.nav.chooseLanguage}</span>
      <svg
        aria-hidden="true"
        viewBox="0 0 24 24"
        className="h-4 w-4 shrink-0 text-muted-foreground"
        fill="none"
        stroke="currentColor"
        strokeWidth={1.5}
      >
        <circle cx="12" cy="12" r="9" />
        <path d="M3 12h18M12 3c2.5 2.6 2.5 15.4 0 18M12 3c-2.5 2.6-2.5 15.4 0 18" />
      </svg>
      <select
        value={locale}
        onChange={(event) => setLocale(event.target.value as Locale)}
        className="rounded-md border border-border bg-background px-2 py-1 text-foreground"
      >
        {LOCALES.map((code) => (
          // lang on each option so a screen reader pronounces "मराठी" with a
          // Marathi voice rather than reading Devanagari through English rules.
          <option key={code} value={code} lang={LOCALE_META[code].tag}>
            {LOCALE_META[code].nativeName}
          </option>
        ))}
      </select>
    </label>
  );
}
