/**
 * Tests for API rate limiting (issue #101).
 *
 * Two things matter here. The limiter must not be bypassable by a client
 * rotating addresses inside its own IPv6 prefix, which is the bug found in
 * tourneyradar-api (#30 there) and fixed here before it could ship. And it must
 * be inert until credentials exist, because the code lands before the store
 * does and a half-configured limiter rejecting real traffic would be worse than
 * no limiter at all.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";

const ORIGINAL_ENV = { ...process.env };

const mockLimit = vi.fn();

// The stubs keep the real signatures so a change to how the limiter is
// constructed shows up here, which is why the parameters are present and unused.
/* eslint-disable @typescript-eslint/no-unused-vars */
vi.mock("@upstash/redis", () => ({
  Redis: class {
    constructor(_config: unknown) {}
  },
}));

vi.mock("@upstash/ratelimit", () => ({
  Ratelimit: class {
    limit = mockLimit;
    static slidingWindow(_tokens: number, _window: string) {
      return {};
    }
  },
}));
/* eslint-enable @typescript-eslint/no-unused-vars */

beforeEach(() => {
  vi.resetModules();
  mockLimit.mockReset();
  process.env = { ...ORIGINAL_ENV };
});

afterEach(() => {
  process.env = { ...ORIGINAL_ENV };
});

async function load() {
  const mod = await import("./rateLimit");
  mod._resetRateLimitForTests();
  return mod;
}

function headers(values: Record<string, string>) {
  return new Headers(values);
}

describe("rateLimitKey", () => {
  it("leaves an IPv4 address alone", async () => {
    const { rateLimitKey } = await load();
    expect(rateLimitKey(headers({ "x-forwarded-for": "203.0.113.4" }))).toBe("203.0.113.4");
  });

  it("takes the first hop of x-forwarded-for", async () => {
    const { rateLimitKey } = await load();
    expect(
      rateLimitKey(headers({ "x-forwarded-for": "203.0.113.4, 70.41.3.18, 150.172.238.178" }))
    ).toBe("203.0.113.4");
  });

  it("falls back to x-real-ip, then to unknown", async () => {
    const { rateLimitKey } = await load();
    expect(rateLimitKey(headers({ "x-real-ip": "203.0.113.9" }))).toBe("203.0.113.9");
    expect(rateLimitKey(headers({}))).toBe("unknown");
  });

  it("masks IPv6 to its /64, so rotating inside a prefix does not reset the count", async () => {
    const { rateLimitKey } = await load();
    const a = rateLimitKey(headers({ "x-forwarded-for": "2001:db8:85a3:8d3::1" }));
    const b = rateLimitKey(headers({ "x-forwarded-for": "2001:db8:85a3:8d3:abcd:ef01:2345:6789" }));
    expect(a).toBe("2001:db8:85a3:8d3::/64");
    expect(a).toBe(b);
  });

  it("keeps separate /64s apart", async () => {
    const { rateLimitKey } = await load();
    expect(rateLimitKey(headers({ "x-forwarded-for": "2001:db8:85a3:8d3::1" }))).not.toBe(
      rateLimitKey(headers({ "x-forwarded-for": "2001:db8:85a3:8d4::1" }))
    );
  });

  it("normalises compression, padding and case to one key", async () => {
    const { rateLimitKey } = await load();
    const keys = [
      "2001:0db8:85a3:08d3:0000:0000:0000:0001",
      "2001:db8:85a3:8d3::1",
      "2001:DB8:85A3:8D3::1",
    ].map((ip) => rateLimitKey(headers({ "x-forwarded-for": ip })));
    expect(new Set(keys).size).toBe(1);
  });

  it("treats an IPv4-mapped address as the IPv4 client it is", async () => {
    const { rateLimitKey } = await load();
    expect(rateLimitKey(headers({ "x-forwarded-for": "::ffff:203.0.113.4" }))).toBe("203.0.113.4");
  });

  it("strips brackets, a port and a zone id", async () => {
    const { rateLimitKey } = await load();
    expect(rateLimitKey(headers({ "x-forwarded-for": "[2001:db8:85a3:8d3::1]:443" }))).toBe(
      "2001:db8:85a3:8d3::/64"
    );
    expect(rateLimitKey(headers({ "x-forwarded-for": "203.0.113.4:5678" }))).toBe("203.0.113.4");
    expect(rateLimitKey(headers({ "x-forwarded-for": "fe80::1%eth0" }))).toBe("fe80:0:0:0::/64");
  });

  it("keys an unparseable value on itself rather than a shared bucket", async () => {
    const { rateLimitKey } = await load();
    const a = rateLimitKey(headers({ "x-forwarded-for": "not:an:address:at:all:x:y:z" }));
    const b = rateLimitKey(headers({ "x-forwarded-for": "also:not:an:address:q:r:s:t" }));
    expect(a).not.toBe(b);
  });
});

