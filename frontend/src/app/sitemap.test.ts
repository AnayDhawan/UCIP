import { describe, it, expect } from "vitest";
import sitemap from "./sitemap";

describe("sitemap", () => {
  const entries = sitemap();
  const wardEntries = entries.filter(({ url }) => url.includes("/ward/"));

  it("lists one page per ward, with slashes in ward codes made URL-safe", () => {
    expect(wardEntries).toHaveLength(24);
    expect(new Set(wardEntries.map(({ url }) => url)).size).toBe(24);
    expect(wardEntries.map(({ url }) => url.split("/ward/")[1])).toEqual(
      expect.arrayContaining(["A", "L", "F-N", "R-C"])
    );
    for (const { url } of wardEntries) expect(url.split("/ward/")[1]).not.toContain("/");
  });

  it("gives ward pages priority 0.5 and the refresh date the data pages carry", () => {
    const dashboard = entries.find(({ url }) => url.endsWith("/dashboard"));
    expect(dashboard?.lastModified).toBeInstanceOf(Date);
    for (const entry of wardEntries) {
      expect(entry.priority).toBe(0.5);
      expect(entry.lastModified).toEqual(dashboard?.lastModified);
    }
  });

  it("keeps the existing site pages", () => {
    const urls = entries.map(({ url }) => url);
    expect(urls.some((u) => u.endsWith("/methodology"))).toBe(true);
    expect(urls.some((u) => u.endsWith("/dashboard"))).toBe(true);
  });
});
