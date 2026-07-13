#!/usr/bin/env python3
"""Swap every label in a .drawio via a mapping — layout, styles, ids untouched.

The main use-case is language variants of one diagram (EN <-> CN docs figures):
extract the labels, translate the values, apply the map — the geometry never
moves, so both variants stay pixel-identical except for the text.

  python3 relabel.py diagram.drawio --extract -o labels.json     # step 1
  # edit labels.json: keep keys, replace each value with the new text
  python3 relabel.py diagram.drawio --map labels.json -o diagram_cn.drawio

Extract emits an identity JSON map {"label": "label", ...} of every non-empty
vertex/edge label, UserObject label, and page name, in document order. Apply
replaces each label that exactly matches a map key (raw string, HTML markup
included) and reports what matched. Unmapped labels stay unchanged; map keys
that matched nothing are listed on stderr so translations don't silently miss.

Usage: relabel.py <file.drawio> (--extract | --map <labels.json>) [-o <out>]
"""
import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET


def label_slots(tree):
    """Yield (element, attribute) for every label-bearing slot in the file."""
    for diagram in tree.getroot().iter("diagram"):
        if diagram.get("name"):
            yield diagram, "name"
        model = diagram.find("mxGraphModel")
        root = model.find("root") if model is not None else None
        if root is None:                       # compressed page — can't edit
            sys.stderr.write("warning: skipping compressed page "
                             f"'{diagram.get('name', '?')}' (open+save in draw.io to decompress)\n")
            continue
        for child in root:
            if child.tag == "mxCell":
                if child.get("value"):
                    yield child, "value"
            elif child.tag in ("UserObject", "object"):
                if child.get("label"):
                    yield child, "label"
                inner = child.find("mxCell")
                if inner is not None and inner.get("value"):
                    yield inner, "value"


def main():
    p = argparse.ArgumentParser(description="Extract or swap .drawio labels via a JSON map.")
    p.add_argument("file", help="input .drawio")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--extract", action="store_true",
                      help="dump an identity label map as JSON")
    mode.add_argument("--map", metavar="JSON", dest="mapfile",
                      help="JSON map {old label: new label} to apply")
    p.add_argument("-o", "--output", help="output path (default: stdout for --extract, "
                                          "<file>-relabel.drawio for --map)")
    args = p.parse_args()

    if not os.path.isfile(args.file):
        sys.exit(f"error: {args.file} not found")
    tree = ET.parse(args.file)

    if args.extract:
        seen = {}
        for el, attr in label_slots(tree):
            seen.setdefault(el.get(attr), el.get(attr))
        out = json.dumps(seen, ensure_ascii=False, indent=2)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(out + "\n")
            sys.stderr.write(f"wrote {args.output} ({len(seen)} labels)\n")
        else:
            print(out)
        return

    with open(args.mapfile, encoding="utf-8") as f:
        mapping = json.load(f)
    if not isinstance(mapping, dict):
        sys.exit("error: map file must be a JSON object {old: new}")

    matched, used = 0, set()
    for el, attr in label_slots(tree):
        old = el.get(attr)
        if old in mapping:
            el.set(attr, str(mapping[old]))
            matched += 1
            used.add(old)

    out = args.output or os.path.splitext(args.file)[0] + "-relabel.drawio"
    tree.write(out, encoding="utf-8", xml_declaration=False)
    unused = [k for k in mapping if k not in used]
    if unused:
        sys.stderr.write("warning: %d map key(s) matched no label: %s\n"
                         % (len(unused), ", ".join(repr(k)[:60] for k in unused[:10])))
    sys.stderr.write(f"wrote {out} ({matched} labels replaced)\n")


if __name__ == "__main__":
    main()
