#!/usr/bin/env python3
"""Read a .drawio and describe it as structured Markdown.

The inverse of the skill's generators: instead of data -> diagram, this turns a
diagram -> documentation. It lists the components (grouped by their container /
swimlane / tier), the relations between them (edge labels become the relation
verb), and a per-page breakdown for multi-page files (e.g. a C4 model). Handy
for dropping an architecture summary into a README or PR, or for a text-only
description of a diagram someone handed you.

  python3 explain.py architecture.drawio            # Markdown to stdout
  python3 explain.py c4.drawio -o architecture.md

Components are the leaf vertices; a vertex that contains others is treated as a
container and becomes a grouping heading. Relations read `source -> target`,
annotated with the edge label when present. A handful of common shapes are
named (data store, actor, decision, queue, cloud, and AWS/Azure/GCP/Kubernetes
vendor icons). UserObject/object wrappers are unwrapped; compressed pages are
reported but cannot be described (this skill always writes uncompressed XML).

Usage: python3 explain.py <file.drawio> [-o out.md]
"""
import argparse
import html
import re
import sys
import xml.etree.ElementTree as ET

# style fragment -> human noun. First match wins; order matters (specific first).
SHAPE_TYPES = [
    ("mxgraph.aws", "AWS"), ("img/lib/azure", "Azure"), ("mxgraph.gcp", "GCP"),
    ("mxgraph.kubernetes", "Kubernetes"), ("umlActor", "actor"), ("shape=actor", "actor"),
    ("shape=cylinder", "data store"), ("shape=datastore", "data store"),
    ("shape=cloud", "cloud"), ("rhombus", "decision"), ("mscae", "Azure"),
    ("shape=process", "process"), ("shape=hexagon", "queue"),
]


def clean(text):
    """Strip HTML tags/entities draw.io stores in labels; collapse whitespace."""
    if not text:
        return ""
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def shape_of(style):
    for frag, noun in SHAPE_TYPES:
        if frag in (style or ""):
            return noun
    return None


def cells_of(page):
    """[(cell, id, label)] for a page, unwrapping UserObject/object wrappers."""
    model = page.find("mxGraphModel")
    root = model.find("root") if model is not None else None
    if root is None:
        return None                                    # compressed / empty page
    out = []
    for child in root:
        if child.tag == "mxCell":
            out.append((child, child.get("id"), clean(child.get("value"))))
        elif child.tag in ("UserObject", "object"):
            inner = child.find("mxCell")
            if inner is not None:
                inner.set("id", child.get("id", ""))
                out.append((inner, child.get("id"),
                            clean(child.get("label") or child.get("value"))))
    return out


def describe_page(page):
    """Markdown body lines for one <diagram> page (no page heading)."""
    cells = cells_of(page)
    if cells is None:
        return ["_(compressed page — cannot describe)_"]
    label = {cid: lbl for _, cid, lbl in cells}
    style = {cid: (c.get("style") or "") for c, cid, _ in cells}
    parents = {c.get("parent") for c, _, _ in cells if c.get("parent")}

    vertices = [(c, cid) for c, cid, _ in cells if c.get("vertex") == "1"]
    containers = {cid for c, cid in vertices if cid in parents}   # holds other cells
    leaves = [(c, cid) for c, cid in vertices
              if cid not in containers and "edgeLabel" not in style.get(cid, "")]

    # Group leaves by their container's label (else "Ungrouped").
    groups, order = {}, []
    for c, cid in leaves:
        parent = c.get("parent")
        gname = label.get(parent) or "" if parent in containers else ""
        gname = gname or "Ungrouped"
        if gname not in groups:
            groups[gname] = []
            order.append(gname)
        typ = shape_of(style.get(cid, ""))
        name = label.get(cid) or f"(unlabeled {cid})"
        groups[gname].append(f"{name}" + (f" _{typ}_" if typ else ""))

    lines = [f"### Components ({len(leaves)})", ""]
    single = len(order) == 1 and order[0] == "Ungrouped"
    for gname in order:
        if not single:
            lines.append(f"- **{gname}**")
            lines += [f"  - {item}" for item in groups[gname]]
        else:
            lines += [f"- {item}" for item in groups[gname]]
    lines.append("")

    edges = [c for c, _, _ in cells if c.get("edge") == "1"]
    rels = []
    for e in edges:
        s, t = label.get(e.get("source")), label.get(e.get("target"))
        if not s or not t:                             # dangling endpoint — skip
            continue
        verb = clean(e.get("value"))
        rels.append(f"- {s} —{verb}→ {t}" if verb else f"- {s} → {t}")
    lines.append(f"### Relations ({len(rels)})")
    lines.append("")
    lines += rels or ["_(none)_"]
    lines.append("")
    return lines


def main():
    ap = argparse.ArgumentParser(description="Describe a .drawio diagram as Markdown.")
    ap.add_argument("file")
    ap.add_argument("-o", "--output", help="output Markdown path (default: stdout)")
    args = ap.parse_args()
    try:
        tree = ET.parse(args.file)
    except (ET.ParseError, OSError) as exc:
        sys.exit(f"error: cannot parse {args.file}: {exc}")
    pages = tree.getroot().findall("diagram") or [tree.getroot()]

    title = args.file.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    lines = [f"# {title}", ""]
    for i, page in enumerate(pages, 1):
        name = page.get("name")
        if len(pages) > 1:
            lines.append(f"## Page {i}: {name}" if name else f"## Page {i}")
            lines.append("")
        lines += describe_page(page)

    text = "\n".join(lines).rstrip() + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        sys.stderr.write(f"wrote {args.output}\n")
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
