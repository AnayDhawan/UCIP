/**
 * The dictionaries, and the type that keeps them in step.
 *
 * `Dictionary` is derived from the English file, and `mr.ts` and `hi.ts`
 * annotate themselves with it. That is the whole rot-prevention mechanism: a
 * key added to English and not to Marathi fails `next build`, rather than
 * shipping a Marathi page with an English sentence in the middle of it.
 *
 * The English literal is `as const`, so `Dictionary` would inherit its exact
 * string literal types and demand that Marathi say "Dashboard" too. `Loose<T>`
 * widens those back to `string` while keeping the key structure, which is the
 * part that has to match.
 */

import en from "./en";
import hi from "./hi";
import mr from "./mr";
import type { Locale } from "../locales";

/** Recursively widens literal types to string, keeping the shape. */
type Loose<T> = {
  [K in keyof T]: T[K] extends string ? string : Loose<T[K]>;
};

export type Dictionary = Loose<typeof en>;

/** Every dictionary, keyed by locale. */
export const DICTIONARIES: Record<Locale, Dictionary> = { en, mr, hi };

export { en, mr, hi };
