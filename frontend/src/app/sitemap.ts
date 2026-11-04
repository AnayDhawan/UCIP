import type { MetadataRoute } from "next";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { wardPageUrl } from "@/lib/wardShare";
import { wardFeatures } from "@/lib/wardSnapshot";

// Falls back to the production domain (see layout.tsx's siteUrl for why), so a
// deploy with no env vars set still emits real URLs instead of localhost ones.
const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "https://uciplatform.vercel.app";

// When the data last changed, from the pipeline run log. Using the build time
// would stamp every page as modified on each deploy. Undefined when no run has
// been recorded, which omits lastModified rather than guessing one.
function lastRefresh(): Date | undefined {
  try {
    const log = JSON.parse(
      readFileSync(join(process.cwd(), "public", "pipeline_run_log.json"), "utf8")
    ) as { finished_at?: string };
    const finished = log.finished_at ? new Date(log.finished_at) : undefined;
    return finished && !Number.isNaN(finished.getTime()) ? finished : undefined;
  } catch {
    return undefined;
  }
}

export default function sitemap(): MetadataRoute.Sitemap {
  const refreshed = lastRefresh();

  const routes = [
    { path: "/", priority: 1, dataPage: false },
    { path: "/dashboard", priority: 0.9, dataPage: true },
    { path: "/cities", priority: 0.6 },
    { path: "/methodology", priority: 0.8, dataPage: true },
    { path: "/mission", priority: 0.6 },
    { path: "/simulate", priority: 0.6 },
    { path: "/contribute", priority: 0.5 },
    { path: "/contact", priority: 0.4 },
    { path: "/legal", priority: 0.2 },
  ];

  const pages = routes.map(({ path, priority, dataPage }) => ({
    url: `${siteUrl}${path}`,
    ...(dataPage && refreshed ? { lastModified: refreshed } : {}),
    priority,
  }));

  // The ward pages show scores from the same pipeline run as the dashboard.
  const wardPages = wardFeatures.map(({ properties }) => ({
    url: wardPageUrl(properties.ward_id),
    ...(refreshed ? { lastModified: refreshed } : {}),
    priority: 0.5,
  }));

  return [...pages, ...wardPages];
}
