#!/usr/bin/env node
/**
 * MCP server for UCIP (issue #102).
 *
 * Lets an assistant answer "which Mumbai ward should we cool first, and what
 * should go there" against the real dataset, with the citation attached to the
 * answer rather than invented after it.
 *
 * Every tool wraps a public REST endpoint. There is no key and no privileged
 * path: an assistant reaches exactly what a person with curl reaches.
 *
 * The design decision worth stating: every response carries its caveats
 * inline. An assistant summarises whatever it is handed, and a bare ranking
 * handed to a language model comes back out as a confident recommendation with
 * the uncertainty sanded off. So `hvi` travels with the note that no ward's
 * rank is certain, and a recommendation travels with its citation. The data is
 * defensible; the tool should make it hard to quote indefensibly.
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";
import { UcipClient, UcipError, type Ward } from "./client.js";

// One source of truth for the version: ../package.json resolves from both src/ and dist/.
const { version: SERVER_VERSION } = createRequire(import.meta.url)("../package.json") as {
  version: string;
};

/**
 * What every ranked response must say. No figure is written here: the interval
 * widths come from the API's own data (`rank_ci_low`, `rank_ci_high`) and are
 * added by `rankingNotes`, so the caveat cannot drift from the bootstrap that
 * produced it.
 */
export const RANKING_CAVEAT =
  "Ranks are not precise. Each ward carries a 95% bootstrap interval " +
  "(rank_ci_low to rank_ci_high) and no ward's rank is certain. Treat the " +
  "ranking as broad bands, and do not read a gap smaller than the interval as " +
  "a real difference between two wards. The interval covers sampling " +
  "uncertainty in the grid cells only, not measurement error in the " +
  "indicators or the choice of indicators and weighting.";

/** Notes that quote the intervals actually present in `wards`, if any. */
export function rankingNotes(wards: Ward[]): string[] {
  const widths: number[] = [];
  for (const w of wards) {
    if (typeof w.rank_ci_low === "number" && typeof w.rank_ci_high === "number") {
      widths.push(w.rank_ci_high - w.rank_ci_low);
    }
  }
  widths.sort((a, b) => a - b);
  if (widths.length === 0) return [RANKING_CAVEAT];
  const mid = Math.floor(widths.length / 2);
  const median = widths.length % 2 ? widths[mid]! : (widths[mid - 1]! + widths[mid]!) / 2;
  const widest = widths[widths.length - 1]!;
  return [
    RANKING_CAVEAT,
    `In this response the median 95% rank interval is ${median} places wide ` +
      `and the widest is ${widest}.`,
  ];
}

export const INDEX_CAVEAT =
  "HVI is a 0-100 relative index within Mumbai, not an absolute or " +
  "cross-city measure. It combines five standardised indicators with " +
  "PCA-derived weights (Reid et al. 2009).";

export const TOOLS = [
  {
    name: "list_wards",
    description:
      "All 24 Mumbai BMC wards ranked by heat vulnerability, most vulnerable first. " +
      "Use this to answer which wards to prioritise.",
    inputSchema: {
      type: "object",
      properties: {
        limit: {
          type: "number",
          description: "How many wards to return, 1 to 24. Defaults to all 24.",
        },
      },
    },
  },
  {
    name: "get_ward",
    description:
      "One ward with its score, rank, per-factor contribution breakdown and its " +
      "ranked, cited recommendations. The factor breakdown is the explainability " +
      "layer: the index is a transparent linear combination, so a score decomposes " +
      "exactly into its drivers.",
    inputSchema: {
      type: "object",
      properties: {
        ward_id: {
          type: "string",
          description: "BMC ward code, e.g. 'C', 'F/N', 'R/C'. Case insensitive.",
        },
      },
      required: ["ward_id"],
    },
  },
  {
    name: "lookup_ward",
    description:
      "The ward containing a coordinate, with its top recommendation. Use this " +
      "when someone gives a location rather than a ward code.",
    inputSchema: {
      type: "object",
      properties: {
        lat: { type: "number", description: "Latitude, -90 to 90." },
        lon: { type: "number", description: "Longitude, -180 to 180." },
      },
      required: ["lat", "lon"],
    },
  },
  {
    name: "get_recommendations",
    description:
      "Nature-based cooling recommendations, for one ward or across all of them, " +
      "ordered by priority. Every recommendation carries the rule that fired it " +
      "and the paper backing it.",
    inputSchema: {
      type: "object",
      properties: {
        ward_id: { type: "string", description: "Optional. Restrict to one ward." },
        limit: { type: "number", description: "Optional. Maximum rows to return." },
      },
    },
  },
  {
    name: "get_methodology",
    description:
      "How the index is built, what the data is, when it was last refreshed, and " +
      "its stated limitations. Call this before presenting numbers as findings.",
    inputSchema: { type: "object", properties: {} },
  },
] as const;

