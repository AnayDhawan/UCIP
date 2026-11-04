import { describe, it, expect, vi, afterEach } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import WardDetailHeader from "./WardDetailHeader";
import type { WardProps } from "@/lib/wardTypes";

const ward = { ward_id: "F/N", ward_gid: 7, HVI: 58.4, rank: 12, n_cells: 13 } as WardProps;

function renderHeader() {
  return render(<WardDetailHeader ward={ward} totalWards={24} onClose={() => {}} />);
}

afterEach(() => {
  vi.unstubAllGlobals();
  Reflect.deleteProperty(navigator, "share");
});

describe("WardDetailHeader share actions", () => {
  it("links to WhatsApp with the message and the ward page URL", () => {
    renderHeader();

    const link = screen.getByRole("link", { name: "Share ward F/N on WhatsApp" });
    const href = link.getAttribute("href")!;
    expect(href.startsWith("https://wa.me/?text=")).toBe(true);
    const message = decodeURIComponent(href.slice("https://wa.me/?text=".length));
    expect(message).toContain("Heat vulnerability in Mumbai ward F/N, priority 12 of 24 (UCIP)");
    expect(message).toMatch(/https?:\/\/\S+\/ward\/F-N$/);
  });

  it("copies the ward page URL", async () => {
    const writeText = vi.fn(async () => {});
    vi.stubGlobal("navigator", { ...navigator, clipboard: { writeText } });
    renderHeader();

    fireEvent.click(screen.getByRole("button", { name: "Copy link to ward F/N page" }));

    await waitFor(() => expect(writeText).toHaveBeenCalledTimes(1));
    expect(writeText.mock.calls[0]).toEqual([expect.stringMatching(/\/ward\/F-N$/)]);
  });

  it("hides the native share button when the browser has no share sheet", () => {
    renderHeader();

    expect(screen.queryByRole("button", { name: "Share ward F/N" })).toBeNull();
  });

  it("opens the native share sheet with the ward page URL when the browser has one", async () => {
    const share = vi.fn(async () => {});
    Object.defineProperty(navigator, "share", { value: share, configurable: true });
    renderHeader();

    fireEvent.click(screen.getByRole("button", { name: "Share ward F/N" }));

    await waitFor(() => expect(share).toHaveBeenCalledTimes(1));
    expect(share.mock.calls[0]).toEqual([
      expect.objectContaining({ url: expect.stringMatching(/\/ward\/F-N$/) }),
    ]);
  });
});
