#!/usr/bin/env python3
"""Extract a Terraform configuration's resource graph as autolayout graph JSON.

Parses ``.tf`` files with a small regex + brace-matching pass (no HCL library
needed), builds resource-reference edges (``aws_iam_role.lambda.arn`` inside
another resource's body -> edge), and resolves each resource type to its
official draw.io cloud icon via the bundled shape index — AWS (aws4 set),
Azure (azure2 set) and GCP (Google Cloud icon set). The output feeds
autolayout.py:

  python3 tfimports.py ./infra -o graph.json
  python3 autolayout.py graph.json -o infra.drawio

Nodes are the ``resource`` and ``module`` blocks declared in the scanned files;
data sources, variables, locals and providers are ignored. A reference is any
``type.name`` / ``module.name`` token in a resource body that matches a
declared node — attribute chains (``aws_s3_bucket.logs.arn``), ``"${...}"``
interpolations and ``depends_on`` entries all count. Transitive reduction
(Graphviz ``tred``) keeps big graphs readable; ``--no-reduce`` keeps every
edge. Heredoc bodies with unbalanced braces are the one known parse limit.

Usage: python3 tfimports.py <dir-or-file.tf> [-o graph.json]
       [--direction TB|LR] [--group] [--no-reduce] [--no-icons]
"""
import argparse
import glob
import importlib.util
import json
import os
import re
import subprocess
import sys

# provider prefix of the resource type -> (icon query prefix, style predicate).
# The predicate pins results to the modern shape set for that cloud — a bare
# keyword search happily returns another vendor's icon (e.g. "kubernetes
# deployment" -> Azure Arc), so set filtering is what makes resolution safe.
PROVIDERS = {
    "aws": ("aws", lambda st: "mxgraph.aws4" in st),
    "azurerm": ("azure", lambda st: "img/lib/azure2" in st),
    "azuread": ("azure", lambda st: "img/lib/azure2" in st),
    "google": ("gcp", lambda st: "editableCssRules" in st),
}

# Resource types whose derived query ("aws lambda function") misses or mis-hits
# the intended icon; values are the query that finds it. Keep alphabetical.
QUERY_OVERRIDES = {
    "aws_alb": "aws elastic load balancing",
    "aws_apigatewayv2_api": "aws api gateway",
    "aws_autoscaling_group": "aws ec2 auto scaling",
    "aws_cloudwatch_log_group": "aws cloudwatch",
    "aws_db_instance": "aws rds",
    "aws_dynamodb_table": "aws dynamodb",
    "aws_ecr_repository": "aws elastic container registry",
    "aws_ecs_cluster": "aws elastic container service",
    "aws_ecs_service": "aws elastic container service",
    "aws_ecs_task_definition": "aws elastic container service",
    "aws_efs_file_system": "aws elastic file system",
    "aws_eks_cluster": "aws elastic kubernetes service",
    "aws_elasticache_cluster": "aws elasticache",
    "aws_iam_policy": "aws identity and access management",
    "aws_instance": "aws ec2",
    "aws_kms_key": "aws key management service",
    "aws_lambda_function": "aws lambda",
    "aws_lb": "aws elastic load balancing",
    "aws_rds_cluster": "aws aurora",
    "aws_s3_bucket": "aws simple storage service",
    "aws_secretsmanager_secret": "aws secrets manager",
    "aws_sfn_state_machine": "aws step functions",
    "aws_sns_topic": "aws simple notification service",
    "aws_sqs_queue": "aws simple queue service",
    "azurerm_app_service": "azure app services",
    "azurerm_application_gateway": "azure application gateways",
    "azurerm_cosmosdb_account": "azure cosmos db",
    "azurerm_kubernetes_cluster": "azure kubernetes services",
    "azurerm_linux_function_app": "azure function apps",
    "azurerm_linux_virtual_machine": "azure virtual machine",
    "azurerm_linux_web_app": "azure app services",
    "azurerm_mssql_database": "azure sql database",
    "azurerm_mssql_server": "azure sql database",
    "azurerm_servicebus_namespace": "azure service bus",
    "azurerm_storage_account": "azure storage accounts",
    "azurerm_virtual_network": "azure virtual networks",
    "azurerm_windows_function_app": "azure function apps",
    "azurerm_windows_virtual_machine": "azure virtual machine",
    "azurerm_windows_web_app": "azure app services",
    "google_cloudfunctions2_function": "gcp cloud functions",
    "google_cloudfunctions_function": "gcp cloud functions",
    "google_compute_instance": "gcp compute engine",
    "google_container_cluster": "gcp kubernetes engine",
    "google_redis_instance": "gcp memorystore",
    "google_sql_database_instance": "gcp cloud sql",
    "google_storage_bucket": "gcp cloud storage",
}

_COMMENT = re.compile(r"/\*.*?\*/|(?:#|//)[^\n]*", re.S)
_BLOCK = re.compile(r'^[ \t]*(resource|module)[ \t]+"([\w.-]+)"(?:[ \t]+"([\w.-]+)")?[ \t]*\{', re.M)
_REF = re.compile(r"\b([a-z][a-z0-9_]*\.[A-Za-z_][A-Za-z0-9_-]*)")


def parse_blocks(text):
    """Yield (kind, label1, label2, body) for resource/module blocks."""
    text = _COMMENT.sub("", text)
    for m in _BLOCK.finditer(text):
        depth, i = 1, m.end()
        while i < len(text) and depth:
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
            i += 1
        yield m.group(1), m.group(2), m.group(3), text[m.end():i - 1]


