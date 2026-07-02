#!/usr/bin/env python3
"""Deterministic sequence-diagram layout: message list JSON -> .drawio XML.

Sequence diagrams are the easiest type to get wrong by hand-placing
coordinates (lifelines, activation bars and message arrows all share exact
x/y math) and the least suited to Graphviz — but their geometry is pure
arithmetic: participants split the x axis, messages advance the y axis.
This script computes all of it, using the same official styles as
references/diagram-types.md (umlLifeline shapes, block/open arrows).

  python3 seqlayout.py seq.json -o diagram.drawio

Input JSON:
  {
    "title": "Login flow",                    # optional page name
    "participants": [
      {"id": "u", "label": "User", "actor": true},
      {"id": "s", "label": "Server"}          # order = left-to-right order
    ],
    "messages": [
      {"from": "u", "to": "s", "label": "POST /login"},          # sync (solid, filled arrow)
      {"from": "s", "to": "s", "label": "validate()"},           # self message
      {"from": "s", "to": "u", "label": "200 OK", "return": true},  # return (grey dashed)
      {"from": "u", "to": "s", "label": "notify", "async": true},   # async (dashed, open arrow)
      {"note": "token cached", "over": "s"}                      # note beside a lifeline
    ]
  }

Activation bars are automatic: a sync/async message opens a bar on the
target, a return message closes the sender's bar, and bars still open at the
end run to the bottom. Override per message with "activate": false (don't
open on target) or "deactivate": true (close the sender's bar after this
message). Arrows attach to the bar edge when a bar is active, else to the
lifeline. Fragments (alt/loop/opt frames) are out of scope — add them in
draw.io afterwards.

Usage: python3 seqlayout.py <seq.json> [-o diagram.drawio]
"""
import argparse
import json
import sys
from xml.sax.saxutils import escape

LIFELINE_W, HEADER_H = 100, 40
BAR_W = 10
TOP, ROW, SELF_ROW, NOTE_ROW, BOTTOM_PAD = 40, 50, 70, 60, 40
MIN_SPACING = 200

LIFELINE = ("shape=umlLifeline;perimeter=lifelinePerimeter;whiteSpace=wrap;html=1;"
            "container=1;dropTarget=0;collapsible=0;recursiveResize=0;outlineConnect=0;"
            f"portConstraint=eastwest;size={HEADER_H};")
# Actor lifelines render a stick figure in the header — anchor the name at
# the header bottom (white-backed) so figure and label don't overlap.
ACTOR = LIFELINE + ("participant=umlActor;verticalAlign=bottom;"
                    "spacingBottom=-14;labelBackgroundColor=#ffffff;")
BAR = "html=1;points=[];perimeter=orthogonalPerimeter;outlineConnect=0;fillColor=#ffffff;"
NOTE = ("shape=note;whiteSpace=wrap;html=1;size=14;fillColor=#fff2cc;"
        "strokeColor=#d6b656;")
SYNC = "html=1;verticalAlign=bottom;endArrow=block;curved=0;rounded=0;"
ASYNC = "html=1;verticalAlign=bottom;endArrow=open;dashed=1;curved=0;rounded=0;"
RETURN = ("html=1;verticalAlign=bottom;endArrow=open;dashed=1;curved=0;rounded=0;"
          "strokeColor=#999999;fontColor=#999999;")


def attr(value):
    return escape(str(value), {'"': "&quot;", "\n": "&#xa;"})


def frac(y, top, height):
    return round(max(0.0, min(1.0, (y - top) / height)), 4)


