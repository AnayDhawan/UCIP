"use client";

import { useEffect, useMemo } from "react";
import { Canvas, useThree, type ThreeEvent } from "@react-three/fiber";
import * as THREE from "three";
import { hviColor } from "@/lib/hvi";
import type { HeroCityData, HeroCityWard, HeroRegionData, HeroPart } from "./heroCityData";

/**
 * The extruded-Mumbai hero model, sitting on a curved piece of the planet.
 *
 * Two registers, deliberately:
 *   - The 24 BMC wards are the subject. Real boundaries
 *     (data/bmc_wards.geojson), height and colour from their real HVI, lit and
 *     crisp, using the same locked ColorBrewer ramp as the map legend
 *     (lib/hvi.ts, DESIGN.md semantic data colours).
 *   - Everything else is context. The surrounding coast is Natural Earth 1:10m
 *     (public domain), drawn unlit, desaturated and faded into fog so it reads
 *     as out-of-focus geography and never competes with a scored ward.
 *
 * North is up and the model does not rotate: it reads as a map that happens to
 * have height, not a turntable. The only motion is the hover response.
 *
 * Kept in its own file so `three` only enters the bundle through HeroCity.tsx's
 * dynamic import, never on the server render or on a no-WebGL client.
 */

/** Flat slab height for a ward scoring 0, so nothing renders as zero-thickness. */
const BASE_HEIGHT = 0.035;
/** Extra height at HVI 100. Tuned so the tallest ward reads clearly at hero scale without towering. */
const HEIGHT_AT_MAX_HVI = 0.26;

/**
 * Radius of the curved ground, in model units (1 unit is about 20.8 km).
 *
 * True Earth would be roughly 307 units here, which bends the 7.5-unit region
 * by under a tenth of a unit: real, invisible, pointless. This is exaggerated
 * by around 10x so a horizon actually appears behind the city. It is a
 * deliberate visual choice on a decorative surface, and it never touches the
 * ward geometry's own shape, only where the wards sit.
 */
const CURVATURE_RADIUS = 32;

/** Land is lifted a hair above the ocean shell so the two never z-fight along the coast. */
const LAND_LIFT = 0.004;

/** Camera elevation above the ground plane, radians. Roughly 58 degrees, so the
 *  city reads as a map with height rather than a skyline in perspective. */
const CAMERA_ELEVATION = 1.01;
/** Half-extents of the city plus margin, in model units, that must stay in frame.
 *  North-south is the long axis here, since the model is not rotated. */
const REQUIRED_HALF_WIDTH = 0.72;
const REQUIRED_HALF_DEPTH = 1.12;

/**
 * Where the city sits inside the canvas.
 *
 * The canvas spans the entire hero, not a band under the copy, so the section
 * reads as one scene rather than two stacked panels. That only works if the
 * model gets out of the headline's way: on a wide viewport it moves right and
 * forward, into the space the copy leaves empty. On a narrow one there is no
 * such space, so it stays centred and simply sits lower.
 *
 * +x is right on screen; +z is toward the camera, which reads as downward.
 */
function framingFor(aspect: number): { offsetX: number; offsetZ: number } {
  if (aspect > 1.5) return { offsetX: 0.62, offsetZ: 0.34 };
  // Portrait: no side column to move into, so the city drops well below the
  // centred copy instead. The larger offset also pushes the camera back, which
  // shrinks the model and keeps it from crowding the headline.
  return { offsetX: 0, offsetZ: 1.05 };
}

const CAMERA_FOV = 34;

/** Extra breathing room around the city, as a multiplier on the framing extents.
 *  Above 1 the camera sits further back and the model reads smaller. */
const FRAME_MARGIN = 1.2;

/**
 * How far back the camera has to sit for the whole city, including its framing
 * offset, to stay in shot at this canvas shape. Shared with the fog so the haze
 * always begins past the city rather than washing over it.
 */
function cameraDistanceFor(aspect: number): number {
  const halfV = (CAMERA_FOV * Math.PI) / 360;
  const halfH = Math.atan(Math.tan(halfV) * aspect);
  const { offsetX, offsetZ } = framingFor(aspect);
  // North-south depth is foreshortened by the camera's elevation.
  const projectedHalfDepth = (REQUIRED_HALF_DEPTH + Math.abs(offsetZ)) * Math.sin(CAMERA_ELEVATION);
  return (
    FRAME_MARGIN *
    Math.max(
      (REQUIRED_HALF_WIDTH + Math.abs(offsetX)) / Math.tan(halfH),
      projectedHalfDepth / Math.tan(halfV)
    )
  );
}

