#!/usr/bin/env python3
"""Find CONCEPT icons (shield, brain, flask, gear, ...) as self-contained draw.io styles.

Complements aiicons.py (brand logos): this resolves a concept keyword to a Phosphor
icon (https://phosphoricons.com, MIT, 1512 glyphs) and emits a draw.io `image` style
with the SVG inlined as a url-encoded data URI and the ink color BAKED INTO the SVG.

Why baked: draw.io renders embedded SVG without CSS, so `fill` must live inside the
SVG itself. The payload is URL-ENCODED here; marker-less base64 after the comma
(`data:image/svg+xml,<b64>`, aiicons.py's form) also renders. What breaks is a
literal `;base64,` MARKER — its `;` splits draw.io's `key=value;` style parser
and the icon renders blank (verified on drawio 30.2.4).

Every glyph exists in two weights — `regular` (line) and `fill` (solid). Both are
first-class; pick per figure with --weight.

  python3 concepticons.py search "shield security"
  python3 concepticons.py style shield-check --weight fill --ink "#C00C3C" --size 48
  python3 concepticons.py style brain --weight regular --json

Fetches are cached under $CC_CACHE_ROOT/drawio-skill/phosphor/ (fallback
~/.cache/drawio-skill/phosphor/), so a glyph is downloaded once per machine.
--svg-file bypasses the network entirely (useful offline / for tests).
"""
import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request

INDEX = os.path.join(os.path.dirname(__file__), "..", "data", "phosphor-index.json")
STYLE = ("shape=image;html=1;imageAspect=0;aspect=fixed;"
         "verticalLabelPosition=bottom;verticalAlign=top;image=")
WEIGHTS = ("regular", "fill")

_XMLDECL = re.compile(r"<\?xml.*?\?>", re.S)
_COMMENT = re.compile(r"<!--.*?-->", re.S)
_ROOTWH = re.compile(r'\s+(?:width|height)="[^"]*"')
_ROOTFILL = re.compile(r'\s+fill="[^"]*"')


def load_index():
    with open(INDEX, encoding="utf-8") as f:
        return json.load(f)


def search(names, query, limit=10):
    """Rank icon names against space-separated query tokens."""
    toks = [t for t in re.split(r"[\s_-]+", query.lower()) if t]
    if not toks:
        return []
    scored = []
    for name in names:
        parts = name.split("-")
        score = 0
        hit = 0
        for t in toks:
            if t == name:
                score += 60
                hit += 1
            elif t in parts:
                score += 40
                hit += 1
            elif any(p.startswith(t) for p in parts):
                score += 15
                hit += 1
            elif t in name:
                score += 5
                hit += 1
        if hit == len(toks):
            score += 30  # every query token matched somewhere in this name
        if score:
            scored.append((-score, name))
    scored.sort()
    return [n for _, n in scored[:limit]]


def bake_ink(svg, ink):
    """Strip decl/comments/root width+height; force root fill=<ink> (replace currentColor)."""
    s = _XMLDECL.sub("", svg)
    s = _COMMENT.sub("", s)

    def fix_root(m):
        tag = _ROOTWH.sub("", m.group(0))
        tag = _ROOTFILL.sub("", tag)
        return tag[:-1] + ' fill="%s">' % ink

    return re.sub(r"<svg\b[^>]*>", fix_root, s, count=1).strip()


def icon_uri(svg, ink):
    return "data:image/svg+xml," + urllib.parse.quote(bake_ink(svg, ink), safe="")


def _cache_dir():
    root = os.environ.get("CC_CACHE_ROOT") or os.path.join(os.path.expanduser("~"), ".cache")
    return os.path.join(root, "drawio-skill", "phosphor")


def fetch_svg(name, weight, cdn):
    fname = name + ("-fill" if weight == "fill" else "") + ".svg"
    cpath = os.path.join(_cache_dir(), weight, fname)
    if os.path.isfile(cpath):
        with open(cpath, encoding="utf-8") as f:
            return f.read()
    url = cdn + weight + "/" + fname
    svg = urllib.request.urlopen(url, timeout=15).read().decode("utf-8")
    os.makedirs(os.path.dirname(cpath), exist_ok=True)
    with open(cpath, "w", encoding="utf-8") as f:
        f.write(svg)
    return svg


def _cmd_search(args):
    idx = load_index()
    hits = search(idx["names"], args.query, args.limit)
    if not hits:
        sys.exit("no icon matches %r — try broader tokens (e.g. 'shield', 'chart')" % args.query)
    for h in hits:
        print(h)


def _cmd_style(args):
    idx = load_index()
    if args.name not in set(idx["names"]):
        hint = ", ".join(search(idx["names"], args.name, 5)) or "run: concepticons.py search <keywords>"
        sys.exit("unknown icon %r — close matches: %s" % (args.name, hint))
    if args.svg_file:
        with open(args.svg_file, encoding="utf-8") as f:
            svg = f.read()
    else:
        try:
            svg = fetch_svg(args.name, args.weight, idx["cdn"])
        except Exception as exc:  # noqa: BLE001 - offline is an expected mode
            sys.exit("fetch failed for %s/%s (%s) — offline? Pass --svg-file <local.svg>"
                     % (args.weight, args.name, exc))
    style = STYLE + icon_uri(svg, args.ink) + ";"
    rec = {"name": args.name, "weight": args.weight, "ink": args.ink,
           "w": args.size, "h": args.size, "style": style}
    if args.json:
        print(json.dumps(rec, indent=2))
    else:
        print(style)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="rank icon names for keywords")
    s.add_argument("query")
    s.add_argument("--limit", type=int, default=10)
    s.set_defaults(fn=_cmd_search)

    t = sub.add_parser("style", help="emit a baked-ink draw.io style for an icon")
    t.add_argument("name", help="exact icon name (see search)")
    t.add_argument("--weight", choices=WEIGHTS, default="regular",
                   help="line (regular) or solid (fill) — both first-class")
    t.add_argument("--ink", default="#141414", help="baked fill color (#RRGGBB)")
    t.add_argument("--size", type=int, default=48, help="suggested square size (px)")
    t.add_argument("--svg-file", help="use a local SVG instead of fetching (offline/tests)")
    t.add_argument("--json", action="store_true")
    t.set_defaults(fn=_cmd_style)

    args = p.parse_args(argv)
    if not re.match(r"^#[0-9A-Fa-f]{6}$", getattr(args, "ink", "#000000")):
        sys.exit("--ink must be #RRGGBB")
    args.fn(args)


if __name__ == "__main__":
    main()
