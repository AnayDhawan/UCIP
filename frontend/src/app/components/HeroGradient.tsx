"use client";

import { useEffect, useState, useSyncExternalStore } from "react";
import { useTheme } from "next-themes";
import { MeshGradient } from "@paper-design/shaders-react";

function supportsWebGL(): boolean {
  try {
    const canvas = document.createElement("canvas");
    return !!(canvas.getContext("webgl2") || canvas.getContext("webgl"));
  } catch (err) {
    console.warn("[HeroGradient] WebGL probe failed:", err);
    return false;
  }
}

function subscribeReducedMotion(callback: () => void) {
  const mql = window.matchMedia("(prefers-reduced-motion: reduce)");
  mql.addEventListener("change", callback);
  return () => mql.removeEventListener("change", callback);
}

function getCanAnimateSnapshot(): boolean {
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  return !reducedMotion && supportsWebGL();
}

function getCanAnimateServerSnapshot(): boolean {
  return false;
}

/** ms to hold the canvas invisible after mount, giving the shader time to paint its first real frame before it's revealed. */
const CANVAS_REVEAL_DELAY_MS = 150;

/**
 * Animated mesh-gradient backdrop for the landing hero, built on
 * @paper-design/shaders-react. Theme-split palette: dark mode keeps the
 * original brand teal/emerald mesh; light mode uses a lightened tint of the
 * same teal/emerald hues (not the map's amber/green) so both modes read as
 * one family and the near-black body text keeps its contrast margin.
 * Scoped strictly to its own absolutely-positioned layer (`-z-10`) — never
 * touches text, which stays solid-color per DESIGN.md's gradient-text ban.
 * Skips mounting the WebGL canvas entirely (falls back to a static CSS
 * gradient) when the OS requests reduced motion or WebGL isn't available, so
 * there's no wasted GPU/battery cost either way. Subscribed to the OS
 * reduced-motion media query live, so toggling it while the page is open
 * takes effect immediately.
 *
 * The static gradient stays mounted underneath for the whole page lifetime
 * and the canvas crossfades in on top once its first shader frame has had
 * time to land, instead of an instant unmount/remount swap. No
 * black/transparent flash from an un-painted canvas either.
 *
 * Theme comes from next-themes' `resolvedTheme`, gated behind the same
 * `useMounted()` guard `ThemeToggle.tsx` already uses: next-themes reads
 * `localStorage` synchronously inside its own `useState` initializer (see
 * its source), so `resolvedTheme` is NOT safely `undefined` pre-mount — a
 * returning dark-mode visitor gets the real value on the client's hydration
 * render itself, mismatching the server's render. Forcing `isDark = false`
 * until mounted keeps both passes deterministic; the fallback div's
 * `transition-colors` fades the post-mount correction in for real
 * dark-mode visitors instead of popping.
 */
const noopSubscribe = () => () => {};

function useMounted(): boolean {
  return useSyncExternalStore(
    noopSubscribe,
    () => true,
    () => false
  );
}

/**
 * "full" floods the whole hero, the original behaviour. "glow" masks the mesh
 * down to a soft halo low in the section, so it reads as light spilling off the
 * 3D city model instead of a background wash, and the headline above it sits on
 * a clean high-contrast surface.
 */
export type HeroGradientVariant = "full" | "glow";

/** Broad and low: light pooling under and behind the city model, fading out well
 *  before the headline so the copy keeps a clean, high-contrast surface. */
const GLOW_MASK = "radial-gradient(ellipse 92% 68% at 56% 74%, #000 0%, #000 22%, transparent 80%)";
/** Subtle on purpose: a hint of light behind the model, not a second background.
 *  The model's own HVI colours stay the brightest thing in the section. */
const GLOW_OPACITY = 0.5;

export default function HeroGradient({ variant = "full" }: { variant?: HeroGradientVariant }) {
  const canAnimate = useSyncExternalStore(
    subscribeReducedMotion,
    getCanAnimateSnapshot,
    getCanAnimateServerSnapshot
  );
  const { resolvedTheme } = useTheme();
  const mounted = useMounted();
  const isDark = mounted && resolvedTheme === "dark";
  const [canvasVisible, setCanvasVisible] = useState(false);
  const isGlow = variant === "glow";

  /**
   * The glow behind the hero model is deliberately static: the animated mesh
   * kept the backdrop drifting under a model that does not move, which read as
   * the hero never settling. The static CSS gradient is the same palette, holds
   * still, and saves a WebGL context on the page that owns the site's LCP.
   */
  const useMeshCanvas = canAnimate && !isGlow;

  useEffect(() => {
    if (!useMeshCanvas) return;
    const id = setTimeout(() => setCanvasVisible(true), CANVAS_REVEAL_DELAY_MS);
    return () => clearTimeout(id);
  }, [useMeshCanvas]);

  const mesh = isDark
    ? { colors: ["#0EA5B3", "#22C55E", "#0b3a3f", "#0EA5B3"], distortion: 0.85, swirl: 0.35 }
    : { colors: ["#5EEAD4", "#6EE7B7", "#99F6E4", "#5EEAD4"], distortion: 0.55, swirl: 0.18 };

  const fallbackClass = isDark
    ? "bg-gradient-to-br from-brand-teal/25 via-background to-brand-emerald/20"
    : "bg-gradient-to-br from-[#5EEAD4]/35 via-background to-[#6EE7B7]/30";

  const maskStyle = isGlow
    ? { maskImage: GLOW_MASK, WebkitMaskImage: GLOW_MASK, opacity: GLOW_OPACITY }
    : undefined;

  return (
    <div className="absolute inset-0 overflow-hidden" aria-hidden>
      <div className="absolute inset-0" style={maskStyle}>
        <div
          className={`h-full w-full transition-colors transition-opacity duration-700 ease-out ${fallbackClass} ${canvasVisible ? "opacity-0" : "opacity-100"}`}
        />
        {useMeshCanvas && (
          <div
            className={`absolute inset-0 transition-opacity duration-700 ease-out ${canvasVisible ? "opacity-100" : "opacity-0"}`}
          >
            <MeshGradient
              colors={mesh.colors}
              distortion={mesh.distortion}
              swirl={mesh.swirl}
              speed={0.22}
              style={{ width: "100%", height: "100%" }}
            />
          </div>
        )}
      </div>
      {/* The scrim exists to hold text contrast over the mesh. In glow mode the
          text no longer sits on the mesh at all, so scrimming the whole section
          would only mute the halo. */}
      {!isGlow && <div className="absolute inset-0 mesh-hero-scrim" />}
    </div>
  );
}
