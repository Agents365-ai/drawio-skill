#!/usr/bin/env python3
"""Draw the containers that are ACTUALLY running from `docker inspect` output.

Where composeimports.py reads the *declared* stack (compose file), this reads
the *live* one: pipe `docker inspect` of the running containers and it maps the
real topology — every container, the user networks they are attached to, the
named volumes they mount, and the container->container edges recorded in
`links` / compose `depends_on` labels. The output feeds autolayout.py:

  docker inspect $(docker ps -q) | python3 dockerimports.py - -o graph.json
  python3 autolayout.py graph.json -o running.drawio

Input is the JSON array `docker inspect` prints (a file path, or `-` for
stdin). Containers become rounded boxes (name + image), user networks become
green ellipses, named volumes become cylinders — visually matching the compose
importer so declared and live diagrams read alike. `--group` boxes containers
by their compose project (falling back to their first user network).

Usage: docker inspect $(docker ps -q) | python3 dockerimports.py - [-o graph.json]
       [--direction TB|LR] [--group]
"""
import argparse
import json
import sys

CONTAINER_STYLE = "rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;"
NETWORK_STYLE = "ellipse;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;"
VOLUME_STYLE = ("shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;size=15;"
                "fillColor=#f5f5f5;strokeColor=#666666;")
# Docker's built-in networks are topology noise — a compose stack's own
# networks are what tell the architecture story.
BUILTIN_NETS = {"bridge", "host", "none", "ingress"}


def cname(obj):
    """A container's short name (strip docker's leading slash)."""
    return (obj.get("Name") or obj.get("Id", "")[:12]).lstrip("/")


def links_of(obj):
    """Container names this one links to (HostConfig.Links + per-network Links)."""
    out = set()
    raw = list((obj.get("HostConfig") or {}).get("Links") or [])
    for net in ((obj.get("NetworkSettings") or {}).get("Networks") or {}).values():
        raw.extend((net or {}).get("Links") or [])
    for link in raw:
        # "/db:/web/db" -> target container is the part before the first colon.
        target = str(link).lstrip("/").split(":", 1)[0]
        if target:
            out.add(target)
    return out


def depends_on(obj):
    """Compose service names this container depends on (label form)."""
    label = (obj.get("Config") or {}).get("Labels", {}).get("com.docker.compose.depends_on")
    if not label:
        return set()
    # "db:service_healthy:false,cache:service_started:false" -> {db, cache}
    return {part.split(":", 1)[0] for part in label.split(",") if part.strip()}


def main():
    ap = argparse.ArgumentParser(description="`docker inspect` output -> autolayout graph JSON.")
    ap.add_argument("input", help="`docker inspect` JSON file, or - for stdin")
    ap.add_argument("-o", "--output", help="output JSON path (default: stdout)")
    ap.add_argument("--direction", default="TB", choices=["TB", "LR"])
    ap.add_argument("--group", action="store_true",
                    help="group containers by compose project (else first network)")
    args = ap.parse_args()

    text = sys.stdin.read() if args.input == "-" else open(args.input, encoding="utf-8").read()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        sys.exit(f"error: input is not valid JSON ({exc}) — feed `docker inspect ...`")
    containers = data if isinstance(data, list) else [data]
    containers = [c for c in containers if isinstance(c, dict) and c.get("Id")]
    if not containers:
        sys.exit("error: no containers found (feed `docker inspect $(docker ps -q)`)")

    names = {cname(c) for c in containers}
    # compose service label -> container name, so depends_on (which names
    # services) can resolve to the real container node.
    svc_to_name = {}
    for c in containers:
        svc = (c.get("Config") or {}).get("Labels", {}).get("com.docker.compose.service")
        if svc:
            svc_to_name[svc] = cname(c)

    nodes, edges, nets, vols = [], set(), set(), set()
    for c in containers:
        name = cname(c)
        image = (c.get("Config") or {}).get("Image") or "?"
        labels = (c.get("Config") or {}).get("Labels", {}) or {}
        node = {"id": name, "label": f"{name}\n{image}", "style": CONTAINER_STYLE,
                "width": 160, "height": 60}

        attached = [n for n in ((c.get("NetworkSettings") or {}).get("Networks") or {})
                    if n not in BUILTIN_NETS]
        if args.group:
            project = labels.get("com.docker.compose.project")
            grp = project or (attached[0] if attached else None)
            if grp:
                node["group"] = str(grp)
        nodes.append(node)

        for net in attached:
            nets.add(net)
            edges.add((name, f"net:{net}"))
        for m in c.get("Mounts") or []:
            if m.get("Type") == "volume" and m.get("Name"):
                vols.add(m["Name"])
                edges.add((name, f"vol:{m['Name']}"))
        for target in links_of(c):
            if target in names and target != name:
                edges.add((name, target))
        for dep in depends_on(c):
            target = svc_to_name.get(dep, dep)
            if target in names and target != name:
                edges.add((name, target))

    for net in sorted(nets):
        nodes.append({"id": f"net:{net}", "label": net, "style": NETWORK_STYLE,
                      "width": 120, "height": 70})
    for vol in sorted(vols):
        nodes.append({"id": f"vol:{vol}", "label": vol, "style": VOLUME_STYLE,
                      "width": 120, "height": 70})

    graph = {"direction": args.direction, "nodes": nodes,
             "edges": [{"source": s, "target": t} for s, t in sorted(edges)]}
    out = json.dumps(graph, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)
        sys.stderr.write(f"wrote {args.output}\n")
    else:
        sys.stdout.write(out)
    sys.stderr.write(f"{len(nodes)} nodes ({len(containers)} containers, "
                     f"{len(nets)} networks, {len(vols)} volumes), {len(edges)} edges\n")


if __name__ == "__main__":
    main()
