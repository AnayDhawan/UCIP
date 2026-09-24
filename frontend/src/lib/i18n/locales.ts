/**
 * The locales this site ships (issue #122).
 *
 * A civic tool about Mumbai that exists only in English excludes most of
 * Mumbai, and heat vulnerability concentrates in exactly the communities least
 * likely to be served by an English-only interface. Marathi is the state
 * language and Hindi is the city's most widely understood second language, so
 * those are the two that matter first.
 *
 * `reviewed` is the honest part. It records whether a native speaker has
 * checked the translation, and it is false for both new locales. The
 * translations are careful, but "careful" is not "checked", and a tool telling
 * people where heat risk is highest is the wrong place to quietly assume they
 * are the same thing. It is surfaced in the repo and in the contributor docs
 * rather than in the interface: a banner saying "this may be wrong" on the
 * Marathi version only, and not on the English, would be its own kind of
 * insult.
 */

export const LOCALES = ["en", "mr", "hi"] as const;

export type Locale = (typeof LOCALES)[number];

export const DEFAULT_LOCALE: Locale = "en";

export type LocaleMeta = {
  /** The language's name in that language, which is what a switcher should show. */
  nativeName: string;
  /** The name in English, for documentation and the `lang` attribute's sake. */
  englishName: string;
  /** BCP 47 tag for the `lang` attribute. */
  tag: string;
  /** Whether a native speaker has reviewed this translation. */
  reviewed: boolean;
};

export const LOCALE_META: Record<Locale, LocaleMeta> = {
  en: {
    nativeName: "English",
    englishName: "English",
    tag: "en-IN",
    reviewed: true,
  },
  mr: {
    nativeName: "मराठी",
    englishName: "Marathi",
    tag: "mr-IN",
    reviewed: false,
  },
  hi: {
    nativeName: "हिंदी",
    englishName: "Hindi",
    tag: "hi-IN",
    reviewed: false,
  },
};

export function isLocale(value: unknown): value is Locale {
  return typeof value === "string" && (LOCALES as readonly string[]).includes(value);
}

/**
 * The locale to use, given a URL parameter and a stored preference.
 *
 * The URL wins, so a shared link carries its language. That matters for the
 * thing this feature is for: someone sending a ward's heat risk to a neighbour
 * should be able to send it in the language they will read it in.
 */
export function resolveLocale(fromUrl: string | null, stored: string | null): Locale {
  if (isLocale(fromUrl)) return fromUrl;
  if (isLocale(stored)) return stored;
  return DEFAULT_LOCALE;
}
