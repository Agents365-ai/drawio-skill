#!/usr/bin/env python3
"""Deterministic structural linter for .drawio files.

Catches the class of mistakes a vision self-check is slow and unreliable at:
dangling edge endpoints, duplicate or reserved ids, broken parent references,
and (as warnings) off-grid geometry, overlapping sibling nodes, and edge
routing defects. Runs without launching draw.io, so it is a fast pre-check
before the visual review step.

  python3 validate.py diagram.drawio
  python3 validate.py poster.drawio --page 4800x3600 --margin 40

Edge routing checks (warnings): an edge segment crossing a non-incident leaf
vertex ("routes through vertex"), and two edges crossing each other ("edges X
and Y cross") — the two defects the SKILL.md step-5 self-check looks for
("Edge-shape overlap", "Stacked edges"), but caught here deterministically.

Routing is only knowable from the XML when an edge carries explicit waypoints
(``<Array as="points">``) — exactly the hand-routed case the SKILL.md tells
authors to use to route around shapes. Edges with no waypoints are auto-routed
by draw.io at render time (the path is not stored), so they are NOT geometry-
checked here, keeping these warnings free of false positives. Endpoints honour
``exitX/exitY``/``entryX/entryY`` when present, else the node centre, and
absolute positions are resolved through parent containers.

Exit status is non-zero when any error (or, with --strict, any warning) is
found, so it can gate a workflow. Compressed (non-XML) diagram pages are
skipped with a warning — this skill always writes uncompressed XML.

--page WxH additionally resolves every vertex to ABSOLUTE coordinates (walking
container parents) and errors on any cell outside the page rect — content past
the page silently tiles onto extra PDF pages on export. --margin N warns when
content intrudes into the outer N px margin.

Usage: python3 validate.py <file.drawio> [--strict] [--page WxH] [--margin N]
"""
import argparse
import re
import sys
import xml.etree.ElementTree as ET

RESERVED = {"0", "1"}


def rect(cell):
    """Return (x, y, w, h) floats for a cell's geometry, or None if absent/bad.

    x/y default to 0 when omitted: draw.io treats a missing position as the
    origin, and container-managed children (table rows, swimlane/UML-class
    lines under tableLayout) legitimately omit x/y while keeping width/height.
    Only width/height are required to be present and numeric.
    """
    g = cell.find("mxGeometry")
    if g is None:
        return None
    try:
        return (float(g.get("x", "0")), float(g.get("y", "0")),
                float(g.get("width", "nan")), float(g.get("height", "nan")))
    except ValueError:
        return None


def is_edge_label(cell):
    """True for a draw.io edge label / relative-positioned child vertex.

    These legitimately omit width/height: their position is given relative to a
    parent edge (style ``edgeLabel``) or via ``relative="1"`` geometry. Treating
    them as normal vertices wrongly flags them as missing/invalid geometry.
    """
    if "edgeLabel" in (cell.get("style") or ""):
        return True
    g = cell.find("mxGeometry")
    return g is not None and g.get("relative") == "1"


