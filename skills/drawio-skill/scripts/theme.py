#!/usr/bin/env python3
"""theme.py — derive a full drawio-skill preset (+ extended theme tokens) from ONE brand hex,
and emit soft-shadow backing-cell XML.

Subcommands:
  derive <brand-hex> --name <name> [--out-dir DIR] [--override key=hex ...] [--stdout]
      Writes <name>.json        (preset, validates against styles/schema.json conventions)
         and <name>.theme.json  (extended tokens: brand/deep/tint/ink/gray/hair + slot snapshot).
      Override keys: tokens (deep, tint, ink, gray, hair) or slot colors
      (primary.fill, danger.stroke, ...). Example — pinning an exact crimson brand ramp:
        theme.py derive "#C00C3C" --name crimson \
          --override deep=#8A0A2B --override tint=#F7E3E9 \
          --override ink=#141414 --override gray=#5A6672 --override hair=#D8DEE4

  shadow --style soft|softer [--canvas 4800] [--x X --y Y --w W --h H] [--rx 12] [--id-prefix sh]
      Prints stacked backing-cell mxCell XML (place BEFORE the card cell so it renders behind).
      Offsets/opacity scale linearly with --canvas (reference canvas 1600).

Stdlib only. Deterministic. Both files are plain JSON — safe to hand-edit.
"""
import argparse
import colorsys
import json
import os
import re
import sys

HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")

# Fixed, brand-independent defaults (overridable): academic-muted semantics + grayscale.
DEFAULT_TOKENS = {
    "ink": "#141414",      # global text color
    "gray": "#5A6672",     # neutral stroke / secondary text
    "hair": "#D8DEE4",     # hairline rules / subtle borders
}
SEMANTIC_STROKES = {
    "success": "#2F7D4F",
    "warning": "#B07C1F",
    "danger": "#A93226",
}
TINT_F = 0.12      # fill = brand mixed 12% into white
SHADE_F = 0.28     # deep = brand mixed 28% toward black
NEUTRAL_TINT_F = 0.10


def _rgb(hexs):
    hexs = hexs.lstrip("#")
    return tuple(int(hexs[i:i + 2], 16) for i in (0, 2, 4))


def _hex(rgb):
    return "#%02X%02X%02X" % tuple(max(0, min(255, round(c))) for c in rgb)


def tint(hexs, f):
    """Mix color f-fraction over white: f=0.12 -> 12% color, 88% white."""
    r, g, b = _rgb(hexs)
    return _hex((r * f + 255 * (1 - f), g * f + 255 * (1 - f), b * f + 255 * (1 - f)))


def shade(hexs, f):
    """Mix color toward black by f: f=0.28 -> keep 72% of each channel."""
    r, g, b = _rgb(hexs)
    k = 1 - f
    return _hex((r * k, g * k, b * k))


def desaturate(hexs, keep=0.30):
    """Keep `keep` of the saturation, same hue/lightness."""
    r, g, b = (c / 255 for c in _rgb(hexs))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    r2, g2, b2 = colorsys.hls_to_rgb(h, l, s * keep)
    return _hex((r2 * 255, g2 * 255, b2 * 255))


def luminance(hexs):
    """WCAG relative luminance of #RRGGBB (0=black, 1=white)."""
    def chan(c):
        c /= 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (chan(c) for c in _rgb(hexs))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    """WCAG contrast ratio between two #RRGGBB colors (1..21)."""
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def build_theme(brand, overrides=None):
    """Return (preset_dict, theme_dict). overrides: {key: hex} for tokens or slot colors."""
    overrides = dict(overrides or {})
    if not HEX_RE.match(brand):
        raise ValueError("brand must be #RRGGBB, got %r" % brand)

    tokens = {
        "brand": brand,
        "deep": overrides.pop("deep", shade(brand, SHADE_F)),
        "tint": overrides.pop("tint", tint(brand, TINT_F)),
        "ink": overrides.pop("ink", DEFAULT_TOKENS["ink"]),
        "gray": overrides.pop("gray", DEFAULT_TOKENS["gray"]),
        "hair": overrides.pop("hair", DEFAULT_TOKENS["hair"]),
    }
    for k, v in tokens.items():
        if not HEX_RE.match(v):
            raise ValueError("token %s must be #RRGGBB, got %r" % (k, v))

    muted = desaturate(brand)
    palette = {
        "primary": {"fillColor": tokens["tint"], "strokeColor": brand},
        "accent": {"fillColor": tint(tokens["deep"], TINT_F), "strokeColor": tokens["deep"]},
        "secondary": {"fillColor": tint(muted, TINT_F), "strokeColor": muted},
        "neutral": {"fillColor": tint(tokens["gray"], NEUTRAL_TINT_F), "strokeColor": tokens["gray"]},
    }
    for slot, stroke in SEMANTIC_STROKES.items():
        palette[slot] = {"fillColor": tint(stroke, TINT_F), "strokeColor": stroke}

    # Slot-color overrides: primary.fill=#..., danger.stroke=#...
    for key, val in overrides.items():
        m = re.match(r"^(primary|success|warning|accent|danger|neutral|secondary)\.(fill|stroke)$", key)
        if not m:
            raise ValueError("unknown override key %r" % key)
        if not HEX_RE.match(val):
            raise ValueError("override %s must be #RRGGBB, got %r" % (key, val))
        palette[m.group(1)]["fillColor" if m.group(2) == "fill" else "strokeColor"] = val

    preset = {
        "$schema": "https://github.com/Agents365-ai/drawio-skill/styles/schema.json",
        "name": None,  # filled by caller
        "version": 1,
        "default": False,
        "source": {"type": "hand-authored"},
        "confidence": "high",
        "palette": palette,
        "roles": {
            "service": "primary", "database": "success", "queue": "warning",
            "gateway": "accent", "error": "danger", "external": "neutral",
            "security": "secondary",
        },
        "shapes": {
            "service": "rounded=1", "database": "shape=cylinder3", "queue": "rounded=1",
            "decision": "rhombus", "external": "rounded=1;dashed=1",
            "container": "swimlane;startSize=30",
        },
        "font": {"fontFamily": "Helvetica", "fontSize": 12, "titleFontSize": 14, "titleBold": True},
        "edges": {
            "style": "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1",
            "arrow": "endArrow=classic;endFill=1",
            "dashedFor": [],
        },
        "extras": {"sketch": False, "globalStrokeWidth": 1},
    }
    theme = {
        "version": 1,
        "name": None,  # filled by caller
        "tokens": tokens,
        "palette": {k: dict(v) for k, v in palette.items()},
    }
    return preset, theme


