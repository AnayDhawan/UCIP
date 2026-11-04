import type { Metadata } from "next";
import SiteHeader from "../components/SiteHeader";
import SiteFooter from "../components/SiteFooter";
import { SourceAttribution } from "../components/Citation";
import { SOURCES } from "@/lib/citations";

export const metadata: Metadata = {
  title: "Legal and data attribution | UCIP",
  description: "License, data sources, and disclaimers for UCIP",
};

export default function LegalPage() {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <SiteHeader />
      <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-12">
        <h1 className="text-2xl font-semibold text-foreground">Legal and data attribution</h1>

        <h2 id="license" className="mt-8 text-lg font-semibold text-foreground">
          License
        </h2>
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
          UCIP&apos;s code is released under the Apache License 2.0. You are free to use, modify,
          and redistribute it, including commercially, as long as the license and attribution
          notices are preserved.
        </p>

        <h2 id="data-sources" className="mt-8 text-lg font-semibold text-foreground">
          Data sources
        </h2>
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
          Every dataset behind UCIP is free and public. Each carries its own license, which remains
          with the upstream provider:
        </p>
        <SourceAttribution sources={SOURCES} />

        <h2 id="disclaimers" className="mt-8 text-lg font-semibold text-foreground">
          Disclaimers
        </h2>
        <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-relaxed text-muted-foreground">
          <li>
            UCIP is a research prototype, built independently. It is not an official tool of the
            Brihanmumbai Municipal Corporation or any government body, and no decision should rest
            on it alone.
          </li>
          <li>
            The heat measure is land surface temperature from satellites, which is not the same as
            the air temperature people feel.
          </li>
          <li>
            Slum density is estimated from mapped slum-cluster boundaries, not census records.
            The methodology page lists every proxy openly.
          </li>
          <li>
            Intervention recommendations are literature-based suggestions, not engineering
            assessments of specific sites.
          </li>
        </ul>

        <h2 id="privacy" className="mt-8 text-lg font-semibold text-foreground">
          Privacy
        </h2>
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
          UCIP has no accounts. This is what leaves your browser, or stays in it:
        </p>
        <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-relaxed text-muted-foreground">
          <li>
            <strong className="text-foreground">PostHog</strong> receives page views, interaction
            events and errors the site runs into, to show which pages are used and what breaks.
            It keeps a random visitor id in a cookie and local storage so repeat visits count once.
          </li>
          <li>
            <strong className="text-foreground">Vercel Analytics</strong> receives page views, for
            the same reason.
          </li>
          <li>
            <strong className="text-foreground">Open-Meteo</strong>: the home page asks
            api.open-meteo.com for Mumbai&apos;s current temperature directly from your browser, so
            Open-Meteo sees your IP address. Ward weather is fetched by UCIP&apos;s server for the
            ward&apos;s centre, so your browser does not contact Open-Meteo for it.
          </li>
          <li>
            <strong className="text-foreground">Location</strong>: only if you use find my ward
            and allow it, your browser&apos;s coordinates are sent to UCIP&apos;s own{" "}
            <code>/api/v1/lookup</code> to find the ward you are in. UCIP does not store them.
          </li>
          <li>
            <strong className="text-foreground">API requests</strong> are counted per IP address
            over a one-minute window to apply the rate limit.
          </li>
          <li>
            <strong className="text-foreground">Stored on your device</strong>: the wards you
            track (<code>ucip-tracked-wards</code>), whether you closed the dashboard hint (
            <code>ucip-dashboard-hint-dismissed</code>) and your light or dark theme, in your
            browser&apos;s local storage. They are never sent anywhere.
          </li>
        </ul>
      </main>
      <SiteFooter />
    </div>
  );
}
