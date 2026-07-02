#!/usr/bin/env python3
"""Extract a docker-compose file's service graph as autolayout graph JSON.

Services become rounded boxes (labeled name + image), named volumes become
cylinders, and edges come from real wiring: `depends_on` (list or mapping
form), `links`, `volumes_from`, and named-volume mounts (short "vol:/path"
and long {type: volume, source: ...} syntax). The output feeds autolayout.py:

  python3 composeimports.py docker-compose.yml -o graph.json
  python3 autolayout.py graph.json -o stack.drawio

Given a directory, the usual compose file names are tried
(compose.yaml/compose.yml/docker-compose.yml/docker-compose.yaml).
Requires PyYAML (pip install pyyaml). `--group` boxes services by their
first network.

Usage: python3 composeimports.py <compose-file-or-dir> [-o graph.json]
       [--direction TB|LR] [--group]
"""
import argparse
import json
import os
import sys

SERVICE_STYLE = "rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;"
VOLUME_STYLE = ("shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;size=15;"
                "fillColor=#f5f5f5;strokeColor=#666666;")


def find_compose(path):
    if os.path.isfile(path):
        return path
    for name in ("compose.yaml", "compose.yml", "docker-compose.yml", "docker-compose.yaml"):
        cand = os.path.join(path, name)
        if os.path.isfile(cand):
            return cand
    sys.exit(f"error: no compose file found under {path}")


def volume_mounts(svc):
    """Named volumes a service mounts (short and long syntax)."""
    for v in svc.get("volumes") or []:
        if isinstance(v, str):
            src = v.split(":", 1)[0]
            if src and not src.startswith((".", "/", "~", "$")):
                yield src
        elif isinstance(v, dict) and v.get("type", "volume") == "volume" and v.get("source"):
            yield v["source"]


def dependencies(svc):
    dep = svc.get("depends_on") or []
    deps = list(dep) if isinstance(dep, (list, dict)) else []
    for link in svc.get("links") or []:
        deps.append(str(link).split(":", 1)[0])
    for vf in svc.get("volumes_from") or []:
        deps.append(str(vf).split(":", 1)[0])
    return deps


def main():
    ap = argparse.ArgumentParser(description="docker-compose -> autolayout graph JSON.")
    ap.add_argument("path", help="compose file, or directory containing one")
    ap.add_argument("-o", "--output", help="output JSON path (default: stdout)")
    ap.add_argument("--direction", default="TB", choices=["TB", "LR"])
    ap.add_argument("--group", action="store_true",
                    help="group services into containers by their first network")
    args = ap.parse_args()

    try:
        import yaml
    except ImportError:
        sys.exit("error: PyYAML is required (pip install pyyaml)")
    path = find_compose(args.path)
    with open(path, encoding="utf-8") as f:
        spec = yaml.safe_load(f) or {}
    services = spec.get("services") or {}
    if not services:
        sys.exit(f"error: no services in {path}")
    declared_volumes = set(spec.get("volumes") or {})

    nodes, edges = [], set()
    for name, svc in services.items():
        svc = svc or {}
        image = svc.get("image") or ("build: " + str((svc.get("build") or {}).get("context", ".")
                                                     if isinstance(svc.get("build"), dict)
                                                     else svc.get("build", ".")))
        node = {"id": name, "label": f"{name}\n{image}", "style": SERVICE_STYLE,
                "width": 160, "height": 60}
        nets = svc.get("networks")
        first_net = (sorted(nets)[0] if isinstance(nets, dict) else nets[0]) if nets else None
        if args.group and first_net:
            node["group"] = str(first_net)
        nodes.append(node)
        for dep in dependencies(svc):
            if dep in services and dep != name:
                edges.add((name, dep))
        for vol in volume_mounts(svc):
            if vol in declared_volumes:
                edges.add((name, f"vol:{vol}"))
    for vol in sorted({t[4:] for _, t in edges if t.startswith("vol:")}):
        nodes.append({"id": f"vol:{vol}", "label": vol, "style": VOLUME_STYLE,
                      "width": 120, "height": 70})

    graph = {"direction": args.direction, "nodes": nodes,
             "edges": [{"source": s, "target": t} for s, t in sorted(edges)]}
    text = json.dumps(graph, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        sys.stderr.write(f"wrote {args.output}\n")
    else:
        sys.stdout.write(text)
    sys.stderr.write(f"{len(nodes)} nodes, {len(edges)} edges\n")


if __name__ == "__main__":
    main()
