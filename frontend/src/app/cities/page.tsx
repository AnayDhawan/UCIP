import Link from "next/link";
import SiteFooter from "../components/SiteFooter";
import SiteHeader from "../components/SiteHeader";
import { CITY_REGISTRY } from "@/lib/city";

export const metadata = { title: "City registry | UCIP" };

export default function CityRegistryPage() {
  return (
    <>
      <SiteHeader />
      <main className="mx-auto w-full max-w-5xl flex-1 px-6 py-14">
        <p className="kicker">City registry</p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight">Where UCIP is maintained</h1>
        <p className="mt-3 max-w-2xl text-muted-foreground">Published cities are ready to use. Cities still in calibration are listed plainly so their data is not mistaken for a live decision tool.</p>
        <div className="mt-8 overflow-hidden rounded-xl border border-border">
          <table className="w-full text-left text-sm">
            <thead className="bg-muted/50 text-muted-foreground"><tr><th className="p-4">City</th><th className="p-4">Status</th><th className="p-4">Last refresh</th><th className="p-4">Maintainer</th></tr></thead>
            <tbody>{CITY_REGISTRY.map((city) => <tr key={city.slug} className="border-t border-border align-top"><td className="p-4 font-medium">{city.published ? <Link className="underline" href="/dashboard">{city.name}</Link> : city.name}<p className="mt-1 text-xs font-normal text-muted-foreground">{city.country}</p></td><td className="p-4">{city.published ? "Live" : "In progress"}<p className="mt-1 text-xs text-muted-foreground">{city.note}</p></td><td className="p-4">{city.lastRefreshed ?? "Not yet published"}</td><td className="p-4">{city.maintainer}</td></tr>)}</tbody>
          </table>
        </div>
      </main>
      <SiteFooter />
    </>
  );
}
