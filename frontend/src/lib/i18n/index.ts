/**
 * The translation runtime (issue #122).
 *
 * Deliberately small, and deliberately not a library. The site has one
 * dictionary shape, three locales and no pluralisation rules that a lookup
 * plus a placeholder substitution cannot express. next-intl or i18next would
 * add a dependency, a build step and a config file to do what `format()` below
 * does in ten lines, and would not make the translations any better, which is
 * the part that is actually hard.
 *
 * Locale lives in the URL as `?lang=`, with localStorage as the fallback. The
 * URL winning matters for what this feature is for: someone sending a
 * neighbour a link to their ward's heat risk should be able to send it in the
 * language they will read it in. It also matches how map state is already
 * shared (see lib/mapState.ts).
 */

import { DICTIONARIES, type Dictionary } from "./dictionaries";
import { DEFAULT_LOCALE, type Locale } from "./locales";

export type { Dictionary };
export * from "./locales";
export { DICTIONARIES };

/** The query parameter carrying the language, alongside the map's own state. */
export const LOCALE_PARAM = "lang";

/** Where the preference persists between visits. */
export const LOCALE_STORAGE_KEY = "ucip.locale";

export function getDictionary(locale: Locale): Dictionary {
  return DICTIONARIES[locale] ?? DICTIONARIES[DEFAULT_LOCALE];
}

/**
 * Substitutes `{named}` placeholders.
 *
 * Named rather than positional because word order moves: English puts the rank
 * before the total ("3 of 24") and both Marathi and Hindi put the total first
 * ("२४ पैकी ३"). A positional scheme would silently swap the two numbers.
 *
 * A placeholder with no matching value is left as written rather than replaced
 * with "undefined", so a missing value looks like the bug it is instead of
 * like copy.
 */
export function format(template: string, values?: Record<string, string | number>): string {
  if (!values) return template;
  return template.replace(/\{(\w+)\}/g, (whole, key: string) =>
    key in values ? String(values[key]) : whole
  );
}

/**
 * Reads a dotted key out of a dictionary.
 *
 * Exists for the cases where a key is computed rather than written, such as
 * the indicator labels being looked up by indicator id. Component code
 * should prefer reaching into the dictionary directly, which the type checker
 * can verify and this cannot.
 */
export function lookup(dict: Dictionary, path: string): string | undefined {
  const value = path.split(".").reduce<unknown>(
    (node, key) => (node && typeof node === "object" ? (node as Record<string, unknown>)[key] : undefined),
    dict
  );
  return typeof value === "string" ? value : undefined;
}

/**
 * Translates recommendation text that arrives from the pipeline in English.
 *
 * `interventions` and `rationales` in the dictionary are keyed by the exact
 * English the rule engine emits. Text with no entry comes back unchanged, which
 * is the right failure: a rule added to the pipeline shows in English until
 * someone translates it, instead of vanishing or showing a key.
 */
export function translateRec(
  dict: Dictionary,
  group: "interventions" | "rationales" | "citations",
  text: string
): string {
  return (dict.recs[group] as Record<string, string>)[text] ?? text;
}
