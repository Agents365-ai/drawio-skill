#!/usr/bin/env python3
"""Extract a Kubernetes manifest set's object graph as autolayout graph JSON.

Reads manifest files (a directory, or explicit .yaml/.yml/.json paths), maps
each object kind to its official draw.io Kubernetes icon (mxgraph.kubernetes
set, resolved from the bundled shape index), and derives the reference edges
that make an architecture readable:

  Ingress -> Service            (spec backend service names)
  Service -> workload           (selector labels match the pod template)
  workload -> ConfigMap/Secret  (env / envFrom / volumes)
  workload -> PVC               (persistentVolumeClaim volumes)
  HPA -> target workload        (scaleTargetRef)

Workloads: Deployment, StatefulSet, DaemonSet, ReplicaSet, Job, CronJob, Pod.
Edges only land on objects that are themselves in the manifest set. The output
feeds autolayout.py:

  python3 k8simports.py ./manifests -o graph.json
  python3 autolayout.py graph.json -o cluster.drawio

JSON input (single object, or a `kind: List` as produced by
`kubectl get ... -o json`) parses with the stdlib alone; .yaml/.yml files
need PyYAML (`pip install pyyaml`). Pass `-` to read a live cluster snapshot
from stdin: `kubectl get all,ing,cm,secret,pvc -o json | k8simports.py -`.

Usage: python3 k8simports.py <dir-or-manifest...|-> [-o graph.json]
       [--direction TB|LR] [--group] [--no-icons]
"""
import argparse
import glob
import gzip
import json
import os
import re
import sys

# Object kind -> prIcon name inside the mxgraph.kubernetes.icon2 shape set.
KIND_ICON = {
    "ClusterRole": "c-role", "ClusterRoleBinding": "crb", "ConfigMap": "cm",
    "CronJob": "cronjob", "CustomResourceDefinition": "crd", "DaemonSet": "ds",
    "Deployment": "deploy", "Endpoints": "ep", "HorizontalPodAutoscaler": "hpa",
    "Ingress": "ing", "Job": "job", "Namespace": "ns", "NetworkPolicy": "netpol",
    "Node": "node", "PersistentVolume": "pv", "PersistentVolumeClaim": "pvc",
    "Pod": "pod", "ReplicaSet": "rs", "Role": "role", "RoleBinding": "rb",
    "Secret": "secret", "Service": "svc", "ServiceAccount": "sa",
    "StatefulSet": "sts", "StorageClass": "sc",
}
WORKLOADS = {"Deployment", "StatefulSet", "DaemonSet", "ReplicaSet", "Job", "CronJob", "Pod"}
_INDEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data",
                      "shape-index.json.gz")


def icon_styles():
    """prIcon name -> (style, w, h) from the bundled official shape index."""
    with gzip.open(_INDEX, "rt", encoding="utf-8") as f:
        shapes = json.load(f)
    out = {}
    for s in shapes:
        st = s["style"]
        m = re.search(r"prIcon=([\w-]+)", st)
        # Skip the kubernetesLabel=1 variants (they paint the kind name into
        # the icon; our node label already names the object below it).
        if "mxgraph.kubernetes.icon2" in st and m and "kubernetesLabel" not in st:
            out.setdefault(m.group(1), (st, s["w"], s["h"]))
    return out


def load_manifests(paths):
    """Parse all given files into a list of k8s objects."""
    files = []
    for p in paths:
        if os.path.isdir(p):
            for ext in ("yaml", "yml", "json"):
                files.extend(glob.glob(os.path.join(p, "**", f"*.{ext}"), recursive=True))
        else:
            files.append(p)
    objs = []
    for path in sorted(set(files)):
        if path == "-":                                  # `kubectl get ... -o json | k8simports.py -`
            docs = [json.loads(sys.stdin.read())]
        elif path.endswith(".json"):
            with open(path, encoding="utf-8") as f:
                docs = [json.loads(f.read())]
        else:
            with open(path, encoding="utf-8") as f:
                text = f.read()
            try:
                import yaml
            except ImportError:
                sys.exit(f"error: {path} is YAML but PyYAML is not installed "
                         "(pip install pyyaml) — or feed JSON from `kubectl get ... -o json`")
            docs = list(yaml.safe_load_all(text))
        for doc in docs:
            if not isinstance(doc, dict):
                continue
            if doc.get("kind") == "List":
                objs.extend(i for i in doc.get("items", []) if isinstance(i, dict))
            else:
                objs.append(doc)
    return [o for o in objs if o.get("kind") and o.get("metadata", {}).get("name")]


def pod_spec(obj):
    spec = obj.get("spec") or {}
    if obj["kind"] == "Pod":
        return spec
    if obj["kind"] == "CronJob":
        spec = (spec.get("jobTemplate") or {}).get("spec") or {}
    return (spec.get("template") or {}).get("spec") or {}


