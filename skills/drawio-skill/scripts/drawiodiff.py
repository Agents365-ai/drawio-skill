#!/usr/bin/env python3
"""Diff two .drawio diagrams into a colour-coded autolayout graph JSON.

Compares an OLD and a NEW .drawio and emits a single graph where every node and
edge is tinted by what happened to it:

  added    (in new only)                 -> green
  removed  (in old only)                 -> red, dashed
  changed  (matched, label moved)        -> orange
  moved    (matched, same label, new x/y) -> violet
  same     (matched, unchanged)          -> grey

Edges can additionally be **rerouted** (orange): a new edge whose old
counterpart kept one endpoint and swapped the other for a freshly added node
("service repointed from cache to worker"), or whose direction flipped
((a,b) in old, (b,a) in new). A flipped edge suppresses its reversed old
counterpart so the pair is shown once.

The output is a normal graph JSON — feed it to autolayout.py for one clean,
freshly laid-out "what changed" diagram:

  python3 drawiodiff.py old.drawio new.drawio -o diff.json
  python3 autolayout.py diff.json -o diff.drawio

Nodes are matched by cell **id** (the default) — perfect for diagrams the
bundled importers generate, whose ids are stable semantic keys
(`aws_instance.web`, `shop-db-1`), so two snapshots line up exactly. This makes
it the natural companion to the live-infra importers: snapshot `terraform show
-json` / `docker inspect` / `kubectl get -o json` twice and diff the two to see
drift. For hand-drawn diagrams whose ids are random, pass `--by-label` to match
on the visible label text instead.

Because the output is re-laid-out by autolayout, a "moved" tint is only
reported for hand-placed coordinates — and only when it is selective. If every
matched node changed position, the two files were laid out by different runs
(the usual importer + autolayout case), so movement is layout noise, not a
fact, and all matched nodes stay "same".

Only leaf vertices and the edges between them are compared; container/group
cells and edge labels are skipped. The diff is a flat colour-coded view, so the
original icons/shapes are replaced by status colours (the label is kept).

Usage: python3 drawiodiff.py <old.drawio> <new.drawio> [-o diff.json]
       [--direction TB|LR] [--by-label]
"""
import argparse
import json
import sys
import xml.etree.ElementTree as ET

STYLE = {
    "added":   "rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;",
    "removed": "rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;dashed=1;",
    "changed": "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;",
    "moved":   "rounded=1;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;",
    "same":    "rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#999999;",
}
EDGE_STYLE = {
    "added":    "endArrow=classic;html=1;strokeColor=#82b366;strokeWidth=2;",
    "removed":  "endArrow=classic;html=1;strokeColor=#b85450;strokeWidth=2;dashed=1;",
    "rerouted": "endArrow=classic;html=1;strokeColor=#d79b00;strokeWidth=2;",
    "same":     "endArrow=classic;html=1;strokeColor=#999999;",
}


def parse(path):
    """Return (nodes, edges) for a .drawio: nodes {id: (label, style, pos)} for
    leaf vertices (pos = (x, y) or None when no geometry), edges
    {(source_id, target_id)}. Cells are flattened across pages; UserObject/object
    wrappers are unwrapped (id on the wrapper, cell inside)."""
    try:
        tree = ET.parse(path)
    except (ET.ParseError, OSError) as exc:
        sys.exit(f"error: cannot parse {path}: {exc}")
    pages = tree.getroot().findall("diagram") or [tree.getroot()]
    cells, labels = [], {}
    for page in pages:
        model = page.find("mxGraphModel")
        root = model.find("root") if model is not None else None
        if root is None:
            if (page.text or "").strip():
                sys.stderr.write(f"warning: {path}: a page is compressed, skipped\n")
            continue
        for child in root:
            if child.tag == "mxCell":
                cells.append(child)
                labels[child.get("id")] = child.get("value") or ""
            elif child.tag in ("UserObject", "object"):
                inner = child.find("mxCell")
                if inner is not None:
                    inner.set("id", child.get("id", ""))
                    cells.append(inner)
                    labels[child.get("id")] = child.get("label") or child.get("value") or ""
    parents = {c.get("parent") for c in cells}                # ids that have children
    nodes, edges = {}, set()
    for c in cells:
        cid = c.get("id")
        if c.get("edge") == "1":
            s, t = c.get("source"), c.get("target")
            if s and t:
                edges.add((s, t))
        elif c.get("vertex") == "1" and cid not in parents:   # leaf vertices only
            if "edgeLabel" in (c.get("style") or ""):
                continue
            g = c.find("mxGeometry")
            if g is not None and g.get("relative") == "1":    # edge-label child
                continue
            pos = None
            if g is not None:
                try:
                    pos = (float(g.get("x", "0")), float(g.get("y", "0")))
                except ValueError:
                    pos = None
            nodes[cid] = (labels.get(cid, ""), c.get("style") or "", pos)
    return nodes, edges


