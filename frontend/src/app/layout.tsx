import type { Metadata, Viewport } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import ThemeProvider from "./components/ThemeProvider";
import { cn } from "@/lib/utils";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
});

// Production domain, confirmed live 2026-09-03. Defaulting to it rather than
// localhost so canonical URLs, OG images and the sitemap are correct on a
// deploy with no env vars set; NEXT_PUBLIC_SITE_URL still overrides for
// previews and local work.
const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "https://uciplatform.vercel.app";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: "UCIP: Urban Climate Intelligence Platform",
  description: "Mumbai ward-level heat vulnerability decision-support platform.",
  keywords: [
    "urban heat vulnerability",
    "Mumbai",
    "urban planning",
    "climate resilience",
    "heat island",
    "ward-level data",
    "climate intelligence",
  ],
  manifest: "/site.webmanifest",
  robots: {
    index: true,
    follow: true,
  },
  openGraph: {
    title: "UCIP: Urban Climate Intelligence Platform",
    description: "Mumbai ward-level heat vulnerability decision-support platform.",
    url: siteUrl,
    siteName: "UCIP",
    images: ["/og-image.png"],
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "UCIP: Urban Climate Intelligence Platform",
    description: "Mumbai ward-level heat vulnerability decision-support platform.",
    images: ["/og-image.png"],
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#FAFAFA" },
    { media: "(prefers-color-scheme: dark)", color: "#0b0f0e" },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={cn("h-full", "antialiased", inter.variable, jetbrainsMono.variable, "font-sans")}
    >
      <body className="min-h-full flex flex-col">
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