describe("checkRateLimit", () => {
  it("is inert with no credentials configured", async () => {
    delete process.env.UPSTASH_REDIS_REST_URL;
    delete process.env.UPSTASH_REDIS_REST_TOKEN;

    const { checkRateLimit } = await load();
    expect(await checkRateLimit(headers({ "x-forwarded-for": "203.0.113.4" }))).toBeNull();
    expect(mockLimit).not.toHaveBeenCalled();
  });

  it("passes a request under the limit", async () => {
    process.env.UPSTASH_REDIS_REST_URL = "https://example.upstash.io";
    process.env.UPSTASH_REDIS_REST_TOKEN = "test-token";
    mockLimit.mockResolvedValue({
      success: true, limit: 120, remaining: 119, reset: Date.now() + 60_000,
    });

    const { checkRateLimit } = await load();
    const result = await checkRateLimit(headers({ "x-forwarded-for": "203.0.113.4" }));
    expect(result?.ok).toBe(true);
    expect(result?.limit).toBe(120);
  });

  it("reports a refusal with a retry-after in seconds", async () => {
    process.env.UPSTASH_REDIS_REST_URL = "https://example.upstash.io";
    process.env.UPSTASH_REDIS_REST_TOKEN = "test-token";
    mockLimit.mockResolvedValue({
      success: false, limit: 120, remaining: 0, reset: Date.now() + 30_000,
    });

    const { checkRateLimit } = await load();
    const result = await checkRateLimit(headers({ "x-forwarded-for": "203.0.113.4" }));
    expect(result?.ok).toBe(false);
    expect(result?.retryAfterSeconds).toBeGreaterThan(0);
    expect(result?.retryAfterSeconds).toBeLessThanOrEqual(30);
  });

  it("fails open when the store errors", async () => {
    process.env.UPSTASH_REDIS_REST_URL = "https://example.upstash.io";
    process.env.UPSTASH_REDIS_REST_TOKEN = "test-token";
    mockLimit.mockRejectedValue(new Error("connection refused"));

    const { checkRateLimit } = await load();
    // Null means "no opinion", so the request proceeds. A read-only public API
    // going down because the thing meant to protect it is down would be worse
    // than the quota pressure it was protecting against.
    expect(await checkRateLimit(headers({ "x-forwarded-for": "203.0.113.4" }))).toBeNull();
  });

  it("counts two addresses in one /64 against the same key", async () => {
    process.env.UPSTASH_REDIS_REST_URL = "https://example.upstash.io";
    process.env.UPSTASH_REDIS_REST_TOKEN = "test-token";
    mockLimit.mockResolvedValue({
      success: true, limit: 120, remaining: 119, reset: Date.now() + 60_000,
    });

    const { checkRateLimit } = await load();
    await checkRateLimit(headers({ "x-forwarded-for": "2001:db8:85a3:8d3:1319:8a2e:370:7348" }));
    await checkRateLimit(headers({ "x-forwarded-for": "2001:db8:85a3:8d3:ffff:ffff:ffff:1" }));

    expect(mockLimit).toHaveBeenCalledTimes(2);
    expect(mockLimit.mock.calls[0][0]).toBe(mockLimit.mock.calls[1][0]);
  });
});