/**
 * Drop a point onto the curved ground. Shapes are authored in the XY plane and
 * extruded along +Z, so "down onto the sphere" is a -Z offset here; the parent
 * group tips the whole thing flat afterwards.
 */
function surfaceDrop(x: number, y: number): number {
  const rSq = x * x + y * y;
  const inner = CURVATURE_RADIUS * CURVATURE_RADIUS - rSq;
  if (inner <= 0) return -CURVATURE_RADIUS;
  return Math.sqrt(inner) - CURVATURE_RADIUS;
}

/** Bend a flat extruded geometry onto the curved ground, in place. */
function curve(geometry: THREE.BufferGeometry): THREE.BufferGeometry {
  const pos = geometry.attributes.position;
  for (let i = 0; i < pos.count; i++) {
    const x = pos.getX(i);
    const y = pos.getY(i);
    pos.setZ(i, pos.getZ(i) + surfaceDrop(x, y));
  }
  pos.needsUpdate = true;
  geometry.computeVertexNormals();
  return geometry;
}

function partsToShapes(parts: HeroPart[]): THREE.Shape[] {
  return parts.map((part) => {
    const shape = new THREE.Shape(part.outer.map(([x, y]) => new THREE.Vector2(x, y)));
    for (const hole of part.holes) {
      shape.holes.push(new THREE.Path(hole.map(([x, y]) => new THREE.Vector2(x, y))));
    }
    return shape;
  });
}

function wardHeight(hvi: number | null): number {
  if (hvi === null) return BASE_HEIGHT;
  return BASE_HEIGHT + (Math.max(0, Math.min(100, hvi)) / 100) * HEIGHT_AT_MAX_HVI;
}

export type HoverPayload = { ward: HeroCityWard; x: number; y: number } | null;

/** One ward: every part of its (Multi)Polygon extruded to the same height. */
function WardMesh({
  ward,
  hovered,
  onHover,
}: {
  ward: HeroCityWard;
  hovered: boolean;
  onHover: (payload: HoverPayload) => void;
}) {
  const geometry = useMemo(
    () =>
      curve(
        new THREE.ExtrudeGeometry(partsToShapes(ward.parts), {
          depth: wardHeight(ward.hvi),
          bevelEnabled: false,
          curveSegments: 1,
        })
      ),
    [ward]
  );

  // offsetX/offsetY are already relative to the canvas, which shares its box
  // with the tooltip's positioning parent. Using them avoids measuring the
  // wrapper during render.
  const track = (e: ThreeEvent<PointerEvent>) => {
    e.stopPropagation();
    onHover({ ward, x: e.nativeEvent.offsetX, y: e.nativeEvent.offsetY });
  };

  return (
    <mesh
      geometry={geometry}
      onPointerOver={track}
      onPointerMove={track}
      onPointerOut={(e) => {
        e.stopPropagation();
        onHover(null);
      }}
    >
      <meshLambertMaterial
        color={hviColor(ward.hvi)}
        emissive={hviColor(ward.hvi)}
        emissiveIntensity={hovered ? 0.42 : 0}
      />
    </mesh>
  );
}

/**
 * The surrounding coast: flat, unlit, hazed. Context, not subject.
 *
 * Slightly translucent, along with the ocean below it, so the hero's mesh
 * gradient still reads through the ground. The canvas covers the whole section
 * now, and a fully opaque ground simply painted the glow out.
 */
function RegionLand({ region, color }: { region: HeroRegionData; color: string }) {
  const geometry = useMemo(
    () => curve(new THREE.ShapeGeometry(partsToShapes(region.parts), 1)),
    [region]
  );
  return (
    <mesh geometry={geometry} position={[0, 0, LAND_LIFT]}>
      <meshBasicMaterial color={color} transparent opacity={0.86} />
    </mesh>
  );
}

/**
 * The curved ground the whole scene sits on: a genuine sphere cap, so the
 * horizon behind the city is real geometry rather than a faded gradient.
 */
function Ocean({ radius, color }: { radius: number; color: string }) {
  const geometry = useMemo(() => {
    const capAngle = Math.asin(Math.min(1, radius / CURVATURE_RADIUS));
    return new THREE.SphereGeometry(CURVATURE_RADIUS, 96, 48, 0, Math.PI * 2, 0, capAngle);
  }, [radius]);
  return (
    <mesh geometry={geometry} position={[0, -CURVATURE_RADIUS, 0]}>
      <meshBasicMaterial color={color} transparent opacity={0.78} />
    </mesh>
  );
}

/**
 * Pull the camera back far enough that the whole city fits, whatever the canvas
 * shape is. Vertical FOV is fixed, so a narrow phone viewport has a much
 * narrower horizontal FOV than a wide desktop band and would otherwise crop the
 * city's ends. Elevation is preserved, only the distance changes.
 */
