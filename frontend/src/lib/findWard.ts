/**
 * Find-my-ward plumbing (issue #116): turn the browser's location into a BMC
 * ward id.
 *
 * Two pure, testable steps, wired together by the dashboard's "find my ward"
 * button: geolocation (navigator.geolocation) -> /api/v1/lookup -> ward id.
 * Everything here is deliberately UI-free. The policy decisions that matter to
 * users — only asking for location on a button tap, never on page load, and
 * wording every refusal without blaming the user — live with the caller, which
 * is also where the button's loading/disabled state is owned.
 *
 * Failures are typed as {@link LocateFailure} so the caller can render the
 * right message instead of sniffing strings. {@link LOCATE_ERROR_MESSAGE}
 * keeps that copy in one place.
 */

/** Why "where am I" failed, from the user's point of view. */
export type LocateFailureKind =
  | "unsupported" // no geolocation API at all
  | "denied" // user refused the permission prompt
  | "unavailable" // permission granted, position unknown
  | "timeout" // position did not arrive in time
  | "outside" // position resolved, but not inside any BMC ward
  | "lookup"; // the ward lookup failed for another reason

export interface LocateFailure {
  kind: LocateFailureKind;
}

/** Copy for each failure kind, one sentence, no jargon. */
export const LOCATE_ERROR_MESSAGE: Record<LocateFailureKind, string> = {
  unsupported: "Location isn't available in this browser.",
  denied: "Location permission was denied. You can pick your ward from the list instead.",
  unavailable: "Your location couldn't be determined right now.",
  timeout: "Finding your location timed out. Try again.",
  outside: "You're outside the 24 BMC wards, so there's no ward here.",
  lookup: "Couldn't look up your ward. Try again in a moment.",
};

export function isLocateFailure(value: unknown): value is LocateFailure {
  return (
    typeof value === "object" &&
    value !== null &&
    "kind" in value &&
    typeof (value as LocateFailure).kind === "string"
  );
}

function positionErrorKind(error: GeolocationPositionError): LocateFailure {
  // GeolocationPositionError codes are 1 (denied), 2 (unavailable), 3 (timeout).
  switch (error.code) {
    case 1:
      return { kind: "denied" };
    case 2:
      return { kind: "unavailable" };
    case 3:
      return { kind: "timeout" };
    default:
      return { kind: "unavailable" };
  }
}

export interface LatLng {
  lat: number;
  lng: number;
}

/**
 * Requests the current position, resolving to coordinates or rejecting with a
 * {@link LocateFailure}. Called from a click handler only — never from an
 * effect — so the browser's permission prompt is tied to a user gesture.
 *
 * The timeout and maximumAge are deliberate: a 10s cap stops a slow fix from
 * hanging the button forever, and maximumAge accepts a cached fix from the
 * last few minutes — still accurate enough for a ward lookup, which only
 * needs to know which of the 24 wards contains the visitor.
 */
export function requestLocation(): Promise<LatLng> {
  return new Promise((resolve, reject) => {
    if (typeof navigator === "undefined" || !("geolocation" in navigator)) {
      reject({ kind: "unsupported" } satisfies LocateFailure);
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) =>
        resolve({ lat: position.coords.latitude, lng: position.coords.longitude }),
      (error) => reject(positionErrorKind(error)),
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 5 * 60 * 1000 }
    );
  });
}

export interface WardHit {
  ward_id: string;
}

/**
 * Resolves a coordinate to its containing ward via GET /api/v1/lookup.
 * A 404 means the point is outside the 24 BMC wards; anything else non-OK or
 * malformed is treated as a lookup failure rather than guessed at.
 */
export async function lookupWard(lat: number, lng: number): Promise<WardHit> {
  const params = new URLSearchParams({ lat: String(lat), lon: String(lng) });
  let res: Response;
  try {
    res = await fetch(`/api/v1/lookup?${params.toString()}`);
  } catch {
    throw { kind: "lookup" } satisfies LocateFailure;
  }
  if (res.status === 404) throw { kind: "outside" } satisfies LocateFailure;
  if (!res.ok) throw { kind: "lookup" } satisfies LocateFailure;
  const data = (await res.json().catch(() => null)) as {
    ward?: WardHit;
  } | null;
  if (!data?.ward?.ward_id) throw { kind: "lookup" } satisfies LocateFailure;
  return { ward_id: data.ward.ward_id };
}

/**
 * The whole find-my-ward flow: location fix, then ward lookup. Resolves to the
 * containing ward id, rejects with a {@link LocateFailure}.
 */
export async function findMyWard(): Promise<string> {
  const { lat, lng } = await requestLocation();
  const { ward_id } = await lookupWard(lat, lng);
  return ward_id;
}
