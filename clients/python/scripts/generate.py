"""Generate `src/ucip/models.py` from the OpenAPI spec (issue #104).

Reads `clients/openapi.json`, the artifact the TypeScript generator emits from
`frontend/src/lib/openapiSpec.ts`. Both clients are generated from that one
file, so neither can describe a shape the other does not, and CI regenerates
and diffs all three outputs together.

TypedDicts rather than dataclasses. The client hands back what the API sent,
and a dataclass would mean constructing objects on every response, discarding
any field the schema did not anticipate, and forcing a conversion step before
the data reaches pandas. A TypedDict is a plain dict at runtime: it costs
nothing, keeps unexpected fields, and still gives editors and type checkers the
field names and types.

`total=False` on every TypedDict, because the API omits rather than nulls
optional fields, and a required-by-default TypedDict would make every correct
response a type error.
"""

from __future__ import annotations

import json
import keyword
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = HERE.parent.parent / "openapi.json"
TARGET = HERE.parent / "src" / "ucip" / "models.py"

# JSON schema types to Python annotations.
PRIMITIVES = {
    "string": "str",
    "number": "float",
    "integer": "int",
    "boolean": "bool",
    "null": "None",
}

# `Error` is a builtin-adjacent name and a poor export; the TypeScript client
# renames it the same way, so the two stay recognisably the same API.
TYPE_NAMES = {"Error": "ApiError"}


def type_name(schema_name: str) -> str:
    return TYPE_NAMES.get(schema_name, schema_name)


def wrap(text: str, width: int, indent: str) -> list[str]:
    words = text.split()
    lines: list[str] = []
    line = ""
    for word in words:
        if line and len(line) + 1 + len(word) > width:
            lines.append(indent + line)
            line = word
        else:
            line = f"{line} {word}" if line else word
    if line:
        lines.append(indent + line)
    return lines


def annotation(schema: dict, nested: list[str], prefix: str) -> str:
    """The Python annotation for a schema, appending any nested TypedDicts."""
    if "$ref" in schema:
        return type_name(schema["$ref"].rsplit("/", 1)[-1])

    if "oneOf" in schema:
        parts = [annotation(s, nested, prefix) for s in schema["oneOf"]]
        return " | ".join(dict.fromkeys(parts))

    raw = schema.get("type")
    types = raw if isinstance(raw, list) else [raw] if raw else []

    if not types:
        # `items: {}` means "any JSON value". Anything else untyped is a spec
        # bug worth failing on rather than silently emitting Any.
        if not schema:
            return "Any"
        raise ValueError(f"schema has no type: {json.dumps(schema)[:120]}")

    parts: list[str] = []
    for kind in types:
        if kind == "array":
            items = schema.get("items")
            if items is None:
                raise ValueError("array schema has no items")
            parts.append(f"list[{annotation(items, nested, prefix)}]")
        elif kind == "object":
            if "properties" in schema:
                # An inline object becomes its own TypedDict, named for where
                # it appeared, because a nested dict annotation is unreadable.
                name = prefix
                nested.append(typed_dict(name, schema, nested, name))
                parts.append(name)
            elif "additionalProperties" in schema:
                parts.append(
                    f"dict[str, {annotation(schema['additionalProperties'], nested, prefix)}]"
                )
            else:
                parts.append("dict[str, Any]")
        elif kind == "string" and "enum" in schema:
            literals = ", ".join(json.dumps(v) for v in schema["enum"])
            parts.append(f"Literal[{literals}]")
        else:
            mapped = PRIMITIVES.get(kind)
            if mapped is None:
                raise ValueError(f"unsupported type: {kind}")
            parts.append(mapped)

    return " | ".join(dict.fromkeys(parts))


def field_name(name: str) -> str:
    """A safe Python identifier, or None when the key needs the functional form."""
    if keyword.iskeyword(name) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        return ""
    return name


def typed_dict(name: str, schema: dict, nested: list[str], prefix: str) -> str:
    lines = [f"class {name}(TypedDict, total=False):"]

    doc = schema.get("description")
    if doc:
        body = wrap(doc, 72, "    ")
        if len(body) == 1:
            lines.append(f'    """{body[0].strip()}"""')
        else:
            lines.append('    """')
            lines.extend(body)
            lines.append('    """')
        lines.append("")

    props: dict = schema.get("properties", {})
    if not props:
        lines.append("    pass")
        return "\n".join(lines)

    for key, prop in props.items():
        safe = field_name(key)
        if not safe:
            # No key in this spec needs it, but emitting a broken identifier
            # silently would be worse than failing here.
            raise ValueError(f"field name is not a Python identifier: {key}")
        child_prefix = f"{prefix}{''.join(p.title() for p in key.split('_'))}"
        lines.append(f"    {safe}: {annotation(prop, nested, child_prefix)}")
        description = prop.get("description")
        if description:
            lines.append('    """')
            lines.extend(wrap(description, 72, "    "))
            lines.append('    """')

    return "\n".join(lines)


def generate() -> str:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    schemas: dict = spec["components"]["schemas"]

    out = [
        '"""Response types for the UCIP API.',
        "",
        "GENERATED FILE. Do not edit.",
        "",
        "Produced by scripts/generate.py from clients/openapi.json, which the",
        "TypeScript generator emits from frontend/src/lib/openapiSpec.ts.",
        "Regenerate with `python scripts/generate.py`. CI regenerates and diffs,",
        "so an API change that is not reflected here fails the build rather than",
        "shipping a client that describes the wrong shapes.",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "from typing import Any, Literal, TypedDict",
        "",
        "",
    ]

    blocks: list[str] = []
    for schema_name, schema in schemas.items():
        nested: list[str] = []
        name = type_name(schema_name)
        block = typed_dict(name, schema, nested, name)
        # Nested definitions first: Python resolves names at class-creation
        # time, and `from __future__ import annotations` only defers the
        # annotations, not the TypedDict field collection.
        blocks.extend(nested)
        blocks.append(block)

    out.append("\n\n\n".join(blocks))
    out.append("")

    names = [type_name(n) for n in schemas]
    out.append("")
    out.append("__all__ = [")
    for n in sorted(names):
        out.append(f'    "{n}",')
    out.append("]")
    out.append("")

    return "\n".join(out)


if __name__ == "__main__":
    TARGET.write_text(generate(), encoding="utf-8")
    print(f"wrote {TARGET}")
