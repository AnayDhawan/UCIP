/**
 * A typed client for the UCIP API (issue #103).
 *
 * The response types in `types.gen.ts` are generated from the OpenAPI spec, so
 * they cannot drift from the API without CI noticing. The methods here are
 * hand-written over those types, because there are seven of them and a
 * generated method layer would be harder to read than the thing it replaced.
 *
 * Design notes worth stating once:
 *
 * No default retries. The API is cached hard at the edge and the failure a
 * consumer usually hits is a 429 from defeating that cache in a loop, which a
 * retry makes worse. `retryAfterSeconds` is surfaced on the error instead, so
 * a caller who wants to back off can do it deliberately.
 *
 * No client-side defaults for query parameters. The server decides what
 * `limit` means when it is absent, and a client that fills in its own default
 * starts disagreeing with the server the moment the server's changes.
 *
 * Ward codes are encoded here. `F/N` is a real ward code and the slash breaks
 * the path if it is passed through, which is the single most likely way to
 * misuse this API by hand.
 */

export * from "./types.gen.js";
export { UcipError, UcipHttpError, UcipNetworkError } from "./errors.js";

import { UcipHttpError, UcipNetworkError } from "./errors.js";
import type {
  Cell,
  CellListResponse,
  ListCellsParams,
  ListRecommendationsParams,
  ListWardsParams,
  LookupResponse,
  Meta,
  RecommendationListResponse,
  Ward,
  WardDetailResponse,
  WardListResponse,
} from "./types.gen.js";

export const DEFAULT_BASE_URL = "https://uciplatform.vercel.app/api/v1";

export type UcipClientOptions = {
  /** Defaults to the public deployment. Point this at a local `next dev` to test against it. */
  baseUrl?: string;
  /** Defaults to the global `fetch`. Supply one to stub requests or add instrumentation. */
  fetch?: typeof globalThis.fetch;
  /** Milliseconds before a request is aborted. Omit for no client-side timeout. */
  timeoutMs?: number;
  /** Extra headers on every request, for a `user-agent` identifying your tool. */
  headers?: Record<string, string>;
};

/** A GeoJSON FeatureCollection, as returned by the export endpoint. */
export type FeatureCollection = {
  type: "FeatureCollection";
  features: Array<{
    type: "Feature";
    geometry: unknown;
    properties: Record<string, unknown>;
  }>;
};

export class UcipClient {
  readonly baseUrl: string;
  readonly #fetch: typeof globalThis.fetch;
  readonly #timeoutMs: number | undefined;
  readonly #headers: Record<string, string>;

  constructor(options: UcipClientOptions = {}) {
    // Trailing slashes are stripped so `new UcipClient({ baseUrl: ".../v1/" })`
    // does not produce a double slash in every path.
    this.baseUrl = (options.baseUrl ?? DEFAULT_BASE_URL).replace(/\/+$/, "");
    this.#fetch = options.fetch ?? globalThis.fetch;
    this.#timeoutMs = options.timeoutMs;
    this.#headers = { accept: "application/json", ...options.headers };

    if (typeof this.#fetch !== "function") {
      throw new TypeError(
        "No fetch available. Node 18 or newer has one built in; otherwise pass `fetch` in the options."
      );
    }
  }

  /** What this deployment serves: coverage, counts, method, data vintage. */
  meta(signal?: AbortSignal): Promise<Meta> {
    return this.#get<Meta>("/meta", {}, signal);
  }

  /** Every ward, ranked most vulnerable first. */
  wards(params: ListWardsParams = {}, signal?: AbortSignal): Promise<WardListResponse> {
    return this.#get<WardListResponse>("/wards", params, signal);
  }

  /**
   * One ward and its ranked recommendations. Encodes split codes such as `F/N`.
   *
   * `async` so the argument check rejects rather than throwing synchronously.
   * A promise-returning method that throws on its own stack is not caught by
   * the `.catch()` the caller wrote, which is a nasty way to learn that a ward
   * id was empty.
   */
  async ward(wardId: string, signal?: AbortSignal): Promise<WardDetailResponse> {
    if (!wardId?.trim()) throw new TypeError("wardId is required");
    return this.#get<WardDetailResponse>(`/wards/${encodeURIComponent(wardId.trim())}`, {}, signal);
  }

