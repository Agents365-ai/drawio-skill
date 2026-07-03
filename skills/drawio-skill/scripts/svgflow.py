#!/usr/bin/env python3
"""Make a diagram's edges *flow* — an animated data-flow SVG.

Exports a .drawio to SVG (or takes an .svg directly) and turns every edge into a
marching-ants animation: dashes travel along each connector in the direction of
the arrow, so the diagram shows data/flow moving through it. The result is a
single self-contained .svg that loops forever in any browser — nice for a README
(GitHub renders SVG), a docs page, or a slide background.

  python3 svgflow.py architecture.drawio -o architecture-flow.svg
  python3 svgflow.py already-exported.svg  -o flow.svg

Edges are found by draw.io's own marker: connector *lines* carry
`pointer-events="stroke"` (shape outlines and arrowheads use `="all"`), so only
the real edges animate — arrowheads and shapes stay put. `--speed` sets seconds
per cycle, `--dash` the dash pattern, `--reverse` flips the flow direction.

Usage: python3 svgflow.py <file.drawio|file.svg> [-o out.svg]
       [--speed SEC] [--dash "6 4"] [--reverse]
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile

EDGE_PATH = re.compile(r'(<path )((?:(?!/?>)[^>])*pointer-events="stroke"(?:(?!/?>)[^>])*/?>)')


def to_svg(path):
    """Return SVG text for a .drawio (export via CLI) or .svg (read directly)."""
    if path.lower().endswith(".svg"):
        with open(path, encoding="utf-8") as f:
            return f.read()
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "d.svg")
        r = subprocess.run(["drawio", "-x", "-f", "svg", "-o", out, path],
                           capture_output=True)
        if r.returncode != 0 or not os.path.exists(out):
            sys.exit("error: draw.io SVG export failed (is the draw.io CLI installed?)")
        with open(out, encoding="utf-8") as f:
            return f.read()


def animate(svg, speed, dash, reverse):
    """Tag edge paths and inject the flow keyframes. Returns (svg, edge_count)."""
    svg, n = EDGE_PATH.subn(r'\1class="dio-flow" \2', svg)
    # One dash+gap of travel per cycle => seamless loop. Reverse flips the sign.
    period = sum(float(x) for x in dash.split()) or 10
    offset = period if reverse else -period
    style = (f"<style>.dio-flow{{stroke-dasharray:{dash};"
             f"animation:dio-flow {speed}s linear infinite;}}"
             f"@keyframes dio-flow{{to{{stroke-dashoffset:{offset:g};}}}}</style>")
    svg = re.sub(r"(<svg\b[^>]*>)", r"\1" + style, svg, count=1)
    return svg, n


def main():
    ap = argparse.ArgumentParser(description="Animate a diagram's edges into a flowing SVG.")
    ap.add_argument("file", help=".drawio (exported to SVG) or an .svg")
    ap.add_argument("-o", "--output", help="output .svg (default: <name>-flow.svg)")
    ap.add_argument("--speed", type=float, default=1.2, help="seconds per flow cycle (default 1.2)")
    ap.add_argument("--dash", default="6 4", help='dash pattern, e.g. "6 4" (default)')
    ap.add_argument("--reverse", action="store_true", help="flow toward the source")
    args = ap.parse_args()

    if not os.path.isfile(args.file):
        sys.exit(f"error: {args.file} not found")
    svg = to_svg(args.file)
    if "<svg" not in svg:
        sys.exit("error: no <svg> element found in the exported output")
    svg, n = animate(svg, args.speed, args.dash, args.reverse)
    if n == 0:
        sys.stderr.write("warning: no edges found to animate "
                         "(a diagram with no connectors?)\n")

    out = args.output or os.path.splitext(args.file)[0] + "-flow.svg"
    with open(out, "w", encoding="utf-8") as f:
        f.write(svg)
    sys.stderr.write(f"wrote {out} ({n} edge{'s' if n != 1 else ''} animated)\n")


if __name__ == "__main__":
    main()
