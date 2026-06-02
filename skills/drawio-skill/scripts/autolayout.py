#!/usr/bin/env python3
"""Auto-layout a logical graph into draw.io XML using Graphviz.

Minimal layout pass for the drawio skill: takes a graph (nodes + edges as
JSON), runs `dot` to position the nodes, and emits a .drawio file with the
mxGeometry x/y filled in. draw.io routes the edges itself (orthogonal style).
This removes the manual-coordinate ceiling for medium/large diagrams.

Input JSON:
  {
    "direction": "TB",          # TB (top-bottom, default) or LR (left-right)
    "nodes": [
      {"id": "a", "label": "Service A", "style": "rounded=1;...",
       "width": 120, "height": 60}
    ],
    "edges": [
      {"source": "a", "target": "b", "label": "calls"}
    ]
  }
Only "id" is required per node; label defaults to id and style/width/height
have defaults. Node ids must be unique and must not be "0" or "1" (reserved
for the draw.io root cells). Requires Graphviz `dot` on PATH.

Usage: python3 autolayout.py graph.json [-o diagram.drawio]
"""
import argparse
import json
import shlex
import subprocess
import sys
from xml.sax.saxutils import escape

DEFAULT_W, DEFAULT_H = 120, 60
NODE_STYLE = "rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;"
EDGE_STYLE = "html=1;rounded=0;"
GROUP_STYLE = ("rounded=0;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#999999;"
               "verticalAlign=top;fontStyle=2;dashed=1;")
GROUP_PAD, GROUP_TOP = 16, 24                            # padding, and title strip on top


def attr(value):
    return escape(str(value), {'"': "&quot;"})


def snap(value, grid=10):
    # Align to the grid the skill uses everywhere (multiples of 10).
    return int(round(value / grid) * grid)


def build_dot(graph):
    rankdir = "LR" if str(graph.get("direction", "TB")).upper() == "LR" else "TB"
    # splines=ortho makes dot route edges as orthogonal polylines; we replay
    # those bends as draw.io waypoints so edges go around nodes, not through them.
    lines = [f"digraph G {{ rankdir={rankdir}; splines=ortho; node [shape=box fixedsize=true];"]
    # Group nodes into clusters so dot keeps each group together; a node's first
    # appearance fixes its cluster, so list members before the size attributes.
    members = {}
    for node in graph["nodes"]:
        g = node.get("group")
        if g is not None:
            members.setdefault(str(g), []).append(node["id"])
    for i, ms in enumerate(members.values()):
        # margin matches GROUP_PAD so dot separates clusters enough that the
        # padded container boxes we draw below do not overlap each other.
        lines.append(f"subgraph cluster_{i} {{ margin={GROUP_PAD};")
        lines += [f'"{m}";' for m in ms]
        lines.append("}")
    for node in graph["nodes"]:
        # Pass our pixel sizes to dot as inches so it lays out at the real size.
        w = node.get("width", DEFAULT_W) / 72.0
        h = node.get("height", DEFAULT_H) / 72.0
        lines.append(f'"{node["id"]}" [width={w:.4f} height={h:.4f}];')
    for edge in graph.get("edges", []):
        lines.append(f'"{edge["source"]}" -> "{edge["target"]}";')
    lines.append("}")
    return "\n".join(lines)


def layout(dot_src):
    """Run `dot -Tplain`; return (height_in, {id: (xc, yc)}, {(src, dst): [(x, y), ...]}).

    Node coords are inches (bottom-left origin); each edge's value is the list
    of orthogonal control points dot computed for routing, endpoints included.
    """
    try:
        proc = subprocess.run(
            ["dot", "-Tplain"], input=dot_src,
            capture_output=True, text=True, check=True,
        )
    except FileNotFoundError:
        sys.exit("error: Graphviz `dot` not found on PATH (brew install graphviz)")
    except subprocess.CalledProcessError as exc:
        sys.exit(f"error: dot failed: {exc.stderr.strip()}")
    height, pos, edges = 0.0, {}, {}
    for line in proc.stdout.splitlines():
        tok = shlex.split(line)
        if not tok:
            continue
        if tok[0] == "graph":
            height = float(tok[3])                        # graph scale width height
        elif tok[0] == "node":
            pos[tok[1]] = (float(tok[2]), float(tok[3]))  # node name x y ...
        elif tok[0] == "edge":                            # edge tail head n x1 y1 ... xn yn
            n = int(tok[3])
            edges[(tok[1], tok[2])] = [
                (float(tok[4 + 2 * i]), float(tok[5 + 2 * i])) for i in range(n)
            ]
    return height, pos, edges


