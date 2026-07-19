type BaseProps = {
  label: string;
  value: number;
  max: number;
  format?: (value: number) => string;
};

type BidirectionalProps = BaseProps & {
  mode?: "bidirectional";
};

type UnidirectionalProps = BaseProps & {
  mode: "unidirectional";
  /** 0-100 position of an optional reference tick, e.g. a cited threshold */
  thresholdPct?: number;
};

type CoefficientSparklineProps = BidirectionalProps | UnidirectionalProps;

/**
 * Small inline data bar, generalized from the dashboard's original per-ward
 * `ContribBar`. Two modes:
 * - `bidirectional` (default): centered, positive/negative around zero — for
 *   factor contributions (WardCards) where sign carries meaning.
 * - `unidirectional`: left-to-right fill against `max` — for PCA weights and
 *   /simulate's coefficient results, where only magnitude matters.
 */
export default function CoefficientSparkline(props: CoefficientSparklineProps) {
  const { label, value, max, format } = props;
  const displayValue = format ? format(value) : value.toFixed(2);

  if (props.mode === "unidirectional") {
    const pct = Math.min(Math.max(value, 0) / max, 1) * 100;
    return (
      <div className="flex items-center gap-3 text-xs">
        <span className="w-36 shrink-0 text-muted-foreground">{label}</span>
        <div className="relative h-2 flex-1 rounded-full bg-muted">
          {props.thresholdPct !== undefined && (
            <div
              className="absolute inset-y-0 w-px bg-muted-foreground/60"
              style={{ left: `${props.thresholdPct}%` }}
              aria-hidden
            />
          )}
          <div
            className="absolute inset-y-0 left-0 rounded-full bg-brand-teal"
            style={{ width: `${pct}%` }}
          />
        </div>
        <span className="w-16 shrink-0 text-right font-mono text-muted-foreground">
          {displayValue}
        </span>
      </div>
    );
  }

  const pct = Math.min(Math.abs(value) / max, 1) * 50;
  const positive = value >= 0;
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-32 shrink-0 text-muted-foreground">{label}</span>
      <div className="relative h-3 flex-1 bg-muted">
        <div className="absolute inset-y-0 left-1/2 w-px bg-border" aria-hidden />
        <div
          className={`absolute inset-y-0 ${positive ? "bg-red-400" : "bg-emerald-400"}`}
          style={
            positive ? { left: "50%", width: `${pct}%` } : { right: "50%", width: `${pct}%` }
          }
        />
      </div>
    </div>
  );
}
