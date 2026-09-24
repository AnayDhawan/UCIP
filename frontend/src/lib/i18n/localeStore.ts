/**
 * The current locale, as an external store.
 *
 * The locale comes from the URL and localStorage, neither of which exists on
 * the server, so it cannot be read during render without the server HTML and
 * the first client render disagreeing. The obvious workaround is to start at
 * English and correct it in an effect, which works but is a `setState` in an
 * effect: React's own lint rule flags it, and it renders the English copy once
 * before replacing it, which on a slow phone is a visible flash of the wrong
 * language.
 *
 * `useSyncExternalStore` is the mechanism React provides for exactly this. The
 * server snapshot is the default locale, the client snapshot reads the real
 * source, and React handles the hydration boundary rather than the component
 * doing it by hand.
 */

import {
  DEFAULT_LOCALE,
  LOCALE_PARAM,
  LOCALE_STORAGE_KEY,
  resolveLocale,
  type Locale,
} from "./index";

type Listener = () => void;

const listeners = new Set<Listener>();

/** Cached so getSnapshot returns a stable value; React calls it on every render. */
let current: Locale | null = null;

function read(): Locale {
  let stored: string | null = null;
  try {
    stored = window.localStorage.getItem(LOCALE_STORAGE_KEY);
  } catch {
    // Private browsing, or storage disabled. The URL still carries it.
  }
  const fromUrl = new URLSearchParams(window.location.search).get(LOCALE_PARAM);
  return resolveLocale(fromUrl, stored);
}

export function subscribe(listener: Listener): () => void {
  listeners.add(listener);
  // The URL can change without this module doing it: the back button, or the
  // dashboard's own replaceState when map state moves.
  const onPop = () => {
    current = read();
    listeners.forEach((l) => l());
  };
  window.addEventListener("popstate", onPop);
  return () => {
    listeners.delete(listener);
    window.removeEventListener("popstate", onPop);
  };
}

export function getSnapshot(): Locale {
  current ??= read();
  return current;
}

/** The server has no URL parameters or storage, so it renders the default. */
export function getServerSnapshot(): Locale {
  return DEFAULT_LOCALE;
}

export function setLocale(next: Locale): void {
  current = next;

  try {
    window.localStorage.setItem(LOCALE_STORAGE_KEY, next);
  } catch {
    // Not fatal: the choice just will not survive a reload.
  }

  // replaceState rather than a router navigation, for the same reason the map's
  // own URL state uses it: this should not add a history entry per toggle, and
  // it must not remount the map underneath the reader.
  const url = new URL(window.location.href);
  if (next === DEFAULT_LOCALE) url.searchParams.delete(LOCALE_PARAM);
  else url.searchParams.set(LOCALE_PARAM, next);
  window.history.replaceState(null, "", url);

  listeners.forEach((l) => l());
}

/** Test seam: drops the cached value so the next read re-derives it. */
export function resetForTests(): void {
  current = null;
  listeners.clear();
}
