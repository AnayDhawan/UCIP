import type { Metadata } from "next";
import Link from "next/link";
import SiteHeader from "../components/SiteHeader";
import SiteFooter from "../components/SiteFooter";
import { GithubMark } from "../components/icons";

export const metadata: Metadata = {
  title: "Support the project | UCIP",
  description: "Star, share, or improve UCIP",
};

export default function SupportPage() {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <SiteHeader />
      <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-12">
        <h1 className="text-2xl font-semibold text-foreground">Support the project</h1>
        <p className="mt-3 leading-relaxed text-muted-foreground">
          UCIP is free, open, and built by one student. If it is useful to you, here is how to help.
        </p>

        <h2 className="mt-10 text-lg font-semibold text-foreground">Star it on GitHub</h2>
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
          Stars help other people find open projects. The repository goes public in August 2026; if
          the link does not resolve yet, check back then.
        </p>
        <p className="mt-3">
          <a
            href="https://github.com/AnayDhawan/ucip"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-lg bg-foreground px-5 py-2.5 text-sm font-semibold text-background transition-colors hover:opacity-90"
          >
            <GithubMark className="h-4 w-4" />
            github.com/AnayDhawan/ucip
          </a>
        </p>

        <h2 className="mt-10 text-lg font-semibold text-foreground">Share it</h2>
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
          Know someone who works on urban planning, climate adaptation, or civic data in an Indian
          city? Send them the{" "}
          <Link href="/dashboard" className="text-brand-teal hover:underline">
            dashboard
          </Link>
          . The method ports to any city with open data.
        </p>

        <h2 className="mt-10 text-lg font-semibold text-foreground">Improve the data</h2>
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
          Spotted something wrong, or have access to better ward-level data?{" "}
          <Link href="/contact" className="text-brand-teal hover:underline">
            Tell me
          </Link>
          . Corrections beat compliments.
        </p>
      </main>
      <SiteFooter />
    </div>
  );
}