def overlap(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah


def contains(a, b):
    """True if rect a fully contains rect b (layering, not a collision)."""
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax <= bx and ay <= by and ax + aw >= bx + bw and ay + ah >= by + bh


def is_backing(cell):
    """True for decorative backing cells (soft-shadow layers): near-transparent,
    unlabeled, strokeless — visual depth, never a layout collision."""
    if (cell.get("value") or "").strip():
        return False
    style = cell.get("style") or ""
    if "strokeColor=none" not in style:
        return False
    m = re.search(r"opacity=(\d+)", style)
    return m is not None and int(m.group(1)) <= 15


# --- Edge routing geometry -------------------------------------------------
#
# These helpers reason about edge paths. They only apply to edges with explicit
# waypoints (the route is otherwise computed by draw.io at render time and not
# stored in the XML), so the checks never guess an auto-routed path.

def style_num(style, key):
    """Return float value of ``key=`` in a draw.io style string, or None."""
    for part in (style or "").split(";"):
        if part.startswith(key + "="):
            try:
                return float(part.split("=", 1)[1])
            except ValueError:
                return None
    return None


def abs_rect(cell, by_id):
    """Absolute (x, y, w, h) of a vertex, summing parent-container offsets.

    Children of a container use coordinates relative to the container origin, so
    an edge spanning containers needs absolute positions to be compared.
    """
    r = rect(cell)
    if r is None or any(v != v for v in r):
        return None
    x, y, w, h = r
    parent, seen = cell.get("parent"), set()
    while parent and parent in by_id and parent not in seen:
        seen.add(parent)
        p = by_id[parent]
        if p.get("vertex") == "1":
            pr = rect(p)
            if pr and not any(v != v for v in pr):
                x += pr[0]
                y += pr[1]
        parent = p.get("parent")
    return (x, y, w, h)


def endpoint(edge, end, by_id):
    """Absolute (x, y) where ``edge`` meets its source/target vertex.

    Honours exitX/exitY (source) and entryX/entryY (target) if the style pins
    them; otherwise the vertex centre. Returns None if the vertex is unresolved.
    """
    vid = edge.get(end)
    if not vid or vid not in by_id:
        return None
    box = abs_rect(by_id[vid], by_id)
    if box is None:
        return None
    x, y, w, h = box
    style = edge.get("style") or ""
    fx = style_num(style, "exitX" if end == "source" else "entryX")
    fy = style_num(style, "exitY" if end == "source" else "entryY")
    return (x + (fx if fx is not None else 0.5) * w,
            y + (fy if fy is not None else 0.5) * h)


def edge_waypoints(edge):
    """Explicit <Array as="points"> waypoints of an edge as [(x, y), ...]."""
    g = edge.find("mxGeometry")
    if g is None:
        return []
    arr = g.find("Array")
    if arr is None:
        return []
    pts = []
    for pt in arr.findall("mxPoint"):
        px, py = pt.get("x"), pt.get("y")
        if px is not None and py is not None:
            try:
                pts.append((float(px), float(py)))
            except ValueError:
                pass
    return pts


def edge_route(edge, by_id):
    """Absolute polyline [(x, y), ...] for a waypointed edge, or None.

    Returns None when the edge has no explicit waypoints (auto-routed; path
    unknown) or an endpoint cannot be resolved.
    """
    waypoints = edge_waypoints(edge)
    if not waypoints:
        return None
    s, t = endpoint(edge, "source", by_id), endpoint(edge, "target", by_id)
    if s is None or t is None:
        return None
    return [s] + waypoints + [t]


def _orient(a, b, c):
    v = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    return 0 if abs(v) < 1e-9 else (1 if v > 0 else -1)


def segments_cross(p1, p2, p3, p4):
    """True if segments p1p2 and p3p4 properly cross (interior intersection).

    Proper crossing only: collinear overlap and shared-endpoint touches return
    False, so edges meeting at a common node or grazing a corner are not flagged.
    """
    o1, o2 = _orient(p1, p2, p3), _orient(p1, p2, p4)
    o3, o4 = _orient(p3, p4, p1), _orient(p3, p4, p2)
    return o1 != o2 and o3 != o4 and 0 not in (o1, o2, o3, o4)


def _point_in_rect(p, box, eps=1e-6):
    x, y, w, h = box
    return x + eps < p[0] < x + w - eps and y + eps < p[1] < y + h - eps


def route_hits_rect(points, box):
    """True if a polyline enters a rectangle's interior or crosses a border."""
    x, y, w, h = box
    corners = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    borders = list(zip(corners, corners[1:] + corners[:1]))
    for a, b in zip(points, points[1:]):
        if _point_in_rect(a, box) or _point_in_rect(b, box):
            return True
        if any(segments_cross(a, b, c, d) for c, d in borders):
            return True
    return False


def routes_cross(pa, pb):
    """True if any segment of polyline pa properly crosses any of pb."""
    for a1, a2 in zip(pa, pa[1:]):
        for b1, b2 in zip(pb, pb[1:]):
            if segments_cross(a1, a2, b1, b2):
                return True
    return False


def geometry_warnings(cells, ids, parents):
    """Edge-through-vertex and edge-crossing warnings for waypointed edges."""
    warns = []
    routed = []          # (edge_id, polyline, {source, target})
    for c in cells:
        if c.get("edge") == "1":
            pts = edge_route(c, ids)
            if pts:
                routed.append((c.get("id"), pts,
                               {c.get("source"), c.get("target")}))
    # Edge routes through an unrelated leaf vertex (containers wrap children, so
    # an edge legitimately traverses them — restrict to leaves, as overlap does).
    leaves = [(c.get("id"), abs_rect(c, ids)) for c in cells
              if c.get("vertex") == "1" and c.get("id") not in parents
              and not is_edge_label(c)]
    leaves = [(vid, box) for vid, box in leaves if box]
    for eid, pts, ends in routed:
        for vid, box in leaves:
            if vid not in ends and route_hits_rect(pts, box):
                warns.append(f"edge {eid!r} routes through vertex {vid!r}")
    # Edge-edge crossings (both routes known).
    for i in range(len(routed)):
        for j in range(i + 1, len(routed)):
            (ia, pa, _), (ib, pb, _) = routed[i], routed[j]
            if routes_cross(pa, pb):
                warns.append(f"edges {ia!r} and {ib!r} cross")
    return warns


def check_bounds(diagram, page_w, page_h, margin):
    """Return (errors, warnings) for vertices outside the page / inside the margin."""
    model = diagram.find("mxGraphModel")
    if model is None:
        return [], []
    root = model.find("root")
    cells = root.findall("mxCell") if root is not None else []
    ids = {c.get("id"): c for c in cells}
    errors, warns = [], []
    for c in cells:
        if c.get("vertex") != "1":
            continue
        r = abs_rect(c, ids)
        if r is None or any(v != v for v in r):
            continue  # geometry errors already reported by check_page
        x, y, w, h = r
        cid = c.get("id")
        if x < 0 or y < 0 or x + w > page_w or y + h > page_h:
            errors.append(f"vertex {cid!r} outside page: ({x:g},{y:g}) {w:g}x{h:g} "
                          f"vs page {page_w:g}x{page_h:g} — exported PDF will tile extra pages")
        elif margin and (x < margin or y < margin
                         or x + w > page_w - margin or y + h > page_h - margin):
            warns.append(f"vertex {cid!r} intrudes into the {margin:g}px page margin")
    return errors, warns


def check_page(diagram):
    """Return (errors, warnings) for one <diagram> page."""
    name = diagram.get("name", "?")
    model = diagram.find("mxGraphModel")
    if model is None:
        if (diagram.text or "").strip():
            return [], [f"page {name!r}: compressed, skipped (cannot lint)"]
        return [f"page {name!r}: no <mxGraphModel>"], []
    root = model.find("root")
    # Normalize UserObject/object wrappers (used for links & metadata): the id
    # lives on the wrapper, geometry/style on the inner mxCell — fold the two
    # into one cell so edges referencing the wrapper id resolve.
    cells = []
    for child in (root if root is not None else []):
        if child.tag == "mxCell":
            cells.append(child)
        elif child.tag in ("UserObject", "object"):
            inner = child.find("mxCell")
            if inner is not None:
                inner.set("id", child.get("id", ""))
                cells.append(inner)
    errors, warns = [], []
    ids = {}
    for c in cells:
        cid = c.get("id")
        if cid in ids:
            errors.append(f"duplicate id {cid!r}")
        ids[cid] = c
    parents = {c.get("parent") for c in cells}            # ids that have children
    for c in cells:
        cid, parent = c.get("id"), c.get("parent")
        is_v, is_e = c.get("vertex") == "1", c.get("edge") == "1"
        if parent is not None and parent not in ids:
            errors.append(f"cell {cid!r} parent {parent!r} does not exist")
        for end in ("source", "target"):
            ref = c.get(end)
            if ref and ref not in ids:
                errors.append(f"edge {cid!r} {end} {ref!r} does not exist")
        if (is_v or is_e) and cid in RESERVED:
            errors.append(f"cell {cid!r} reuses reserved id 0/1")
        if is_v and not is_edge_label(c):
            r = rect(c)
            if r is None or any(v != v for v in r):       # None or NaN
                errors.append(f"vertex {cid!r} has missing/invalid geometry")
            else:
                x, y, w, h = r
                if w <= 0 or h <= 0:
                    warns.append(f"vertex {cid!r} non-positive size {w:g}x{h:g}")
                if x < 0 or y < 0:
                    warns.append(f"vertex {cid!r} negative position ({x:g},{y:g})")
    # Sibling overlap: only leaf vertices (containers legitimately wrap children).
    # Deliberate layering is not a collision: skip pairs where one box fully
    # CONTAINS the other (text/rule cells sit on their card by design), and skip
    # decorative backing cells (shadow layers: near-transparent, unlabeled,
    # strokeless) entirely.
    boxes = [(c.get("id"), c.get("parent"), rect(c)) for c in cells
             if c.get("vertex") == "1" and c.get("id") not in parents and rect(c)
             and not any(v != v for v in rect(c)) and not is_backing(c)]
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            (ia, pa, ra), (ib, pb, rb) = boxes[i], boxes[j]
            if pa == pb and overlap(ra, rb) and not (contains(ra, rb) or contains(rb, ra)):
                warns.append(f"vertices {ia!r} and {ib!r} overlap")
    warns += geometry_warnings(cells, ids, parents)
    # Container-bounds: a child drawn past its parent's rect silently breaks the
    # card/box layout (and only trips the page gate if it also crosses the page).
    for c in cells:
        if c.get("vertex") != "1" or is_edge_label(c):
            continue
        p = ids.get(c.get("parent"))
        if p is None or p.get("vertex") != "1":
            continue
        cr, pr = rect(c), rect(p)
        if not cr or not pr or any(v != v for v in cr + pr):
            continue
        x, y, w, h = cr
        if x < 0 or y < 0 or x + w > pr[2] or y + h > pr[3]:
            warns.append(f"vertex {c.get('id')!r} exceeds its container "
                         f"{p.get('id')!r} bounds ({x:g},{y:g}) {w:g}x{h:g} "
                         f"vs {pr[2]:g}x{pr[3]:g}")
    return errors, warns


def main():
    ap = argparse.ArgumentParser(description="Lint a .drawio file for structural errors.")
    ap.add_argument("file")
    ap.add_argument("--strict", action="store_true", help="treat warnings as failure too")
    ap.add_argument("--score", action="store_true",
                    help="also print a readability score (lower is better) — "
                         "useful for comparing layout variants of the same graph")
    ap.add_argument("--page", metavar="WxH", help="also error on content outside a WxH px page")
    ap.add_argument("--margin", type=float, default=0,
                    help="with --page: warn when content intrudes into the outer N px")
    args = ap.parse_args()
    page_wh = None
    if args.page:
        try:
            pw, ph = args.page.lower().split("x", 1)
            page_wh = (float(pw), float(ph))
        except ValueError:
            ap.error("--page expects WxH, e.g. 4800x3600")
    try:
        tree = ET.parse(args.file)
    except (ET.ParseError, OSError) as exc:
        sys.exit(f"error: cannot parse {args.file}: {exc}")
    pages = tree.getroot().findall("diagram") or [tree.getroot()]
    errors, warns = [], []
    for page in pages:
        e, w = check_page(page)
        errors += e
        warns += w
        if page_wh:
            e, w = check_bounds(page, page_wh[0], page_wh[1], args.margin)
            errors += e
            warns += w
    for w in warns:
        print(f"warning: {w}")
    for e in errors:
        print(f"error: {e}")
    print(f"{len(errors)} error(s), {len(warns)} warning(s)")
    if args.score:
        # Weighted by how badly each defect hurts readability. Comparable only
        # across variants of the SAME graph (same nodes/edges).
        through = sum(1 for w in warns if "routes through" in w)
        cross = sum(1 for w in warns if " cross" in w)
        olap = sum(1 for w in warns if " overlap" in w)
        print(f"score: {20 * through + 10 * cross + 5 * olap} "
              f"({through} through-vertex, {cross} crossings, {olap} overlaps)")
    if errors or (args.strict and warns):
        sys.exit(1)


if __name__ == "__main__":
    main()
