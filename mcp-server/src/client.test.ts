import { describe, expect, it, vi } from "vitest";
import { UcipClient } from "./client.js";

describe("UcipClient request timeout", () => {
  it("passes an abort signal to fetch", async () => {
    const fetchStub = vi.fn(async (_url: RequestInfo | URL, init?: RequestInit) => {
      expect(init?.signal).toBeInstanceOf(AbortSignal);
      expect(init?.signal?.aborted).toBe(false);
      return new Response(JSON.stringify({ name: "UCIP" }), { status: 200 });
    }) as unknown as typeof globalThis.fetch;

    const client = new UcipClient({ fetch: fetchStub });
    await expect(client.meta()).resolves.toEqual({ name: "UCIP" });
    expect(fetchStub).toHaveBeenCalledTimes(1);
  });

  it("aborts a request that outlives the timeout", async () => {
    // A fetch that never settles on its own and rejects only when its signal fires.
    const hangingFetch = ((_url: RequestInfo | URL, init?: RequestInit) =>
      new Promise<Response>((_resolve, reject) => {
        init?.signal?.addEventListener("abort", () => reject(init.signal?.reason));
      })) as typeof globalThis.fetch;

    const client = new UcipClient({ fetch: hangingFetch, timeoutMs: 20 });
    await expect(client.meta()).rejects.toMatchObject({ name: "TimeoutError" });
  });
});
