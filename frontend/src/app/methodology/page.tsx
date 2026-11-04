import fs from "fs";
import path from "path";
import type { Metadata } from "next";
import Image from "next/image";
import SiteHeader from "../components/SiteHeader";
import SiteFooter from "../components/SiteFooter";
import { StepCard } from "../components/Card";
import { CitationList } from "../components/Citation";
import CoefficientSparkline from "../components/CoefficientSparkline";
import {
  formatCompositeWindow,
  formatRunDate,
  type RunLog,
} from "@/lib/runLog";

export const metadata: Metadata = {
  title: "Methodology | UCIP",
  description: "Methodology, citations, and stated limitations behind UCIP's heat vulnerability index",
};

type PcaLog = {
  explained_variance_pc1: number;
  loadings_pc1?: Record<string, number>;
  weights: Record<string, number>;
  fallback_used: boolean;
};

type Sensitivity = {
  mean_kendall_tau: number;
  mean_top5_overlap: number;
  n_runs: number;
  perturbation_pct: number;
  all_top5_stable?: boolean;
};

type LstValidation = {
  window: { start: string; end: string };
  is_pipeline_window: boolean;
  stations: {
    name: string;
    setting: string;
    n_matched_overpasses: number;
    pearson_r: number;
    mean_bias_c: number;
  }[];
  pooled_within_station?: { n: number; pearson_r: number };
  bias_spread_c?: { min: number; max: number };
};

const INDICATOR_LABELS: Record<string, { label: string; direction: string; source: string }> = {
  LST_C: {
    label: "Land surface temperature",
    direction: "+ (higher = more vulnerable)",
    source: "Landsat 8/9, USGS, public domain",
  },
  NDVI: {
    label: "Green cover (NDVI)",
    direction: "- (higher = less vulnerable)",
    source: "Landsat 8/9, USGS, public domain",
  },
  pop_density_km2: { label: "Population density", direction: "+", source: "WorldPop 2020, CC BY 4.0" },
  hospital_dist_m: { label: "Hospital distance", direction: "+", source: "OpenStreetMap, ODbL" },
  impervious_pct: {
    label: "Impervious / built-up %",
    direction: "+",
    source: "ESA WorldCover 2021, CC BY 4.0",
  },
};

const WEIGHT_BAR_MAX = 0.35;

function readJson<T>(filename: string): T {
  const p = path.join(process.cwd(), "..", "data", filename);
  return JSON.parse(fs.readFileSync(p, "utf-8"));
}

/** For outputs that may not exist yet on a given checkout, such as a validation
 *  run that needs Earth Engine credentials to produce. */
function readJsonOptional<T>(filename: string): T | null {
  try {
    return readJson<T>(filename);
  } catch {
    return null;
  }
}

