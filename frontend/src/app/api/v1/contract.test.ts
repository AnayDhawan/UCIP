/**
 * The published client is a constraint on these route handlers (issue #103).
 *
 * The acceptance criterion for the client package was that the frontend itself
 * uses it, "so it cannot silently rot". This file is the mechanism. It is not
 * a demonstration of the client making HTTP calls to its own server, which
 * would be circular and would prove nothing: it imports the client's generated
 * types and asserts that what the handlers return still satisfies them.
 *
 * Two directions, two mechanisms, because neither catches the other's case:
 *
 * 1. Type-level, here. A handler whose row type stops matching the published
 *    shape fails `next build`, which typechecks these files. TypeScript is
 *    structural, so this catches renamed, removed and retyped fields.
 *
 * 2. Runtime, in api.test.ts. Structural typing permits extra properties, so a
 *    handler that starts returning an undocumented field is invisible here.
 *    The conformance tests in api.test.ts walk real responses against the spec
 *    and fail on anything returned but undocumented.
 *
 * Together: the spec cannot describe a shape the routes do not return, and the
 * routes cannot return a shape the spec does not describe.
 */

import { describe, it, expect } from "vitest";
import type { Cell, Ward, Recommendation, ApiError } from "ucip-client";
import type { WardRow } from "./wards/route";
import type { CellRow } from "./cells/route";

/**
 * Compiles only if `T` is assignable to `U`. The whole point of this file.
 *
 * `T` is unused in the body on purpose: all the work happens in the `extends`
 * constraint, which TypeScript checks at the use site.
 */
// eslint-disable-next-line @typescript-eslint/no-unused-vars
type Assignable<T extends U, U> = true;

// What GET /wards returns must be something the published `Ward` type describes.
type WardRowIsAWard = Assignable<WardRow, Ward>;

// Same for the grid cells.
type CellRowIsACell = Assignable<CellRow, Cell>;

// And the shapes the handlers build inline.
type RecommendationShape = {
  ward_id?: string;
  intervention: string;
  rationale: string;
  citation: string;
  priority: number;
  cell_count?: number | null;
};
type RecommendationMatches = Assignable<RecommendationShape, Recommendation>;

type ErrorShape = { error: { status: number; message: string; hint?: string } };
type ErrorMatches = Assignable<ErrorShape, ApiError>;

describe("the published client types describe these routes", () => {
  it("compiles, which is the assertion", () => {
    // The checks above are erased at runtime. This test exists so the file is
    // a test file rather than a lone type declaration somebody deletes as dead
    // code, and so the suite reports that the contract was checked.
    const checked: Array<true> = [
      true satisfies WardRowIsAWard,
      true satisfies CellRowIsACell,
      true satisfies RecommendationMatches,
      true satisfies ErrorMatches,
    ];
    expect(checked).toHaveLength(4);
  });

  it("names the client as the source of truth for consumers", async () => {
    // A cheap guard against the alias being removed and this file silently
    // falling back to `any`: if `ucip-client` stopped resolving, the import
    // above would fail to typecheck and the build would break, but a stale
    // alias pointing somewhere empty would not. Importing it for real catches
    // that.
    const client = await import("ucip-client");
    expect(typeof client.UcipClient).toBe("function");
    expect(client.DEFAULT_BASE_URL).toContain("/api/v1");
  });
});
