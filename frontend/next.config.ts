import type { NextConfig } from "next";

// Headers every route gets. Geolocation stays on for the site itself because
// the dashboard's find-my-ward uses it; camera and microphone are never used.
const baseHeaders = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "geolocation=(self), camera=(), microphone=()" },
];

// The policy lists every third party the site talks to (PostHog, Vercel
// Analytics, Esri tiles, Open-Meteo, Supabase). It ran Report-Only first; on
// 2026-11-04 a Playwright pass over eleven production pages, including the
// dashboard with a ward open and an embed card, recorded no violations, so it
// now enforces. Next.js needs 'unsafe-inline' for its bootstrap scripts without
// a nonce setup, and dev mode needs 'unsafe-eval'.
const isDev = process.env.NODE_ENV !== "production";
const csp = [
  "default-src 'self'",
  `script-src 'self' 'unsafe-inline'${isDev ? " 'unsafe-eval'" : ""} https://va.vercel-scripts.com https://*.posthog.com`,
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: blob: https://*.arcgisonline.com",
  "font-src 'self' data:",
  "connect-src 'self' https://*.posthog.com https://*.supabase.co https://api.open-meteo.com https://vitals.vercel-insights.com https://va.vercel-scripts.com",
  "worker-src 'self' blob:",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
].join("; ");

const nextConfig: NextConfig = {
  async headers() {
    return [
      {
        // Everything except the embeddable ward cards: nothing else should be
        // framed by another origin.
        source: "/((?!embed/).*)",
        headers: [
          ...baseHeaders,
          { key: "Content-Security-Policy", value: `${csp}; frame-ancestors 'self'` },
        ],
      },
      {
        // /embed/ward/* cards exist to be framed by other sites, so no frame
        // restriction here.
        source: "/embed/:path*",
        headers: [
          ...baseHeaders,
          { key: "Content-Security-Policy", value: csp },
        ],
      },
    ];
  },
};

export default nextConfig;
