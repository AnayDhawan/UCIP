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
