#!/usr/bin/env python3
"""Colour a diagram by data — turn a .drawio into a metric heatmap.

Reads a .drawio and a metrics file (CSV `key,value` or JSON `{key: value}`),
matches each metric key to a node by cell id or by its label text, and recolours
that node along a gradient from the lowest value to the highest. Optionally
scales node size by value (`--size`) and drops in a legend. The result is a new
.drawio you can export like any other — an architecture diagram that now shows
cost / latency / traffic / error-rate as a heat map.

  python3 heatmap.py architecture.drawio --metrics latency.csv -o hot.drawio
  python3 heatmap.py architecture.drawio -m cost.json --palette cool --size

Metrics match on cell id first, then on the (HTML-stripped) label, case-
insensitively. Unmatched nodes keep their original style. `--palette` picks the
colour ramp (heat|cool|warm), `--reverse` flips it (so low = hot).

Usage: python3 heatmap.py <file.drawio> --metrics <file.csv|json> [-o out.drawio]
       [--palette heat|cool|warm] [--reverse] [--size] [--no-legend]
"""
import argparse
import csv
import html
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

# Sequential ramps as (low, mid, high) anchor colours; value is lerped across them.
PALETTES = {
    "heat": ("#57bb8a", "#ffd666", "#e67c73"),   # green -> yellow -> red
    "cool": ("#deebf7", "#6baed6", "#08519c"),   # light -> deep blue
    "warm": ("#fff7bc", "#fec44f", "#d95f0e"),   # pale -> deep amber
}


def clean(text):
    """Strip the HTML tags/entities draw.io stores in labels; collapse whitespace."""
    if not text:
        return ""
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def load_metrics(path):
    """{key: float} from a JSON object/list or a CSV/TSV (first col key, last numeric col value)."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    if path.lower().endswith(".json"):
        data = json.loads(text)
        if isinstance(data, dict):
            return {str(k): _num(v) for k, v in data.items() if _num(v) is not None}
        out = {}
        for row in data:
            key = row.get("id") or row.get("key") or row.get("name") or row.get("label")
            val = _num(row.get("value", row.get("val", row.get("metric"))))
            if key is not None and val is not None:
                out[str(key)] = val
        return out
    delim = "\t" if text.splitlines() and "\t" in text.splitlines()[0] else ","
    out = {}
    for row in csv.reader(text.splitlines(), delimiter=delim):
        if len(row) < 2:
            continue
        v = _num(row[-1])
        if v is not None:                       # skip header / non-numeric rows
            out[row[0].strip()] = v
    return out


def _rgb(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def ramp(anchors, t):
    """t in [0,1] -> #rrggbb across a 3-stop (low, mid, high) ramp."""
    lo, mid, hi = (_rgb(c) for c in anchors)
    a, b, u = (lo, mid, t * 2) if t < 0.5 else (mid, hi, (t - 0.5) * 2)
    return "#%02x%02x%02x" % tuple(round(a[i] + (b[i] - a[i]) * u) for i in range(3))


def darker(hexcolor, f=0.6):
    return "#%02x%02x%02x" % tuple(round(c * f) for c in _rgb(hexcolor))


def set_style(style, fill, stroke):
    """Replace/insert fillColor & strokeColor in a draw.io style string."""
    s = re.sub(r"(fillColor|strokeColor)=[^;]*;?", "", style or "").strip("; ")
    return (s + ";" if s else "") + f"fillColor={fill};strokeColor={stroke};"


def vertices(root):
    """Yield (cell, id, label) for every vertex, unwrapping UserObject/object wrappers."""
    for child in root:
        if child.tag == "mxCell" and child.get("vertex") == "1":
            yield child, child.get("id"), clean(child.get("value"))
        elif child.tag in ("UserObject", "object"):
            inner = child.find("mxCell")
            if inner is not None and inner.get("vertex") == "1":
                yield inner, child.get("id"), clean(child.get("label") or child.get("value"))


def scale_geom(cell, factor):
    """Grow/shrink a cell about its centre by `factor`."""
    g = cell.find("mxGeometry")
    if g is None:
        return
    w, h = _num(g.get("width")), _num(g.get("height"))
    if w is None or h is None:
        return
    nw, nh = w * factor, h * factor
    g.set("width", "%g" % nw)
    g.set("height", "%g" % nh)
    for attr, delta in (("x", (nw - w) / 2), ("y", (nh - h) / 2)):
        v = _num(g.get(attr))
        if v is not None:
            g.set(attr, "%g" % (v - delta))


