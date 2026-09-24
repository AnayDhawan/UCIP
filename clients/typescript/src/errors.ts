/**
 * Errors the client throws.
 *
 * Three classes rather than one, because the three cases call for different
 * handling and a caller should not have to parse a message to tell them apart:
 * the network never answered, the API answered with a refusal, or something
 * else went wrong. `UcipError` is the base, so `catch (e) { if (e instanceof
 * UcipError) }` catches everything this library throws and nothing it does not.
 */

/** Base class for every error this client throws. */
export class UcipError extends Error {
  constructor(message: string, options?: { cause?: unknown }) {
    super(message, options);
    this.name = new.target.name;
  }
}

/** The request never produced a response: DNS, TLS, connection refused, timeout. */
export class UcipNetworkError extends UcipError {}

/**
 * The API answered with a non-2xx status.
 *
 * `status` and the parsed `message`/`hint` from the API's error envelope are
 * exposed as fields, so handling a 404 does not mean matching on a string.
 */
export class UcipHttpError extends UcipError {
  readonly status: number;
  readonly url: string;
  /** The API's own explanation, when it sent one. */
  readonly detail: string | undefined;
  /** The API's suggested next step, when it sent one. */
  readonly hint: string | undefined;
  /** Seconds to wait, from the `retry-after` header on a 429. */
  readonly retryAfterSeconds: number | undefined;
  /** The raw body, for the case where it was not the expected envelope. */
  readonly body: string;

  constructor(init: {
    status: number;
    url: string;
    detail?: string;
    hint?: string;
    retryAfterSeconds?: number;
    body: string;
  }) {
    const summary = init.detail ?? init.body.slice(0, 200) ?? "";
    super(`UCIP API returned ${init.status} for ${init.url}${summary ? `: ${summary}` : ""}`);
    this.status = init.status;
    this.url = init.url;
    this.detail = init.detail;
    this.hint = init.hint;
    this.retryAfterSeconds = init.retryAfterSeconds;
    this.body = init.body;
  }

  /** True when backing off and retrying is the right response. */
  get isRateLimited(): boolean {
    return this.status === 429;
  }

  /**
   * Builds the error from a response.
   *
   * Reads the body defensively. An error from an edge proxy rather than the
   * API itself is HTML, not the JSON envelope, and failing to parse it must
   * not replace a useful 502 with a JSON syntax error.
   */
  static async from(res: Response, url: string): Promise<UcipHttpError> {
    let body = "";
    try {
      body = await res.text();
    } catch {
      body = "";
    }

    let detail: string | undefined;
    let hint: string | undefined;
    try {
      const parsed = JSON.parse(body) as { error?: { message?: string; hint?: string } };
      detail = parsed?.error?.message;
      hint = parsed?.error?.hint;
    } catch {
      // Not the API's envelope. `body` still carries whatever arrived.
    }

    const retryAfter = Number(res.headers.get("retry-after"));

    return new UcipHttpError({
      status: res.status,
      url,
      detail,
      hint,
      retryAfterSeconds: Number.isFinite(retryAfter) && retryAfter > 0 ? retryAfter : undefined,
      body,
    });
  }
}
