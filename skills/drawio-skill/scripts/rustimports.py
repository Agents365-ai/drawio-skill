#!/usr/bin/env python3
"""Extract a Rust crate's module-use graph as autolayout graph JSON.

The Rust counterpart to pyimports.py / jsimports.py / goimports.py. Treats each
.rs file as a module (path-derived: src/foo/bar.rs -> module foo::bar; main.rs /
lib.rs / mod.rs name the enclosing module), and records intra-crate `use` edges
resolved through Rust's path roots:

  use crate::a::b::C;   -> edge to module a::b
  use super::sibling;   -> resolved against the current module's parent
  use self::child::Item;-> resolved against the current module
  use other_crate::...; / use std::...;  -> external, ignored

Brace groups (`use crate::a::{B, C};`, `use crate::{a, b};`) are expanded.
Transitive reduction is on by default so the diagram stays readable.

  python3 rustimports.py ./mycrate --group -o graph.json
  python3 autolayout.py graph.json -o diagram.drawio

Parsing is regex-based, not a full parser: inline `mod { ... }` blocks are not
split out, `#[cfg]`-gated modules are always included, and 2015-edition bare
intra-crate paths (without `crate::`) are not resolved.

Usage: python3 rustimports.py <crate_dir> [-o graph.json] [--direction TB|LR]
                                           [--group] [--no-reduce]
"""
import argparse
import json
import os
import re
import subprocess
import sys

USE = re.compile(r"\buse\s+([^;]+);")


def crate_name(root):
    cargo = os.path.join(root, "Cargo.toml")
    if os.path.exists(cargo):
        m = re.search(r'(?m)^\s*name\s*=\s*"([^"]+)"',
                      open(cargo, encoding="utf-8", errors="ignore").read())
        if m:
            return m.group(1)
    return "crate"


def discover(root):
    """Map module path (tuple of segments; () is the crate root) -> file path."""
    root = os.path.abspath(root)
    src = os.path.join(root, "src") if os.path.isdir(os.path.join(root, "src")) else root
    modules = {}
    for dirpath, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d != "target" and not d.startswith(".")]
        for fn in files:
            if not fn.endswith(".rs"):
                continue
            parts = os.path.relpath(os.path.join(dirpath, fn), src)[:-3].split(os.sep)
            if parts[-1] == "mod":
                parts = parts[:-1]
            if len(parts) == 1 and parts[0] in ("main", "lib"):
                parts = []                                   # crate root
            modules[tuple(parts)] = os.path.join(dirpath, fn)
    return modules, src


def split_top(inner):
    """Split a brace group on top-level commas, ignoring nested braces."""
    out, depth, cur = [], 0, ""
    for ch in inner:
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur)
    return out


def base_segments(prefix, current):
    """Classify a `use` path prefix into intra-crate base segments, or None."""
    segs = [s for s in (p.strip() for p in prefix.split("::")) if s]
    if not segs:
        return None
    if segs[0] == "crate":
        return segs[1:]
    if segs[0] == "self":
        return list(current) + segs[1:]
    if segs[0] == "super":
        n = 0
        while segs and segs[0] == "super":
            n += 1
            segs = segs[1:]
        if n > len(current):
            return None                                      # climbs above the crate root
        return list(current)[: len(current) - n] + segs
    return None                                              # std / external crate


def resolve(parts, modules, current):
    """Longest known module prefix of `parts` (a tuple), or None."""
    if not parts:
        return () if () in modules and () != tuple(current) else None
    p = list(parts)
    while p:
        if tuple(p) in modules and tuple(p) != tuple(current):
            return tuple(p)
        p = p[:-1]
    return None


def edges_of(current, path, modules):
    """Intra-crate module paths used by the module at `current`."""
    found = set()
    try:
        src = open(path, encoding="utf-8", errors="ignore").read()
    except OSError:
        return found
    for stmt in USE.findall(src):
        if "{" in stmt:
            prefix = stmt[: stmt.index("{")]
            inner = stmt[stmt.index("{") + 1: stmt.rindex("}")] if "}" in stmt else ""
            leaves = split_top(inner)
        else:
            prefix, leaves = stmt, [None]
        base = base_segments(prefix, current)
        if base is None:
            continue
        for leaf in leaves:
            segs = list(base)
            if leaf:
                first = leaf.strip().split("::")[0].split()[0]
                if first and first not in ("self", "*"):
                    segs.append(first)
            target = resolve(tuple(segs), modules, current)
            if target is not None and target != current:
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


def main():
    ap = argparse.ArgumentParser(description="Rust module-use graph -> autolayout graph JSON.")
    ap.add_argument("crate", help="crate directory (contains Cargo.toml and/or src/)")
    ap.add_argument("-o", "--output", help="output JSON path (default: stdout)")
    ap.add_argument("--direction", default="TB", choices=["TB", "LR"])
    ap.add_argument("--group", action="store_true",
                    help="box modules by their parent module path (nested)")
    ap.add_argument("--no-reduce", action="store_true",
                    help="keep every edge (skip transitive reduction)")
    args = ap.parse_args()

    modules, _ = discover(args.crate)
    if not modules:
        sys.exit(f"error: no .rs modules found under {args.crate}")
    name = crate_name(args.crate)
    mid = lambda parts: name if not parts else "::".join(parts)
    edges = sorted({(mid(m), mid(t)) for m, path in modules.items()
                    for t in edges_of(m, path, modules)})
    raw = len(edges)
    if not args.no_reduce:
        edges = transitive_reduce([mid(m) for m in modules], edges)

    def node(parts):
        d = {"id": mid(parts), "label": name if not parts else parts[-1]}
        if args.group and len(parts) > 1:
            d["group"] = "/".join(parts[:-1])                # parent module path -> nested boxes
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