  /** The ward containing a coordinate, with its top recommendation. */
  async lookup(lat: number, lon: number, signal?: AbortSignal): Promise<LookupResponse> {
    // Checked here rather than spending a round trip to be told 400. The server
    // validates too; this is about the error arriving at the call site.
    if (!Number.isFinite(lat) || lat < -90 || lat > 90) {
      throw new RangeError(`lat must be between -90 and 90, got ${lat}`);
    }
    if (!Number.isFinite(lon) || lon < -180 || lon > 180) {
      throw new RangeError(`lon must be between -180 and 180, got ${lon}`);
    }
    return this.#get<LookupResponse>("/lookup", { lat, lon }, signal);
  }

  /** Nature-based-solution recommendations, optionally for one ward. */
  recommendations(
    params: ListRecommendationsParams = {},
    signal?: AbortSignal
  ): Promise<RecommendationListResponse> {
    return this.#get<RecommendationListResponse>("/recommendations", params, signal);
  }

  /** The 1 km analysis grid the ward scores are built from. */
  cells(params: ListCellsParams = {}, signal?: AbortSignal): Promise<CellListResponse> {
    return this.#get<CellListResponse>("/cells", params, signal);
  }

  /**
   * The whole dataset as GeoJSON, in one cached request.
   *
   * Prefer this over paging `cells()` or `wards()`. It is one edge-cached call
   * rather than many, which is easier on this project's free-tier database and
   * far less likely to meet the rate limiter.
   */
  async export(
    dataset: "cells" | "wards" = "cells",
    signal?: AbortSignal
  ): Promise<FeatureCollection> {
    return this.#get<FeatureCollection>("/export", { dataset, format: "geojson" }, signal);
  }

  /** The whole dataset as CSV text, with the feature centre as lon/lat columns. */
  async exportCsv(dataset: "cells" | "wards" = "cells", signal?: AbortSignal): Promise<string> {
    const res = await this.#request(
      this.#url("/export", { dataset, format: "csv" }),
      { accept: "text/csv" },
      signal
    );
    return res.text();
  }

  /**
   * Every ward, as a plain array, ranked most vulnerable first.
   *
   * The common case is wanting the wards, not the envelope around them. The
   * envelope carries `source`, which matters when you are debugging and not
   * otherwise, so `wards()` remains available for that.
   */
  async allWards(signal?: AbortSignal): Promise<Ward[]> {
    return (await this.wards({}, signal)).wards;
  }

  /** Every grid cell, as a plain array. */
  async allCells(signal?: AbortSignal): Promise<Cell[]> {
    return (await this.cells({ limit: 1000 }, signal)).cells;
  }

  #url(path: string, params: Record<string, unknown>): string {
    const url = new URL(`${this.baseUrl}${path}`);
    for (const [key, value] of Object.entries(params)) {
      // Undefined means "not specified", which must mean the parameter is
      // absent rather than the string "undefined".
      if (value === undefined || value === null) continue;
      url.searchParams.set(key, String(value));
    }
    return url.toString();
  }

  async #get<T>(path: string, params: Record<string, unknown>, signal?: AbortSignal): Promise<T> {
    const res = await this.#request(this.#url(path, params), {}, signal);
    return (await res.json()) as T;
  }

  async #request(
    url: string,
    headers: Record<string, string>,
    signal?: AbortSignal
  ): Promise<Response> {
    // A caller's own signal and the timeout both have to be able to abort the
    // request, and AbortSignal.any is the only way to combine them without
    // leaking a timer per call.
    const signals: AbortSignal[] = [];
    if (signal) signals.push(signal);
    if (this.#timeoutMs !== undefined) signals.push(AbortSignal.timeout(this.#timeoutMs));

    let res: Response;
    try {
      res = await this.#fetch(url, {
        method: "GET",
        headers: { ...this.#headers, ...headers },
        signal: signals.length ? AbortSignal.any(signals) : undefined,
      });
    } catch (cause) {
      // An abort the caller asked for is theirs, and is rethrown untouched so
      // `err.name === "AbortError"` keeps working.
      if (cause instanceof Error && cause.name === "AbortError" && signal?.aborted) throw cause;
      throw new UcipNetworkError(`Request to ${url} failed`, { cause });
    }

    if (!res.ok) throw await UcipHttpError.from(res, url);
    return res;
  }
}