def load_shapesearch():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shapesearch.py")
    spec = importlib.util.spec_from_file_location("shapesearch", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class IconResolver:
    """Resolve a Terraform resource type to an official draw.io icon style."""

    def __init__(self):
        import gzip
        self.ss = load_shapesearch()
        with gzip.open(self.ss.INDEX, "rt", encoding="utf-8") as f:
            self.shapes = json.load(f)
        self.tag_map = self.ss.build_tag_map(self.shapes)
        self.cache = {}

    def _and_styles(self, words):
        """Style strings of shapes whose tags match EVERY query word.
        shapesearch.search() falls back to scored OR matching when the AND set
        is empty — fine interactively, but here a partial match means a visibly
        wrong icon, so results outside this set are rejected and the caller's
        back-off handles the miss (a plain box beats a wrong icon)."""
        idxs = None
        for t in words:
            exact, phonetic = self.ss.match_term(self.tag_map, t)
            s = exact | phonetic
            idxs = s if idxs is None else idxs & s
            if not idxs:
                return set()
        return {self.shapes[i]["style"] for i in idxs}

    def resolve(self, rtype):
        if rtype in self.cache:
            return self.cache[rtype]
        provider = rtype.split("_", 1)[0]
        hit = None
        if provider in PROVIDERS:
            prefix, want = PROVIDERS[provider]
            words = (QUERY_OVERRIDES.get(rtype) or
                     f"{prefix} {rtype.split('_', 1)[1].replace('_', ' ')}").split()
            # Back off one trailing word at a time: "aws lambda event source
            # mapping" eventually matches on "aws lambda".
            while len(words) > 1 and hit is None:
                allowed = self._and_styles(words)
                good = [r for r in
                        self.ss.search(self.shapes, self.tag_map, " ".join(words), 40)
                        if r["style"] in allowed and want(r["style"])
                        and "group" not in r["style"].lower()]
                # Prefer aws4 service icons (resIcon=) over scenario glyphs.
                hit = next((r for r in good if "resIcon=" in r["style"]), None) or \
                      (good[0] if good else None)
                words = words[:-1]
        if hit and max(hit["w"], hit["h"]) < 44:
            # Some sets (GCP) ship tiny nominal sizes; scale up so the icon
            # is not dwarfed by its label. aspect=fixed keeps the ratio.
            f = 48 / max(hit["w"], hit["h"])
            hit = dict(hit, w=round(hit["w"] * f), h=round(hit["h"] * f))
        self.cache[rtype] = hit
        return hit


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
    ap = argparse.ArgumentParser(description="Terraform resource graph -> autolayout graph JSON.")
    ap.add_argument("path", help=".tf file or directory containing .tf files")
    ap.add_argument("-o", "--output", help="output JSON path (default: stdout)")
    ap.add_argument("--direction", default="TB", choices=["TB", "LR"])
    ap.add_argument("--group", action="store_true",
                    help="group resources into containers by service (aws_s3_* -> s3)")
    ap.add_argument("--no-reduce", action="store_true",
                    help="keep every edge (skip transitive reduction)")
    ap.add_argument("--no-icons", action="store_true",
                    help="plain boxes instead of official cloud icons")
    args = ap.parse_args()

    files = ([args.path] if os.path.isfile(args.path)
             else sorted(glob.glob(os.path.join(args.path, "**", "*.tf"), recursive=True)))
    blocks = []
    for path in files:
        with open(path, encoding="utf-8") as f:
            blocks.extend(parse_blocks(f.read()))
    if not blocks:
        sys.exit(f"error: no resource/module blocks found under {args.path}")

    declared = {}                                    # node id -> (rtype or None, name, body)
    for kind, l1, l2, body in blocks:
        nid = f"{l1}.{l2}" if kind == "resource" else f"module.{l1}"
        declared[nid] = (l1 if kind == "resource" else None, l2 or l1, body)

    edges = sorted({(nid, ref) for nid, (_, _, body) in declared.items()
                    for ref in _REF.findall(body) if ref in declared and ref != nid})
    raw = len(edges)
    if not args.no_reduce:
        edges = transitive_reduce(list(declared), edges)

    resolver = None if args.no_icons else IconResolver()
    unmatched = []
    nodes = []
    for nid, (rtype, name, _) in declared.items():
        node = {"id": nid, "label": name}
        icon = resolver.resolve(rtype) if resolver and rtype else None
        if icon:
            node.update(style=icon["style"], width=icon["w"], height=icon["h"])
        else:
            # No icon: keep the type visible on the box (second line).
            node["label"] = f"{name}\n{rtype}" if rtype else f"module {name}"
            if rtype:
                unmatched.append(rtype)
        if args.group and rtype and "_" in rtype:
            node["group"] = rtype.split("_")[1]
        nodes.append(node)

    graph = {"direction": args.direction, "nodes": nodes,
             "edges": [{"source": s, "target": t} for s, t in edges]}
    if resolver:
        # Icon labels render below the shape — reserve extra layout spacing.
        graph.update(ranksep=0.7, nodesep=0.6)
    text = json.dumps(graph, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        sys.stderr.write(f"wrote {args.output}\n")
    else:
        sys.stdout.write(text)
    note = "" if args.no_reduce else f" (reduced from {raw})"
    sys.stderr.write(f"{len(nodes)} nodes, {len(edges)} edges{note}\n")
    if unmatched:
        sys.stderr.write("no icon for: " + ", ".join(sorted(set(unmatched))) + "\n")


if __name__ == "__main__":
    main()
