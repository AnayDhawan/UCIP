import type { Metadata } from "next";
import SiteHeader from "../components/SiteHeader";
import SiteFooter from "../components/SiteFooter";

export const metadata: Metadata = {
  title: "Contact | UCIP",
  description: "Get in touch about UCIP",
};

export default function ContactPage() {
  return (
    <div className="flex min-h-screen flex-col bg-zinc-50 dark:bg-zinc-950">
      <SiteHeader />
      <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-12">
        <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-50">Contact</h1>
        <p className="mt-3 leading-relaxed text-zinc-700 dark:text-zinc-300">
          UCIP is built and maintained by one person. The fastest way to reach me is email:
        </p>
        <p className="mt-4">
          <a
            href="mailto:dhawansanay@gmail.com"
            className="rounded-lg bg-teal-700 px-5 py-2.5 text-sm font-semibold text-teal-50 transition-colors hover:bg-teal-800 dark:bg-teal-500 dark:text-teal-950 dark:hover:bg-teal-400"
          >
            dhawansanay@gmail.com
          </a>
        </p>
        <h2 className="mt-10 text-lg font-semibold text-zinc-900 dark:text-zinc-50">
          What to include
        </h2>
        <ul className="mt-3 list-disc space-y-1.5 pl-5 text-sm leading-relaxed text-zinc-700 dark:text-zinc-300">
          <li>Spotted a data error? Name the ward and what looks wrong.</li>
          <li>Methodology question? Point at the section on the how-it-works page.</li>
          <li>Want to adapt UCIP for another city? Say which one, the pipeline is city-agnostic.</li>
          <li>Press or hackathon queries: anything goes.</li>
        </ul>
      </main>
      <SiteFooter />
    </div>
  );
}
