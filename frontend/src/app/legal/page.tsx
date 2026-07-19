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
          UCIP&apos;s code is released under the MIT License. You are free to use, modify, and
          redistribute it, including commercially, as long as the license notice is preserved.
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
            UCIP is a research prototype built for a hackathon. It is not an official tool of the
            Brihanmumbai Municipal Corporation or any government body, and no decision should rest
            on it alone.
          </li>
          <li>
            The heat measure is land surface temperature from satellites, which is not the same as
            the air temperature people feel.
          </li>
          <li>
            Slum density and elderly share are estimated from public proxies, not census records.
            The methodology page lists every proxy openly.
          </li>
          <li>
            Intervention recommendations are literature-based suggestions, not engineering
            assessments of specific sites.
          </li>
        </ul>
      </main>
      <SiteFooter />
    </div>
  );
}
