import Image from "next/image";

export default function Logo({ className = "" }: { className?: string }) {
  return (
    <span className={`inline-flex items-center gap-2 ${className}`}>
      {/* icon-192 is a square, safely-padded export of the mark (the raw
          logo.svg is a tall 492x654 leaf-and-stem shape and gets squished
          when forced into a square box at nav size). */}
      <Image src="/icon-192.png" alt="UCIP" width={28} height={28} className="h-7 w-7" />
      <span className="text-xl font-semibold tracking-tight text-foreground">UCIP</span>
    </span>
  );
}
