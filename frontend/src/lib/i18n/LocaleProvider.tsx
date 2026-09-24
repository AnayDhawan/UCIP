"use client";

/**
 * Makes the current locale and its dictionary available to the tree.
 *
 * Client-side rather than a `[locale]` route segment. That is a real trade-off
 * and worth stating: route segments give each language its own URL and let
 * search engines index them separately, which is better for discovery. They
 * also mean restructuring all ten pages and every internal link, and this
 * change is already the first time any copy in the codebase has been anything
 * other than a hardcoded English string. `?lang=` keeps the language in the
 * URL, so links remain shareable in the reader's language, which was the
 * point. Moving to segments later is a routing change, not a copy change,
 * because the dictionaries and the call sites stay exactly as they are.
 *
 * The locale itself lives in `localeStore.ts` and is read through
 * `useSyncExternalStore`; see that file for why it is not a `useState` plus an
 * effect.
 *
 * The document's `lang` attribute is kept in step, because a screen reader
 * announcing Marathi text with an English voice is unusable, and that is
 * precisely the audience this feature exists for.
 */

import { createContext, useContext, useEffect, useMemo, useSyncExternalStore } from "react";
import {
  DEFAULT_LOCALE,
  LOCALE_META,
  format,
  getDictionary,
  type Dictionary,
  type Locale,
} from "./index";
import { getServerSnapshot, getSnapshot, setLocale, subscribe } from "./localeStore";

type LocaleContextValue = {
  locale: Locale;
  /** The dictionary for the current locale. */
  t: Dictionary;
  setLocale: (next: Locale) => void;
  /** `format`, so a call site needs one import rather than two. */
  f: (template: string, values?: Record<string, string | number>) => string;
};

const LocaleContext = createContext<LocaleContextValue | null>(null);

export function LocaleProvider({ children }: { children: React.ReactNode }) {
  const locale = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  useEffect(() => {
    document.documentElement.lang = LOCALE_META[locale].tag;
  }, [locale]);

  const value = useMemo<LocaleContextValue>(
    () => ({ locale, t: getDictionary(locale), setLocale, f: format }),
    [locale]
  );

  return <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>;
}

/**
 * The dictionary and the current locale.
 *
 * Falls back to English rather than throwing when there is no provider above
 * it. A missing provider should degrade to the language the site already
 * spoke, not blank the page: this wraps a map someone may be using to decide
 * something.
 */
export function useLocale(): LocaleContextValue {
  const ctx = useContext(LocaleContext);
  if (ctx) return ctx;
  return {
    locale: DEFAULT_LOCALE,
    t: getDictionary(DEFAULT_LOCALE),
    setLocale: () => {},
    f: format,
  };
}
