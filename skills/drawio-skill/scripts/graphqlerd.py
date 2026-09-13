#!/usr/bin/env python3
"""Turn a GraphQL SDL schema into an entity type diagram as autolayout graph JSON.

Parses ``.graphql`` / ``.gql`` SDL (file or directory) or an introspection JSON
dump into one node per ``type`` / ``interface`` / ``input`` / ``enum`` /
``union`` / custom ``scalar``, listing each field with its type, and edges for
field references, ``implements`` and union membership.

Feeds autolayout.py:
  python3 graphqlerd.py ./schema --group -o graph.json
  python3 autolayout.py graph.json -o schema.drawio

The SDL parser is stdlib-only (no graphql-core). It understands descriptions,
comments, field arguments with defaults, list and non-null wrappers, directives
and ``extend``. Anything it does not recognise is skipped rather than guessed at,
so the worst case is a missing field, never a wrong edge.

Usage: python3 graphqlerd.py <file.graphql-or-dir-or-introspection.json>
       [-o graph.json] [--direction TB|LR] [--group] [--no-types]
"""
import argparse
import glob
import json
import os
import re
import sys

OBJECT_STYLE = (
    "rounded=1;whiteSpace=wrap;html=1;align=left;verticalAlign=top;"
    "spacingLeft=8;spacingTop=6;fillColor=#dae8fc;strokeColor=#6c8ebf;"
)
INTERFACE_STYLE = (
    "rounded=1;whiteSpace=wrap;html=1;align=left;verticalAlign=top;"
    "spacingLeft=8;spacingTop=6;fillColor=#e1d5e7;strokeColor=#9673a6;"
)
INPUT_STYLE = (
    "rounded=1;whiteSpace=wrap;html=1;align=left;verticalAlign=top;"
    "spacingLeft=8;spacingTop=6;fillColor=#d5e8d4;strokeColor=#82b366;"
)
UNION_STYLE = (
    "rounded=1;whiteSpace=wrap;html=1;align=left;verticalAlign=top;"
    "spacingLeft=8;spacingTop=6;fillColor=#ffe6cc;strokeColor=#d79b00;"
)
# Enums and custom scalars are leaves. The issue asks for them unlinked or
# dimmed; dimming keeps the field references visible while letting the object
# types carry the diagram.
LEAF_STYLE = (
    "rounded=1;whiteSpace=wrap;html=1;align=left;verticalAlign=top;"
    "spacingLeft=8;spacingTop=6;fillColor=#f5f5f5;strokeColor=#b3b3b3;"
    "fontColor=#666666;"
)

REF_EDGE = (
    "edgeStyle=orthogonalEdgeStyle;html=1;rounded=0;fontSize=10;"
    "dashed=1;endArrow=open;strokeColor=#6c8ebf;"
)
# UML realization, the conventional arrow for "implements".
IMPLEMENTS_EDGE = (
    "edgeStyle=orthogonalEdgeStyle;html=1;rounded=0;fontSize=10;"
    "dashed=1;endArrow=block;endFill=0;strokeColor=#9673a6;"
)
MEMBER_EDGE = (
    "edgeStyle=orthogonalEdgeStyle;html=1;rounded=0;fontSize=10;"
    "endArrow=open;strokeColor=#d79b00;"
)

STYLES = {
    "type": OBJECT_STYLE,
    "interface": INTERFACE_STYLE,
    "input": INPUT_STYLE,
    "union": UNION_STYLE,
    "enum": LEAF_STYLE,
    "scalar": LEAF_STYLE,
}

# The five built-in scalars never become nodes; a schema that references Int
# everywhere would otherwise bury the type graph under one hub.
BUILTIN_SCALARS = {"Int", "Float", "String", "Boolean", "ID"}

KINDS = ("type", "interface", "input", "enum", "union", "scalar")