def layout(spec):
    parts = spec["participants"]
    if not parts:
        sys.exit("error: no participants")
    order = {p["id"]: i for i, p in enumerate(parts)}
    if len(order) != len(parts):
        sys.exit("error: duplicate participant ids")

    # x axis: uniform spacing, widened if any label needs it (~7px/char).
    spacing = max([MIN_SPACING] + [7 * len(str(p.get("label", p["id"]))) + 80 for p in parts])
    spacing = -(-spacing // 10) * 10                      # snap up to the grid
    cx = {p["id"]: TOP + i * spacing + LIFELINE_W // 2 for i, p in enumerate(parts)}

    # y axis: walk the messages once, assigning each row a y position and
    # tracking one open activation bar per participant ({pid: start_y}).
    y = TOP + HEADER_H + 50
    rows, open_bar, bars = [], {}, []           # bars: (pid, y0, y1)

    def close(pid, at):
        if pid in open_bar:
            bars.append((pid, open_bar.pop(pid), at))

    for i, m in enumerate(spec.get("messages", [])):
        if "note" in m:
            rows.append(("note", m, y))
            y += NOTE_ROW
            continue
        src, dst = m["from"], m["to"]
        if src not in order or dst not in order:
            sys.exit(f"error: message {i} references unknown participant")
        is_return = m.get("return", False)
        if src == dst:
            rows.append(("self", m, y))
            y += SELF_ROW
            continue
        rows.append(("msg", m, y))
        if is_return:
            close(src, y)                       # returning ends the caller's work
        elif m.get("activate", True) and dst not in open_bar:
            open_bar[dst] = y                   # call starts work on the target
        if m.get("deactivate"):
            close(src, y)
        y += ROW
    height = y + BOTTOM_PAD - TOP
    for pid in list(open_bar):
        close(pid, TOP + height - BOTTOM_PAD)

    cells = []
    for p in parts:
        style = ACTOR if p.get("actor") else LIFELINE
        cells.append(
            f'        <mxCell id="{attr(p["id"])}" value="{attr(p.get("label", p["id"]))}" '
            f'style="{style}" vertex="1" parent="1">\n'
            f'          <mxGeometry x="{cx[p["id"]] - LIFELINE_W // 2}" y="{TOP}" '
            f'width="{LIFELINE_W}" height="{height}" as="geometry"/>\n'
            "        </mxCell>")

    # Activation bars: children of their lifeline (coordinates relative to it).
    bar_of = {}                                 # pid -> list of (y0, y1, cell_id)
    for n, (pid, y0, y1) in enumerate(bars):
        bid = f"act{n}"
        bar_of.setdefault(pid, []).append((y0, y1, bid))
        cells.append(
            f'        <mxCell id="{bid}" value="" style="{BAR}" vertex="1" '
            f'parent="{attr(pid)}">\n'
            f'          <mxGeometry x="{LIFELINE_W // 2 - BAR_W // 2}" y="{y0 - TOP}" '
            f'width="{BAR_W}" height="{y1 - y0}" as="geometry"/>\n'
            "        </mxCell>")

    def anchor(pid, my, side):
        """(cell_id, exitX-style fragment values) for a message endpoint: the
        activation bar's edge when one is active at this y, else the lifeline."""
        for y0, y1, bid in bar_of.get(pid, []):
            if y0 <= my <= y1:
                return bid, (1 if side == "right" else 0), frac(my, y0, y1 - y0)
        return pid, 0.5, frac(my, TOP, height)

    for i, (kind, m, my) in enumerate(rows):
        if kind == "note":
            pid = m.get("over")
            if pid not in cx:
                sys.exit(f"error: note {i} is over unknown participant {pid!r}")
            w = max(120, 7 * len(str(m["note"])) + 30)
            cells.append(
                f'        <mxCell id="note{i}" value="{attr(m["note"])}" style="{NOTE}" '
                f'vertex="1" parent="1">\n'
                f'          <mxGeometry x="{cx[pid] + 20}" y="{my - 20}" '
                f'width="{min(w, spacing - 60)}" height="40" as="geometry"/>\n'
                "        </mxCell>")
            continue
        src, dst = m["from"], m["to"]
        style = RETURN if m.get("return") else ASYNC if m.get("async") else SYNC
        if kind == "self":
            sid, sx, sy = anchor(src, my, "right")
            _, tx, ty = anchor(src, my + 30, "right")
            loop_x = cx[src] + 60
            cells.append(
                f'        <mxCell id="m{i}" value="{attr(m.get("label", ""))}" '
                f'style="{style}exitX={sx};exitY={sy};entryX={tx};entryY={ty};" '
                f'edge="1" parent="1" source="{attr(sid)}" target="{attr(sid)}">\n'
                f'          <mxGeometry relative="1" as="geometry">\n'
                f'            <Array as="points">'
                f'<mxPoint x="{loop_x}" y="{my}"/><mxPoint x="{loop_x}" y="{my + 30}"/>'
                f'</Array>\n'
                "          </mxGeometry>\n"
                "        </mxCell>")
            continue
        rightward = order[src] < order[dst]
        sid, sx, sy = anchor(src, my, "right" if rightward else "left")
        tid, tx, ty = anchor(dst, my, "left" if rightward else "right")
        cells.append(
            f'        <mxCell id="m{i}" value="{attr(m.get("label", ""))}" '
            f'style="{style}exitX={sx};exitY={sy};entryX={tx};entryY={ty};" '
            f'edge="1" parent="1" source="{attr(sid)}" target="{attr(tid)}">\n'
            f'          <mxGeometry relative="1" as="geometry"/>\n'
            "        </mxCell>")

    name = attr(spec.get("title", "Sequence"))
    return (
        f'<mxfile>\n  <diagram id="seqlayout" name="{name}">\n'
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
    ap = argparse.ArgumentParser(description="Sequence-diagram JSON -> draw.io XML.")
    ap.add_argument("input", help="sequence JSON file")
    ap.add_argument("-o", "--output", help="output .drawio path (default: stdout)")
    args = ap.parse_args()
    with open(args.input, encoding="utf-8") as f:
        spec = json.load(f)
    xml = layout(spec)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(xml)
        print(f"wrote {args.output} ({len(spec['participants'])} participants, "
              f"{len(spec.get('messages', []))} messages)", file=sys.stderr)
    else:
        sys.stdout.write(xml)


if __name__ == "__main__":
    main()
