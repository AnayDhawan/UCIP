export default function Card({
  children,
  className = "",
  id,
}: {
  children: React.ReactNode;
  className?: string;
  id?: string;
}) {
  return (
    <div id={id} className={`rounded-xl border border-border bg-surface p-6 ${className}`}>
      {children}
    </div>
  );
}

/** Numbered step card — methodology's "what we measure / how it's built / ..." sequence. */
export function StepCard({
  step,
  title,
  description,
  children,
  id,
}: {
  step: number;
  title: string;
  description?: string;
  children: React.ReactNode;
  id?: string;
}) {
  return (
    <Card id={id}>
      <div className="flex items-baseline gap-3">
        <span className="font-mono text-sm text-brand-teal">{String(step).padStart(2, "0")}</span>
        <h3 className="text-lg font-semibold text-foreground">{title}</h3>
      </div>
      {description && <p className="mt-1 text-sm text-muted-foreground">{description}</p>}
      <div className="mt-4">{children}</div>
    </Card>
  );
}
