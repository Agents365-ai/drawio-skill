#!/usr/bin/env python3
"""Turn an OpenAPI / Swagger spec into an API diagram as autolayout graph JSON.

Reads an OpenAPI 3 or Swagger 2 spec (JSON, or YAML with PyYAML) and emits one
node per operation — coloured by HTTP method — plus one node per component
schema, with edges from each operation to the schemas it references (request /
response bodies) and between schemas that nest one another. Feeds autolayout.py:

  python3 openapiimports.py openapi.yaml -o graph.json
  python3 autolayout.py graph.json -o api.drawio

Operations are grouped by their first `tag` (falling back to the first path
segment) with `--group`; `--no-schemas` drops the data-model nodes to show just
the endpoint surface. `$ref`s are resolved to their final name; only schemas
defined under components/definitions become nodes, so external refs are ignored.

Usage: python3 openapiimports.py <spec.json|spec.yaml> [-o graph.json]
       [--direction TB|LR] [--group] [--no-schemas]
"""
import argparse
import json
import os
import sys

METHODS = ("get", "post", "put", "patch", "delete", "head", "options", "trace")
# HTTP method -> (fill, stroke). GET reads, POST creates, PUT/PATCH update, DELETE removes.
METHOD_STYLE = {
    "get": ("#dae8fc", "#6c8ebf"), "post": ("#d5e8d4", "#82b366"),
    "put": ("#ffe6cc", "#d79b00"), "patch": ("#ffe6cc", "#d79b00"),
    "delete": ("#f8cecc", "#b85450"),
}
OTHER_STYLE = ("#f5f5f5", "#666666")
SCHEMA_STYLE = "rounded=1;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;"
OP_EDGE = "edgeStyle=orthogonalEdgeStyle;html=1;rounded=0;fontSize=10;endArrow=open;"
REF_EDGE = ("edgeStyle=orthogonalEdgeStyle;html=1;rounded=0;fontSize=10;"
            "dashed=1;endArrow=open;strokeColor=#9673a6;")


def load_spec(path):
    """Parse the spec: JSON directly, YAML (or ambiguous) via PyYAML if present."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    if path.lower().endswith((".yaml", ".yml")):
        try:
            import yaml
        except ImportError:
            sys.exit("error: spec is YAML but PyYAML is not installed "
                     "(pip install pyyaml) — or convert the spec to JSON")
        return yaml.safe_load(text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            import yaml
        except ImportError:
            sys.exit("error: could not parse spec as JSON (install PyYAML to read YAML)")
        return yaml.safe_load(text)


def find_refs(obj):
    """Yield the final name of every $ref anywhere inside a spec fragment."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "$ref" and isinstance(v, str):
                yield v.split("/")[-1]
            else:
                yield from find_refs(v)
    elif isinstance(obj, list):
        for item in obj:
            yield from find_refs(item)


def method_style(method):
    fill, stroke = METHOD_STYLE.get(method, OTHER_STYLE)
    return ("rounded=1;whiteSpace=wrap;html=1;align=left;spacingLeft=6;"
            f"fillColor={fill};strokeColor={stroke};")


def build(spec, group, no_schemas, direction):
    """Spec dict -> autolayout graph JSON dict."""
    paths = spec.get("paths") or {}
    # components.schemas (OpenAPI 3) or definitions (Swagger 2)
    schemas = (spec.get("components") or {}).get("schemas") or spec.get("definitions") or {}
    want_schemas = bool(schemas) and not no_schemas
    sid = {name: f"S:{name}" for name in schemas}

    nodes, edges, seen = [], [], set()

    def add_edge(src, dst, style):
        if src != dst and (src, dst) not in seen:
            seen.add((src, dst))
            edges.append({"source": src, "target": dst, "style": style, "label": ""})

    i = 0
    for path, item in paths.items():
        if not isinstance(item, dict):
            continue
        for method in METHODS:
            op = item.get(method)
            if not isinstance(op, dict):
                continue
            oid = f"op{i}"
            i += 1
            summary = (op.get("summary") or op.get("operationId") or "").strip()
            head = f"{method.upper()} {path}"
            nodes.append({
                "id": oid, "label": head + (f"\n{summary}" if summary else ""),
                "style": method_style(method),
                "width": max(160, 8 * len(head) + 20), "height": 40,
                **({"group": (op.get("tags") or [path.strip('/').split('/')[0] or "root"])[0]}
                   if group else {}),
            })
            if want_schemas:
                for ref in set(find_refs(op)):
                    if ref in sid:
                        add_edge(oid, sid[ref], OP_EDGE)

    if want_schemas:
        for name, schema in schemas.items():
            fields = schema.get("properties") if isinstance(schema, dict) else None
            count = len(fields) if fields else 0
            nodes.append({
                "id": sid[name],
                "label": name + (f"\n({count} field{'s' if count != 1 else ''})" if count else ""),
                "style": SCHEMA_STYLE, "width": max(140, 9 * len(name) + 20), "height": 40,
                **({"group": "schemas"} if group else {}),
            })
            for ref in set(find_refs(schema)):
                if ref in sid:
                    add_edge(sid[name], sid[ref], REF_EDGE)

    return {"direction": direction, "nodes": nodes, "edges": edges}


def main():
    ap = argparse.ArgumentParser(description="OpenAPI/Swagger spec -> API diagram graph JSON.")
    ap.add_argument("spec", help="OpenAPI 3 / Swagger 2 spec (.json or .yaml)")
    ap.add_argument("-o", "--output", help="output JSON path (default: stdout)")
    ap.add_argument("--direction", default="LR", choices=["TB", "LR"])
    ap.add_argument("--group", action="store_true", help="group operations by tag")
    ap.add_argument("--no-schemas", action="store_true",
                    help="show only endpoints, omit schema nodes and edges")
    args = ap.parse_args()

    if not os.path.isfile(args.spec):
        sys.exit(f"error: {args.spec} not found")
    spec = load_spec(args.spec) or {}
    if not (spec.get("paths")):
        sys.exit("error: no paths found (is this an OpenAPI/Swagger spec?)")

    graph = build(spec, args.group, args.no_schemas, args.direction)
    text = json.dumps(graph, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        sys.stderr.write(f"wrote {args.output}\n")
    else:
        sys.stdout.write(text)
    ops = sum(1 for n in graph["nodes"] if n["id"].startswith("op"))
    sys.stderr.write(f"{ops} operations, {len(graph['nodes']) - ops} schemas, "
                     f"{len(graph['edges'])} edges\n")


if __name__ == "__main__":
    main()
