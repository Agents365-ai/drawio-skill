#!/usr/bin/env python3
"""posterqa.py — one gate for print-ready poster exports.

Runs the checks that make a 48x36 (or any page-exact) poster safe to send to print:

  1. PDF page count == 1        — content past the page rect silently TILES onto
                                  extra pages; a "48x36 poster" PDF with 4 pages
                                  is the classic silent failure.
  2. PDF page size exact        — expected pt = pageWidth/pageHeight px * 0.72
                                  (verified mapping on drawio desktop 26.x), +/-1 pt.
  3. Geometry bounds            — validate.py --page WxH --margin N (absolute
                                  coordinates, container-relative resolved).
  4. Font floor                 — any non-empty text cell with fontSize < --min-font
                                  fails (print safety); per-class poster floors
                                  (title/section/body/caption) reported as warnings
                                  for poster.py-generated ids.
  5. Preview render (optional)  — --preview out.png exports a width-capped PNG
                                  (no -e) for the vision self-check loop.

  python3 posterqa.py poster.drawio --pdf poster.pdf [--margin 40] [--min-font 25]
                                    [--preview preview.png] [--drawio BIN]

Exit non-zero on any hard failure (1/2/3/4). Page size is read from the .drawio
mxGraphModel pageWidth/pageHeight. pdfinfo is used when present, else the PDF's
MediaBox is parsed directly.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
PT_PER_PX = 0.72
POSTER_FLOORS = {"title": 100, "section": 64, "body": 33, "caption": 25}
ID_CLASS = (("hdr-title", "title"), ("-title", "section"), ("hdr-authors", "body"),
            ("tk-band", "body"), ("hdr-logo-l", "caption"), ("hdr-logo-r", "caption"),
            ("hdr-qr", "caption"), ("-icon", "caption"))


def read_page_px(drawio_path):
    try:
        tree = ET.parse(drawio_path)
    except (ET.ParseError, OSError) as exc:
        sys.exit("error: cannot parse %s: %s" % (drawio_path, exc))
    model = tree.getroot().find(".//mxGraphModel")
    if model is None:
        sys.exit("error: no mxGraphModel in %s (compressed? re-save uncompressed)" % drawio_path)
    try:
        return float(model.get("pageWidth")), float(model.get("pageHeight")), tree
    except (TypeError, ValueError):
        sys.exit("error: %s has no numeric pageWidth/pageHeight — poster files must set them"
                 % drawio_path)


def pdf_pages_and_size(pdf_path):
    """Return (n_pages, w_pt, h_pt) via pdfinfo, falling back to raw MediaBox parse."""
    if shutil.which("pdfinfo") and not os.environ.get("POSTERQA_NO_PDFINFO"):
        out = subprocess.run(["pdfinfo", pdf_path], capture_output=True, text=True).stdout
        mp = re.search(r"^Pages:\s+(\d+)", out, re.M)
        ms = re.search(r"^Page size:\s+([\d.]+) x ([\d.]+)", out, re.M)
        if mp and ms:
            return int(mp.group(1)), float(ms.group(1)), float(ms.group(2))
        sys.exit("error: pdfinfo could not read %s — is it a valid PDF?" % pdf_path)
    # Best-effort fallback: counts literal /Type /Page objects; a PDF that stores
    # its page tree inside compressed object streams undercounts here — prefer
    # pdfinfo (poppler) for authoritative gating.
    with open(pdf_path, "rb") as f:
        raw = f.read()
    pages = len(re.findall(rb"/Type\s*/Page\b(?!s)", raw))
    m = re.search(rb"/MediaBox\s*\[\s*[\d.]+\s+[\d.]+\s+([\d.]+)\s+([\d.]+)", raw)
    if not m:
        sys.exit("error: cannot read MediaBox from %s (install pdfinfo for robust parsing)"
                 % pdf_path)
    return pages, float(m.group(1)), float(m.group(2))


def check_fonts(tree, min_font):
    """Return (fails, warns) for text-bearing cells below floors."""
    fails, warns = [], []
    for c in tree.getroot().iter("mxCell"):
        value = (c.get("value") or "").strip()
        style = c.get("style") or ""
        if not value:
            continue
        cid = c.get("id") or "?"
        m = re.search(r"fontSize=(\d+)", style)
        if m:
            fs = int(m.group(1))
        else:
            # No fontSize in the CELL style: draw.io renders at its default 12 px
            # (HTML span sizes don't vertically center and previously slipped past
            # this gate entirely — the likeliest state of hand-filled body cells).
            spans = [int(s) for s in re.findall(r"font-size:\s*(\d+)", value)]
            fs = max(spans) if spans else 12
            if spans:
                warns.append("cell %r sizes text only in an HTML span (%d px) — put "
                             "fontSize in the cell style or the text centers wrong"
                             % (cid, fs))
        if fs < min_font:
            fails.append("cell %r fontSize=%d < hard floor %d%s"
                         % (cid, fs, min_font,
                            "" if m else " (no cell-style fontSize — draw.io default)"))
            continue
        for suffix, cls in ID_CLASS:
            if cid.endswith(suffix) or cid == suffix:
                floor = POSTER_FLOORS[cls]
                if fs < floor:
                    warns.append("cell %r (%s) fontSize=%d < poster %s floor %d"
                                 % (cid, cls, fs, cls, floor))
                break
    return fails, warns


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("drawio", help="poster .drawio (uncompressed, pageWidth/pageHeight set)")
    p.add_argument("--pdf", help="exported PDF to verify (skip PDF checks if omitted)")
    p.add_argument("--margin", type=float, default=40, help="page-margin intrusion warning band")
    p.add_argument("--min-font", type=int, default=25, help="hard fail below this fontSize")
    p.add_argument("--preview", metavar="PNG", help="also export a width-capped preview PNG")
    p.add_argument("--preview-width", type=int, default=2000)
    p.add_argument("--drawio-bin", default="drawio", help="draw.io CLI binary for --preview")
    args = p.parse_args(argv)

    fails, warns = [], []
    pw, ph, tree = read_page_px(args.drawio)

    if args.pdf:
        if not os.path.isfile(args.pdf):
            sys.exit("error: no such PDF: %s" % args.pdf)
        pages, w_pt, h_pt = pdf_pages_and_size(args.pdf)
        exp_w, exp_h = pw * PT_PER_PX, ph * PT_PER_PX
        if pages != 1:
            fails.append("PDF has %d pages (content outside the page rect tiles onto "
                         "extra pages) — expected exactly 1" % pages)
        if abs(w_pt - exp_w) > 1 or abs(h_pt - exp_h) > 1:
            fails.append("PDF page %.2fx%.2f pt != expected %.2fx%.2f pt "
                         "(%gx%g px * %.2f) — was it exported with --crop?"
                         % (w_pt, h_pt, exp_w, exp_h, pw, ph, PT_PER_PX))

    r = subprocess.run([sys.executable, os.path.join(HERE, "validate.py"), args.drawio,
                        "--page", "%gx%g" % (pw, ph), "--margin", str(args.margin)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        fails.append("validate.py --page failed:\n" + (r.stdout + r.stderr).strip())
    else:
        for line in r.stdout.splitlines():
            if line.startswith("warning:") and "margin" in line:
                warns.append(line[len("warning: "):])

    ffails, fwarns = check_fonts(tree, args.min_font)
    fails += ffails
    warns += fwarns

    if args.preview:
        cmd = [args.drawio_bin, "-x", "-f", "png", "--width", str(args.preview_width),
               "-o", args.preview, args.drawio]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0 or not os.path.isfile(args.preview):
            warns.append("preview export failed: %s" % (r.stderr.strip() or r.stdout.strip()))
        else:
            print("preview: %s" % args.preview)

    for w in warns:
        print("warning: %s" % w)
    for f_ in fails:
        print("FAIL: %s" % f_)
    print("%d failure(s), %d warning(s)" % (len(fails), len(warns)))
    if fails:
        sys.exit(1)


if __name__ == "__main__":
    main()
