import type { MetadataRoute } from "next";

// TODO: NEXT_PUBLIC_SITE_URL isn't set anywhere in the repo yet (see
// layout.tsx's siteUrl), so this falls back to localhost until a production
// domain is documented.
const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";

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
