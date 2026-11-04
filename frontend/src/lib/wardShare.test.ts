import { describe, it, expect } from "vitest";
import { wardPageUrl, wardShareText, whatsappHref } from "./wardShare";

describe("wardPageUrl", () => {
  it("builds the page URL from the ward slug, so a split code has no slash", () => {
    expect(wardPageUrl("F/N")).toMatch(/^https?:\/\/[^/]+\/ward\/F-N$/);
    expect(wardPageUrl("L")).toMatch(/\/ward\/L$/);
  });
});

describe("wardShareText", () => {
  it("names the ward, city and priority", () => {
    expect(wardShareText("F/N", 12, 24)).toBe(
      "Heat vulnerability in Mumbai ward F/N, priority 12 of 24 (UCIP)"
    );
  });

  it("leaves the priority out when the ward has no rank", () => {
    expect(wardShareText("A", null, 24)).toBe("Heat vulnerability in Mumbai ward A (UCIP)");
  });
});

describe("whatsappHref", () => {
  it("puts the encoded text and page URL in the wa.me text parameter", () => {
    const href = whatsappHref("Ward F/N & more", "https://uciplatform.vercel.app/ward/F-N");
    expect(href.startsWith("https://wa.me/?text=")).toBe(true);
    expect(href).not.toContain(" ");
    expect(decodeURIComponent(href.slice("https://wa.me/?text=".length))).toBe(
      "Ward F/N & more https://uciplatform.vercel.app/ward/F-N"
    );
  });
});