def to_drawio(graph, height, pos, edge_pts):
    nodes = graph["nodes"]
    # Absolute snapped rect for every placed node.
    rects = {}
    for node in nodes:
        nid = node["id"]
        if nid not in pos:
            continue
        w, h = node.get("width", DEFAULT_W), node.get("height", DEFAULT_H)
        xc, yc = pos[nid]
        x = snap(xc * 72 - w / 2)
        y = snap((height - yc) * 72 - h / 2)             # flip: dot origin is bottom-left
        rects[nid] = (x, y, w, h)
    # Group membership -> container id + bounding box (members + padding + title strip).
    members, glabel = {}, {}
    for node in nodes:
        g = node.get("group")
        if g is None or node["id"] not in rects:
            continue
        members.setdefault(str(g), []).append(node["id"])
        glabel.setdefault(str(g), str(node.get("groupLabel", g)))
    used = {n["id"] for n in nodes}
    gid, gbox = {}, {}
    for i, (g, ms) in enumerate(members.items()):
        cid = f"group_{i}"
        while cid in used:                               # never collide with a node id
            cid += "_"
        used.add(cid)
        gid[g] = cid
        x0 = min(rects[m][0] for m in ms) - GROUP_PAD
        y0 = min(rects[m][1] for m in ms) - GROUP_PAD - GROUP_TOP
        x1 = max(rects[m][0] + rects[m][2] for m in ms) + GROUP_PAD
        y1 = max(rects[m][1] + rects[m][3] for m in ms) + GROUP_PAD
        gbox[g] = (x0, y0, x1 - x0, y1 - y0)

    # Shift everything positive: a container's title strip can push its top edge
    # above the page origin. Only translates when something would be negative.
    absx = [r[0] for r in rects.values()] + [b[0] for b in gbox.values()]
    absy = [r[1] for r in rects.values()] + [b[1] for b in gbox.values()]
    dx = GROUP_PAD - min(absx) if absx and min(absx) < 0 else 0
    dy = GROUP_PAD - min(absy) if absy and min(absy) < 0 else 0

    cells = []
    # Containers first so they render behind their children.
    for g, (gx, gy, gw, gh) in gbox.items():
        cells.append(
            f'        <mxCell id="{attr(gid[g])}" value="{attr(glabel[g])}" '
            f'style="{GROUP_STYLE}" vertex="1" parent="1">\n'
            f'          <mxGeometry x="{gx + dx}" y="{gy + dy}" width="{gw}" height="{gh}" as="geometry"/>\n'
            f"        </mxCell>"
        )
    node_group = {n["id"]: str(n["group"]) for n in nodes
                  if n.get("group") is not None and n["id"] in rects}
    for node in nodes:
        nid = node["id"]
        if nid not in rects:
            continue
        x, y, w, h = rects[nid]
        parent = "1"
        if nid in node_group:                            # rebase into its container
            g = node_group[nid]
            gx, gy = gbox[g][0], gbox[g][1]
            parent, x, y = gid[g], x - gx, y - gy        # relative; shift cancels
        else:
            x, y = x + dx, y + dy
        style = node.get("style", NODE_STYLE)
        cells.append(
            f'        <mxCell id="{attr(nid)}" value="{attr(node.get("label", nid))}" '
            f'style="{style}" vertex="1" parent="{attr(parent)}">\n'
            f'          <mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/>\n'
            f"        </mxCell>"
        )
    for i, edge in enumerate(graph.get("edges", [])):
        # Drop the first/last points (they sit on the node borders, where
        # draw.io attaches anyway) and replay the interior bends as waypoints.
        interior = edge_pts.get((edge["source"], edge["target"]), [])[1:-1]
        if interior:
            points = "".join(
                f'<mxPoint x="{snap(x * 72) + dx}" y="{snap((height - y) * 72) + dy}"/>'
                for x, y in interior
            )
            geom = (f'<mxGeometry relative="1" as="geometry">'
                    f'<Array as="points">{points}</Array></mxGeometry>')
        else:
            geom = '<mxGeometry relative="1" as="geometry"/>'
        cells.append(
            f'        <mxCell id="e{i}" value="{attr(edge.get("label", ""))}" '
            f'style="{EDGE_STYLE}" edge="1" parent="1" '
            f'source="{attr(edge["source"])}" target="{attr(edge["target"])}">\n'
            f"          {geom}\n"
            f"        </mxCell>"
        )
    return (
        '<mxfile>\n  <diagram id="autolayout" name="Page-1">\n'
        '    <mxGraphModel dx="800" dy="600" grid="1" gridSize="10" guides="1" '
        'tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" '
        'pageWidth="850" pageHeight="1100" math="0" shadow="0">\n'
        "      <root>\n"
        '        <mxCell id="0"/>\n'
        '        <mxCell id="1" parent="0"/>\n'
        + "\n".join(cells)
        + "\n      </root>\n    </mxGraphModel>\n  </diagram>\n</mxfile>\n"
    )


def main():
    ap = argparse.ArgumentParser(description="Auto-layout a graph JSON into draw.io XML.")
    ap.add_argument("input", help="graph JSON file")
    ap.add_argument("-o", "--output", help="output .drawio path (default: stdout)")
    args = ap.parse_args()
    with open(args.input, encoding="utf-8") as f:
        graph = json.load(f)
    height, pos, edge_pts = layout(build_dot(graph))
    xml = to_drawio(graph, height, pos, edge_pts)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(xml)
        print(f"wrote {args.output} ({len(graph['nodes'])} nodes, "
              f"{len(graph.get('edges', []))} edges)", file=sys.stderr)
    else:
        sys.stdout.write(xml)


if __name__ == "__main__":
    main()
