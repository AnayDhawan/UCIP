import Link from "next/link";
import HeroCity from "../HeroCity";
import HeroGradient from "../HeroGradient";
import LiveTempStrip from "../LiveTempStrip";

/**
 * Stacked hero: copy on top, subject underneath.
 *
 * The subject is the real city, not an illustration. HeroCity extrudes the 24
 * BMC ward polygons with height and colour taken from their actual HVI scores,
 * so the tallest and reddest blocks are the same wards the dashboard ranks
 * first, surrounded by real Natural Earth coastline held out of focus. That is
 * a data claim, so it carries a credit line; using the map's locked HVI ramp
 * decoratively with nothing to explain it would be the dishonest version.
 *
 * The city sits in normal flow rather than absolutely positioned, so it can
 * never ride up over the copy at an awkward viewport height. The mesh gradient
 * is masked down to a glow behind it (variant="glow") instead of flooding the
 * section, which grounds the model in light and leaves the headline on a clean,
 * high-contrast surface.
 */
export default function Hero() {
  return (
    // Sized to the viewport minus the header, with the city taking whatever the
    // copy does not, so the whole composition is visible without scrolling and
    // the model can never be pushed below the fold on a short screen.
    <section className="relative isolate flex min-h-[calc(100svh-3.25rem)] flex-col overflow-hidden border-b border-border">
      <HeroGradient variant="glow" />
      {/* Spans the whole section, behind the copy, so the hero reads as one
          scene the text is standing in rather than a headline panel stacked on
          top of a separate model panel. The model frames itself into the space
          the copy leaves empty (see framingFor in HeroCityScene). */}
      <HeroCity />
      <div className="relative z-10 mx-auto w-full max-w-6xl px-6 pt-12 sm:px-8 md:pt-16">
        {/* Centred on phones, where the model sits centred behind the copy and
            there is no side column to align against; left-aligned from md up,
            where the model moves right and the copy holds the left. */}
        <div className="max-w-3xl animate-fade-up text-center md:text-left">
          <p className="hero-text-shadow kicker !text-foreground">Urban Climate Intelligence Platform</p>
          <h1 className="hero-text-shadow mt-4 text-3xl font-bold leading-[1.1] tracking-tight text-foreground sm:text-4xl md:text-5xl">
            Mumbai&apos;s ward-level
            <br />
            heat vulnerability.
          </h1>
          <div className="mx-auto mt-6 h-1.5 w-44 rounded-full bg-gradient-to-r from-brand-teal to-brand-emerald md:mx-0" />
          <p className="hero-text-shadow mx-auto mt-6 max-w-xl text-lg leading-relaxed text-foreground md:mx-0">
            Satellite and population data, scored ward by ward. Every number sourced.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3 md:justify-start">
            <Link
              href="/dashboard"
              className="rounded-lg bg-brand-teal px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-brand-teal-hover"
            >
              Open the dashboard
            </Link>
            <Link
              href="/methodology"
              className="rounded-lg border border-border bg-surface/60 px-5 py-2.5 text-sm font-semibold text-foreground backdrop-blur-sm transition-colors hover:bg-surface-hover"
            >
              Methodology
            </Link>
          </div>
          <div className="mt-6 flex justify-center md:block">
            <LiveTempStrip />
          </div>
        </div>
      </div>

      {/* Reserves the lower half of the section for the model, which is painted
          by the full-bleed canvas behind rather than by this element. */}
      <div className="pointer-events-none min-h-[220px] flex-1" />

      {/* Fades the model into the section edge so it reads as a fragment of
          something larger, and gives the credit line a surface to sit on. */}
      <div className="pointer-events-none absolute inset-x-0 bottom-0 z-10 h-24 bg-gradient-to-t from-background to-transparent" />
      <p className="pointer-events-none absolute inset-x-0 bottom-3 z-10 mx-auto max-w-6xl px-6 text-center text-[11px] leading-relaxed text-muted-foreground sm:px-8 md:text-left">
        All 24 wards, raised and coloured by heat vulnerability.
        <br className="hidden sm:inline" /> Real BMC boundaries, coastline from Natural Earth.
      </p>
    </section>
  );
}
