import Image from "next/image";

export default function Logo({ className = "" }: { className?: string }) {
  return (
    <span className={`inline-flex items-center gap-2 ${className}`}>
      <Image src="/logo-icon.png" alt="UCIP" width={28} height={28} className="h-7 w-7" />
      <span className="text-xl font-semibold tracking-tight text-black dark:text-zinc-50">
        UCIP
      </span>
    </span>
  );
}
