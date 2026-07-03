#!/usr/bin/env python3
"""C4 model diagrams: levels JSON -> one multi-page .drawio with drill-down.

Generates a C4 architecture diagram set (System Context -> Containers ->
Components, as many levels as you define) in a single `.drawio` file: one
page per level, official draw.io C4 shapes and colors, Graphviz placement
per page (via autolayout), and **drill-down links** — an element with a
`"children"` key becomes clickable and jumps to that level's page in
draw.io / the diagrams.net viewer.

  python3 c4.py c4.json -o architecture.drawio

Input JSON:
  {
    "title": "Internet Banking",
    "levels": [
      {
        "name": "System Context",
        "elements": [
          {"id": "customer", "type": "person", "label": "Personal Customer",
           "desc": "A customer of the bank"},
          {"id": "ibs", "type": "system", "label": "Internet Banking System",
           "desc": "Lets customers manage accounts", "children": "Containers"},
          {"id": "email", "type": "external", "label": "E-mail System",
           "desc": "Microsoft Exchange"}
        ],
        "relations": [
          {"from": "customer", "to": "ibs", "label": "Uses"},
          {"from": "ibs", "to": "email", "label": "Sends e-mail via"}
        ]
      },
      {
        "name": "Containers",
        "elements": [
          {"id": "spa", "type": "container", "label": "Single-Page App",
           "tech": "React", "desc": "Banking UI in the browser"},
          {"id": "api", "type": "container", "label": "API Application",
           "tech": "Java/Spring", "children": "Components"},
          {"id": "db", "type": "database", "label": "Database",
           "tech": "PostgreSQL"}
        ],
        "relations": [
          {"from": "spa", "to": "api", "label": "JSON/HTTPS"},
          {"from": "api", "to": "db", "label": "JDBC"}
        ]
      }
    ]
  }

Element types: person, system, external (greyed external system), container,
component, database. `tech` renders as the [Type: Tech] line, `desc` as the
description line — the standard C4 label. Element ids must be unique across
ALL levels (pages share one link namespace). Requires Graphviz `dot`.

Usage: python3 c4.py <c4.json> [-o out.drawio] [--direction TB|LR]
"""
import argparse
import importlib.util
import json
import os
import re
import sys

# Official draw.io C4 template styles (colors from c4model.com).
_BASE = "html=1;whiteSpace=wrap;fontSize=12;fontColor=#ffffff;align=center;"
STYLES = {
    "person": ("shape=mxgraph.c4.person2;" + _BASE +
               "fillColor=#083F75;strokeColor=#06315C;", 200, 180),
    "system": ("rounded=1;arcSize=10;" + _BASE +
               "fillColor=#1061B0;strokeColor=#0D5091;", 240, 120),
    "external": ("rounded=1;arcSize=10;" + _BASE +
                 "fillColor=#8C8496;strokeColor=#736782;", 240, 120),
    "container": ("rounded=1;arcSize=10;" + _BASE +
                  "fillColor=#23A2D9;strokeColor=#0E7DAD;", 240, 120),
    "component": ("rounded=1;arcSize=10;" + _BASE +
                  "fillColor=#63BEF2;strokeColor=#2086C9;", 240, 120),
    "database": ("shape=cylinder3;size=15;boundedLbl=1;" + _BASE +
                 "fillColor=#23A2D9;strokeColor=#0E7DAD;", 240, 120),
}
TYPE_WORD = {"person": "Person", "system": "Software System",
             "external": "Software System", "container": "Container",
             "component": "Component", "database": "Container"}
EDGE = ("endArrow=blockThin;endFill=1;endSize=10;html=1;fontSize=11;"
        "fontColor=#404040;strokeColor=#828282;labelBackgroundColor=#ffffff;"
        "rounded=0;")


def load_autolayout():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "autolayout.py")
    spec = importlib.util.spec_from_file_location("autolayout", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", str(name).lower()).strip("-") or "page"


def c4_label(el):
    """Standard C4 element label: Name / [Type: Tech] / description."""
    kind = TYPE_WORD.get(el.get("type", "system"), "Software System")
    bracket = f"[{kind}: {el['tech']}]" if el.get("tech") else f"[{kind}]"
    lines = [el.get("label", el["id"]), bracket]
    if el.get("desc"):
        lines.append(el["desc"])
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="C4 levels JSON -> multi-page draw.io.")
    ap.add_argument("input", help="C4 JSON file")
    ap.add_argument("-o", "--output", help="output .drawio path (default: stdout)")
    ap.add_argument("--direction", default="TB", choices=["TB", "LR"])
    args = ap.parse_args()
    with open(args.input, encoding="utf-8") as f:
        spec = json.load(f)
    levels = spec.get("levels") or []
    if not levels:
        sys.exit("error: no levels in input")
    al = load_autolayout()

    page_ids = {lv["name"]: slug(lv["name"]) for lv in levels}
    seen = set()
    pages = []
    for lv in levels:
        nodes = []
        for el in lv.get("elements", []):
            if el["id"] in seen:
                sys.exit(f"error: duplicate element id {el['id']!r} "
                         "(ids must be unique across all levels)")
            seen.add(el["id"])
            style, w, h = STYLES.get(el.get("type", "system"), STYLES["system"])
            node = {"id": el["id"], "label": c4_label(el), "style": style,
                    "width": w, "height": h}
            child = el.get("children")
            if child:
                if child not in page_ids:
                    sys.exit(f"error: element {el['id']!r} drills down to "
                             f"unknown level {child!r}")
                node["link"] = f"data:page/id,{page_ids[child]}"
            nodes.append(node)
        edges = [{"source": r["from"], "target": r["to"],
                  "label": r.get("label", ""), "style": EDGE}
                 for r in lv.get("relations", [])]
        graph = {"direction": args.direction, "nodes": nodes, "edges": edges,
                 "ranksep": 0.9, "nodesep": 0.5}
        height, pos, edge_pts = al.layout(al.build_dot(graph))
        pages.append(al.wrap_page(al.page_cells(graph, height, pos, edge_pts, color=False),
                                  page_id=page_ids[lv["name"]], name=lv["name"]))

    xml = "<mxfile>\n" + "".join(pages) + "</mxfile>\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(xml)
        print(f"wrote {args.output} ({len(pages)} pages, {len(seen)} elements)",
              file=sys.stderr)
    else:
        sys.stdout.write(xml)


if __name__ == "__main__":
    main()