_DEF = re.compile(
    r"^[ \t]*(?:extend[ \t]+)?(type|interface|input|enum|union|scalar)[ \t]+"
    r"([A-Za-z_][A-Za-z0-9_]*)",
    re.M,
)
_DEPRECATED = re.compile(r"@deprecated\b")


def strip_ignored(text):
    """Blank out block strings, quoted strings and comments, preserving offsets.

    Every removed character is replaced by a space (newlines kept), so byte
    offsets and therefore line numbers stay correct for the caller.
    """
    out = list(text)
    i, n = 0, len(text)

    def blank(start, end):
        for j in range(start, min(end, n)):
            if out[j] != "\n":
                out[j] = " "

    while i < n:
        ch = text[i]
        if text.startswith('"""', i):
            end = text.find('"""', i + 3)
            end = n if end == -1 else end + 3
            blank(i, end)
            i = end
        elif ch == '"':
            j = i + 1
            while j < n and text[j] != '"':
                j += 2 if text[j] == "\\" else 1
            blank(i, j + 1)
            i = j + 1
        elif ch == "#":
            end = text.find("\n", i)
            end = n if end == -1 else end
            blank(i, end)
            i = end
        else:
            i += 1
    return "".join(out)


def match_block(text, open_idx):
    """Index just past the brace block that opens at ``open_idx``."""
    depth, i = 0, open_idx
    while i < len(text):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return len(text)


def split_fields(body):
    """Split a block body into field-sized chunks on top-level newlines/commas."""
    items, depth, cur = [], 0, []
    for ch in body:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if depth == 0 and ch in "\n,":
            items.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    items.append("".join(cur))
    return items


def base_type(type_ref):
    """`[Thing!]!` -> `Thing`."""
    return type_ref.replace("[", "").replace("]", "").replace("!", "").strip()


def parse_field(chunk):
    """A field chunk -> (name, type_ref, deprecated) or None."""
    stripped = chunk.strip()
    if not stripped:
        return None
    m = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\s*", stripped)
    if not m:
        return None
    name = m.group(1)
    rest = stripped[m.end():]
    if rest.startswith("("):
        close = 0
        for idx, ch in enumerate(rest):
            if ch == "(":
                close += 1
            elif ch == ")":
                close -= 1
                if close == 0:
                    rest = rest[idx + 1:].lstrip()
                    break
        else:
            return None
    if not rest.startswith(":"):
        return None
    type_part = rest[1:].split("@")[0].strip()
    if not type_part:
        return None
    return name, type_part, bool(_DEPRECATED.search(rest))


def parse_sdl(text, file_path=""):
    """SDL -> list of definition dicts."""
    clean = strip_ignored(text)
    defs = []
    for m in _DEF.finditer(clean):
        kind, name = m.group(1), m.group(2)
        line = clean.count("\n", 0, m.start()) + 1
        entry = {
            "kind": kind,
            "name": name,
            "file": file_path,
            "line": line,
            "fields": [],
            "implements": [],
            "members": [],
        }
        tail = clean[m.end():]
        if kind == "union":
            eq = tail.find("=")
            stop = tail.find("\n\n")
            segment = tail[eq + 1: stop if stop != -1 else len(tail)] if eq != -1 else ""
            # A union body can wrap, but a following definition ends it.
            nxt = re.search(r"^[ \t]*(?:extend[ \t]+)?(?:%s)\b" % "|".join(KINDS),
                            segment, re.M)
            if nxt:
                segment = segment[: nxt.start()]
            entry["members"] = [p.strip() for p in segment.split("|") if p.strip()]
        elif kind != "scalar":
            impl_m = re.match(r"[^\{\n]*", tail)
            impl = impl_m.group(0) if impl_m else ""
            if "implements" in impl:
                after = impl.split("implements", 1)[1].split("@")[0]
                entry["implements"] = [
                    p.strip() for p in re.split(r"[&,]", after) if p.strip()
                ]
            brace = tail.find("{")
            if brace != -1:
                end = match_block(clean, m.end() + brace)
                body = clean[m.end() + brace + 1: end - 1]
                body_start = m.end() + brace + 1
                if kind == "enum":
                    for chunk in split_fields(body):
                        value = chunk.strip().split("@")[0].strip()
                        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
                            entry["fields"].append(
                                (value, "", bool(_DEPRECATED.search(chunk)))
                            )
                else:
                    offset = 0
                    for chunk in split_fields(body):
                        field = parse_field(chunk)
                        if field:
                            fline = clean.count("\n", 0, body_start + offset) + 1
                            entry["fields"].append(field + (fline,))
                        offset += len(chunk) + 1
        defs.append(entry)
    return defs


