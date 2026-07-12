#!/usr/bin/env python3
"""poster.py — parametric academic-poster skeleton generator (.drawio).

One config JSON in, one page-exact .drawio out (plus a theme sidecar for retheme.py).
Layout is computed, never hand-placed: header band (logos / title / authors / QR),
optional full-width framework band, N columns of section cards (concept-icon +
title header, empty body group to fill), and a takeaway banner.

  python3 poster.py config.json -o poster.drawio [--no-icons]

Page math (verified on drawio desktop 26.x): plain `-x -f pdf` honors
pageWidth/pageHeight at 0.72 pt/px — a 48x36 in poster at 100 px/in (4800x3600 px)
exports to exactly 3456x2592 pt. Content past the page rect silently tiles onto
extra PDF pages, so keep everything inside (posterqa.py asserts this).

Config (all knobs optional; shown with defaults):

  {
    "page":     {"w_in": 48, "h_in": 36, "px_per_in": 100},
    "theme":    "crimson"                       // preset/theme name under ~/.drawio-skill/styles/
                or {"brand": "#C00C3C", "overrides": {"tint": "#F7E3E9"}},
    "knobs":    {"margin": 80, "gutter": 60, "pad": 40,
                 "header_h": 420, "framework_h": 900, "takeaway_h": 260,
                 "fs": {"title": 120, "authors": 56, "section": 64,
                        "body": 34, "caption": 26, "takeaway": 72}},
    "header":   {"title": "...", "authors": "...", "affils": "...",
                 "logo_left": "LOGO", "logo_right": null, "qr": true},
    "framework": {"title": "Framework", "slots": 3},   // or null to omit the band
    "columns":  [[{"title": "Motivation", "icon": "lightbulb", "weight": 1}, ...], ...],
    "takeaway": {"text": "One-sentence takeaway."}
  }

Column count = len(columns) — a pure knob (2 for policydissect-faithful, 3 default).
Section heights split the column by `weight`. Icons resolve via concepticons.py
(cached fetch; offline or --no-icons -> hairline placeholder slot, generation never
blocks on network). Every text cell carries fontSize + fontColor in the CELL style.

Font floors (warn here, hard-gated by posterqa.py): title>=100, section>=64,
body>=33, caption>=25 px at 100 px/in.
"""
import argparse
import importlib.util
import json
import os
import sys
from xml.sax.saxutils import escape, quoteattr

HERE = os.path.dirname(os.path.abspath(__file__))

FS_DEFAULT = {"title": 120, "authors": 56, "section": 64, "body": 34, "caption": 26, "takeaway": 72}
FS_FLOOR = {"title": 100, "section": 64, "body": 33, "caption": 25}
KNOBS_DEFAULT = {"margin": 80, "gutter": 60, "pad": 40,
                 "header_h": 420, "framework_h": 900, "takeaway_h": 260}


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def resolve_theme(cfg_theme):
    """Return extended theme dict (tokens + palette) from name / inline spec / default."""
    theme_mod = _load("theme")
    if isinstance(cfg_theme, str):
        for base in (os.path.join(os.path.expanduser("~"), ".drawio-skill", "styles"),):
            path = os.path.join(base, cfg_theme.lower() + ".theme.json")
            if os.path.isfile(path):
                with open(path, encoding="utf-8") as f:
                    return json.load(f)
        sys.exit("error: theme %r not found (expected %s.theme.json under ~/.drawio-skill/styles/; "
                 "create it with theme.py derive)" % (cfg_theme, cfg_theme.lower()))
    spec = cfg_theme or {}
    brand = spec.get("brand", "#C00C3C")
    _, theme = theme_mod.build_theme(brand, spec.get("overrides") or {})
    theme["name"] = spec.get("name", "inline")
    return theme


class Cells:
    def __init__(self):
        self.xml = []

    def add(self, cid, value, style, x, y, w, h, parent="1"):
        self.xml.append(
            '        <mxCell id=%s value=%s style=%s vertex="1" parent=%s>\n'
            '          <mxGeometry x="%g" y="%g" width="%g" height="%g" as="geometry" />\n'
            "        </mxCell>" % (quoteattr(cid), quoteattr(value), quoteattr(style),
                                   quoteattr(parent), x, y, w, h))

    def raw(self, cell_xml):
        self.xml.append("        " + cell_xml)


