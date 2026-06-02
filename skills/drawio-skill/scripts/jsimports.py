#!/usr/bin/env python3
"""Extract a JS/TS project's module-import graph as autolayout graph JSON.

The JavaScript/TypeScript counterpart to pyimports.py: walks a source
directory, scans each module for static and dynamic import specifiers
(`import`/`export ... from`, `require()`, `import()`), keeps only the
intra-project edges (relative specifiers that resolve to a file under the
root), and applies transitive reduction so the diagram stays readable.

  python3 jsimports.py src -o graph.json
  python3 autolayout.py graph.json -o diagram.drawio

Resolution is path-based: relative specifiers are resolved against the
importing file's directory, trying the .ts/.tsx/.js/.jsx/.mjs/.cjs extensions
and directory index files. Bare specifiers (node_modules packages such as
"react") are ignored. Scanning is regex-based rather than a full parser, so a
specifier inside a comment or string literal is counted in rare cases.

Usage: python3 jsimports.py <src_dir> [-o graph.json] [--direction TB|LR]
                                       [--group] [--no-reduce]
"""
import argparse
import json
import os
import re
import subprocess
import sys

EXTS = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")
SPEC = re.compile(
    r"(?:import|export)\b[^'\";]*?\bfrom\s*['\"]([^'\"]+)['\"]"  # import/export ... from "x"
    r"|import\s*['\"]([^'\"]+)['\"]"                              # import "x" (side effect)
    r"|require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"                   # require("x")
    r"|import\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"                    # import("x") dynamic
)


def modid(path, root):
    """Module id = path relative to root, extension stripped, posix separators."""
    rel = os.path.relpath(path, root)
    for ext in EXTS:
        if rel.endswith(ext):
            rel = rel[: -len(ext)]
            break
    return rel.replace(os.sep, "/")


def discover(root):
    """Map module id -> absolute file path for every source file under root."""
    root = os.path.abspath(root)
    modules = {}
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d != "node_modules" and not d.startswith(".")]
        for fn in files:
            if fn.endswith(EXTS) and not fn.endswith(".d.ts"):
                full = os.path.join(dirpath, fn)
                modules[modid(full, root)] = full
    return modules, root


def resolve(spec, importer, root, modules):
    """Resolve a relative specifier to a known module id, or None (external)."""
    if not spec.startswith("."):
        return None
    base = os.path.normpath(os.path.join(os.path.dirname(importer), spec))
    candidates = ([base + e for e in EXTS]
                  + [os.path.join(base, "index" + e) for e in EXTS]
                  + [base])
    for cand in candidates:
        mid = modid(cand, root)
        if mid in modules and modules[mid] != importer:
            return mid
    return None


def edges_of(mid, path, root, modules):
    """Intra-project modules imported by module `mid`."""
    found = set()
    try:
        src = open(path, encoding="utf-8", errors="ignore").read()
    except OSError:
        return found
    for m in SPEC.finditer(src):
        spec = m.group(1) or m.group(2) or m.group(3) or m.group(4)
        target = resolve(spec, path, root, modules)
        if target and target != mid:
            found.add(target)
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


def common_dir(ids):
    """Longest shared leading path segment across module ids (e.g. 'src/')."""
    common = []
    for parts in zip(*[m.split("/") for m in ids]):
        if len(set(parts)) == 1:
            common.append(parts[0])
        else:
            break
    return "/".join(common) + "/" if common else ""


def main():
    ap = argparse.ArgumentParser(description="JS/TS import graph -> autolayout graph JSON.")
    ap.add_argument("src", help="source directory")
    ap.add_argument("-o", "--output", help="output JSON path (default: stdout)")
    ap.add_argument("--direction", default="TB", choices=["TB", "LR"])
    ap.add_argument("--group", action="store_true",
                    help="group nodes into containers by top-level directory")
    ap.add_argument("--no-reduce", action="store_true",
                    help="keep every edge (skip transitive reduction)")
    args = ap.parse_args()

    modules, root = discover(args.src)
    if not modules:
        sys.exit(f"error: no JS/TS modules found under {args.src}")
    edges = sorted({(m, t) for m, p in modules.items()
                    for t in edges_of(m, p, root, modules)})
    raw = len(edges)
    if not args.no_reduce:
        edges = transitive_reduce(list(modules), edges)
    strip = common_dir(list(modules))
    label = lambda m: (m[len(strip):] if strip and m.startswith(strip) else m) or m

    def node(m):
        d = {"id": m, "label": label(m)}
        if args.group:
            rest = label(m).split("/")
            if len(rest) > 1:                            # has a sub-directory
                d["group"] = "/".join(rest[:-1])         # full directory path -> nested boxes
        return d

    graph = {
        "direction": args.direction,
        "nodes": [node(m) for m in modules],
        "edges": [{"source": s, "target": t} for s, t in edges],
    }
    text = json.dumps(graph, indent=2)
    if args.output:
        open(args.output, "w", encoding="utf-8").write(text)
        sys.stderr.write(f"wrote {args.output}\n")
    else:
        sys.stdout.write(text)
    note = "" if args.no_reduce else f" (reduced from {raw})"
    sys.stderr.write(f"{len(modules)} modules, {len(edges)} edges{note}\n")


if __name__ == "__main__":
    main()
