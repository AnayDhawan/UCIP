"use client";

import { useState } from "react";
import { Sun, TreePine } from "lucide-react";
import Card from "../components/Card";
import CoefficientSparkline from "../components/CoefficientSparkline";
import { CANOPY_THRESHOLD_PCT, simulate } from "@/lib/coefficients";

export default function SimulatePanel() {
  const [canopyPct, setCanopyPct] = useState(40);
  const [albedoIncrease, setAlbedoIncrease] = useState(0.1);

  const result = simulate(canopyPct, albedoIncrease);

  return (
    <div className="space-y-6">
      <Card>
        <div className="grid gap-8 sm:grid-cols-2">
          <div>
            <label htmlFor="canopy" className="flex items-center gap-2 text-sm font-medium text-foreground">
              <TreePine className="h-4 w-4 text-brand-emerald" aria-hidden />
              Tree canopy cover
            </label>
            <input
              id="canopy"
              type="range"
              min={0}
              max={100}
              step={1}
              value={canopyPct}
              onChange={(e) => setCanopyPct(Number(e.target.value))}
              className="mt-3 w-full accent-brand-teal"
            />
            <p className="mt-1 font-mono text-sm text-muted-foreground">{canopyPct}% cover</p>
            <p className="mt-2 text-xs text-muted-foreground">
              Ziter et al. 2019 found negligible daytime cooling below ~{CANOPY_THRESHOLD_PCT}%
              canopy in a 60-90m radius; cooling only shows up above that threshold.
            </p>
          </div>

          <div>
            <label htmlFor="albedo" className="flex items-center gap-2 text-sm font-medium text-foreground">
              <Sun className="h-4 w-4 text-brand-teal" aria-hidden />
              Cool-roof albedo increase
            </label>
            <input
              id="albedo"
              type="range"
              min={0}
              max={0.3}
              step={0.01}
              value={albedoIncrease}
              onChange={(e) => setAlbedoIncrease(Number(e.target.value))}
              className="mt-3 w-full accent-brand-teal"
            />
            <p className="mt-1 font-mono text-sm text-muted-foreground">
              +{albedoIncrease.toFixed(2)} albedo
            </p>
            <p className="mt-2 text-xs text-muted-foreground">
              Santamouris 2014&apos;s city-scale review range; Li, Bou-Zeid &amp; Oppenheimer 2014
              supports treating the relationship as roughly linear.
            </p>
          </div>
        </div>
      </Card>

      <Card>
        <p className="kicker">Estimated daytime cooling</p>
        <div className="mt-4 space-y-3">
          <CoefficientSparkline
            mode="unidirectional"
            label="From tree canopy"
            value={result.canopyC}
            max={1.2}
            thresholdPct={0}
            format={(v) => `${v.toFixed(2)}°C`}
          />
          <CoefficientSparkline
            mode="unidirectional"
            label="From cool roofs"
            value={result.coolRoof.headlineC}
            max={1.2}
            format={(v) => `${v.toFixed(2)}°C`}
          />
        </div>
        <p className="mt-4 text-sm text-foreground">
          Combined estimate: <span className="font-mono">{result.totalHeadlineC.toFixed(2)}°C</span>{" "}
          <span className="text-muted-foreground">
            (cool-roof range: {result.coolRoof.rangeLowC.toFixed(2)}-
            {result.coolRoof.rangeHighC.toFixed(2)}°C)
          </span>
        </p>
      </Card>

      <div className="rounded-xl border border-brand-teal/30 bg-brand-teal/5 p-4 text-sm text-muted-foreground">
        This is a cited coefficient estimator, not a trained model and not a validated climate
        simulation. The coefficients above are transferred from other cities&apos; studies, not
        Mumbai-calibrated, and the two interventions are summed as independent illustrative terms,
        not a coupled physical model.
      </div>
    </div>
  );
}