def text_style(fs, ink, bold=False, align="center", extra=""):
    return ("text;html=1;whiteSpace=wrap;align=%s;verticalAlign=middle;fontSize=%d;"
            "fontColor=%s;%s%s" % (align, fs, ink, "fontStyle=1;" if bold else "", extra))


def card_style(fill, stroke, arc=14):
    return ("rounded=1;arcSize=%d;whiteSpace=wrap;html=1;fillColor=%s;strokeColor=%s;"
            % (arc, fill, stroke))


def build(cfg, no_icons=False):
    """Return (drawio_xml, theme_dict, warnings)."""
    warnings = []
    page = {**{"w_in": 48, "h_in": 36, "px_per_in": 100}, **(cfg.get("page") or {})}
    W = int(page["w_in"] * page["px_per_in"])
    H = int(page["h_in"] * page["px_per_in"])
    knobs = {**KNOBS_DEFAULT, **(cfg.get("knobs") or {})}
    fs = {**FS_DEFAULT, **((cfg.get("knobs") or {}).get("fs") or {})}
    for k, floor in FS_FLOOR.items():
        if fs[k] < floor:
            warnings.append("fs.%s=%d below poster floor %d px" % (k, fs[k], floor))

    theme = resolve_theme(cfg.get("theme"))
    tok = theme["tokens"]
    brand, deep, tintc = tok["brand"], tok["deep"], tok["tint"]
    ink, gray, hair = tok["ink"], tok["gray"], tok["hair"]

    theme_mod = _load("theme")
    icons_mod = None if no_icons else _load("concepticons")
    max_off = max(max(dx, dy) for dx, dy, _ in theme_mod.SHADOW_LAYERS["soft"]) * (W / 1600.0)
    if knobs["margin"] < max_off:
        warnings.append("margin %g < max shadow offset %g at this canvas — shadow cells may "
                        "cross the page rect (posterqa/validate --page will flag them)"
                        % (knobs["margin"], max_off))

    M, GUT, PAD = knobs["margin"], knobs["gutter"], knobs["pad"]
    c = Cells()

    # ---- header band -------------------------------------------------------
    hy, hh = M, knobs["header_h"]
    hdr = cfg.get("header") or {}
    logo_w, logo_h = 400, 300
    if hdr.get("logo_left"):
        c.add("hdr-logo-l", escape(str(hdr["logo_left"])),
              card_style("#FFFFFF", hair) + "fontSize=%d;fontColor=%s;" % (fs["caption"], gray),
              M, hy + (hh - logo_h) / 2, logo_w, logo_h)
    if hdr.get("logo_right"):
        c.add("hdr-logo-r", escape(str(hdr["logo_right"])),
              card_style("#FFFFFF", hair) + "fontSize=%d;fontColor=%s;" % (fs["caption"], gray),
              W - M - logo_w, hy + (hh - logo_h) / 2, logo_w, logo_h)
    if hdr.get("qr"):
        qr = 260
        rx = W - M - logo_w - (GUT + qr if hdr.get("logo_right") else 0)
        if not hdr.get("logo_right"):
            rx = W - M - qr
        c.add("hdr-qr", "QR", card_style("#FFFFFF", hair) +
              "fontSize=%d;fontColor=%s;" % (fs["caption"], gray),
              rx, hy + (hh - qr) / 2, qr, qr)
    tx0 = M + (logo_w + GUT if hdr.get("logo_left") else 0)
    tx1 = W - M - ((logo_w + GUT) if hdr.get("logo_right") else 0) \
        - ((260 + GUT) if hdr.get("qr") else 0)
    c.add("hdr-title", escape(hdr.get("title", "Untitled Poster")),
          text_style(fs["title"], ink, bold=True), tx0, hy, tx1 - tx0, hh * 0.55)
    c.add("hdr-authors", "%s%s" % (escape(hdr.get("authors", "")),
                                   ("<br>" + escape(hdr.get("affils", ""))) if hdr.get("affils") else ""),
          text_style(fs["authors"], gray), tx0, hy + hh * 0.55, tx1 - tx0, hh * 0.45)
    c.add("hdr-rule", "", "line;strokeWidth=3;strokeColor=%s;html=1;" % brand,
          M, hy + hh + GUT / 2 - 2, W - 2 * M, 4)

    y = hy + hh + GUT

    # ---- framework band (optional) ----------------------------------------
    fw = cfg.get("framework")
    if fw:
        fh = knobs["framework_h"]
        for cell in theme_mod.shadow_cells(M, y, W - 2 * M, fh, style="soft", canvas=W,
                                           rx=14, id_prefix="fw-sh"):
            c.raw(cell)
        c.add("fw-band", "", card_style(tintc, brand), M, y, W - 2 * M, fh)
        c.add("fw-title", escape(fw.get("title", "Framework")),
              text_style(fs["section"], deep, bold=True, align="left"),
              M + PAD, y + PAD / 2, W - 2 * M - 2 * PAD, fs["section"] * 1.6)
        nslots = int(fw.get("slots") or 0)
        if nslots > 0:
            sy = y + PAD + fs["section"] * 1.6
            sh = fh - (sy - y) - PAD
            sw = (W - 2 * M - 2 * PAD - (nslots - 1) * GUT) / nslots
            for i in range(nslots):
                c.add("fw-slot%d" % (i + 1), "slot %d" % (i + 1),
                      card_style("#FFFFFF", hair) + "dashed=1;fontSize=%d;fontColor=%s;"
                      % (fs["caption"], gray),
                      M + PAD + i * (sw + GUT), sy, sw, sh)
        y += fh + GUT

    # ---- columns of section cards ------------------------------------------
    cols = cfg.get("columns") or []
    tk_h = knobs["takeaway_h"] if cfg.get("takeaway") else 0
    body_bottom = H - M - (tk_h + GUT if tk_h else 0)
    ncols = max(1, len(cols))
    col_w = (W - 2 * M - (ncols - 1) * GUT) / ncols
    icon_sz = int(fs["section"] * 1.25)
    for ci, sections in enumerate(cols):
        cx = M + ci * (col_w + GUT)
        weights = [max(0.1, float(s.get("weight", 1))) for s in sections]
        avail = body_bottom - y - GUT * (len(sections) - 1)
        if avail <= 0:
            sys.exit("error: no vertical room for column %d sections — reduce header/framework/"
                     "takeaway heights or margins" % (ci + 1))
        sy = y
        for si, sec in enumerate(sections):
            sh = avail * weights[si] / sum(weights)
            cid = "c%ds%d" % (ci + 1, si + 1)
            for cell in theme_mod.shadow_cells(cx, sy, col_w, sh, style="soft", canvas=W,
                                               rx=14, id_prefix=cid + "-sh"):
                c.raw(cell)
            c.add(cid + "-card", "", card_style("#FFFFFF", hair), cx, sy, col_w, sh)
            # header row: icon + title + hairline
            ic_x, ic_y = cx + PAD, sy + PAD
            icon_style = None
            if sec.get("icon_style"):
                icon_style = sec["icon_style"]
            elif sec.get("icon") and icons_mod:
                try:
                    idx = icons_mod.load_index()
                    icon_name = sec["icon"]
                    icon_weight = sec.get("icon_weight", "regular")
                    # Validate against the index like the concepticons CLI does —
                    # these strings become a cache path and a URL path segment.
                    if icon_name not in set(idx["names"]) or icon_weight not in icons_mod.WEIGHTS:
                        raise ValueError("unknown icon %r / weight %r (see "
                                         "concepticons.py search)" % (icon_name, icon_weight))
                    svg = icons_mod.fetch_svg(icon_name, icon_weight, idx["cdn"])
                    icon_style = icons_mod.STYLE + icons_mod.icon_uri(svg, brand) + ";"
                except Exception as exc:  # noqa: BLE001 - offline must not block generation
                    warnings.append("icon %r fetch failed (%s) — placeholder emitted"
                                    % (sec["icon"], exc))
            if icon_style:
                c.add(cid + "-icon", "", icon_style, ic_x, ic_y, icon_sz, icon_sz)
            elif sec.get("icon"):
                c.add(cid + "-icon", escape(str(sec["icon"])),
                      card_style("#FFFFFF", hair) + "dashed=1;fontSize=%d;fontColor=%s;"
                      % (fs["caption"], gray),
                      ic_x, ic_y, icon_sz, icon_sz)
            tx = ic_x + (icon_sz + PAD / 2 if sec.get("icon") or sec.get("icon_style") else 0)
            c.add(cid + "-title", escape(sec.get("title", "Section")),
                  text_style(fs["section"], deep, bold=True, align="left"),
                  tx, ic_y, cx + col_w - PAD - tx, icon_sz)
            rule_y = ic_y + icon_sz + PAD / 2
            c.add(cid + "-rule", "", "line;strokeWidth=2;strokeColor=%s;html=1;" % hair,
                  cx + PAD, rule_y, col_w - 2 * PAD, 3)
            # empty body group: children use coordinates relative to this group
            body_h = sy + sh - PAD - (rule_y + PAD / 2)
            if body_h <= 0:
                warnings.append("section %s body height %g <= 0 — its card is too "
                                "short for the icon+title header; give the section "
                                "more weight or the page more room" % (cid, body_h))
            c.add(cid + "-body", "", "group;pointerEvents=0;",
                  cx + PAD, rule_y + PAD / 2, col_w - 2 * PAD, body_h)
            sy += sh + GUT

    # ---- takeaway banner ----------------------------------------------------
    tk = cfg.get("takeaway")
    if tk:
        ty = H - M - tk_h
        for cell in theme_mod.shadow_cells(M, ty, W - 2 * M, tk_h, style="soft", canvas=W,
                                           rx=14, id_prefix="tk-sh"):
            c.raw(cell)
        # White text needs a dark-enough band; a light brand (e.g. #FFE45E) makes
        # white unreadable — fall back to ink and say so.
        band_fg = "#FFFFFF"
        if theme_mod.contrast(brand, "#FFFFFF") < 3.0:
            band_fg = ink
            warnings.append("brand %s is too light for white takeaway text "
                            "(contrast %.2f < 3.0) — using ink %s instead"
                            % (brand, theme_mod.contrast(brand, "#FFFFFF"), ink))
        c.add("tk-band", escape(tk.get("text", "")),
              card_style(brand, deep) + "fontSize=%d;fontColor=%s;fontStyle=1;align=center;"
              "verticalAlign=middle;" % (fs["takeaway"], band_fg),
              M, ty, W - 2 * M, tk_h)

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<mxfile host="drawio" version="26.0.0">\n'
        '  <diagram name="poster">\n'
        '    <mxGraphModel dx="0" dy="0" grid="0" gridSize="10" guides="1" tooltips="1" '
        'connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="%d" '
        'pageHeight="%d" math="0" shadow="0">\n'
        "      <root>\n"
        '        <mxCell id="0" />\n'
        '        <mxCell id="1" parent="0" />\n'
        "%s\n"
        "      </root>\n"
        "    </mxGraphModel>\n"
        "  </diagram>\n"
        "</mxfile>\n" % (W, H, "\n".join(c.xml))
    )
    return xml, theme, warnings


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("config", help="poster config JSON")
    p.add_argument("-o", "--out", required=True, help="output .drawio path")
    p.add_argument("--no-icons", action="store_true", help="emit placeholder icon slots, no network")
    args = p.parse_args(argv)

    try:
        with open(args.config, encoding="utf-8") as f:
            cfg = json.load(f)
    except (OSError, ValueError) as exc:
        sys.exit("error: cannot read config %s: %s" % (args.config, exc))
    xml, theme, warnings = build(cfg, no_icons=args.no_icons)
    outdir = os.path.dirname(os.path.abspath(args.out))
    os.makedirs(outdir, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(xml)
    sidecar = os.path.splitext(args.out)[0] + ".theme.json"
    with open(sidecar, "w", encoding="utf-8") as f:
        json.dump(theme, f, indent=2)
        f.write("\n")
    for w in warnings:
        print("warning: %s" % w, file=sys.stderr)
    print(args.out)
    print(sidecar)


if __name__ == "__main__":
    main()