# Shadow presets: list of (dx, dy, opacity) at reference canvas 1600px wide.
SHADOW_LAYERS = {
    "soft": [(3, 4, 6), (6, 8, 4), (9, 12, 2)],
    "softer": [(2, 3, 4), (5, 7, 2)],
}


def shadow_cells(x, y, w, h, style="soft", canvas=1600, rx=12, id_prefix="sh", parent="1"):
    """Return list of mxCell XML strings for stacked soft-shadow backing cells.

    Emit these BEFORE the card cell (draw.io paints in document order).
    Offsets scale linearly with canvas width vs the 1600px reference.
    """
    if style not in SHADOW_LAYERS:
        raise ValueError("style must be one of %s" % sorted(SHADOW_LAYERS))
    k = canvas / 1600.0
    cells = []
    # Deepest (largest offset, faintest) first so closer layers paint on top.
    for i, (dx, dy, op) in enumerate(reversed(SHADOW_LAYERS[style])):
        cells.append(
            '<mxCell id="%s%d" value="" style="rounded=1;arcSize=%d;fillColor=#000000;'
            'strokeColor=none;opacity=%d;" vertex="1" parent="%s">'
            '<mxGeometry x="%g" y="%g" width="%g" height="%g" as="geometry" /></mxCell>'
            % (id_prefix, i, rx, op, parent, x + dx * k, y + dy * k, w, h)
        )
    return cells


def _cmd_derive(args):
    overrides = {}
    for ov in args.override or []:
        if "=" not in ov:
            sys.exit("--override expects key=hex, got %r" % ov)
        k, v = ov.split("=", 1)
        overrides[k.strip()] = v.strip()
    try:
        preset, theme = build_theme(args.brand, overrides)
    except ValueError as e:
        sys.exit("error: %s" % e)
    name = args.name.lower()
    if not re.match(r"^[a-z0-9][a-z0-9_-]*$", name):
        sys.exit("error: name must be lowercase [a-z0-9_-], got %r" % name)
    preset["name"] = name
    theme["name"] = name
    if args.stdout:
        json.dump({"preset": preset, "theme": theme}, sys.stdout, indent=2)
        print()
        return
    out = args.out_dir or os.path.join(os.path.expanduser("~"), ".drawio-skill", "styles")
    os.makedirs(out, exist_ok=True)
    ppath = os.path.join(out, name + ".json")
    tpath = os.path.join(out, name + ".theme.json")
    for path, obj in ((ppath, preset), (tpath, theme)):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2)
            f.write("\n")
    print(ppath)
    print(tpath)


def _cmd_shadow(args):
    for c in shadow_cells(args.x, args.y, args.w, args.h, style=args.style,
                          canvas=args.canvas, rx=args.rx, id_prefix=args.id_prefix):
        print(c)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("derive", help="brand hex -> preset + theme JSON")
    d.add_argument("brand", help="#RRGGBB brand color")
    d.add_argument("--name", required=True, help="preset name (lowercase)")
    d.add_argument("--out-dir", help="output dir (default ~/.drawio-skill/styles)")
    d.add_argument("--override", action="append", metavar="KEY=HEX",
                   help="token (deep|tint|ink|gray|hair) or slot color (primary.fill, danger.stroke, ...)")
    d.add_argument("--stdout", action="store_true", help="print JSON instead of writing files")
    d.set_defaults(fn=_cmd_derive)

    s = sub.add_parser("shadow", help="print soft-shadow backing-cell XML")
    s.add_argument("--style", choices=sorted(SHADOW_LAYERS), default="soft")
    s.add_argument("--canvas", type=float, default=1600, help="canvas width px (scales offsets)")
    s.add_argument("--x", type=float, default=0)
    s.add_argument("--y", type=float, default=0)
    s.add_argument("--w", type=float, default=400)
    s.add_argument("--h", type=float, default=200)
    s.add_argument("--rx", type=int, default=12, help="arcSize matching the card")
    s.add_argument("--id-prefix", default="sh")
    s.set_defaults(fn=_cmd_shadow)

    args = p.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
