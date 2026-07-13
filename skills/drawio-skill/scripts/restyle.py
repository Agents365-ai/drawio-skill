#!/usr/bin/env python3
"""Re-theme an EXISTING .drawio with a style preset — layout and shapes untouched.

Style presets (styles/schema.json) normally apply at generation time; this is
the post-processor for diagrams that already exist: "make this dark", "apply my
corporate style to last week's diagram".

  python3 restyle.py diagram.drawio --preset dark
  python3 restyle.py diagram.drawio --preset ~/.drawio-skill/styles/corp.json -o out.drawio

What it changes, per the preset application rules in references/style-presets.md:
- Every vertex fill/stroke is remapped to the preset palette. Each existing
  fillColor is matched to its nearest palette slot by hue (grey/low-saturation
  -> neutral), so same-colored nodes stay same-colored in the new theme.
- font.fontFamily on every vertex; existing fontSize values are kept (they
  encode hierarchy).
- extras: fontColor (vertices + text cells), edgeColor (edge stroke + label),
  sketch=1, globalStrokeWidth, page background on <mxGraphModel>.
Edge ROUTING styles and shape keywords are left alone — rewriting them would
break existing waypoints and geometry. fillColor=none is structural (lanes,
transparent containers) and is never replaced.

Usage: restyle.py <file.drawio> --preset <name|path.json> [-o <out.drawio>]
"""
import argparse
import colorsys
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Canonical hue (degrees) of each palette slot in the built-in conventions.
SLOT_HUES = {"primary": 210, "success": 120, "warning": 50, "accent": 30,
             "danger": 0, "secondary": 280}
SLOT_ORDER = ["primary", "success", "warning", "accent", "danger", "neutral", "secondary"]


def find_preset(name):
    """Resolve a preset name/path to its JSON dict (user dir, then built-ins)."""
    candidates = [name] if name.endswith(".json") else [
        os.path.expanduser(f"~/.drawio-skill/styles/{name.lower()}.json"),
        os.path.join(SKILL_DIR, "styles", "built-in", f"{name.lower()}.json"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as f:
                return json.load(f)
    builtin = os.path.join(SKILL_DIR, "styles", "built-in")
    known = sorted(f[:-5] for f in os.listdir(builtin) if f.endswith(".json"))
    sys.exit(f"error: preset '{name}' not found (built-ins: {', '.join(known)})")


def hue_slot(hexcolor, palette):
    """Nearest non-null palette slot for an existing fill color, by hue."""
    r, g, b = (int(hexcolor[i:i + 2], 16) / 255 for i in (1, 3, 5))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    if s < 0.15 or l > 0.97 or l < 0.03:                  # grey / near-white / near-black
        slot = "neutral"
    else:
        deg = h * 360
        slot = min(SLOT_HUES, key=lambda k: min(abs(deg - SLOT_HUES[k]),
                                                360 - abs(deg - SLOT_HUES[k])))
    if palette.get(slot):
        return slot
    for k in SLOT_ORDER:                                   # fallback ladder
        if palette.get(k):
            return k
    sys.exit("error: preset palette has no non-null slots")


def get_key(style, key):
    m = re.search(rf"(?:^|;){key}=([^;]*)", style)
    return m.group(1) if m else None


def set_keys(style, **kv):
    """Replace/insert style keys, dropping existing occurrences first."""
    for key in kv:
        style = re.sub(rf"(?:^|;){key}=[^;]*", "", style)
    style = style.strip("; ")
    tail = ";".join(f"{k}={v}" for k, v in kv.items() if v is not None)
    return (style + ";" if style else "") + tail + ";"


def main():
    p = argparse.ArgumentParser(description="Apply a style preset to an existing .drawio.")
    p.add_argument("file", help="input .drawio")
    p.add_argument("--preset", required=True, help="preset name (user or built-in) or JSON path")
    p.add_argument("-o", "--output", help="output path (default: <file>-<preset>.drawio)")
    args = p.parse_args()

    if not os.path.isfile(args.file):
        sys.exit(f"error: {args.file} not found")
    preset = find_preset(args.preset)
    palette, extras, font = preset["palette"], preset.get("extras", {}), preset["font"]

    vertex_extra = {"fontFamily": font["fontFamily"]}
    if extras.get("fontColor"):
        vertex_extra["fontColor"] = extras["fontColor"]
    if extras.get("sketch"):
        vertex_extra["sketch"] = "1"
    if extras.get("globalStrokeWidth") not in (None, 1):
        vertex_extra["strokeWidth"] = "%g" % extras["globalStrokeWidth"]

    tree = ET.parse(args.file)
    slot_map, n_vert, n_edge = {}, 0, 0
    for diagram in tree.getroot().iter("diagram"):
        model = diagram.find("mxGraphModel")
        root = model.find("root") if model is not None else None
        if root is None:
            sys.stderr.write(f"warning: skipping compressed page '{diagram.get('name', '?')}'\n")
            continue
        if extras.get("background"):
            model.set("background", extras["background"])
        for child in root:
            cell = child if child.tag == "mxCell" else child.find("mxCell")
            if cell is None:
                continue
            style = cell.get("style") or ""
            if cell.get("edge") == "1":
                kv = {}
                if extras.get("edgeColor"):
                    # labelBackgroundColor=none: the default white label box is
                    # unreadable under a light edgeColor on dark backgrounds
                    kv.update(strokeColor=extras["edgeColor"], fontColor=extras["edgeColor"],
                              labelBackgroundColor="none")
                if extras.get("sketch"):
                    kv["sketch"] = "1"
                if extras.get("globalStrokeWidth") not in (None, 1):
                    kv["strokeWidth"] = "%g" % extras["globalStrokeWidth"]
                if kv:
                    cell.set("style", set_keys(style, **kv))
                    n_edge += 1
                continue
            if cell.get("vertex") != "1":
                continue
            kv = dict(vertex_extra)
            fill = get_key(style, "fillColor")
            if fill and re.fullmatch(r"#[0-9A-Fa-f]{6}", fill):
                slot = slot_map.setdefault(fill.lower(), hue_slot(fill.lower(), palette))
                pair = palette[slot]
                kv.update(fillColor=pair["fillColor"], strokeColor=pair["strokeColor"])
            elif fill is None:
                # No fillColor -> draw.io default white fill. Keep its default
                # dark text: extras.fontColor would be unreadable on white.
                kv.pop("fontColor", None)
            cell.set("style", set_keys(style, **kv))
            n_vert += 1

    out = args.output or "%s-%s.drawio" % (os.path.splitext(args.file)[0],
                                           preset.get("name", "restyled"))
    tree.write(out, encoding="utf-8", xml_declaration=False)
    remap = ", ".join(f"{c}->{s}" for c, s in sorted(slot_map.items()))
    sys.stderr.write(f"wrote {out} ({n_vert} vertices, {n_edge} edges restyled"
                     + (f"; colors: {remap}" if remap else "") + ")\n")


if __name__ == "__main__":
    main()
