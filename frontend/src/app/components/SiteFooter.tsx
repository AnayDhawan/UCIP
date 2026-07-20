import Link from "next/link";
import { Mail } from "lucide-react";
import Logo from "./Logo";
import { GithubMark } from "./icons";

const QUICK_LINKS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/methodology", label: "Methodology" },
  { href: "/simulate", label: "Simulator" },
  { href: "/mission", label: "Mission" },
  { href: "/contribute", label: "Contribute" },
];

const LEGAL_LINKS = [
  { href: "/legal#license", label: "License" },
  { href: "/legal#data-sources", label: "Data sources" },
  { href: "/legal#disclaimers", label: "Disclaimers" },
];

export default function SiteFooter() {
  return (
    <footer className="border-t border-border bg-background">
      <div className="mx-auto max-w-5xl px-6 py-12">
        <div className="grid grid-cols-2 gap-8 sm:grid-cols-4">
          <div className="col-span-2 sm:col-span-1">
            <Logo />
            <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
              A decision-support tool for Mumbai&apos;s urban heat, ward by ward, with every claim
              cited.
            </p>
          </div>

          <div>
            <p className="kicker">Quick links</p>
            <ul className="mt-3 space-y-2">
              {QUICK_LINKS.map((l) => (
                <li key={l.href}>
                  <Link href={l.href} className="text-sm text-muted-foreground transition-colors hover:text-foreground">
                    {l.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <p className="kicker">Legal</p>
            <ul className="mt-3 space-y-2">
              {LEGAL_LINKS.map((l) => (
                <li key={l.href}>
                  <Link href={l.href} className="text-sm text-muted-foreground transition-colors hover:text-foreground">
                    {l.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <p className="kicker">Connect</p>
            <ul className="mt-3 space-y-2">
              <li>
                <Link href="/contact" className="text-sm text-muted-foreground transition-colors hover:text-foreground">
                  Contact
                </Link>
              </li>
              <li>
                <a
                  href="mailto:dhawansanay@gmail.com"
                  className="flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
                >
                  <Mail className="h-3.5 w-3.5" aria-hidden />
                  Email
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/AnayDhawan/ucip"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
                >
                  <GithubMark className="h-3.5 w-3.5" />
                  GitHub
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-10 border-t border-border pt-6 text-xs text-muted-foreground">
          <p>
            UCIP is a research prototype, built independently. It is not an official tool of the
            BMC or any government body.
          </p>
          <p className="mt-2">
            Data: Landsat (USGS), WorldPop, ESA WorldCover via Google Earth Engine; OpenStreetMap
            contributors; Datameet ward boundaries. Basemap by CARTO.
          </p>
          <p className="mt-4">
            © {new Date().getFullYear()} UCIP. Code released under the Apache License 2.0.
          </p>
        </div>
      </div>
    </footer>
  );
}