def color_for(val, lo, hi, anchors, reverse):
    t = (val - lo) / (hi - lo) if hi > lo else 0.5
    fill = ramp(anchors, 1 - t if reverse else t)
    return fill, darker(fill), t


def content_bounds(root):
    """(min_x, min_y) of the page's top-level cells, so the legend sits clear of them."""
    xs, ys = [], []
    for child in root:
        cell = child if child.tag == "mxCell" else child.find("mxCell")
        if cell is None or cell.get("parent") != "1":     # skip nested (relative-coord) cells
            continue
        g = cell.find("mxGeometry")
        x, y = (_num(g.get("x")), _num(g.get("y"))) if g is not None else (None, None)
        if x is not None and y is not None:
            xs.append(x)
            ys.append(y)
    return (min(xs) if xs else 20, min(ys) if ys else 20)


def add_legend(root, anchors, lo, hi, reverse):
    """Drop a small min/mid/max swatch legend just left of the page's content."""
    w, h = 90, 26
    cx, cy = content_bounds(root)
    x0, y0 = cx - w - 40, cy                               # to the left of the diagram

    def cell(cid, value, style, gy, gh):
        c = ET.SubElement(root, "mxCell", {"id": cid, "value": value, "style": style,
                                           "vertex": "1", "parent": "1"})
        ET.SubElement(c, "mxGeometry", {"x": "%g" % x0, "y": "%g" % gy,
                                        "width": "%g" % w, "height": "%g" % gh, "as": "geometry"})

    cell("hm-title", "Heatmap",
         "text;html=1;fontStyle=1;align=left;verticalAlign=middle;", y0, 20)
    for i, val in enumerate((hi, (lo + hi) / 2, lo)):
        fill, stroke, _ = color_for(val, lo, hi, anchors, reverse)
        cell("hm-%d" % i, "%g" % val,
             set_style("rounded=0;whiteSpace=wrap;html=1;", fill, stroke),
             y0 + 24 + i * (h + 4), h)


def main():
    ap = argparse.ArgumentParser(description="Recolour a .drawio into a metric heatmap.")
    ap.add_argument("file", help="input .drawio (uncompressed)")
    ap.add_argument("-m", "--metrics", required=True, help="metrics .csv or .json")
    ap.add_argument("-o", "--output", help="output .drawio (default: <name>-heat.drawio)")
    ap.add_argument("--palette", default="heat", choices=list(PALETTES))
    ap.add_argument("--reverse", action="store_true", help="flip the ramp (low = hot)")
    ap.add_argument("--size", action="store_true", help="also scale node size by value")
    ap.add_argument("--no-legend", dest="legend", action="store_false", help="skip the legend")
    args = ap.parse_args()

    if not os.path.isfile(args.file):
        sys.exit(f"error: {args.file} not found")
    if not os.path.isfile(args.metrics):
        sys.exit(f"error: {args.metrics} not found")
    metrics = load_metrics(args.metrics)
    if not metrics:
        sys.exit(f"error: no numeric metrics parsed from {args.metrics}")
    low_map = {k.lower(): v for k, v in metrics.items()}
    anchors = PALETTES[args.palette]
    lo, hi = min(metrics.values()), max(metrics.values())

    tree = ET.parse(args.file)
    matched, first_root = 0, None
    for diagram in tree.getroot().iter("diagram"):
        model = diagram.find("mxGraphModel")
        root = model.find("root") if model is not None else None
        if root is None:                       # compressed / empty page
            continue
        if first_root is None:
            first_root = root
        for cell, cid, label in list(vertices(root)):
            val = metrics.get(cid)
            if val is None and label:
                val = metrics.get(label, low_map.get(label.lower()))
            if val is None:
                continue
            fill, stroke, t = color_for(val, lo, hi, anchors, args.reverse)
            cell.set("style", set_style(cell.get("style"), fill, stroke))
            if args.size and hi > lo:
                scale_geom(cell, 0.7 + 0.8 * t)
            matched += 1

    if args.legend and first_root is not None and matched:
        add_legend(first_root, anchors, lo, hi, args.reverse)

    out = args.output or os.path.splitext(args.file)[0] + "-heat.drawio"
    tree.write(out, encoding="utf-8", xml_declaration=False)
    if matched == 0:
        sys.stderr.write("warning: no nodes matched any metric key (check ids/labels)\n")
    sys.stderr.write(f"wrote {out} ({matched}/{len(metrics)} metrics matched)\n")


if __name__ == "__main__":
    main()
