import type { Metadata } from "next";
import { Mail } from "lucide-react";
import SiteHeader from "../components/SiteHeader";
import SiteFooter from "../components/SiteFooter";

export const metadata: Metadata = {
  title: "Contact | UCIP",
  description: "Get in touch about UCIP",
};

export default function ContactPage() {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <SiteHeader />
      <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-12">
        <h1 className="text-2xl font-semibold text-foreground">Contact</h1>
        <p className="mt-3 leading-relaxed text-muted-foreground">
          UCIP is built and maintained by one person. The fastest way to reach me is email:
        </p>
        <p className="mt-4">
          <a
            href="mailto:dhawansanay@gmail.com"
            className="inline-flex items-center gap-2 rounded-lg bg-brand-teal px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-brand-teal-hover"
          >
            <Mail className="h-4 w-4" aria-hidden />
            dhawansanay@gmail.com
          </a>
        </p>
        <h2 className="mt-10 text-lg font-semibold text-foreground">What to include</h2>
        <ul className="mt-3 list-disc space-y-1.5 pl-5 text-sm leading-relaxed text-muted-foreground">
          <li>Spotted a data error? Name the ward and what looks wrong.</li>
          <li>Methodology question? Point at the section on the how-it-works page.</li>
          <li>Want to adapt UCIP for another city? Say which one, the pipeline is city-agnostic.</li>
          <li>Press or general questions: anything goes.</li>
        </ul>
      </main>
      <SiteFooter />
    </div>
  );
}
