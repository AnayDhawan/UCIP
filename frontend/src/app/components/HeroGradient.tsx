"use client";

import { useSyncExternalStore } from "react";
import { MeshGradient } from "@paper-design/shaders-react";

function supportsWebGL(): boolean {
  try {
    const canvas = document.createElement("canvas");
    return !!(canvas.getContext("webgl2") || canvas.getContext("webgl"));
  } catch {
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

/**
 * Animated mesh-gradient backdrop for the landing hero, built on
 * @paper-design/shaders-react. Colors are drawn from the actual choropleth
 * palette (khaki/yellow low-HVI end, plantability green) rather than the
 * brand teal/emerald pair, so the hero visually echoes the map itself.
 * Scoped strictly to its own absolutely-positioned layer (`-z-10`) — never
 * touches text, which stays solid-color per DESIGN.md's gradient-text ban.
 * Skips mounting the WebGL canvas entirely (falls back to a static CSS
 * gradient) when the OS requests reduced motion or WebGL isn't available, so
 * there's no wasted GPU/battery cost either way. Subscribed to the OS
 * reduced-motion media query live, so toggling it while the page is open
 * takes effect immediately.
 */
export default function HeroGradient() {
  const canAnimate = useSyncExternalStore(
    subscribeReducedMotion,
    getCanAnimateSnapshot,
    getCanAnimateServerSnapshot
  );

  return (
    <div className="absolute inset-0 overflow-hidden" aria-hidden>
      {canAnimate ? (
        <MeshGradient
          colors={["#fed976", "#4ade80", "#4d3d1f", "#fed976"]}
          distortion={0.85}
          swirl={0.35}
          speed={0.22}
          style={{ width: "100%", height: "100%" }}
        />
      ) : (
        <div className="h-full w-full bg-gradient-to-br from-[#fed976]/25 via-background to-[#4ade80]/20" />
      )}
      <div className="absolute inset-0 mesh-hero-scrim" />
    </div>
  );
}