export default function MethodologyPage() {
  const pca = readJson<PcaLog>("hvi_pca_log.json");
  const sensitivity = readJson<Sensitivity>("sensitivity.json");
  const validation = readJsonOptional<LstValidation>("lst_validation.json");
  // Read from ../data/ like sensitivity.json and hvi_pca_log.json above (see the
  // "Frontend sync" section of pipeline/README.md). Absent until a pipeline run
  // commits its log, so the block below renders nothing on a fresh checkout.
  const runLog = readJsonOptional<RunLog>("pipeline_run_log.json");
  const refreshedLabel = runLog
    ? formatRunDate(runLog.finished_at ?? runLog.started_at)
    : null;
  const windowLabel = runLog ? formatCompositeWindow(runLog.composite_window) : null;
  // Indicators whose PC1 loading, after orientation, runs against the rest.
  const against = Object.entries(pca.loadings_pc1 ?? {})
    .filter(([, v]) => v < 0)
    .map(([k]) => k);

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <SiteHeader />
      <div className="mx-auto w-full max-w-3xl flex-1 px-6 py-10">
        <h1 className="text-2xl font-semibold text-foreground">Methodology</h1>
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
          In plain terms: satellites measure how hot each square kilometre of Mumbai&apos;s surface
          gets in the dry season, how green it is and how much of it is paved. Open data adds how
          many people live there and how far the nearest hospital is. Those five factors, all from
          free and open global sources, combine into one vulnerability score per ward, and a set of
          rules turns each score into a candidate intervention with its reasoning. The steps below
          document the process and its limits.
        </p>
        <p className="mt-3 text-sm text-muted-foreground">
          UCIP is a citable, versioned heat vulnerability index. Its score is not a forecast, and
          UCIP is not a warning service; the weather panel on each ward shows Open-Meteo&apos;s
          forecast, labelled as such. It covers the 24 wards in the BMC boundary file it was built
          on, on a 1 km grid. BMC has since split K/E (the K North ward office opened in 2026) and reportedly P North,
          and no open boundary file for the new wards exists yet, so the index still uses 24. The
          pipeline runs from a per-city config, but no second city has been run end to end.
        </p>

        {refreshedLabel && (
          <div className="mt-8 rounded-xl border border-border bg-surface p-6">
            <p className="kicker">Data vintage</p>
            <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
              Refreshed{" "}
              <strong className="font-medium text-foreground">{refreshedLabel}</strong>
              {windowLabel && (
                <>
                  . The underlying measurements come from Landsat imagery captured{" "}
                  <strong className="font-medium text-foreground">{windowLabel}</strong>
                  , Mumbai&apos;s most recent complete dry season. The refresh date alone
                  overstates how current the figures are.
                </>
              )}
            </p>
          </div>
        )}

        <div className="mt-8 space-y-6">
          <StepCard
            step={1}
            title="What we measure"
            description={`${Object.keys(INDICATOR_LABELS).length} indicators, each z-scored, all from free open global data.`}
          >
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left">
                  <th className="py-1 pr-4 font-medium text-foreground">Indicator</th>
                  <th className="py-1 pr-4 font-medium text-foreground">Direction</th>
                  <th className="py-1 font-medium text-foreground">Source</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(INDICATOR_LABELS).map(([key, v]) => (
                  <tr key={key} className="border-b border-border/60">
                    <td className="py-1 pr-4 text-foreground">{v.label}</td>
                    <td className="py-1 pr-4 text-muted-foreground">{v.direction}</td>
                    <td className="py-1 text-muted-foreground">{v.source}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="mt-2 text-xs text-muted-foreground">
              Direction set per the heat-vulnerability literature (see step 5).
            </p>
            <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
              Not scored: the slum share (Datameet slum-cluster polygons) and the under-7 share
              (Census 2011 ward tables). Both used to be in the index. They were taken out on
              17 Oct 2026 because neither exists for most cities or gets updated: the slum polygons
              are a one-off digitisation and the Census is fifteen years old. They are still
              published per cell as context, so the index no longer measures informal housing or
              age directly.
            </p>
          </StepCard>

          <StepCard
            step={2}
            title="How the score is built"
            description="Weighted sum, rescaled 0-100, no black box."
          >
            <p className="text-sm text-muted-foreground">
              Weights are the absolute first-principal-component loadings of Mumbai&apos;s own
              standardised cells, renormalised to sum to one, following the method of Reid et al.
              2009. They come from this run&apos;s data, not from judgement. HVI = weighted sum,
              rescaled 0-100.
              Explainability is the per-factor contribution (weight × z-score), shown as a ranked bar
              breakdown per ward on the dashboard. Transparent linear index, no SHAP: nothing
              black-box to explain.
            </p>
            <p className="mt-3 text-sm text-foreground">
              PC1 explained variance: <strong>{(pca.explained_variance_pc1 * 100).toFixed(1)}%</strong>{" "}
              {pca.fallback_used
                ? "(below the 30% floor: equal-weight fallback used)"
                : "(above 30% floor: PCA weights used directly)"}
            </p>
            <div className="mt-3 space-y-2">
              {Object.entries(pca.weights).map(([k, v]) => (
                <CoefficientSparkline
                  key={k}
                  mode="unidirectional"
                  label={INDICATOR_LABELS[k]?.label ?? k}
                  value={v}
                  max={WEIGHT_BAR_MAX}
                  format={(x) => `${(x * 100).toFixed(1)}%`}
                />
              ))}
            </div>
            {against.length > 0 && (
              <p className="mt-3 text-xs leading-relaxed text-muted-foreground">
                {against.map((k) => INDICATOR_LABELS[k]?.label ?? k).join(", ")}{" "}
                {against.length === 1 ? "runs" : "run"} against the other indicators on the first
                component: in Mumbai the hot, dense, paved cells tend to sit close to hospitals. The
                index keeps the literature&apos;s direction (farther from a hospital is more
                vulnerable) and takes the weight from the size of the loading. That is a judgement,
                and an open question for review.
              </p>
            )}
          </StepCard>

          <StepCard
            step={3}
            title="Does it hold up"
            description="Does the ranking survive a wobble in its own weights?"
          >
            <p className="text-sm text-muted-foreground">
              Weights perturbed ±{(sensitivity.perturbation_pct * 100).toFixed(0)}% one-at-a-time
              ({sensitivity.n_runs} runs); ward priority ranking measured for stability.
            </p>
            <p className="mt-2 text-sm text-foreground">
              Mean Kendall tau vs. baseline ranking:{" "}
              <strong>{sensitivity.mean_kendall_tau.toFixed(3)}</strong>. Mean top-5 overlap:{" "}
              <strong>{sensitivity.mean_top5_overlap.toFixed(1)}/5</strong>.{" "}
              {sensitivity.all_top5_stable
                ? "The top five stayed the same in every run."
                : "The top five changed in at least one run, so treat the exact order as uncertain."}
            </p>
            <Image
              src="/sensitivity_chart.png"
              alt="HVI ward-ranking stability under weight perturbation"
              width={900}
              height={370}
              className="mt-3 w-full max-w-2xl rounded border border-border"
            />

            {validation && (
              <div className="mt-6 border-t border-border pt-4">
                <h4 className="text-sm font-semibold text-foreground">
                  Checked against ground weather stations
                </h4>
                <p className="mt-1 text-sm text-muted-foreground">
                  The sensitivity test above asks whether the index is robust to its own
                  weighting. This asks something different and harder: does the satellite
                  temperature layer track the real world at all? Per-overpass Landsat land
                  surface temperature was correlated against daily observations from the two
                  NOAA GSOD weather stations in Mumbai, over {validation.window.start} to{" "}
                  {validation.window.end}.
                </p>

                <div className="mt-3 overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="border-b border-border text-xs uppercase text-muted-foreground">
                        <th className="py-1.5 pr-3 font-medium">Station</th>
                        <th className="py-1.5 pr-3 font-medium">Overpasses</th>
                        <th className="py-1.5 pr-3 font-medium">Correlation</th>
                        <th className="py-1.5 font-medium">LST − air</th>
                      </tr>
                    </thead>
                    <tbody>
                      {validation.stations.map((s) => (
                        <tr key={s.name} className="border-b border-border/50">
                          <td className="py-1.5 pr-3 text-foreground">
                            {s.name}{" "}
                            <span className="text-muted-foreground">({s.setting})</span>
                          </td>
                          <td className="py-1.5 pr-3 font-mono text-muted-foreground">
                            {s.n_matched_overpasses}
                          </td>
                          <td className="py-1.5 pr-3 font-mono text-foreground">
                            r = {s.pearson_r.toFixed(2)}
                          </td>
                          <td className="py-1.5 font-mono text-muted-foreground">
                            {s.mean_bias_c > 0 ? "+" : ""}
                            {s.mean_bias_c.toFixed(1)} C
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <p className="mt-3 text-sm text-muted-foreground">
                  <strong className="text-foreground">Read this carefully.</strong> Land surface
                  temperature is not air temperature: LST is the radiometric temperature of the
                  ground seen from orbit, a station measures shaded air about 1.5 m up. The large
                  positive offset is expected physics, not error, and it is much bigger at
                  inland Santacruz, which sits over airport tarmac, than at coastal Colaba. That
                  spread{" "}
                  {validation.bias_spread_c && (
                    <>
                      ({validation.bias_spread_c.min.toFixed(1)} to{" "}
                      {validation.bias_spread_c.max.toFixed(1)} C){" "}
                    </>
                  )}
                  is also why no single correction turns this layer into air temperature, and why
                  the index uses it as a relative indicator rather than as a temperature.
                </p>

                <p className="mt-2 text-sm text-foreground">
                  What the correlation shows is that the satellite tracks day-to-day thermal
                  variation at a fixed place
                  {validation.pooled_within_station && (
                    <>
                      {" "}
                      (pooled within-station r ={" "}
                      <strong>{validation.pooled_within_station.pearson_r.toFixed(2)}</strong>,
                      n = {validation.pooled_within_station.n})
                    </>
                  )}
                  , rather than reporting sensor noise or cloud artefacts. That is what the ward
                  ranking rests on.
                </p>

                {!validation.is_pipeline_window && (
                  <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
                    Stated plainly: this validates the method on the most recent dry season where
                    both satellite and station data exist, not the window the published index is
                    computed from. NOAA GSOD publishes on a lag and had no records overlapping the
                    current composite. Two stations is also few, and it is all Mumbai has with a
                    long record.
                  </p>
                )}
              </div>
            )}
          </StepCard>

          <StepCard
            step={4}
            title="What to build"
            description="Rule-based nature-based-solutions engine, ecologically gated."
          >
            <p className="text-sm text-muted-foreground">
              Rule-based; each fired rule carries a rationale and a citation. An ecological
              plantability filter restricts native-tree recommendations to restoration-suitable
              cells that are not native grassland or savanna (Bastin et al. 2019 potential vs.
              Veldman et al. 2019 constraint). Cells that would otherwise get trees but fail this
              check are routed to cool roofs, reflective pavements, or cooling centres instead. In
              Mumbai the tree rule currently fires on no cell, because every hot, bare cell is
              already built up. See
              the &quot;Plantability&quot; layer on the dashboard, or estimate the effect of either
              intervention directly on the{" "}
              <a href="/simulate" className="text-brand-teal hover:underline">
                what-if page
              </a>
              .
            </p>
          </StepCard>

          <StepCard
            step={5}
            title="Every source"
            description="The papers behind the method, the filter and the cooling coefficients."
          >
            <CitationList />
          </StepCard>

          <StepCard
            step={6}
            title="Limitations, stated openly"
            description="What this tool doesn't know."
            id="limitations"
          >
            <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
              <li>
                Land-surface temperature is not air temperature, and it is daytime only. There is no
                night-time data, and night heat is what harms people most.
              </li>
              <li>
                Ranks are uncertain. A bootstrap over the cells gives most wards a plausible range
                several places wide, so the exact order should not be quoted on its own.
              </li>
              <li>Cooling coefficients are transferred from other cities, not Mumbai-calibrated.</li>
              <li>
                Population density is a WorldPop 2020 model (the most recent year available for
                India), not a census count.
              </li>
              <li>
                Informal housing and age are not scored (see step 1), so wards with a large informal
                population may be under-ranked relative to their real vulnerability.
              </li>
              <li>
                The boundary file has 24 wards. BMC&apos;s newer wards (K North, and reportedly a
                split of P North) are not reflected.
              </li>
              <li>The what-if estimator is a first-order estimate, not a validated climate model.</li>
              <li>The ecological plantability layer is coarse-resolution.</li>
            </ul>
          </StepCard>
        </div>
      </div>
      <SiteFooter />
    </div>
  );
}
