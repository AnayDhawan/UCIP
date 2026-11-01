import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const { init, register } = vi.hoisted(() => ({ init: vi.fn(), register: vi.fn() }));

vi.mock("posthog-js", () => ({ default: { init, register } }));

describe("instrumentation-client", () => {
  beforeEach(() => {
    vi.resetModules();
    init.mockClear();
    register.mockClear();
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it("does not throw or init PostHog in development when the variables are unset", async () => {
    vi.stubEnv("NODE_ENV", "development");
    vi.stubEnv("NEXT_PUBLIC_POSTHOG_PROJECT_TOKEN", "");
    vi.stubEnv("NEXT_PUBLIC_POSTHOG_HOST", "");
    const info = vi.spyOn(console, "info").mockImplementation(() => {});

    await expect(import("../../instrumentation-client")).resolves.toBeDefined();

    expect(init).not.toHaveBeenCalled();
    expect(info).toHaveBeenCalledTimes(1);
  });

  it("initialises PostHog with the same options when both variables are set", async () => {
    vi.stubEnv("NODE_ENV", "production");
    vi.stubEnv("NEXT_PUBLIC_POSTHOG_PROJECT_TOKEN", "phc_test");
    vi.stubEnv("NEXT_PUBLIC_POSTHOG_HOST", "https://eu.i.posthog.com");

    await import("../../instrumentation-client");

    expect(init).toHaveBeenCalledWith("phc_test", {
      api_host: "https://eu.i.posthog.com",
      defaults: "2026-01-30",
      capture_exceptions: true,
      debug: false,
    });
    expect(register).toHaveBeenCalledWith({ site: "ucip" });
  });
});
