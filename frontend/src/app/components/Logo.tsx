import Image from "next/image";

export default function Logo({ className = "" }: { className?: string }) {
  return (
    <span className={`inline-flex items-center gap-2 ${className}`}>
      {/* Full gradient mark is brand-restricted to 48px+; below that, brand spec
          calls for logo-small.svg (flat emerald, coarser grid, vein removed). */}
      <Image src="/logo.svg" alt="UCIP" width={28} height={28} className="h-7 w-7" />
      <span className="text-xl font-semibold tracking-tight text-foreground">UCIP</span>
    </span>
  );
}
