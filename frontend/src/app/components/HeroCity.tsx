"use client";

import { useCallback, useEffect, useState, useSyncExternalStore } from "react";
import dynamic from "next/dynamic";
import { useTheme } from "next-themes";
import { hviColor } from "@/lib/hvi";
import { areasForWard } from "@/lib/wardAreas";
import {
  HERO_CITY_URL,
  HERO_REGION_URL,
  type HeroCityData,
  type HeroRegionData,
} from "./heroCityData";
import type { HoverPayload } from "./HeroCityScene";

/**
 * Landing-hero subject: Mumbai's 24 BMC wards extruded in 3D on a curved piece
 * of the planet, height and colour driven by their real HVI scores, with the
 * Natural Earth coastline around them hazed back as out-of-focus context.
 *
 * Loading strategy mirrors HeroGradient.tsx, for the same reasons. `three` and
 * @react-three/fiber are pulled in only through the dynamic import below, so
 * they never reach the server render and never download for a client that
 * cannot use them. Without WebGL the component falls back to a tilted flat SVG
 * of the same geometry and the same colour ramp: less spectacle, identical
 * information, no canvas.
 *
 * North is up and nothing rotates on its own, so there is no idle animation to
 * suppress for reduced-motion users; the renderer only paints on resize, theme
 * change or hover.
 *
 * Hovering a ward names it. That is a mouse-only affordance on a decorative
 * surface, so the canvas stays aria-hidden and the dashboard remains the real,
 * keyboard-reachable way to read any of this.
 */

const HeroCityScene = dynamic(() => import("./HeroCityScene"), { ssr: false });

const noopSubscribe = () => () => {};

let webGLSupport: boolean | null = null;

/** Probed once per page load, then cached: the answer cannot change, and
 *  creating a throwaway canvas on every render would not be free. */
function getWebGLSnapshot(): boolean {
  if (webGLSupport === null) {
    try {
      const canvas = document.createElement("canvas");
      webGLSupport = !!(canvas.getContext("webgl2") || canvas.getContext("webgl"));
    } catch {
      webGLSupport = false;
    }
  }
  return webGLSupport;
}

let colorCanvas: CanvasRenderingContext2D | null = null;
const colorCache = new Map<string, string | null>();

/** Sentinel: an unparseable fillStyle is ignored, leaving the previous value. */
const COLOR_SENTINEL = "#ff00ff";

/**
 * Resolve any CSS colour string to plain `rgb()`.
 *
 * This exists because the brand palette is authored in OKLCH, and the browser
 * hands back a computed `lab()` value, which THREE.Color cannot parse: feeding
 * it straight to the fog silently produced white. A 1x1 canvas is the cheapest
 * correct converter, since the browser already knows every colour space it
 * serialises. Returns null when the value cannot be parsed at all, rather than
 * pretending, so callers can fall back deliberately.
 */
function cssColorToRgb(value: string): string | null {
  if (!value) return null;
  const cached = colorCache.get(value);
  if (cached !== undefined) return cached;

  if (!colorCanvas) {
    const canvas = document.createElement("canvas");
    canvas.width = 1;
    canvas.height = 1;
    colorCanvas = canvas.getContext("2d", { willReadFrequently: true });
  }
  if (!colorCanvas) return null;

  colorCanvas.fillStyle = COLOR_SENTINEL;
  colorCanvas.fillStyle = value;
  colorCanvas.fillRect(0, 0, 1, 1);
  const [r, g, b] = colorCanvas.getImageData(0, 0, 1, 1).data;
  const parsed = r === 255 && g === 0 && b === 255 ? null : `rgb(${r}, ${g}, ${b})`;

  colorCache.set(value, parsed);
  return parsed;
}

/** next-themes swaps a class on <html>, so that is what we watch. */
function subscribeTheme(callback: () => void) {
  const observer = new MutationObserver(callback);
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
  return () => observer.disconnect();
}

/**
 * The scene fades its ground into exactly this colour, so any drift between the
 * two shows up as a hard horizontal seam where the ground ends. `<body>` already
 * carries `bg-background`, so it is the honest source.
 */
function getBackgroundSnapshot(): string | null {
  return cssColorToRgb(getComputedStyle(document.body).backgroundColor);
}

function getBackgroundServerSnapshot(): string | null {
  return null;
}

/** Same guard ThemeToggle.tsx and HeroGradient.tsx use: next-themes reads
 *  localStorage synchronously, so resolvedTheme is not safely undefined
 *  pre-mount and would mismatch the server render. */
function useMounted(): boolean {
  return useSyncExternalStore(
    noopSubscribe,
    () => true,
    () => false
  );
}

/**
 * No-WebGL fallback: the same ward polygons, same HVI ramp, drawn flat and
 * tipped back with a CSS transform. The city's long axis runs north-south, so
 * coordinates are transposed to lay it across the hero the way the 3D model
 * does. SVG y grows downward, hence the negated y.
 */