const client = new UcipClient();

/** Wraps a payload with the caveats that must travel with it. */
function withNotes(payload: unknown, notes: string[]): string {
  return JSON.stringify({ ...(payload as object), _notes: notes }, null, 2);
}

export async function callTool(name: string, args: Record<string, unknown>): Promise<string> {
  switch (name) {
    case "list_wards": {
      const wards = await client.wards(args.limit as number | undefined);
      return withNotes({ wards }, [INDEX_CAVEAT, ...rankingNotes(wards)]);
    }

    case "get_ward": {
      const wardId = String(args.ward_id ?? "").toUpperCase();
      if (!wardId) throw new Error("ward_id is required.");
      const result = await client.ward(wardId);
      return withNotes(result, [
        INDEX_CAVEAT,
        ...rankingNotes([result.ward]),
        "Each recommendation's citation is the paper behind the rule that fired, " +
          "not a general reference. Quote it with the recommendation.",
      ]);
    }

    case "lookup_ward": {
      const lat = Number(args.lat);
      const lon = Number(args.lon);
      if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
        throw new Error("lat and lon are required and must be numbers.");
      }
      const result = await client.lookup(lat, lon);
      return withNotes(result, [
        INDEX_CAVEAT,
        ...rankingNotes([result.ward]),
        "Coverage is the 24 BMC wards of Mumbai only. A point outside them has no answer here.",
      ]);
    }

    case "get_recommendations": {
      const recommendations = await client.recommendations(
        args.ward_id ? String(args.ward_id).toUpperCase() : undefined,
        args.limit as number | undefined
      );
      return withNotes({ recommendations }, [
        "Priority is the urgency of the intervention, not a ranking between wards.",
        "Tree planting is deliberately absent where the plantability filter refused it: " +
          "planting native grassland destroys an ecosystem to bank carbon (Veldman 2019), " +
          "so those wards get non-tree cooling instead.",
      ]);
    }

    case "get_methodology": {
      const meta = await client.meta();
      return withNotes(meta, [
        INDEX_CAVEAT,
        RANKING_CAVEAT,
        "slum_pct is mapped slum-cluster boundaries, not a census count, and " +
          "hospital_dist_m is straight-line rather than travel distance. Both are proxies.",
        "Land surface temperature is satellite-derived and is not air temperature.",
      ]);
    }

    default:
      throw new Error(`Unknown tool: ${name}`);
  }
}

async function main(): Promise<void> {
  const server = new Server(
    { name: "ucip", version: SERVER_VERSION },
    { capabilities: { tools: {} } }
  );

  server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: TOOLS.map((tool) => ({ ...tool })),
  }));

  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    try {
      const text = await callTool(request.params.name, request.params.arguments ?? {});
      return { content: [{ type: "text", text }] };
    } catch (error) {
      // Returned as content with isError rather than thrown, so the assistant
      // can tell the user what went wrong and try something else instead of
      // the conversation dying on a protocol error.
      const message =
        error instanceof UcipError
          ? `UCIP API returned ${error.status}: ${error.message}`
          : error instanceof Error
            ? error.message
            : String(error);
      return { content: [{ type: "text", text: message }], isError: true };
    }
  });

  await server.connect(new StdioServerTransport());
}

// Only bind stdio when run directly, so tests can import callTool and TOOLS
// without a server attaching itself to the test runner's stdin.
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error("ucip-mcp failed to start:", error);
    process.exit(1);
  });
}
