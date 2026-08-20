#!/usr/bin/env python3
"""Restyle a graph as a London-Underground-style metro map (Tube-Map Mode).

Input JSON describes coloured *lines* (each an ordered list of station ids) and the
*stations* they pass through, placed on an integer grid. The script snaps stations to
a pixel grid, routes every line segment octilinearly (horizontal / vertical / 45°
diagonal, inserting one bend when two stations are not already aligned), draws thick
coloured line strokes, marks interchange stations as white-fill black-ring circles and
regular stops as small white circles, and labels each station — the classic tube-map
look — as an editable `.drawio`.

  python3 tubemap.py metro.json -o metro.drawio

Input schema (see references/tubemap.md for the full authoring guide):

  {
    "stations": {
      "<id>": {"label": "...", "gx": <int>, "gy": <int>, "interchange": <bool?>}
    },
    "lines": [
      {"name": "...", "color": "#rrggbb"?, "stations": ["<id>", "<id>", ...]}
    ]
  }

Keep consecutive stations on a line horizontally, vertically, or 45°-diagonally aligned
for the cleanest routing; any other offset gets one automatic diagonal-then-straight
bend. A line with no "color" is assigned one from the default tube palette by order.

Usage: python3 tubemap.py <metro.json> [-o out.drawio] [--grid N]
"""
import argparse
import json
import sys

# Default palette (approx. real tube-line colours), cycled for lines lacking a "color".
TUBE_PALETTE = [
    "#0098d4",  # blue
    "#007d32",  # green
    "#e1251b",  # red
    "#ee7c0e",  # orange
    "#9b0056",  # magenta
    "#00a4a7",  # teal
    "#ffce00",  # yellow
    "#894e24",  # brown
]


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


def octilinear_waypoints(x1, y1, x2, y2):
    """Waypoints so the path is horizontal, vertical, or 45°: diagonal then straight.

    Returns [] when the two points are already octilinearly aligned, else a single bend
    point (run the 45° diagonal for the shorter delta, then a straight axis segment).
    """
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 or dy == 0 or abs(dx) == abs(dy):
        return []
    sx = 1 if dx > 0 else -1
    sy = 1 if dy > 0 else -1
    d = min(abs(dx), abs(dy))
    if abs(dx) > abs(dy):          # diagonal first, then horizontal into the target
        return [(x1 + sx * d, y2)]
    return [(x2, y1 + sy * d)]      # diagonal first, then vertical into the target


def build(data, grid=110):
    """Build the tube-map `.drawio` XML string from the parsed metro description."""
    stations = data.get("stations", {})
    lines = data.get("lines", [])
    if not stations:
        sys.exit("error: no stations in input")
    for ln in lines:
        for sid in ln.get("stations", []):
            if sid not in stations:
                sys.exit(f"error: line {ln.get('name', '?')!r} references unknown "
                         f"station id {sid!r}")

    ox = oy = 80
    G = grid

    def px(sid):
        s = stations[sid]
        return ox + int(s["gx"]) * G, oy + int(s["gy"]) * G

    maxx = ox + max(int(s["gx"]) for s in stations.values()) * G + 220
    maxy = oy + max(int(s["gy"]) for s in stations.values()) * G + 120
    lw = max(8, G // 12)

    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<mxfile host="drawio-skill" type="device">',
           '  <diagram id="tube" name="Tube Map">',
           f'    <mxGraphModel dx="0" dy="0" grid="0" gridSize="10" pageWidth="{maxx}" '
           f'pageHeight="{maxy}" math="0" shadow="0" background="#ffffff">',
           '      <root><mxCell id="0"/><mxCell id="1" parent="0"/>']

    nid = [2]

    def cid():
        c = nid[0]
        nid[0] += 1
        return c

    # 1) Line strokes first, so station markers sit on top of them.
    for i, ln in enumerate(lines):
        col = ln.get("color") or TUBE_PALETTE[i % len(TUBE_PALETTE)]
        sts = ln.get("stations", [])
        for a, b in zip(sts, sts[1:]):
            x1, y1 = px(a)
            x2, y2 = px(b)
            wps = octilinear_waypoints(x1, y1, x2, y2)
            arr = ""
            if wps:
                pts = "".join(f'<mxPoint x="{wx}" y="{wy}"/>' for wx, wy in wps)
                arr = f'<Array as="points">{pts}</Array>'
            out.append(
                f'        <mxCell id="e{cid()}" edge="1" parent="1" '
                f'style="endArrow=none;startArrow=none;strokeColor={col};strokeWidth={lw};'
                f'rounded=1;html=1;edgeStyle=none;">'
                f'<mxGeometry relative="1" as="geometry">'
                f'<mxPoint x="{x1}" y="{y1}" as="sourcePoint"/>'
                f'<mxPoint x="{x2}" y="{y2}" as="targetPoint"/>{arr}</mxGeometry></mxCell>')

    # 2) Station markers + labels.
    for sid, s in stations.items():
        x, y = px(sid)
        label = esc(str(s.get("label", sid)))
        if s.get("interchange"):
            r = lw + 6
            marker = (f'ellipse;fillColor=#ffffff;strokeColor=#111111;strokeWidth=3;'
                      f'html=1;')
        else:
            r = lw - 1
            marker = (f'ellipse;fillColor=#ffffff;strokeColor=#555555;strokeWidth=2;'
                      f'html=1;')
        out.append(
            f'        <mxCell id="s{cid()}" vertex="1" parent="1" style="{marker}" '
            f'value=""><mxGeometry x="{x - r}" y="{y - r}" width="{2 * r}" '
            f'height="{2 * r}" as="geometry"/></mxCell>')
        out.append(
            f'        <mxCell id="l{cid()}" vertex="1" parent="1" '
            f'style="text;html=1;align=left;verticalAlign=middle;fontSize=13;fontStyle=1;'
            f'fontColor=#222222;labelBackgroundColor=#ffffff;" value="{label}">'
            f'<mxGeometry x="{x + lw + 8}" y="{y - 12}" width="170" height="24" '
            f'as="geometry"/></mxCell>')

    out.append('      </root></mxGraphModel></diagram></mxfile>')
    return "\n".join(out), len(stations), len(lines)


def main():
    ap = argparse.ArgumentParser(description="Restyle a graph as a metro / tube map.")
    ap.add_argument("input", help="metro JSON (or - for stdin)")
    ap.add_argument("-o", "--output", help="output .drawio (default: stdout)")
    ap.add_argument("--grid", type=int, default=110, help="grid pitch in px (default 110)")
    args = ap.parse_args()

    if args.input == "-":
        raw = sys.stdin.read()
    else:
        with open(args.input, encoding="utf-8") as f:
            raw = f.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        sys.exit(f"error: bad JSON in {args.input}: {exc}")

    xml, n_st, n_ln = build(data, grid=args.grid)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(xml)
        sys.stderr.write(f"wrote {args.output} ({n_st} stations, {n_ln} lines)\n")
    else:
        sys.stdout.write(xml)


if __name__ == "__main__":
    main()
