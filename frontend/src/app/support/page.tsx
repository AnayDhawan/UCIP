import type { Metadata } from "next";
import Link from "next/link";
import SiteHeader from "../components/SiteHeader";
import SiteFooter from "../components/SiteFooter";

export const metadata: Metadata = {
  title: "Support the project | UCIP",
  description: "Star, share, or improve UCIP",
};

export default function SupportPage() {
  return (
    <div className="flex min-h-screen flex-col bg-zinc-50 dark:bg-zinc-950">
      <SiteHeader />
      <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-12">
        <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-50">
          Support the project
        </h1>
        <p className="mt-3 leading-relaxed text-zinc-700 dark:text-zinc-300">
          UCIP is free, open, and built by one student. If it is useful to you, here is how to help.
        </p>

        <h2 className="mt-10 text-lg font-semibold text-zinc-900 dark:text-zinc-50">
          Star it on GitHub
        </h2>
        <p className="mt-2 text-sm leading-relaxed text-zinc-700 dark:text-zinc-300">
          Stars help other people find open projects. The repository goes public in August 2026; if
          the link does not resolve yet, check back then.
        </p>
        <p className="mt-3">
          <a
            href="https://github.com/AnayDhawan/ucip"
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-lg bg-zinc-900 px-5 py-2.5 text-sm font-semibold text-zinc-50 transition-colors hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200"
          >
            github.com/AnayDhawan/ucip
          </a>
        </p>

        <h2 className="mt-10 text-lg font-semibold text-zinc-900 dark:text-zinc-50">Share it</h2>
        <p className="mt-2 text-sm leading-relaxed text-zinc-700 dark:text-zinc-300">
          Know someone who works on urban planning, climate adaptation, or civic data in an Indian
          city? Send them the <Link href="/dashboard" className="text-teal-700 hover:underline dark:text-teal-400">dashboard</Link>.
          The method ports to any city with open data.
        </p>

        <h2 className="mt-10 text-lg font-semibold text-zinc-900 dark:text-zinc-50">
          Improve the data
        </h2>
        <p className="mt-2 text-sm leading-relaxed text-zinc-700 dark:text-zinc-300">
          Spotted something wrong, or have access to better ward-level data?{" "}
          <Link href="/contact" className="text-teal-700 hover:underline dark:text-teal-400">
            Tell me
          </Link>
          . Corrections beat compliments.
        </p>
      </main>
      <SiteFooter />
    </div>
  );
}
