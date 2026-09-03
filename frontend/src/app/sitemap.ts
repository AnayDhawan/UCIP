import type { MetadataRoute } from "next";

// Falls back to the production domain (see layout.tsx's siteUrl for why), so a
// deploy with no env vars set still emits real URLs instead of localhost ones.
const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "https://uciplatform.vercel.app";

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();

  const routes = [
    { path: "/", priority: 1 },
    { path: "/dashboard", priority: 0.9 },
    { path: "/methodology", priority: 0.8 },
    { path: "/mission", priority: 0.6 },
    { path: "/simulate", priority: 0.6 },
    { path: "/contribute", priority: 0.5 },
    { path: "/contact", priority: 0.4 },
    { path: "/legal", priority: 0.2 },
  ];

  return routes.map(({ path, priority }) => ({
    url: `${siteUrl}${path}`,
    lastModified: now,
    priority,
  }));
}
