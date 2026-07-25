#!/usr/bin/env python3
"""Assign edge connection points (ports) on an existing .drawio file.

draw.io's floating connections attach every edge of a node to the middle of
whichever side faces the other endpoint. When a node has several connections
leaving the same side they all land on the same point, so the lines stack and
overlap — the usual complaint on swimlane / cross-functional flowcharts, where
handoff edges between lanes share long orthogonal corridors.

This pass pins ``exitX/exitY`` and ``entryX/entryY`` instead:

1. Resolve every vertex to absolute coordinates (through swimlane/container
   parents, via ``validate.abs_rect``).
2. For each edge end, pick the side of the node that faces the other endpoint
   (whichever of dx/dy dominates, measured centre-to-centre).
3. Group the ends by (node, side) and sort each group along the side by the far
   endpoint's position across that axis. Sorting by the far endpoint is what
   removes crossings: two edges leaving the same side keep their relative order
   instead of swapping over each other.
4. Spread the group evenly over the side — k ends get slots 1/(k+1) .. k/(k+1).

Only sides with 2+ ends are touched. Edges that already pin a port are left
alone, so hand-tuned geometry survives a re-run. Idempotent: running it twice
produces the same file.

This is a *port* assignment, not a router — it fixes lines stacking at the
shape boundary, not an edge crossing an unrelated shape in the middle of its
run. For that, add waypoints (see references/xml-authoring.md).

Usage:
    python3 edgeports.py diagram.drawio                 # in place
    python3 edgeports.py diagram.drawio -o routed.drawio
    python3 edgeports.py diagram.drawio --dry-run       # report only
"""

import argparse
import importlib.util
import os
import sys
import xml.etree.ElementTree as ET

_spec = importlib.util.spec_from_file_location(
    "validate", os.path.join(os.path.dirname(os.path.abspath(__file__)), "validate.py"))
validate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(validate)

# Port coordinates per side. Each entry is (fixed_axis_value, varies_along_x).
# 'varies_along_x' says which coordinate the evenly-spaced slot fills in.
SIDES = {
    "N": (0.0, True),    # top edge:    y=0, x varies
    "S": (1.0, True),    # bottom edge: y=1, x varies
    "W": (0.0, False),   # left edge:   x=0, y varies
    "E": (1.0, False),   # right edge:  x=1, y varies
}


def centre(r):
    x, y, w, h = r
    return (x + w / 2.0, y + h / 2.0)


def side_facing(src_rect, dst_rect):
    """Which side of src faces dst: whichever of dx/dy dominates."""
    sx, sy = centre(src_rect)
    dx_, dy_ = centre(dst_rect)
    dx, dy = dx_ - sx, dy_ - sy
    if abs(dx) >= abs(dy):
        return "E" if dx >= 0 else "W"
    return "S" if dy >= 0 else "N"


def has_port(style, end):
    """True if the edge already pins this end's port (hand-tuned — leave it)."""
    prefix = "exit" if end == "source" else "entry"
    return (validate.style_num(style, prefix + "X") is not None
            and validate.style_num(style, prefix + "Y") is not None)


def set_style(style, end, px, py):
    """Return style with this end's port keys set, other keys order-preserved."""
    prefix = "exit" if end == "source" else "entry"
    drop = {prefix + "X", prefix + "Y", prefix + "Dx", prefix + "Dy"}
    parts = [p for p in (style or "").split(";")
             if p and p.split("=", 1)[0] not in drop]
    # Dx/Dy are perpendicular offsets in px; reset them so a re-run is stable.
    parts += [f"{prefix}X={px:g}", f"{prefix}Y={py:g}",
              f"{prefix}Dx=0", f"{prefix}Dy=0"]
    return ";".join(parts) + ";"


