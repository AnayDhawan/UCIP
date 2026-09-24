/**
 * Generates `src/types.gen.ts` from the OpenAPI spec (issue #103).
 *
 * The spec is imported directly from the frontend source rather than fetched
 * from a deployment. That matters: a generator pointed at a URL produces types
 * for whatever is deployed, which is not necessarily what is in the tree, and
 * the drift only shows up after a release. Importing the module means the
 * generated types are a pure function of the committed spec, so `npm run
 * generate && git diff --exit-code` is a meaningful CI check. That check is in
 * the frontend CI workflow and is what makes the "cannot silently rot"
 * acceptance criterion true rather than aspirational.
 *
 * This is deliberately a small generator for one small spec, not a general
 * OpenAPI tool. It handles what `openapiSpec.ts` actually uses: $ref, nullable
 * type arrays, objects, arrays, enums, additionalProperties and oneOf. It
 * throws on anything else rather than silently emitting `unknown`, because a
 * silent `unknown` is how a generated client stops describing the API.
 */

import { writeFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { buildSpec } from "../../../frontend/src/lib/openapiSpec";

type Schema = Record<string, any>;

const here = dirname(fileURLToPath(import.meta.url));

/** OpenAPI JSON types to TypeScript, for the subset the spec uses. */
const PRIMITIVES: Record<string, string> = {
  string: "string",
  number: "number",
  integer: "number",
  boolean: "boolean",
  null: "null",
};

/**
 * Component names that cannot be used verbatim in TypeScript.
 *
 * `Error` is the conventional OpenAPI name for an error envelope and a
 * terrible exported type name: the package re-exports its types, so consumers
 * would get a `ucip-client` export that shadows the global `Error`. Renamed at
 * the boundary rather than in the spec, where `Error` is the right name.
 */
const TYPE_NAMES: Record<string, string> = { Error: "ApiError" };

const typeName = (schemaName: string) => TYPE_NAMES[schemaName] ?? schemaName;

function refName(ref: string): string {
  const name = ref.replace("#/components/schemas/", "");
  if (name.includes("/")) throw new Error(`unsupported $ref: ${ref}`);
  return typeName(name);
}

/** A doc comment, or nothing. Indented to match where it is emitted. */
function docComment(schema: Schema, indent: string): string {
  const text = schema.description;
  if (typeof text !== "string" || !text.trim()) return "";
  const lines = text.trim().split("\n").flatMap((line: string) => wrap(line, 74 - indent.length));
  if (lines.length === 1) return `${indent}/** ${lines[0]} */\n`;
  return `${indent}/**\n${lines.map((l) => `${indent} * ${l}`.trimEnd()).join("\n")}\n${indent} */\n`;
}

function wrap(text: string, width: number): string[] {
  const words = text.split(/\s+/).filter(Boolean);
  if (!words.length) return [""];
  const out: string[] = [];
  let line = "";
  for (const word of words) {
    if (line && line.length + 1 + word.length > width) {
      out.push(line);
      line = word;
    } else {
      line = line ? `${line} ${word}` : word;
    }
  }
  if (line) out.push(line);
  return out;
}

function typeOf(schema: Schema, indent: string): string {
  if (!schema || typeof schema !== "object") throw new Error("empty schema");
  if (schema.$ref) return refName(schema.$ref);

  if (Array.isArray(schema.oneOf)) {
    return schema.oneOf.map((s: Schema) => typeOf(s, indent)).join(" | ");
  }

  const types: string[] = Array.isArray(schema.type)
    ? schema.type
    : schema.type
      ? [schema.type]
      : [];

  if (!types.length) {
    // `items: {}` in the spec means "any JSON value", used for coordinate
    // arrays. Anything else with no type is a spec bug worth failing on.
    if (Object.keys(schema).length === 0) return "unknown";
    throw new Error(`schema has no type: ${JSON.stringify(schema).slice(0, 120)}`);
  }

  const parts = types.map((t) => {
    if (t === "array") {
      if (!schema.items) throw new Error("array schema has no items");
      const inner = typeOf(schema.items, indent);
      return inner.includes("|") || inner.includes("{") ? `Array<${inner}>` : `${inner}[]`;
    }
    if (t === "object") {
      if (schema.properties) return objectType(schema, indent);
      if (schema.additionalProperties) {
        return `Record<string, ${typeOf(schema.additionalProperties, indent)}>`;
      }
      return "Record<string, unknown>";
    }
    if (t === "string" && Array.isArray(schema.enum)) {
      return schema.enum.map((v: string) => JSON.stringify(v)).join(" | ");
    }
    const mapped = PRIMITIVES[t];
    if (!mapped) throw new Error(`unsupported type: ${t}`);
    return mapped;
  });

  return [...new Set(parts)].join(" | ");
}

function objectType(schema: Schema, indent: string): string {
  const inner = `${indent}  `;
  const required: string[] = schema.required ?? [];
  const fields = Object.entries<Schema>(schema.properties).map(([name, prop]) => {
    const optional = required.includes(name) ? "" : "?";
    const key = /^[A-Za-z_$][\w$]*$/.test(name) ? name : JSON.stringify(name);
    return `${docComment(prop, inner)}${inner}${key}${optional}: ${typeOf(prop, inner)};`;
  });
  return `{\n${fields.join("\n")}\n${indent}}`;
}

function generate(): string {
  // The origin is irrelevant to the types; only `servers` uses it.
  const spec = buildSpec("https://uciplatform.vercel.app") as unknown as Schema;
  const schemas = spec.components.schemas as Record<string, Schema>;

  const out: string[] = [
    "/**",
    " * Response types for the UCIP API.",
    " *",
    " * GENERATED FILE. Do not edit.",
    " *",
    " * Produced by scripts/generate.ts from the OpenAPI spec in",
    " * frontend/src/lib/openapiSpec.ts. Regenerate with `npm run generate`.",
    " * CI regenerates and diffs, so an API change that is not reflected here",
    " * fails the build rather than shipping a client that describes the wrong",
    " * shapes.",
    " */",
    "",
  ];

  for (const [name, schema] of Object.entries(schemas)) {
    out.push(docComment(schema, ""));
    out.push(`export type ${typeName(name)} = ${typeOf(schema, "")};`);
    out.push("");
  }

  // The operation parameter shapes, so the client's arguments are generated
  // from the spec too rather than hand-copied from it.
  for (const [path, item] of Object.entries<Schema>(spec.paths)) {
    const op = item.get;
    const params: Schema[] = (op.parameters ?? []).filter((p: Schema) => p.in === "query");
    if (!params.length) continue;
    const name = `${op.operationId[0].toUpperCase()}${op.operationId.slice(1)}Params`;
    const fields = params.map((p) => {
      const doc = docComment(p.description ? { description: p.description } : {}, "  ");
      return `${doc}  ${p.name}?: ${typeOf(p.schema, "  ")};`;
    });
    out.push(`/** Query parameters for \`GET ${path}\`. */`);
    out.push(`export type ${name} = {\n${fields.join("\n")}\n};`);
    out.push("");
  }

  return out.join("\n").replace(/\n{3,}/g, "\n\n");
}

const target = join(here, "..", "src", "types.gen.ts");
writeFileSync(target, generate(), "utf8");
console.log(`wrote ${target}`);