def classify_rerouted(old_ek, new_ek, removed, added):
    """Edge keys that are reroutes of an old edge, not brand-new connections.

    Two decidable cases (everything else stays a plain add):
    - flip:      (a,b) in old and (b,a) in new — same pair, reversed direction.
    - re-point:  old (a,b) with b removed and new (a,c) with c added (the kept
                 endpoint a pins the pairing; ambiguous when a kept endpoint has
                 several candidate re-points, in which case nothing is flagged).
    """
    old_only, new_only = old_ek - new_ek, new_ek - old_ek
    rerouted = {(s, t) for (s, t) in new_only if (t, s) in old_only}
    for a, b in old_only:
        if (b, a) in new_only:
            continue                                          # flip, handled above
        if b in removed and a not in removed:
            cands = [(a, c) for (s, c) in new_only if s == a and c in added]
            if len(cands) == 1:
                rerouted.add(cands[0])
        elif a in removed and b not in removed:
            cands = [(c, b) for (s, t) in new_only if t == b and s in added]
            if len(cands) == 1:
                rerouted.add(cands[0])
    return rerouted


def main():
    ap = argparse.ArgumentParser(description="Diff two .drawio files -> autolayout graph JSON.")
    ap.add_argument("old", help="baseline .drawio")
    ap.add_argument("new", help="updated .drawio")
    ap.add_argument("-o", "--output", help="output JSON path (default: stdout)")
    ap.add_argument("--direction", default="TB", choices=["TB", "LR"])
    ap.add_argument("--by-label", action="store_true",
                    help="match nodes by visible label instead of cell id "
                         "(for hand-drawn diagrams with non-stable ids)")
    args = ap.parse_args()

    old_n, old_e = parse(args.old)
    new_n, new_e = parse(args.new)

    def keyed(nodes):
        """Map match-key -> label. By id (default) the key is the cell id and the
        value is its label; by label the key *is* the label."""
        if args.by_label:
            return {lbl: lbl for lbl, _, _ in nodes.values()}, {i: lbl for i, (lbl, _, _) in nodes.items()}
        return {i: lbl for i, (lbl, _, _) in nodes.items()}, {i: i for i in nodes}

    old_keys, old_id2key = keyed(old_n)
    new_keys, new_id2key = keyed(new_n)
    old_pos = {old_id2key[i]: p for i, (_, _, p) in old_n.items() if i in old_id2key}
    new_pos = {new_id2key[i]: p for i, (_, _, p) in new_n.items() if i in new_id2key}

    # Selective movement only: when every matched node changed position the two
    # files come from different layout runs, so movement carries no information.
    moved = {key for key in set(old_keys) & set(new_keys)
             if old_keys[key] == new_keys[key]
             and old_pos.get(key) and new_pos.get(key)
             and old_pos[key] != new_pos[key]}
    if moved and len(moved) == len(set(old_keys) & set(new_keys)):
        moved = set()

    nodes, counts = [], {"added": 0, "removed": 0, "changed": 0,
                         "moved": 0, "same": 0}
    for key in sorted(set(old_keys) | set(new_keys)):
        if key in old_keys and key not in new_keys:
            status, label = "removed", old_keys[key]
        elif key in new_keys and key not in old_keys:
            status, label = "added", new_keys[key]
        elif old_keys[key] != new_keys[key]:                  # matched, label moved
            status, label = "changed", new_keys[key]
        elif key in moved:
            status, label = "moved", new_keys[key]
        else:
            status, label = "same", new_keys[key]
        counts[status] += 1
        nodes.append({"id": key, "label": label or key, "style": STYLE[status],
                      "width": 160, "height": 60})

    def edge_keys(edges, id2key):
        out = set()
        for s, t in edges:
            if s in id2key and t in id2key:
                out.add((id2key[s], id2key[t]))
        return out

    old_ek, new_ek = edge_keys(old_e, old_id2key), edge_keys(new_e, new_id2key)
    removed = set(old_keys) - set(new_keys)
    added = set(new_keys) - set(old_keys)
    rerouted = classify_rerouted(old_ek, new_ek, removed, added)
    node_keys = {n["id"] for n in nodes}
    edges = []
    for s, t in sorted(old_ek | new_ek):
        if s not in node_keys or t not in node_keys:
            continue
        if (s, t) in old_ek and (s, t) in new_ek:
            status = "same"
        elif (s, t) in new_ek:
            status = "rerouted" if (s, t) in rerouted else "added"
        else:
            status = "removed" if (t, s) not in new_ek else None   # flip: shown once
        if status:
            edges.append({"source": s, "target": t, "style": EDGE_STYLE[status]})
    rerouted_n = sum(1 for e in edges if "d79b00" in e["style"])

    graph = {"direction": args.direction, "nodes": nodes, "edges": edges}
    text = json.dumps(graph, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        sys.stderr.write(f"wrote {args.output}\n")
    else:
        sys.stdout.write(text)
    sys.stderr.write(f"+{counts['added']} added, -{counts['removed']} removed, "
                     f"~{counts['changed']} changed, >{counts['moved']} moved, "
                     f"={counts['same']} unchanged, {rerouted_n} edge(s) rerouted\n")


if __name__ == "__main__":
    main()