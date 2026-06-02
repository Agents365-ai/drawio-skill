#!/usr/bin/env python3
"""Extract a Python project's class-inheritance graph as autolayout graph JSON.

A finer-grained companion to pyimports.py: instead of module->module imports,
it emits one node per class and an edge from each subclass to the project base
classes it extends. With --group, classes are boxed by their module (nested by
sub-package), so the result reads as an auto-generated class hierarchy.

  python3 pyclasses.py myproject --group -o graph.json
  python3 autolayout.py graph.json -o diagram.drawio

Only inheritance is resolved (statically reliable); base classes are matched
by name, preferring a class in the same module. External bases (object,
Exception, third-party) are ignored. This is a *class structure* view, not a
function-level call graph — static call resolution in Python is unreliable, so
that is deliberately out of scope.

Usage: python3 pyclasses.py <project_dir> [-o graph.json] [--direction TB|LR]
                                          [--group] [--no-reduce]
"""
import argparse
import ast
import json
import os
import re
import subprocess
import sys

CLASS_STYLE = "rounded=0;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;"


def discover(root):
    """Map dotted module name -> file path; qualify with the package name when
    root is itself a package (mirrors pyimports.py)."""
    root = os.path.abspath(root)
    base = os.path.basename(root) if os.path.exists(os.path.join(root, "__init__.py")) else ""
    modules = {}
    for dirpath, _, files in os.walk(root):
        for fn in files:
            if not fn.endswith(".py"):
                continue
            rel = os.path.relpath(os.path.join(dirpath, fn), root)[:-3]
            parts = rel.split(os.sep)
            if parts[-1] == "__init__":
                parts = parts[:-1]
            parts = ([base] + parts) if base else parts
            if parts:
                modules[".".join(parts)] = os.path.join(dirpath, fn)
    return modules, base


def base_name(node):
    """Simple name of a base-class expression (`Foo` or `pkg.Foo` -> 'Foo')."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def classes_in(module, path):
    """Top-level classes of a module: list of (qualified_id, simple_name, [base names])."""
    try:
        tree = ast.parse(open(path, encoding="utf-8").read(), filename=path)
    except SyntaxError:
        return []
    out = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            bases = [b for b in (base_name(b) for b in node.bases) if b]
            out.append((f"{module}.{node.name}", node.name, bases))
    return out


def transitive_reduce(nodes, edges):
    """Drop edges implied by a longer path, via Graphviz `tred`."""
    idx = {n: i for i, n in enumerate(nodes)}
    dot = "digraph{" + "".join(f"{idx[s]}->{idx[t]};" for s, t in edges) + "}"
    try:
        out = subprocess.run(["tred"], input=dot, capture_output=True,
                             text=True, check=True).stdout
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        sys.stderr.write(f"warning: tred unavailable, keeping all edges ({exc})\n")
        return edges
    rev = {i: n for n, i in idx.items()}
    return [(rev[int(a)], rev[int(b)]) for a, b in re.findall(r"(\d+)\s*->\s*(\d+)", out)]


def main():
    ap = argparse.ArgumentParser(description="Python class-inheritance graph -> autolayout graph JSON.")
    ap.add_argument("project", help="package or project directory")
    ap.add_argument("-o", "--output", help="output JSON path (default: stdout)")
    ap.add_argument("--direction", default="TB", choices=["TB", "LR"])
    ap.add_argument("--group", action="store_true",
                    help="box classes by their module (nested by sub-package)")
    ap.add_argument("--no-reduce", action="store_true",
                    help="keep every edge (skip transitive reduction)")
    args = ap.parse_args()

    modules, base = discover(args.project)
    classes = {}                                         # qualified id -> (module, bases)
    by_name = {}                                         # simple name -> [qualified ids]
    for mod, path in modules.items():
        for cid, name, bases in classes_in(mod, path):
            classes[cid] = (mod, bases)
            by_name.setdefault(name, []).append(cid)
    if not classes:
        sys.exit(f"error: no classes found under {args.project}")

    def resolve(name, module):
        cands = by_name.get(name, [])
        same = [c for c in cands if classes[c][0] == module]
        if same:
            return same[0]                               # prefer a class in the same module
        return cands[0] if len(cands) == 1 else None     # else only if unambiguous

    edges = set()
    for cid, (mod, bases) in classes.items():
        for b in bases:
            target = resolve(b, mod)
            if target and target != cid:
                edges.add((cid, target))
    edges = sorted(edges)
    raw = len(edges)
    if not args.no_reduce:
        edges = transitive_reduce(list(classes), edges)

    strip = base + "." if base else ""
    short = lambda m: m[len(strip):] if strip and m.startswith(strip) else m

    def node(cid):
        d = {"id": cid, "label": cid.rsplit(".", 1)[1], "style": CLASS_STYLE}
        if args.group:
            mod = classes[cid][0]
            path = short(mod).replace(".", "/")          # module path -> nested boxes
            if path:
                d["group"] = path
        return d

    graph = {
        "direction": args.direction,
        "nodes": [node(cid) for cid in classes],
        "edges": [{"source": s, "target": t} for s, t in edges],
    }
    text = json.dumps(graph, indent=2)
    if args.output:
        open(args.output, "w", encoding="utf-8").write(text)
        sys.stderr.write(f"wrote {args.output}\n")
    else:
        sys.stdout.write(text)
    note = "" if args.no_reduce else f" (reduced from {raw})"
    sys.stderr.write(f"{len(classes)} classes, {len(edges)} inheritance edges{note}\n")


if __name__ == "__main__":
    main()
