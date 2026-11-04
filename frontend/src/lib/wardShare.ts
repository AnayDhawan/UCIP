/**
 * Where a ward's own page lives, for the canonical tag, the sitemap and the
 * share actions. One formula, so the sitemap URL and the canonical URL cannot
 * drift apart.
 *
 * Falls back to the production domain (see layout.tsx's siteUrl for why), so a
 * build with no env vars set still emits real URLs.
 */

import { wardSlug } from "./wardSlug";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://uciplatform.vercel.app";

export function wardPageUrl(wardId: string): string {
  return `${SITE_URL}/ward/${wardSlug(wardId)}`;
}

/** One line for a share message or the native share sheet. */
export function wardShareText(wardId: string, rank: number | null, totalWards: number, city: string): string {
  const place = rank === null ? "" : `, priority ${rank} of ${totalWards}`;
  return `Heat vulnerability in ${city} ward ${wardId}${place} (UCIP)`;
}

export function whatsappHref(text: string, url: string): string {
  return `https://wa.me/?text=${encodeURIComponent(`${text} ${url}`)}`;
}
