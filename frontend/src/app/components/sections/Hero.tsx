import Link from "next/link";
import HeroGradient from "../HeroGradient";
import LiveTempStrip from "../LiveTempStrip";

export default function Hero() {
  return (
    <section className="relative overflow-hidden border-b border-border">
      <HeroGradient />
      <div className="relative mx-auto max-w-5xl px-6 py-20 md:py-28">
        <div className="max-w-3xl animate-fade-up">
          <p className="hero-text-shadow kicker !text-foreground">Urban Climate Intelligence Platform</p>
          <h1 className="hero-text-shadow mt-4 text-4xl font-bold leading-[1.08] tracking-tight text-foreground sm:text-5xl md:text-6xl">
            Mumbai&apos;s ward-level heat vulnerability,{" "}
            <span className="font-black">turned into decisions you can act on.</span>
          </h1>
          <div className="mt-6 h-1.5 w-44 rounded-full bg-gradient-to-r from-[#fbbf24] to-[#16a34a] dark:from-brand-teal dark:to-brand-emerald" />
          <p className="hero-text-shadow mt-6 max-w-xl text-lg leading-relaxed text-foreground">
            UCIP scores heat vulnerability across all 24 city wards using satellite and population
            data, then recommends what to build where: trees, cool roofs, or shaded cooling centres.
            Every number is computed. Every claim cites its source.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-3">
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
          <div className="mt-6">
            <LiveTempStrip />
          </div>
        </div>
      </div>
    </section>
  );
}
