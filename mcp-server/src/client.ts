/**
 * The UCIP REST API, as functions (issue #102).
 *
 * Split out from the tool definitions so the transport can be tested without
 * standing up an MCP server, and so the tools stay about shape and wording
 * rather than about fetch.
 *
 * Everything here reads the same public endpoints a browser would. There is no
 * key, no privileged path, and nothing an assistant can reach through this
 * that a person could not reach with curl.
 */

const DEFAULT_BASE_URL = "https://uciplatform.vercel.app";

export class UcipError extends Error {
  readonly status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "UcipError";
    this.status = status;
  }
}

export type Ward = {
  ward_id: string;
  hvi: number | null;
  rank: number | null;
  n_cells: number | null;
  contrib: Record<string, number> | null;
  dominant_factor?: string | null;
  dominant_share?: number | null;
  single_factor_dominated?: boolean | null;
};

export type Recommendation = {
  ward_id?: string;
  intervention: string;
  rationale: string;
  citation: string;
  priority: number;
};

export type Meta = Record<string, unknown>;

export class UcipClient {
  private readonly baseUrl: string;
  private readonly fetchImpl: typeof globalThis.fetch;

  constructor(options: { baseUrl?: string; fetch?: typeof globalThis.fetch } = {}) {
    this.baseUrl = (options.baseUrl ?? process.env.UCIP_BASE_URL ?? DEFAULT_BASE_URL).replace(/\/+$/, "");
    this.fetchImpl = options.fetch ?? globalThis.fetch;
  }

  private async get<T>(path: string, query: Record<string, unknown> = {}): Promise<T> {
    const url = new URL(`${this.baseUrl}/api/v1${path}`);
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined && value !== null) url.searchParams.set(key, String(value));
    }

    const response = await this.fetchImpl(url.toString(), {
      headers: { accept: "application/json" },
    });

    if (!response.ok) {
      let message = `${response.status} ${response.statusText}`;
      try {
        const body = (await response.json()) as { error?: { message?: string } | string };
        const text = typeof body.error === "string" ? body.error : body.error?.message;
        if (text) message = text;
      } catch {
        // Non-JSON error body, such as a proxy page. The status is the useful part.
      }
      throw new UcipError(message, response.status);
    }

    return (await response.json()) as T;
  }

  meta(): Promise<Meta> {
    return this.get<Meta>("/meta");
  }

  async wards(limit?: number): Promise<Ward[]> {
    const body = await this.get<{ wards: Ward[] }>("/wards", { limit });
    return body.wards;
  }

  ward(wardId: string): Promise<{ ward: Ward; recommendations: Recommendation[] }> {
    // Ward codes contain slashes (F/N, R/C), so the segment must be encoded or
    // the path splits into two.
    return this.get(`/wards/${encodeURIComponent(wardId)}`);
  }

  lookup(lat: number, lon: number): Promise<{ ward: Ward; top_recommendation: Recommendation | null }> {
    return this.get("/lookup", { lat, lon });
  }

  async recommendations(wardId?: string, limit?: number): Promise<Recommendation[]> {
    const body = await this.get<{ recommendations: Recommendation[] }>("/recommendations", {
      ward: wardId,
      limit,
    });
    return body.recommendations;
  }
}