def pod_labels(obj):
    if obj["kind"] == "Pod":
        return (obj.get("metadata") or {}).get("labels") or {}
    spec = obj.get("spec") or {}
    if obj["kind"] == "CronJob":
        spec = (spec.get("jobTemplate") or {}).get("spec") or {}
    return ((spec.get("template") or {}).get("metadata") or {}).get("labels") or {}


def mounted_refs(pspec):
    """(kind, name) pairs a pod spec references via env/envFrom/volumes."""
    refs = set()
    for c in (pspec.get("containers") or []) + (pspec.get("initContainers") or []):
        for e in c.get("env") or []:
            vf = e.get("valueFrom") or {}
            for key, kind in (("configMapKeyRef", "ConfigMap"), ("secretKeyRef", "Secret")):
                if vf.get(key, {}).get("name"):
                    refs.add((kind, vf[key]["name"]))
        for e in c.get("envFrom") or []:
            for key, kind in (("configMapRef", "ConfigMap"), ("secretRef", "Secret")):
                if e.get(key, {}).get("name"):
                    refs.add((kind, e[key]["name"]))
    for v in pspec.get("volumes") or []:
        if v.get("configMap", {}).get("name"):
            refs.add(("ConfigMap", v["configMap"]["name"]))
        if v.get("secret", {}).get("secretName"):
            refs.add(("Secret", v["secret"]["secretName"]))
        if v.get("persistentVolumeClaim", {}).get("claimName"):
            refs.add(("PersistentVolumeClaim", v["persistentVolumeClaim"]["claimName"]))
    return refs


def ingress_backends(obj):
    """Service names referenced by an Ingress (networking.k8s.io/v1 + legacy)."""
    names, stack = set(), [obj.get("spec") or {}]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            svc = cur.get("service")
            if isinstance(svc, dict) and svc.get("name"):
                names.add(svc["name"])
            if isinstance(cur.get("serviceName"), str):
                names.add(cur["serviceName"])
            stack.extend(cur.values())
        elif isinstance(cur, list):
            stack.extend(cur)
    return names


def main():
    ap = argparse.ArgumentParser(description="Kubernetes manifests -> autolayout graph JSON.")
    ap.add_argument("paths", nargs="+", help="manifest files and/or directories")
    ap.add_argument("-o", "--output", help="output JSON path (default: stdout)")
    ap.add_argument("--direction", default="TB", choices=["TB", "LR"])
    ap.add_argument("--group", action="store_true", help="group objects by namespace")
    ap.add_argument("--no-icons", action="store_true",
                    help="plain boxes instead of official Kubernetes icons")
    args = ap.parse_args()

    objs = load_manifests(args.paths)
    if not objs:
        sys.exit("error: no Kubernetes objects found (need kind + metadata.name)")

    def key(obj):
        meta = obj.get("metadata") or {}
        return (meta.get("namespace") or "", obj["kind"], meta["name"])

    by_key = {key(o): o for o in objs}
    icons = {} if args.no_icons else icon_styles()

    edges = set()
    for k, obj in by_key.items():
        ns, kind, _ = k

        def link(tkind, tname):
            if (ns, tkind, tname) in by_key and (ns, tkind, tname) != k:
                edges.add((k, (ns, tkind, tname)))

        if kind == "Ingress":
            for svc in ingress_backends(obj):
                link("Service", svc)
        elif kind == "Service":
            sel = (obj.get("spec") or {}).get("selector") or {}
            if sel:
                for tk, target in by_key.items():
                    if (tk[0] == ns and tk[1] in WORKLOADS
                            and sel.items() <= pod_labels(target).items()):
                        edges.add((k, tk))
        elif kind in WORKLOADS:
            for tkind, tname in mounted_refs(pod_spec(obj)):
                link(tkind, tname)
        elif kind == "HorizontalPodAutoscaler":
            ref = (obj.get("spec") or {}).get("scaleTargetRef") or {}
            if ref.get("kind") and ref.get("name"):
                link(ref["kind"], ref["name"])

    def nid(k):
        ns, kind, name = k
        return f"{ns + '/' if ns else ''}{kind}/{name}"

    nodes = []
    for k in by_key:
        ns, kind, name = k
        node = {"id": nid(k), "label": name}
        icon = icons.get(KIND_ICON.get(kind, ""))
        if icon:
            node.update(style=icon[0], width=icon[1], height=icon[2])
        else:
            node["label"] = f"{name}\n{kind}"
        if args.group and ns:
            node["group"] = ns
        nodes.append(node)

    graph = {"direction": args.direction, "nodes": nodes,
             "edges": [{"source": nid(s), "target": nid(t)} for s, t in sorted(edges)]}
    if icons:
        # Icon labels render below the shape — reserve extra layout spacing.
        graph.update(ranksep=0.7, nodesep=0.6)
    text = json.dumps(graph, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        sys.stderr.write(f"wrote {args.output}\n")
    else:
        sys.stdout.write(text)
    sys.stderr.write(f"{len(nodes)} objects, {len(edges)} edges\n")


if __name__ == "__main__":
    main()