def parse_introspection(payload, file_path=""):
    """An introspection JSON dump -> the same definition dicts as parse_sdl."""
    schema = payload.get("data", payload).get("__schema")
    if not isinstance(schema, dict):
        raise ValueError("no __schema key found")
    kind_map = {
        "OBJECT": "type",
        "INTERFACE": "interface",
        "INPUT_OBJECT": "input",
        "ENUM": "enum",
        "UNION": "union",
        "SCALAR": "scalar",
    }

    def render(ref):
        if not isinstance(ref, dict):
            return ""
        kind = ref.get("kind")
        if kind == "NON_NULL":
            return render(ref.get("ofType")) + "!"
        if kind == "LIST":
            return "[" + render(ref.get("ofType")) + "]"
        return ref.get("name") or ""

    defs = []
    for t in schema.get("types") or []:
        name = t.get("name") or ""
        kind = kind_map.get(t.get("kind"))
        # An introspection dump always lists the five builtin scalars and the
        # __-prefixed meta types. Neither is part of the schema being drawn.
        if not kind or name.startswith("__") or name in BUILTIN_SCALARS:
            continue
        entry = {
            "kind": kind,
            "name": name,
            "file": file_path,
            "line": 0,
            "fields": [],
            "implements": [i.get("name") for i in (t.get("interfaces") or []) if i.get("name")],
            "members": [u.get("name") for u in (t.get("possibleTypes") or []) if u.get("name")],
        }
        for f in (t.get("fields") or []) + (t.get("inputFields") or []):
            entry["fields"].append(
                (f.get("name") or "", render(f.get("type")), bool(f.get("isDeprecated")), 0)
            )
        for v in t.get("enumValues") or []:
            entry["fields"].append((v.get("name") or "", "", bool(v.get("isDeprecated")), 0))
        defs.append(entry)
    return defs


def merge_extends(defs):
    """Fold ``extend`` definitions into their base type.

    GraphQL names are unique within a schema, so two entries sharing a name
    are a base definition and its extends, possibly across different files.
    Keeping both would emit two nodes with the same id.
    """
    merged, order = {}, []
    for d in defs:
        base = merged.get(d["name"])
        if base is None:
            merged[d["name"]] = d
            order.append(d)
        else:
            base["fields"].extend(d["fields"])
            base["implements"].extend(d["implements"])
            base["members"].extend(d["members"])
    return order


