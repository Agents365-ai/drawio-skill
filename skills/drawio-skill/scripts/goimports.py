#!/usr/bin/env python3
"""Extract a Go module's package-import graph as autolayout graph JSON.

The Go counterpart to pyimports.py / jsimports.py. Reads the module path from
go.mod, walks the module, treats each directory of .go files as one package
(node = its import path), and records the intra-module package imports. Stdlib
and third-party imports are ignored. Transitive reduction is on by default so
the diagram stays readable.

  python3 goimports.py ./mymodule -o graph.json
  python3 autolayout.py graph.json -o diagram.drawio

Parsing is regex-based over `import` statements (single and block form),
which is enough for a structural package graph. *_test.go files and vendor/
are skipped.

Usage: python3 goimports.py <module_dir> [-o graph.json] [--direction TB|LR]
                                          [--group] [--no-reduce]
"""
import argparse
import json
import os
import re
import subprocess
import sys

MODULE = re.compile(r"^module\s+(\S+)", re.MULTILINE)
BLOCK = re.compile(r"import\s*\((.*?)\)", re.DOTALL)
SINGLE = re.compile(r'import\s+(?:[\w.]+\s+|_\s+)?"([^"]+)"')
QUOTED = re.compile(r'"([^"]+)"')


def module_path(root):
    """Read the `module` path from go.mod at the module root, or None."""
    gomod = os.path.join(root, "go.mod")
    if not os.path.exists(gomod):
        return None
    m = MODULE.search(open(gomod, encoding="utf-8", errors="ignore").read())
    return m.group(1) if m else None


def discover(root, modpath):
    """Map package import path -> list of .go files (one entry per directory)."""
    root = os.path.abspath(root)
    pkgs = {}
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs
                   if d not in ("vendor", "testdata") and not d.startswith(".")]
        gofiles = [os.path.join(dirpath, f) for f in files
                   if f.endswith(".go") and not f.endswith("_test.go")]
        if not gofiles:
            continue
        rel = os.path.relpath(dirpath, root).replace(os.sep, "/")
        ip = modpath if rel == "." else f"{modpath}/{rel}"
        pkgs[ip] = gofiles
    return pkgs


def imports_of(files, modpath, pkgs):
    """Intra-module package import paths referenced by a package's files."""
    found = set()
    for path in files:
        try:
            src = open(path, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        specs = []
        for block in BLOCK.findall(src):
            specs += QUOTED.findall(block)
        specs += SINGLE.findall(src)
        for spec in specs:
            if (spec == modpath or spec.startswith(modpath + "/")) and spec in pkgs:
                found.add(spec)
    return found


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
    ap = argparse.ArgumentParser(description="Go import graph -> autolayout graph JSON.")
    ap.add_argument("module", help="module directory (contains go.mod)")
    ap.add_argument("-o", "--output", help="output JSON path (default: stdout)")
    ap.add_argument("--direction", default="TB", choices=["TB", "LR"])
    ap.add_argument("--group", action="store_true",
                    help="group nodes into containers by top-level package dir")
    ap.add_argument("--no-reduce", action="store_true",
                    help="keep every edge (skip transitive reduction)")
    args = ap.parse_args()

    modpath = module_path(args.module)
    if not modpath:
        sys.exit(f"error: no go.mod with a module path found in {args.module}")
    pkgs = discover(args.module, modpath)
    if not pkgs:
        sys.exit(f"error: no Go packages found under {args.module}")
    edges = sorted({(ip, t) for ip, files in pkgs.items()
                    for t in imports_of(files, modpath, pkgs) if t != ip})
    raw = len(edges)
    if not args.no_reduce:
        edges = transitive_reduce(list(pkgs), edges)
    # Drop the module prefix from labels for readability; ids stay full.
    strip = modpath + "/"
    label = lambda ip: ip[len(strip):] if ip.startswith(strip) else os.path.basename(ip)

    def node(ip):
        d = {"id": ip, "label": label(ip)}
        if args.group:
            rest = label(ip).split("/")
            if len(rest) > 1:                            # nested under a sub-package
                d["group"] = rest[0]
        return d

    graph = {
        "direction": args.direction,
        "nodes": [node(ip) for ip in pkgs],
        "edges": [{"source": s, "target": t} for s, t in edges],
    }
    text = json.dumps(graph, indent=2)
    if args.output:
        open(args.output, "w", encoding="utf-8").write(text)
        sys.stderr.write(f"wrote {args.output}\n")
    else:
        sys.stdout.write(text)
    note = "" if args.no_reduce else f" (reduced from {raw})"
    sys.stderr.write(f"{len(pkgs)} packages, {len(edges)} edges{note}\n")


if __name__ == "__main__":
    main()
