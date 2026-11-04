import { ImageResponse } from "next/og";
import { notFound } from "next/navigation";
import { ACTIVE_CITY } from "@/lib/city";
import { hviColor } from "@/lib/hvi";
import { wardSlug } from "@/lib/wardSlug";
import { wardFeatures, wardFromSlug } from "@/lib/wardSnapshot";

// The card WhatsApp, X and others show when a ward page is shared.
export const alt = "UCIP ward heat vulnerability card";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export function generateStaticParams() {
  return wardFeatures.map(({ properties }) => ({ wardId: wardSlug(properties.ward_id) }));
}

export const dynamicParams = false;

const INK = "#111827";
const PAPER = "#f3f6f6";
const MUTED = "#9ca3af";
const TEAL = "#0ea5b3";

export default async function Image({ params }: { params: Promise<{ wardId: string }> }) {
  const { wardId } = await params;
  const ward = wardFromSlug(wardId);
  if (!ward) notFound();
  const { ward_id, HVI, rank } = ward.properties;

  return new ImageResponse(
    (
      <div style={{ display: "flex", width: "100%", height: "100%", background: INK, color: PAPER }}>
        <div style={{ width: 40, height: "100%", background: hviColor(HVI) }} />
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
            flex: 1,
            padding: "56px 72px",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div style={{ fontSize: 52, letterSpacing: 6, color: TEAL }}>UCIP</div>
            <div style={{ fontSize: 34, color: MUTED }}>{`${ACTIVE_CITY.name} heat vulnerability`}</div>
          </div>

          <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between" }}>
            <div style={{ display: "flex", flexDirection: "column" }}>
              <div style={{ fontSize: 44, color: MUTED }}>Ward</div>
              <div style={{ display: "flex", fontSize: 220, lineHeight: 1 }}>{ward_id}</div>
            </div>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end" }}>
              <div style={{ display: "flex", fontSize: 150, lineHeight: 1 }}>
                {HVI?.toFixed(1) ?? "n/a"}
              </div>
              <div style={{ display: "flex", alignItems: "center", fontSize: 30, color: MUTED }}>
                <div
                  style={{
                    width: 26,
                    height: 26,
                    borderRadius: 13,
                    marginRight: 14,
                    background: hviColor(HVI),
                  }}
                />
                Heat vulnerability score, 0 to 100
              </div>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "baseline" }}>
            <div style={{ fontSize: 52 }}>{`Priority ${rank ?? "n/a"} of ${wardFeatures.length} wards`}</div>
            <div style={{ fontSize: 30, color: MUTED, marginLeft: 28 }}>1 is the most vulnerable</div>
          </div>
        </div>
      </div>
    ),
    { ...size }
  );
}