def assign(cells, by_id):
    """Compute {(edge_elem, end): (px, py)} for every end worth pinning."""
    rects = {}
    for c in cells:
        if c.get("vertex") == "1" and not validate.is_edge_label(c):
            r = validate.abs_rect(c, by_id)
            if r and not any(v != v for v in r):   # NaN width/height guard
                rects[c.get("id")] = r

    # Collect ends: one entry per (edge, end) whose node and peer are known.
    groups = {}
    for e in cells:
        if e.get("edge") != "1":
            continue
        style = e.get("style") or ""
        src, dst = e.get("source"), e.get("target")
        if src not in rects or dst not in rects:
            continue                                # dangling — validate.py's job
        for end, me, peer in (("source", src, dst), ("target", dst, src)):
            if has_port(style, end):
                continue
            side = side_facing(rects[me], rects[peer])
            groups.setdefault((me, side), []).append((e, end, rects[peer]))

    ports = {}
    for (node_id, side), ends in groups.items():
        if len(ends) < 2:
            continue                                # single edge: centre is fine
        fixed, along_x = SIDES[side]
        # Sort by the far endpoint's position across the axis we spread along.
        # Tie-break on the other axis, then edge id, so the order is total and
        # the output is deterministic.
        ends.sort(key=lambda t: (centre(t[2])[0] if along_x else centre(t[2])[1],
                                 centre(t[2])[1] if along_x else centre(t[2])[0],
                                 t[0].get("id") or ""))
        for i, (edge, end, _) in enumerate(ends):
            slot = (i + 1) / float(len(ends) + 1)
            ports[(edge, end)] = (slot, fixed) if along_x else (fixed, slot)
    return ports


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", help="input .drawio")
    ap.add_argument("-o", "--output", help="output path (default: edit in place)")
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would change, write nothing")
    args = ap.parse_args()

    try:
        tree = ET.parse(args.file)
    except ET.ParseError as exc:
        sys.exit(f"error: {args.file} is not parseable XML ({exc}). "
                 "Compressed .drawio files must be saved uncompressed first.")

    total = 0
    for model in tree.getroot().iter("mxGraphModel"):
        cells = list(model.iter("mxCell"))
        by_id = {c.get("id"): c for c in cells if c.get("id")}
        ports = assign(cells, by_id)
        for (edge, end), (px, py) in ports.items():
            edge.set("style", set_style(edge.get("style") or "", end, px, py))
        total += len(ports)

    if args.dry_run:
        print(f"{total} edge end(s) would be pinned in {args.file}")
        return
    out = args.output or args.file
    tree.write(out, encoding="utf-8", xml_declaration=False)
    print(f"{total} edge end(s) pinned -> {out}")


def demo():
    """Self-check: three edges leaving one node's east side get distinct,
    non-crossing ports, and a re-run is a no-op."""
    xml = """<mxfile><diagram><mxGraphModel><root>
      <mxCell id="0"/><mxCell id="1" parent="0"/>
      <mxCell id="lane" vertex="1" parent="1">
        <mxGeometry x="100" y="0" width="400" height="400" as="geometry"/></mxCell>
      <mxCell id="hub" vertex="1" parent="lane">
        <mxGeometry x="0" y="150" width="80" height="40" as="geometry"/></mxCell>
      <mxCell id="a" vertex="1" parent="1">
        <mxGeometry x="600" y="300" width="80" height="40" as="geometry"/></mxCell>
      <mxCell id="b" vertex="1" parent="1">
        <mxGeometry x="600" y="100" width="80" height="40" as="geometry"/></mxCell>
      <mxCell id="c" vertex="1" parent="1">
        <mxGeometry x="600" y="200" width="80" height="40" as="geometry"/></mxCell>
      <mxCell id="e1" edge="1" parent="1" source="hub" target="a" style="rounded=1;"/>
      <mxCell id="e2" edge="1" parent="1" source="hub" target="b" style="rounded=1;"/>
      <mxCell id="e3" edge="1" parent="1" source="hub" target="c" style="rounded=1;"/>
      <mxCell id="e4" edge="1" parent="1" source="hub" target="a"
              style="rounded=1;exitX=1;exitY=0.9;"/>
    </root></mxGraphModel></diagram></mxfile>"""
    root = ET.fromstring(xml)
    cells = list(root.iter("mxCell"))
    by_id = {c.get("id"): c for c in cells if c.get("id")}

    # hub sits inside 'lane' (x=100), so its absolute x is 100, not 0. Without
    # parent resolution every target would look like it was to the west.
    assert validate.abs_rect(by_id["hub"], by_id)[0] == 100.0

    ports = assign(cells, by_id)
    exits = {e.get("id"): p for (e, end), p in ports.items() if end == "source"}
    assert set(exits) == {"e1", "e2", "e3"}, exits   # e4 pre-pinned, untouched
    assert all(x == 1.0 for x, _ in exits.values())  # all leave the east side
    ys = [exits[i][1] for i in ("e2", "e3", "e1")]   # targets ordered top->bottom
    assert ys == sorted(ys), ys                      # ports follow => no crossing
    assert len(set(ys)) == 3, ys                     # and no two stack

    for (edge, end), (px, py) in ports.items():
        edge.set("style", set_style(edge.get("style"), end, px, py))
    assert not assign(cells, by_id), "second run must be a no-op"
    print("ok")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo()
    else:
        main()
