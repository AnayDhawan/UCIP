# ucip-mcp

MCP server for [UCIP](https://github.com/AnayDhawan/UCIP): Mumbai ward-level
heat vulnerability, with cited nature-based cooling recommendations.

Lets an assistant answer "which Mumbai ward should we cool first, and what
should go there" against the real dataset, with the citation attached to the
answer rather than invented after it.

## Install

The package is not on npm yet, so run it from a clone of the repository:

```bash
cd mcp-server
npm ci
npm run build
```

Then point your MCP client at the built file, using the absolute path to your clone:

```json
{
  "mcpServers": {
    "ucip": {
      "command": "node",
      "args": ["/absolute/path/to/UCIP/mcp-server/dist/index.js"]
    }
  }
}
```

No API key. Every tool reads the same public endpoints a browser would.

## Tools

| Tool | Answers |
|---|---|
| `list_wards` | Which wards to prioritise, ranked |
| `get_ward` | One ward, its factor breakdown and its cited recommendations |
| `lookup_ward` | Which ward contains a coordinate |
| `get_recommendations` | What to do, for one ward or all of them |
| `get_methodology` | How the index is built and what its limits are |

## Every response carries its caveats

This is deliberate and it is the main design decision in the server.

An assistant summarises whatever it is handed. A bare ranking comes back out as
a confident recommendation with the uncertainty sanded off, which is exactly
the failure this dataset is built to avoid. So each response includes a
`_notes` array:

- Ranks travel with the bootstrap result: every ward row carries
  `rank_ci_low` and `rank_ci_high`, the note quotes the median and widest
  interval in that response, and no ward's rank is certain. The interval covers
  sampling uncertainty in the grid cells only.
- Recommendations travel with the reason trees are absent where they are
  absent. The plantability filter refuses native grassland (Veldman 2019), and
  without that note an assistant reads a missing intervention as an oversight
  and suggests planting it.
- Proxies are named as proxies: `slum_pct` is mapped cluster boundaries, not a
  census count, and land surface temperature is not air temperature.

## Configuration

| Variable | Default |
|---|---|
| `UCIP_BASE_URL` | `https://uciplatform.vercel.app` |

Point it at a local instance if you are running one.

Apache-2.0.