def esc(text):
    """Escape HTML metacharacters for draw.io's html=1 labels.

    Without it a field type such as `[Item!]!` renders fine but a description
    containing `<` is swallowed as an unknown HTML tag.
    """
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def compute_dimensions(lines):
    width = max(160, -(-max(7 * len(l) + 30 for l in lines) // 10) * 10)
    height = max(50, -(-(30 + 18 * len(lines)) // 10) * 10)
    return width, height


def build(defs, group=False, direction="TB", show_types=True):
    """Definition dicts -> autolayout graph JSON."""
    defs = merge_extends(defs)
    nodes, edges, seen_edges = [], [], set()
    known = {d["name"] for d in defs}

    def add_edge(src, dst, style, label=""):
        key = (src, dst, label)
        if src != dst and dst in known and key not in seen_edges:
            seen_edges.add(key)
            edges.append({"source": src, "target": dst, "style": style, "label": label})

    for d in defs:
        name = d["name"]
        lines = ["«%s»\n%s" % (d["kind"], name) if d["kind"] != "type" else name, "—"]
        if d["kind"] == "union":
            lines.extend(d["members"] or ["(no members)"])
        elif d["kind"] == "scalar":
            lines.append("(custom scalar)")
        elif d["fields"]:
            for field in d["fields"]:
                fname, ftype, deprecated = field[0], field[1], field[2]
                text = fname if not ftype or not show_types else "%s: %s" % (fname, ftype)
                lines.append(text + (" (deprecated)" if deprecated else ""))
        else:
            lines.append("(no fields)")

        width, height = compute_dimensions(lines)
        node = {
            "id": name,
            "label": esc("\n".join(lines)),
            "style": STYLES[d["kind"]],
            "width": width,
            "height": height,
            "provenance": {"path": d["file"], "line": d["line"]},
        }
        if group and d["file"]:
            node["group"] = os.path.splitext(os.path.basename(d["file"]))[0]
        nodes.append(node)

        for iface in d["implements"]:
            add_edge(name, iface, IMPLEMENTS_EDGE, "implements")
        for member in d["members"]:
            add_edge(name, member, MEMBER_EDGE)
        for field in d["fields"]:
            target = base_type(field[1])
            if target and target not in BUILTIN_SCALARS:
                add_edge(name, target, REF_EDGE, field[0])

    return {"direction": direction, "nodes": nodes, "edges": edges}


def main():
    ap = argparse.ArgumentParser(description="GraphQL SDL -> entity type diagram graph JSON.")
    ap.add_argument("path", help=".graphql/.gql file, a directory, or introspection JSON")
    ap.add_argument("-o", "--output", help="output JSON path (default: stdout)")
    ap.add_argument("--direction", default="TB", choices=["TB", "LR"])
    ap.add_argument("--group", action="store_true",
                    help="group types by the schema file they came from")
    ap.add_argument("--no-types", action="store_true",
                    help="list field names only (hide the GraphQL types)")
    args = ap.parse_args()

    if os.path.isfile(args.path):
        files = [args.path]
    elif os.path.isdir(args.path):
        files = sorted(
            p for pattern in ("*.graphql", "*.gql")
            for p in glob.glob(os.path.join(args.path, "**", pattern), recursive=True)
        )
    else:
        sys.exit("error: %s not found" % args.path)

    if not files:
        sys.exit("error: no .graphql or .gql files found under %s" % args.path)

    defs = []
    for path in files:
        # pi-lens-ignore: ast-grep:unchecked-throwing-call-python
        with open(path, encoding="utf-8", errors="replace") as fh:
            raw = fh.read()
        if path.endswith(".json"):
            try:
                defs.extend(parse_introspection(json.loads(raw), file_path=path))
            except (ValueError, AttributeError) as exc:
                sys.exit("error: %s is not an introspection dump (%s)" % (path, exc))
        else:
            defs.extend(parse_sdl(raw, file_path=path))

    if not defs:
        sys.exit("error: no GraphQL type definitions found under %s" % args.path)

    graph = build(defs, group=args.group, direction=args.direction,
                  show_types=not args.no_types)
    text = json.dumps(graph, indent=2, ensure_ascii=False)
    if args.output:
        # pi-lens-ignore: ast-grep:unchecked-throwing-call-python
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(text)
        sys.stderr.write("wrote %s\n" % args.output)
    else:
        sys.stdout.write(text)

    counts = {}
    for d in merge_extends(defs):
        counts[d["kind"]] = counts.get(d["kind"], 0) + 1
    summary = ", ".join("%d %ss" % (counts[k], k) for k in KINDS if k in counts)
    sys.stderr.write("%s, %d edges\n" % (summary, len(graph["edges"])))


if __name__ == "__main__":
    main()
