#!/usr/bin/env python3
"""Draw the cloud resources ACTUALLY deployed, from `terraform show -json`.

Where tfimports.py reads the *declared* config (`.tf` files), this reads the
*real* state: what Terraform recorded as provisioned. It is provider-agnostic
(the JSON is uniform across AWS / Azure / GCP), expands `count`/`for_each` into
their real instances, keeps module nesting, and reuses tfimports' icon resolver
so every resource shows its official cloud icon. The output feeds autolayout.py:

  terraform show -json | python3 tfstate.py - -o graph.json
  python3 autolayout.py graph.json -o deployed.drawio

Input is the JSON `terraform show -json` prints — from live state (no argument)
or a saved plan (`terraform show -json plan.tfplan`) — as a file path or `-` for
stdin. Nodes are the managed resource instances (data sources are ignored);
edges come from the dependencies Terraform recorded in state (`depends_on`).
`--group` boxes resources by their module; `--no-icons` forces plain boxes.

Usage: terraform show -json | python3 tfstate.py - [-o graph.json]
       [--direction TB|LR] [--group] [--no-reduce] [--no-icons]
"""
import argparse
import importlib.util
import json
import os
import sys


def load_tfimports():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tfimports.py")
    spec = importlib.util.spec_from_file_location("tfimports", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def walk_module(mod, out):
    """Collect (address, type, name, index, module_path, depends_on) for every
    managed resource, recursing into child modules."""
    addr = mod.get("address", "")                    # "" for root, else module.x[...]
    for r in mod.get("resources") or []:
        if r.get("mode") == "data":
            continue
        out.append((r.get("address"), r.get("type"), r.get("name"),
                    r.get("index"), addr, r.get("depends_on") or []))
    for child in mod.get("child_modules") or []:
        walk_module(child, out)


def main():
    ap = argparse.ArgumentParser(description="`terraform show -json` -> autolayout graph JSON.")
    ap.add_argument("input", help="`terraform show -json` output file, or - for stdin")
    ap.add_argument("-o", "--output", help="output JSON path (default: stdout)")
    ap.add_argument("--direction", default="TB", choices=["TB", "LR"])
    ap.add_argument("--group", action="store_true",
                    help="group resources into containers by module")
    ap.add_argument("--no-reduce", action="store_true",
                    help="keep every edge (skip transitive reduction)")
    ap.add_argument("--no-icons", action="store_true",
                    help="plain boxes instead of official cloud icons")
    args = ap.parse_args()

    text = sys.stdin.read() if args.input == "-" else open(args.input, encoding="utf-8").read()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        sys.exit(f"error: input is not valid JSON ({exc}) — feed `terraform show -json`")
    # State: top-level "values"; saved plan: "planned_values".
    root = ((data.get("values") or data.get("planned_values") or {}).get("root_module")) or {}
    resources = []
    walk_module(root, resources)
    if not resources:
        sys.exit("error: no managed resources found in the Terraform state/plan")

    addresses = {r[0] for r in resources}

    def targets(dep):
        """Instance addresses a depends_on entry names. State records the
        un-indexed address (`aws_subnet.this`) for a resource with several
        instances (`aws_subnet.this[0]`), so expand by prefix too."""
        if dep in addresses:
            return {dep}
        return {a for a in addresses if a.startswith(dep + "[")}

    edges = sorted({(addr, t) for addr, _, _, _, _, deps in resources
                    for dep in deps for t in targets(dep) if t != addr})

    tf = load_tfimports()
    raw = len(edges)
    if not args.no_reduce and edges:
        edges = tf.transitive_reduce(list(addresses), edges)

    resolver = None if args.no_icons else tf.IconResolver()
    unmatched, nodes = [], []
    for addr, rtype, name, index, mpath, _ in resources:
        label = name if index is None else f"{name}[{index}]"
        node = {"id": addr, "label": label}
        icon = resolver.resolve(rtype) if resolver and rtype else None
        if icon:
            node.update(style=icon["style"], width=icon["w"], height=icon["h"])
        else:
            node["label"] = f"{label}\n{rtype}" if rtype else label
            if rtype:
                unmatched.append(rtype)
        if args.group and mpath:
            node["group"] = mpath
        nodes.append(node)

    graph = {"direction": args.direction, "nodes": nodes,
             "edges": [{"source": s, "target": t} for s, t in edges]}
    if resolver:
        # Icon labels render below the shape — reserve extra layout spacing.
        graph.update(ranksep=0.7, nodesep=0.6)
    out = json.dumps(graph, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)
        sys.stderr.write(f"wrote {args.output}\n")
    else:
        sys.stdout.write(out)
    note = "" if args.no_reduce else f" (reduced from {raw})"
    sys.stderr.write(f"{len(nodes)} resources, {len(edges)} edges{note}\n")
    if unmatched:
        sys.stderr.write("no icon for: " + ", ".join(sorted(set(unmatched))) + "\n")


if __name__ == "__main__":
    main()
