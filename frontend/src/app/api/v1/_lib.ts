/**
 * Shared plumbing for the public v1 API (issue #70).
 *
 * Design decisions worth stating once, here, rather than repeating per route:
 *
 * Co-located with the site rather than a separate service. TourneyRadar runs its
 * API as its own repo, but here the data, the types and the deployment already
 * exist in this project. One repo means one CI run, one deploy, and no chance of
 * the API and the dashboard disagreeing about what a ward looks like.
 *
 * Read-only and unauthenticated. Everything served is already public: the same
 * numbers are in the committed GeoJSON snapshots and on the dashboard. Requiring
 * a key would add friction and a user table without protecting anything. Writes
 * are impossible regardless, because the anon key is constrained by the RLS
 * policies in supabase/migrations/0005_add_rls_policies.sql, verified on
 * 2026-09-03 by attempting anon INSERT, UPDATE and DELETE against the live
 * database and confirming all three are refused.
 *
 * Cached at the edge, hard. The underlying data changes at most monthly (see
 * pipeline/README.md on refresh cadence), so a long s-maxage with a long
 * stale-while-revalidate keeps Supabase's free tier out of the request path for
 * essentially all traffic, and keeps the dashboard up if the database is
 * unavailable.
 *
 * Falls back to the static snapshots. If Supabase is paused, deleted or simply
 * slow, these routes serve the committed files instead of failing. That is the
 * same demo-safe principle the dashboard was built on, and it earned itself
 * again when the Supabase project was found deleted on 2026-09-03.
 */

import { createClient, type SupabaseClient } from "@supabase/supabase-js";
import { readFile } from "node:fs/promises";
import { join } from "node:path";

export const API_VERSION = "v1";

/** Long cache: the data behind it changes monthly at most. */
export const CACHE_HEADER =
  "public, s-maxage=3600, stale-while-revalidate=86400";

export function jsonResponse(body: unknown, init: ResponseInit = {}): Response {
  return new Response(JSON.stringify(body, null, 2), {
    ...init,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": CACHE_HEADER,
      // Open CORS: the whole point is that other people's pages can call this.
      "access-control-allow-origin": "*",
      "access-control-allow-methods": "GET, OPTIONS",
      ...(init.headers ?? {}),
    },
  });
}

export function errorResponse(status: number, message: string, hint?: string): Response {
  return jsonResponse(
    { error: { status, message, ...(hint ? { hint } : {}) } },
    {
      status,
      // Do not cache errors for as long as data; a 404 may become a 200 after a
      // refresh, and a 503 should retry soon.
      headers: { "cache-control": "public, s-maxage=30" },
    }
  );
}

let cachedClient: SupabaseClient | null = null;

/** The anon-key client, or null when the deployment has no Supabase configured. */
export function supabase(): SupabaseClient | null {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !key) return null;
  cachedClient ??= createClient(url, key, {
    auth: { persistSession: false },
  });
  return cachedClient;
}

/**
 * Reads one of the committed snapshots from `public/`.
 *
 * The fallback path for every route. Slower and coarser than a real query, but
 * it is never unavailable, which is the property that matters when the
 * alternative is a 500.
 */
export async function readSnapshot<T>(filename: string): Promise<T> {
  const path = join(process.cwd(), "public", filename);
  return JSON.parse(await readFile(path, "utf8")) as T;
}

/** Parses and validates a `limit` query param against a sane ceiling. */
export function parseLimit(raw: string | null, fallback: number, max: number): number {
  const n = Number(raw);
  if (!Number.isFinite(n) || n <= 0) return fallback;
  return Math.min(Math.floor(n), max);
}

/**
 * BMC ward codes: one or two uppercase letters, optionally with a single-letter
 * suffix after a slash (A, L, F/N, R/C). Validated rather than trusted, since
 * these arrive from the URL and reach a database query.
 */
const WARD_ID_PATTERN = /^[A-Z]{1,2}(\/[A-Z])?$/;

export function normaliseWardId(raw: string): string | null {
  const id = decodeURIComponent(raw).trim().toUpperCase();
  return WARD_ID_PATTERN.test(id) ? id : null;
}

export function parseCoordinate(raw: string | null, min: number, max: number): number | null {
  if (raw === null || raw.trim() === "") return null;
  const n = Number(raw);
  if (!Number.isFinite(n) || n < min || n > max) return null;
  return n;
}

export function optionsResponse(): Response {
  return new Response(null, {
    status: 204,
    headers: {
      "access-control-allow-origin": "*",
      "access-control-allow-methods": "GET, OPTIONS",
      "access-control-max-age": "86400",
    },
  });
}