function HeroCityFlat({
  data,
  region,
  onReady,
}: {
  data: HeroCityData;
  region: HeroRegionData | null;
  onReady: () => void;
}) {
  const { width, height } = data.extent;
  const pad = 0.32;

  // SVG paints on the next frame, so the fallback reveals on the same schedule
  // the canvas does.
  useEffect(() => {
    const id = requestAnimationFrame(onReady);
    return () => cancelAnimationFrame(id);
  }, [onReady]);
  const ringPath = (ring: [number, number][]) =>
    `M ${ring.map(([x, y]) => `${y} ${-x}`).join(" L ")} Z`;

  return (
    <div className="flex h-full w-full items-end justify-center" style={{ perspective: "900px" }}>
      <svg
        viewBox={`${-height / 2 - pad} ${-width / 2 - pad} ${height + pad * 2} ${width + pad * 2}`}
        className="h-auto w-full max-w-4xl"
        style={{ transform: "rotateX(54deg) scale(1.2)", transformOrigin: "center bottom" }}
      >
        {region?.parts.map((part, i) => (
          <path
            key={`region-${i}`}
            d={[part.outer, ...part.holes].map(ringPath).join(" ")}
            fillRule="evenodd"
            className="fill-muted-foreground/20"
          />
        ))}
        {data.wards.map((ward) => (
          <g key={ward.ward_id}>
            {ward.parts.map((part, i) => (
              <path
                key={i}
                d={[part.outer, ...part.holes].map(ringPath).join(" ")}
                fillRule="evenodd"
                fill={hviColor(ward.hvi)}
                stroke="var(--background)"
                strokeWidth={0.006}
                strokeLinejoin="round"
              />
            ))}
          </g>
        ))}
      </svg>
    </div>
  );
}

export default function HeroCity() {
  const [data, setData] = useState<HeroCityData | null>(null);
  const [region, setRegion] = useState<HeroRegionData | null>(null);
  const [hover, setHover] = useState<HoverPayload>(null);
  const [revealed, setRevealed] = useState(false);
  const webGL = useSyncExternalStore(noopSubscribe, getWebGLSnapshot, () => false);
  const backgroundColor = useSyncExternalStore(
    subscribeTheme,
    getBackgroundSnapshot,
    getBackgroundServerSnapshot
  );
  const { resolvedTheme } = useTheme();
  const mounted = useMounted();
  const isDark = mounted && resolvedTheme === "dark";

  /**
   * onCreated fires before the first frame is on screen, so wait two frames for
   * it to actually land before starting the fade.
   *
   * The timeout is not belt-and-braces: requestAnimationFrame is suspended
   * entirely while a tab is backgrounded or occluded, so a page opened in a
   * background tab would otherwise come back to a permanently invisible model.
   */
  const handleReady = useCallback(() => {
    const reveal = () => setRevealed(true);
    requestAnimationFrame(() => requestAnimationFrame(reveal));
    window.setTimeout(reveal, 400);
  }, []);

  useEffect(() => {
    let cancelled = false;
    fetch(HERO_CITY_URL)
      .then((res) => {
        if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
        return res.json() as Promise<HeroCityData>;
      })
      .then((json) => {
        if (!cancelled) setData(json);
      })
      // The hero still reads without its subject; a failed decorative fetch
      // must never surface an error banner above the fold.
      .catch(() => undefined);

    // The city renders on its own if the surrounding coast fails to load.
    fetch(HERO_REGION_URL)
      .then((res) => (res.ok ? (res.json() as Promise<HeroRegionData>) : null))
      .then((json) => {
        if (!cancelled && json) setRegion(json);
      })
      .catch(() => undefined);

    return () => {
      cancelled = true;
    };
  }, []);

  const hoveredAreas = hover ? areasForWard(hover.ward.ward_id) : [];

  return (
    // Absolute rather than h-full: as a flex item with `flex-basis: 0%`, the
    // parent has no definite height for a percentage to resolve against, so
    // h-full collapsed the canvas to its min-height and let the backdrop show
    // through underneath it.
    <div className="absolute inset-0">
      {data && (
        // Mounted hidden and faded in only once the renderer reports a frame,
        // so the model arrives rather than popping. Fading the wrapper on mount
        // instead would play the animation over a still-empty canvas and the
        // city would appear abruptly at the end of it.
        <div
          aria-hidden
          className={`absolute inset-0 ${hover ? "cursor-pointer" : ""}`}
          // Inline rather than utility classes: the reveal has to be exact, and
          // a stylesheet !important still wins over this, so the global
          // prefers-reduced-motion rule that flattens transition durations
          // continues to apply.
          style={{
            opacity: revealed ? 1 : 0,
            transform: revealed ? "translateY(0)" : "translateY(18px)",
            transition: "opacity 900ms ease-out, transform 900ms ease-out",
          }}
        >
          {webGL ? (
            <HeroCityScene
              data={data}
              region={region}
              isDark={isDark}
              backgroundColor={backgroundColor}
              hoveredId={hover?.ward.ward_id ?? null}
              onHover={setHover}
              onReady={handleReady}
            />
          ) : (
            <HeroCityFlat data={data} region={region} onReady={handleReady} />
          )}
        </div>
      )}

      {hover && (
        <div
          role="status"
          className="pointer-events-none absolute z-10 max-w-[17rem] -translate-x-1/2 -translate-y-full rounded-lg border border-border bg-background/95 px-2.5 py-1.5 shadow-sm backdrop-blur-sm"
          style={{ left: hover.x, top: hover.y - 12 }}
        >
          <p className="text-xs font-semibold text-foreground">Ward {hover.ward.ward_id}</p>
          {hoveredAreas.length > 0 && (
            <p className="mt-0.5 max-w-[15rem] text-[11px] leading-snug text-muted-foreground">
              {hoveredAreas.join(", ")}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