function ResponsiveCamera() {
  const camera = useThree((state) => state.camera);
  const size = useThree((state) => state.size);
  const invalidate = useThree((state) => state.invalidate);

  useEffect(() => {
    if (!("fov" in camera)) return;
    const perspective = camera as THREE.PerspectiveCamera;
    const distance = cameraDistanceFor(size.width / size.height);
    perspective.position.set(
      0,
      distance * Math.sin(CAMERA_ELEVATION),
      distance * Math.cos(CAMERA_ELEVATION)
    );
    perspective.lookAt(0, 0, 0);
    perspective.updateProjectionMatrix();
    invalidate();
  }, [camera, size, invalidate]);

  return null;
}

/** Keeps the on-demand loop painting while a hover highlight is settling. */
function InvalidateOnHover({ hoveredId }: { hoveredId: string | null }) {
  const invalidate = useThree((state) => state.invalidate);
  useEffect(() => invalidate(), [hoveredId, invalidate]);
  return null;
}

function Scene({
  data,
  region,
  hoveredId,
  onHover,
  palette,
}: {
  data: HeroCityData;
  region: HeroRegionData | null;
  hoveredId: string | null;
  onHover: (payload: HoverPayload) => void;
  palette: { land: string; ocean: string; fog: string };
}) {
  const regionRadius = region?.region_radius_units ?? 7.5;
  const size = useThree((state) => state.size);
  const aspect = size.width / size.height;
  const { offsetX, offsetZ } = framingFor(aspect);
  const distance = cameraDistanceFor(aspect);

  return (
    <>
      {/* Haze, not blur: the context fades out with distance instead of being
          optically defocused, which would cost a fullscreen post-processing
          pass on the page that owns the site's LCP.

          `far` is set well inside the ground's own radius and the fog colour is
          sampled from the live --background, so the ground is already fully
          faded into the page before its edge is reached. Without that the sphere
          cap's rim showed up as a hard horizontal seam across the section. */}
      <fog attach="fog" args={[palette.fog, distance + 1.2, distance + regionRadius * 0.7]} />
      <ResponsiveCamera />
      <InvalidateOnHover hoveredId={hoveredId} />
      <group position={[offsetX, -0.06, offsetZ]}>
        <Ocean radius={regionRadius} color={palette.ocean} />
        {/* Shapes are authored in the XY plane and extrude along +Z; tip the
            whole model back so the footprint lies flat, the extrusion points up
            and the data's north ends up pointing away from the camera, which
            projects to up on screen. */}
        <group rotation={[-Math.PI / 2, 0, 0]}>
          {region && <RegionLand region={region} color={palette.land} />}
          {data.wards.map((ward) => (
            <WardMesh
              key={ward.ward_id}
              ward={ward}
              hovered={hoveredId === ward.ward_id}
              onHover={onHover}
            />
          ))}
        </group>
      </group>
    </>
  );
}

export default function HeroCityScene({
  data,
  region,
  isDark,
  backgroundColor,
  hoveredId,
  onHover,
  onReady,
}: {
  data: HeroCityData;
  region: HeroRegionData | null;
  isDark: boolean;
  backgroundColor: string | null;
  hoveredId: string | null;
  onHover: (payload: HoverPayload) => void;
  /** Fired once the renderer exists, so the caller can fade the canvas in on a
   *  painted frame rather than on an empty one. */
  onReady?: () => void;
}) {
  const palette = isDark
    ? { land: "#1b333b", ocean: "#0a1c24", fog: backgroundColor ?? "#07141a" }
    : { land: "#c9d8d8", ocean: "#dfeaec", fog: backgroundColor ?? "#eef4f4" };

  return (
    <Canvas
      // Cap DPR: this is a decorative landing-page canvas and the site's LCP
      // element sits right above it. Retina-native rendering is not worth the fill cost.
      dpr={[1, 1.75]}
      // Nothing animates on its own, so only paint when something actually
      // changes: a resize, a theme swap, or a hover.
      frameloop="demand"
      camera={{ position: [0, 1.7, 1.1], fov: 34, near: 0.05, far: 80 }}
      gl={{ antialias: true, alpha: true, powerPreference: "low-power" }}
      onCreated={() => onReady?.()}
      style={{ width: "100%", height: "100%" }}
    >
      <ambientLight intensity={1.1} />
      <directionalLight position={[2.5, 4, 2]} intensity={1.55} />
      <directionalLight position={[-3, 1.5, -1]} intensity={0.3} color="#0EA5B3" />
      <Scene
        data={data}
        region={region}
        hoveredId={hoveredId}
        onHover={onHover}
        palette={palette}
      />
    </Canvas>
  );
}
