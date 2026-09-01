#!/usr/bin/env python3
"""Shared semantic model for drawio-skill.

This module is intentionally stdlib-only.  It turns graph JSON and uncompressed
or compressed draw.io pages into a versioned Diagram IR, writes IR back to
draw.io, powers incremental reconciliation, semantic queries/reviews, and emits
an accessible story viewer.  Other scripts may import it; it is not itself a
user-facing command.
"""

from __future__ import annotations

import base64
import copy
import html
import importlib.util
import json
import math
import os
import re
import urllib.parse
import xml.etree.ElementTree as ET
import zlib
from collections import defaultdict, deque
from datetime import datetime, timezone

SCHEMA = "drawio-skill/diagram-ir/v1"
DEFAULT_NODE_STYLE = (
    "rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;"
)
DEFAULT_EDGE_STYLE = "endArrow=classic;html=1;rounded=0;"
KIND_STYLE = {
    "database": "shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;fillColor=#d5e8d4;strokeColor=#82b366;",
    "queue": "shape=hexagon;perimeter=hexagonPerimeter2;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;",
    "gateway": "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;",
    "external": "rounded=1;whiteSpace=wrap;html=1;dashed=1;fillColor=#f5f5f5;strokeColor=#666666;",
    "actor": "shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;",
}


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def clean_label(value):
    if not value:
        return ""
    value = re.sub(r"<br\s*/?>", "\n", str(value), flags=re.I)
    value = re.sub(r"<[^>]+>", "", value)
    return html.unescape(value).strip()


def slug(value):
    return re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-") or "item"


def stable_id(value, used=None):
    base = slug(value)
    if not used or base not in used:
        return base
    i = 2
    while f"{base}-{i}" in used:
        i += 1
    return f"{base}-{i}"


def infer_kind(style="", label="", props=None):
    style_l, label_l = (style or "").lower(), (label or "").lower()
    props = props or {}
    explicit = props.get("kind") or props.get("type")
    if explicit:
        return str(explicit).lower()
    checks = [
        (("cylinder", "database", "postgres", "mysql", "dynamodb"), "database"),
        (("queue", "kafka", "rabbit", "pubsub", "sqs", "hexagon"), "queue"),
        (("gateway", "ingress", "load balancer", "api gateway"), "gateway"),
        (("external", "third-party", "internet", "cloud"), "external"),
        (("umlactor", "shape=actor"), "actor"),
    ]
    hay = style_l + " " + label_l
    for needles, kind in checks:
        if any(n in hay for n in needles):
            return kind
    if label_l.strip() in {"user", "customer", "operator", "administrator", "admin"}:
        return "actor"
    return "service"


def normalize_ir(raw, source_path=None):
    """Return a validated-enough canonical IR without rejecting extensions."""
    if not isinstance(raw, dict):
        raise ValueError("diagram input must be a JSON object")
    is_ir = raw.get("schema") == SCHEMA or "metadata" in raw or "views" in raw
    nodes_in = raw.get("nodes") or []
    edges_in = raw.get("edges") or raw.get("relations") or []
    used, nodes = set(), []
    for i, item in enumerate(nodes_in):
        if not isinstance(item, dict):
            raise ValueError(f"node {i} must be an object")
        nid = str(
            item.get("id") or stable_id(item.get("label") or f"node-{i + 1}", used)
        )
        if nid in {"0", "1"}:
            nid = f"node-{nid}"
        if nid in used:
            raise ValueError(f"duplicate node id {nid!r}")
        used.add(nid)
        props = copy.deepcopy(item.get("properties") or {})
        for key in (
            "owner",
            "environment",
            "region",
            "runtime",
            "observability",
            "trust_boundary",
            "importance",
            "technology",
            "description",
        ):
            if key in item and key not in props:
                props[key] = item[key]
        provenance = copy.deepcopy(item.get("provenance") or item.get("source") or {})
        if isinstance(provenance, str):
            provenance = {"id": provenance}
        node = {
            "id": nid,
            "label": str(item.get("label") or nid),
            "kind": str(
                item.get("kind")
                or infer_kind(item.get("style", ""), item.get("label", ""), props)
            ),
            "properties": props,
        }
        for key in (
            "style",
            "group",
            "groupLabel",
            "width",
            "height",
            "x",
            "y",
            "page",
            "labels",
        ):
            if key in item:
                node[key] = copy.deepcopy(item[key])
        if provenance:
            node["provenance"] = provenance
        elif source_path:
            node["provenance"] = {"path": os.path.abspath(source_path)}
        nodes.append(node)

    edges, edge_used = [], set()
    for i, item in enumerate(edges_in):
        if not isinstance(item, dict):
            raise ValueError(f"edge {i} must be an object")
        src = str(item.get("source", item.get("from", "")))
        dst = str(item.get("target", item.get("to", "")))
        if not src or not dst:
            raise ValueError(f"edge {i} needs source/from and target/to")
        eid = str(item.get("id") or f"{src}--{dst}")
        if eid in edge_used:
            eid = stable_id(eid, edge_used)
        edge_used.add(eid)
        props = copy.deepcopy(item.get("properties") or {})
        for key in (
            "protocol",
            "timeout",
            "async",
            "data",
            "trust_boundary",
            "isolates_failure",
            "data_classification",
            "residency_approved",
        ):
            if key in item and key not in props:
                props[key] = item[key]
        edge = {
            "id": eid,
            "source": src,
            "target": dst,
            "label": str(item.get("label") or ""),
            "kind": str(
                item.get("kind") or ("async" if props.get("async") else "relation")
            ),
            "properties": props,
        }
        for key in ("style", "page"):
            if key in item:
                edge[key] = item[key]
        prov = copy.deepcopy(item.get("provenance") or item.get("source_info") or {})
        if prov:
            edge["provenance"] = prov
        edges.append(edge)

    metadata = copy.deepcopy(raw.get("metadata") or {}) if is_ir else {}
    metadata.setdefault(
        "title",
        raw.get("title")
        or (os.path.basename(source_path) if source_path else "Diagram"),
    )
    metadata.setdefault("created", utc_now())
    if source_path:
        metadata.setdefault("source", os.path.abspath(source_path))
    return {
        "schema": SCHEMA,
        "metadata": metadata,
        "nodes": nodes,
        "edges": edges,
        "views": copy.deepcopy(raw.get("views") or []),
    }


def load_ir(path):
    if str(path).lower().endswith((".drawio", ".xml")):
        return drawio_to_ir(path)
    # pi-lens-ignore: ast-grep:unchecked-throwing-call-python
    with open(path, encoding="utf-8") as fh:
        # pi-lens-ignore: ast-grep:unchecked-throwing-call-python
        return normalize_ir(json.load(fh), source_path=path)


def save_ir(ir, path):
    # pi-lens-ignore: ast-grep:unchecked-throwing-call-python
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(normalize_ir(ir), fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def decode_page(page):
    model = page.find("mxGraphModel")
    if model is not None:
        return model
    payload = (page.text or "").strip()
    if not payload:
        return None
    try:
        raw = base64.b64decode(payload)
        xml = urllib.parse.unquote(zlib.decompress(raw, -15).decode("utf-8"))
        return ET.fromstring(xml)
    except (ValueError, zlib.error, UnicodeDecodeError, ET.ParseError):
        return None


def iter_cells(model):
    root = model.find("root") if model is not None else None
    if root is None:
        return
    for child in root:
        if child.tag == "mxCell":
            yield child, child
        elif child.tag in ("UserObject", "object"):
            cell = child.find("mxCell")
            if cell is not None:
                yield child, cell


def _json_attr(holder, name):
    value = holder.get(name)
    if not value:
        return {}
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, dict) else {}
    except ValueError:
        return {}


def drawio_to_ir(path):
    try:
        tree = ET.parse(path)
    except (OSError, ET.ParseError) as exc:
        raise ValueError(f"cannot parse {path}: {exc}") from exc
    pages = tree.getroot().findall("diagram") or [tree.getroot()]
    nodes, edges, used = [], [], set()
    for pi, page in enumerate(pages, 1):
        page_name = page.get("name") or f"Page {pi}"
        model = decode_page(page)
        rows = list(iter_cells(model) or [])
        parent_ids = {cell.get("parent") for _, cell in rows if cell.get("parent")}
        cell_to_model = {}
        for holder, cell in rows:
            cid = holder.get("id") or cell.get("id")
            model_id = holder.get("data-model-id") or cell.get("data-model-id") or cid
            if cid:
                cell_to_model[cid] = model_id
        for holder, cell in rows:
            cid = holder.get("id") or cell.get("id")
            if not cid or cid in {"0", "1"}:
                continue
            model_id = cell_to_model.get(cid, cid)
            if cell.get("vertex") == "1":
                if cid in parent_ids or "edgeLabel" in (cell.get("style") or ""):
                    continue
                geom = cell.find("mxGeometry")
                props = _json_attr(holder, "data-properties") or _json_attr(
                    cell, "data-properties"
                )
                label = (
                    holder.get("label")
                    or holder.get("value")
                    or cell.get("value")
                    or model_id
                )
                node = {
                    "id": model_id,
                    "label": clean_label(label),
                    "kind": holder.get("data-kind")
                    or cell.get("data-kind")
                    or infer_kind(cell.get("style", ""), label, props),
                    "style": cell.get("style") or DEFAULT_NODE_STYLE,
                    "properties": props,
                    "page": page_name,
                }
                for key, attr in (
                    ("owner", "data-owner"),
                    ("trust_boundary", "data-boundary"),
                ):
                    value = holder.get(attr) or cell.get(attr)
                    if value:
                        node["properties"][key] = value
                if geom is not None:
                    for key in ("x", "y", "width", "height"):
                        value = geom.get(key)
                        if value is not None:
                            try:
                                node[key] = float(value)
                            except ValueError:
                                pass
                prov = _json_attr(holder, "data-provenance") or _json_attr(
                    cell, "data-provenance"
                )
                if prov:
                    node["provenance"] = prov
                if model_id in used:
                    node["id"] = f"{slug(page_name)}::{model_id}"
                used.add(node["id"])
                cell_to_model[cid] = node["id"]
                nodes.append(node)
            elif cell.get("edge") == "1":
                src = cell_to_model.get(cell.get("source"), cell.get("source"))
                dst = cell_to_model.get(cell.get("target"), cell.get("target"))
                if src and dst:
                    edges.append(
                        {
                            "id": model_id,
                            "source": src,
                            "target": dst,
                            "label": clean_label(
                                holder.get("label") or cell.get("value") or ""
                            ),
                            "kind": holder.get("data-kind")
                            or cell.get("data-kind")
                            or "relation",
                            "style": cell.get("style") or DEFAULT_EDGE_STYLE,
                            "properties": _json_attr(holder, "data-properties")
                            or _json_attr(cell, "data-properties"),
                            "page": page_name,
                        }
                    )
    return normalize_ir(
        {
            "schema": SCHEMA,
            "metadata": {
                "title": os.path.basename(path),
                "source": os.path.abspath(path),
                "imported": utc_now(),
            },
            "nodes": nodes,
            "edges": edges,
        }
    )


def ir_to_graph(ir, node_ids=None, prefix="", links=None):
    ir = normalize_ir(ir)
    selected = set(node_ids or [n["id"] for n in ir["nodes"]])
    nodes = []
    for n in ir["nodes"]:
        if n["id"] not in selected:
            continue
        node = {
            "id": prefix + n["id"],
            "label": n["label"],
            "style": n.get("style")
            or KIND_STYLE.get(n.get("kind"), DEFAULT_NODE_STYLE),
            "width": n.get("width", 160),
            "height": n.get("height", 70),
        }
        if n.get("group"):
            node["group"] = n["group"]
        if links and n["id"] in links:
            node["link"] = links[n["id"]]
        nodes.append(node)
    edges = []
    for e in ir["edges"]:
        if e["source"] in selected and e["target"] in selected:
            edges.append(
                {
                    "id": prefix + e["id"],
                    "source": prefix + e["source"],
                    "target": prefix + e["target"],
                    "label": e.get("label", ""),
                    "style": e.get("style") or DEFAULT_EDGE_STYLE,
                }
            )
    return {"direction": "TB", "nodes": nodes, "edges": edges}


def _load_autolayout():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "autolayout.py")
    spec = importlib.util.spec_from_file_location("drawio_skill_autolayout", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _grid_page(graph, page_id, name):
    # pi-lens-ignore: ast-grep:unchecked-throwing-call-python
    cols = max(1, int(math.ceil(math.sqrt(max(1, len(graph["nodes"]))))))
    cells = []
    for i, node in enumerate(graph["nodes"]):
        x, y = 60 + (i % cols) * 230, 80 + (i // cols) * 150
        style = html.escape(node.get("style") or DEFAULT_NODE_STYLE, quote=True)
        label = html.escape(str(node.get("label") or node["id"]), quote=True)
        nid = html.escape(node["id"], quote=True)
        cells.append(
            f'        <mxCell id="{nid}" value="{label}" style="{style}" vertex="1" parent="1">\n'
            f'          <mxGeometry x="{x}" y="{y}" width="{node.get("width", 160)}" height="{node.get("height", 70)}" as="geometry"/>\n'
            f"        </mxCell>"
        )
    for i, edge in enumerate(graph.get("edges", [])):
        cells.append(
            f'        <mxCell id="edge-{page_id}-{i}" value="{html.escape(edge.get("label", ""), quote=True)}" '
            f'style="{html.escape(edge.get("style") or DEFAULT_EDGE_STYLE, quote=True)}" edge="1" parent="1" '
            f'source="{html.escape(edge["source"], quote=True)}" target="{html.escape(edge["target"], quote=True)}">\n'
            '          <mxGeometry relative="1" as="geometry"/>\n        </mxCell>'
        )
    al = _load_autolayout()
    return al.wrap_page("\n".join(cells), page_id=page_id, name=name)


def _annotate_page(page, ir, prefix="", selected=None):
    model = page.find("mxGraphModel")
    root = model.find("root") if model is not None else None
    if root is None:
        return
    nodes = {prefix + n["id"]: n for n in ir["nodes"]}
    # autolayout currently names edges e0/e1; pair them in graph order.
    selected = set(selected or [n["id"] for n in ir["nodes"]])
    edge_values = [
        e for e in ir["edges"] if e["source"] in selected and e["target"] in selected
    ]
    edge_i = 0
    for holder, cell in iter_cells(model):
        cid = holder.get("id") or cell.get("id")
        if cid in nodes:
            n = nodes[cid]
            holder.set("data-model-id", n["id"])
            holder.set("data-kind", n.get("kind", "service"))
            properties = json.dumps(
                n.get("properties", {}), ensure_ascii=False, separators=(",", ":")
            )
            holder.set("data-properties", properties)
            holder.set("data-source-properties", properties)
            holder.set("data-source-label", n["label"])
            if n.get("provenance"):
                holder.set(
                    "data-provenance",
                    json.dumps(
                        n["provenance"], ensure_ascii=False, separators=(",", ":")
                    ),
                )
            if n.get("properties", {}).get("owner"):
                holder.set("data-owner", str(n["properties"]["owner"]))
            if n.get("properties", {}).get("trust_boundary"):
                holder.set("data-boundary", str(n["properties"]["trust_boundary"]))
        elif cell.get("edge") == "1" and edge_i < len(edge_values):
            e = edge_values[edge_i]
            edge_i += 1
            cell.set("data-model-id", e["id"])
            cell.set("data-kind", e.get("kind", "relation"))
            properties = json.dumps(
                e.get("properties", {}), ensure_ascii=False, separators=(",", ":")
            )
            cell.set("data-properties", properties)
            cell.set("data-source-properties", properties)
            cell.set("data-source-label", e.get("label", ""))


def write_drawio(ir, path, views=None, direction="TB"):
    ir = normalize_ir(ir)
    requested = views or [{"name": "System", "nodes": [n["id"] for n in ir["nodes"]]}]
    al = _load_autolayout()
    pages = []
    memberships = defaultdict(list)
    for view in requested:
        for nid in view.get("nodes", []):
            memberships[nid].append(view.get("id") or slug(view.get("name") or "view"))
    for i, view in enumerate(requested):
        name = view.get("name") or f"View {i + 1}"
        pid = view.get("id") or slug(name)
        prefix = f"{pid}--" if len(requested) > 1 else ""
        links = {}
        if len(requested) > 1:
            for nid in view.get("nodes", []):
                targets = memberships.get(nid, [])
                if len(targets) > 1:
                    current = targets.index(pid)
                    links[nid] = f"data:page/id,{targets[(current + 1) % len(targets)]}"
        graph = ir_to_graph(ir, view.get("nodes"), prefix=prefix, links=links)
        graph["direction"] = view.get("direction", direction)
        try:
            height, pos, edge_pts = al.layout(al.build_dot(graph))
            page_xml = al.wrap_page(
                al.page_cells(graph, height, pos, edge_pts), page_id=pid, name=name
            )
        except SystemExit:
            page_xml = _grid_page(graph, pid, name)
        page = ET.fromstring(page_xml)
        _annotate_page(page, ir, prefix=prefix, selected=view.get("nodes"))
        pages.append(ET.tostring(page, encoding="unicode"))
    root = ET.Element(
        "mxfile", {"host": "drawio-skill", "agent": "diagram-ir", "version": "3.0.0"}
    )
    for page_xml in pages:
        root.append(ET.fromstring(page_xml))
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(path, encoding="unicode", xml_declaration=False)
    # pi-lens-ignore: ast-grep:unchecked-throwing-call-python
    with open(path, "a", encoding="utf-8") as fh:
        fh.write("\n")


def project_views(ir, names=None):
    """Project a model into audience/concern views.

    Each returned view carries an optional `fallback` flag: when a projection
    had no metadata to work with and therefore fell back to the complete node
    set, `fallback` is True, `fallback_reason` says which metadata was
    missing, and `hint` says what would make that view distinctive.
    """
    ir = normalize_ir(ir)
    nodes = {n["id"]: n for n in ir["nodes"]}
    degree = defaultdict(int)
    for e in ir["edges"]:
        degree[e["source"]] += 1
        degree[e["target"]] += 1
    wanted = names or ["executive", "system", "deployment", "dataflow", "security"]

    def view(name, selected, fallback=False, reason=None, hint=None):
        d = {"id": slug(name), "name": name.title(), "nodes": list(selected)}
        if fallback:
            d["fallback"] = True
            d["fallback_reason"] = reason
            d["hint"] = hint
        return d

    all_ids = list(nodes)
    out = []
    for name in wanted:
        key = name.lower()
        if key == "executive":
            ranked = sorted(
                nodes,
                key=lambda nid: (
                    # pi-lens-ignore: ast-grep:unchecked-throwing-call-python
                    -int(nodes[nid].get("properties", {}).get("importance", 0)),
                    -degree[nid],
                    nid,
                ),
            )
            selected = ranked[:12]
            has_importance = any(
                "importance" in nodes[nid].get("properties", {}) for nid in nodes
            )
            out.append(
                view(
                    name,
                    selected,
                    fallback=not has_importance,
                    reason="no properties.importance metadata; ranked by connection degree only",
                    hint="set properties.importance on the components that matter to executives",
                )
                if not has_importance
                else view(name, selected)
            )
        elif key == "deployment":
            selected = [
                nid
                for nid, n in nodes.items()
                if any(
                    k in n.get("properties", {})
                    for k in ("environment", "region", "runtime", "host", "deployment")
                )
            ]
            out.append(
                view(
                    name,
                    selected or all_ids,
                    fallback=not selected,
                    reason="no deployment metadata (properties.environment/region/runtime/host) on any node",
                    hint="set properties.environment/runtime on deployed components",
                )
            )
        elif key == "dataflow":
            data_edges = [
                e
                for e in ir["edges"]
                if e.get("kind") in {"data", "read", "write", "async"}
                or any(
                    w in (e.get("label") or "").lower()
                    for w in ("data", "event", "read", "write", "publish", "consume")
                )
            ]
            selected = sorted(
                {x for e in data_edges for x in (e["source"], e["target"])}
            )
            out.append(
                view(
                    name,
                    selected or all_ids,
                    fallback=not selected,
                    reason="no data-flow edges (kind data/read/write/async or data-event labels)",
                    hint="set edge kind=data/async or label edges with data verbs (publish, consume, read)",
                )
            )
        elif key == "security":
            selected = [
                nid
                for nid, n in nodes.items()
                if n.get("kind") in {"external", "gateway", "database", "actor"}
                or n.get("properties", {}).get("trust_boundary")
            ]
            for e in ir["edges"]:
                a, b = nodes.get(e["source"], {}), nodes.get(e["target"], {})
                if a.get("properties", {}).get("trust_boundary") != b.get(
                    "properties", {}
                ).get("trust_boundary"):
                    selected.extend([e["source"], e["target"]])
            selected = list(dict.fromkeys(selected))
            out.append(
                view(
                    name,
                    selected or all_ids,
                    fallback=not selected,
                    reason="no trust boundaries (properties.trust_boundary) and no external/database/actor/gateway nodes",
                    hint="set properties.trust_boundary on components or mark external systems with kind=external",
                )
            )
        else:
            out.append(view(name, all_ids))
    return out


def adjacency(ir, reverse=False, kinds=None):
    out = defaultdict(list)
    for e in ir["edges"]:
        if kinds and e.get("kind") not in kinds:
            continue
        a, b = (e["target"], e["source"]) if reverse else (e["source"], e["target"])
        out[a].append((b, e))
    return out


def shortest_path(ir, source, target):
    adj = adjacency(ir)
    q, prev = deque([source]), {source: None}
    while q:
        cur = q.popleft()
        if cur == target:
            break
        for nxt, _ in adj.get(cur, []):
            if nxt not in prev:
                prev[nxt] = cur
                q.append(nxt)
    if target not in prev:
        return []
    path, cur = [], target
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    return list(reversed(path))


def find_cycles(ir):
    adj = {k: [n for n, _ in v] for k, v in adjacency(ir).items()}
    visiting, done, stack, cycles = set(), set(), [], []

    def visit(node):
        if node in visiting:
            i = stack.index(node)
            cyc = stack[i:] + [node]
            if cyc not in cycles:
                cycles.append(cyc)
            return
        if node in done:
            return
        visiting.add(node)
        stack.append(node)
        for nxt in adj.get(node, []):
            visit(nxt)
        stack.pop()
        visiting.remove(node)
        done.add(node)

    for n in [x["id"] for x in ir["nodes"]]:
        visit(n)
    return cycles


def contrast_ratio(a, b):
    def lum(color):
        color = color.lstrip("#")
        if len(color) != 6:
            return None
        try:
            vals = [int(color[i : i + 2], 16) / 255 for i in (0, 2, 4)]
        except ValueError:
            return None
        vals = [
            v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in vals
        ]
        return 0.2126 * vals[0] + 0.7152 * vals[1] + 0.0722 * vals[2]

    la, lb = lum(a), lum(b)
    if la is None or lb is None:
        return None
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def style_value(style, key, default=None):
    m = re.search(rf"(?:^|;){re.escape(key)}=([^;]+)", style or "")
    return m.group(1) if m else default


DEFAULT_RULES = [
    "no-direct-internet-to-database",
    "no-cycles",
    "no-orphans",
    "accessible-contrast",
]

ARCHITECTURE_KINDS = {
    "service",
    "gateway",
    "database",
    "queue",
    "external",
    "actor",
    "cache",
    "topic",
}
CODE_KINDS = {"module", "library", "command", "adapter"}


def infer_profile(ir):
    """Return 'code' when the model is a source-code graph (module/library/
    command kinds and no architecture kinds), else 'architecture'."""
    ir = normalize_ir(ir)
    kinds = {n.get("kind") for n in ir["nodes"]}
    if kinds & ARCHITECTURE_KINDS:
        return "architecture"
    if kinds & CODE_KINDS:
        return "code"
    return "architecture"


def semantic_findings(ir, rule_ids=None):
    ir = normalize_ir(ir)
    rules = rule_ids or DEFAULT_RULES
    nodes = {n["id"]: n for n in ir["nodes"]}
    incoming, outgoing = adjacency(ir, reverse=True), adjacency(ir)
    findings = []

    def add(rule, severity, subject, message, fix):
        findings.append(
            {
                "rule": rule,
                "severity": severity,
                "subject": subject,
                "message": message,
                "fix": fix,
            }
        )

    if "no-direct-internet-to-database" in rules:
        for e in ir["edges"]:
            src, dst = nodes.get(e["source"], {}), nodes.get(e["target"], {})
            if (
                src.get("kind") in {"external", "actor"}
                or "internet" in src.get("label", "").lower()
            ) and dst.get("kind") == "database":
                add(
                    "no-direct-internet-to-database",
                    "error",
                    e["id"],
                    f"{src.get('label')} reaches database {dst.get('label')} directly",
                    "insert an authenticated gateway/service boundary",
                )
    if "no-cycles" in rules:
        for cyc in find_cycles(ir):
            add(
                "no-cycles",
                "warning",
                " -> ".join(cyc),
                "cyclic dependency detected",
                "break the cycle or make the dependency asynchronous",
            )
    if "no-orphans" in rules and len(nodes) > 1:
        for nid, n in nodes.items():
            if not incoming.get(nid) and not outgoing.get(nid):
                add(
                    "no-orphans",
                    "warning",
                    nid,
                    f"{n['label']} is disconnected",
                    "connect it or mark properties.intentional_orphan=true",
                )
    if "every-service-has-owner" in rules:
        for nid, n in nodes.items():
            if n.get("kind") in {
                "service",
                "gateway",
                "database",
                "queue",
            } and not n.get("properties", {}).get("owner"):
                add(
                    "every-service-has-owner",
                    "warning",
                    nid,
                    f"{n['label']} has no owner",
                    "set properties.owner",
                )
    if "production-has-observability" in rules:
        for nid, n in nodes.items():
            p = n.get("properties", {})
            if str(p.get("environment", "")).lower() in {
                "prod",
                "production",
            } and not p.get("observability"):
                add(
                    "production-has-observability",
                    "warning",
                    nid,
                    f"production component {n['label']} has no observability metadata",
                    "set properties.observability or add monitoring",
                )
    if "external-dependencies-have-timeouts" in rules:
        for e in ir["edges"]:
            if nodes.get(e["target"], {}).get("kind") == "external" and not e.get(
                "properties", {}
            ).get("timeout"):
                add(
                    "external-dependencies-have-timeouts",
                    "warning",
                    e["id"],
                    f"external call to {nodes[e['target']]['label']} has no timeout",
                    "set edge properties.timeout",
                )
    if "trust-boundaries-use-protocol" in rules:
        for e in ir["edges"]:
            a = nodes.get(e["source"], {}).get("properties", {}).get("trust_boundary")
            b = nodes.get(e["target"], {}).get("properties", {}).get("trust_boundary")
            if (
                a != b
                and not e.get("properties", {}).get("protocol")
                and not e.get("label")
            ):
                add(
                    "trust-boundaries-use-protocol",
                    "warning",
                    e["id"],
                    "unlabelled connection crosses a trust boundary",
                    "label the protocol and encryption",
                )
    if "accessible-contrast" in rules:
        for nid, n in nodes.items():
            fill = style_value(n.get("style", ""), "fillColor", "#ffffff")
            font = style_value(n.get("style", ""), "fontColor", "#000000")
            ratio = contrast_ratio(fill, font)
            if ratio is not None and ratio < 4.5:
                add(
                    "accessible-contrast",
                    "warning",
                    nid,
                    f"{n['label']} text contrast is {ratio:.2f}:1",
                    "use colors with at least 4.5:1 contrast",
                )
    return findings


def articulation_points(ir):
    graph = defaultdict(set)
    for e in ir["edges"]:
        graph[e["source"]].add(e["target"])
        graph[e["target"]].add(e["source"])
    disc, low, parent, points, tick = {}, {}, {}, set(), [0]

    def dfs(u):
        children = 0
        tick[0] += 1
        disc[u] = low[u] = tick[0]
        for v in graph[u]:
            if v not in disc:
                parent[v] = u
                children += 1
                dfs(v)
                low[u] = min(low[u], low[v])
                if u not in parent and children > 1:
                    points.add(u)
                if u in parent and low[v] >= disc[u]:
                    points.add(u)
            elif parent.get(u) != v:
                low[u] = min(low[u], disc[v])

    for n in [x["id"] for x in ir["nodes"]]:
        if n not in disc:
            dfs(n)
    return sorted(points)


def review(ir):
    ir = normalize_ir(ir)
    node_map = nodes_by_id(ir)
    findings = semantic_findings(
        ir,
        [
            "no-direct-internet-to-database",
            "no-cycles",
            "every-service-has-owner",
            "production-has-observability",
            "external-dependencies-have-timeouts",
            "trust-boundaries-use-protocol",
            "accessible-contrast",
        ],
    )
    degree = defaultdict(int)
    for e in ir["edges"]:
        degree[e["source"]] += 1
        degree[e["target"]] += 1
    labels = {n["id"]: n["label"] for n in ir["nodes"]}
    for nid in articulation_points(ir):
        findings.append(
            {
                "rule": "single-point-of-failure",
                "severity": "warning",
                "subject": nid,
                "message": f"{labels.get(nid, nid)} connects otherwise separated parts of the system",
                "fix": "add redundancy or an alternate path",
            }
        )
    for nid, deg in degree.items():
        if deg >= 6:
            findings.append(
                {
                    "rule": "high-coupling",
                    "severity": "info",
                    "subject": nid,
                    "message": f"{labels.get(nid, nid)} has {deg} connections",
                    "fix": "verify the component is intentionally a hub",
                }
            )
    # Long synchronous chains amplify latency and correlated failure. Limit the
    # search to simple paths and report only maximal chains to avoid noise.
    sync_adj = adjacency(ir, kinds={"sync", "relation", "read", "write"})
    long_paths, budget = set(), [5000]

    def walk(cur, path):
        if budget[0] <= 0:
            return
        budget[0] -= 1
        advanced = False
        for nxt, _ in sync_adj.get(cur, []):
            if nxt not in path and len(path) < 12:
                advanced = True
                walk(nxt, path + [nxt])
        if not advanced and len(path) >= 5:
            long_paths.add(tuple(path))

    for nid in labels:
        walk(nid, [nid])
    for path in sorted(long_paths, key=lambda p: (-len(p), p))[:5]:
        findings.append(
            {
                "rule": "long-synchronous-chain",
                "severity": "info",
                "subject": " -> ".join(path),
                "message": f"synchronous path spans {len(path)} components",
                "fix": "verify latency budget, timeouts, and whether an asynchronous boundary is appropriate",
            }
        )
    for e in ir["edges"]:
        a, b = node_map.get(e["source"], {}), node_map.get(e["target"], {})
        ap, bp = a.get("properties", {}), b.get("properties", {})
        sensitive = e.get("properties", {}).get("data_classification") in {
            "sensitive",
            "restricted",
            "pii",
            "pci",
        }
        if (
            sensitive
            and ap.get("region")
            and bp.get("region")
            and ap["region"] != bp["region"]
            and not e.get("properties", {}).get("residency_approved")
        ):
            findings.append(
                {
                    "rule": "sensitive-data-region-crossing",
                    "severity": "warning",
                    "subject": e["id"],
                    "message": f"sensitive data crosses regions {ap['region']} -> {bp['region']}",
                    "fix": "verify residency requirements or set properties.residency_approved with evidence",
                }
            )
    return {
        "schema": "drawio-skill/review/v1",
        "generated": utc_now(),
        "summary": {
            "nodes": len(ir["nodes"]),
            "edges": len(ir["edges"]),
            "errors": sum(f["severity"] == "error" for f in findings),
            "warnings": sum(f["severity"] == "warning" for f in findings),
        },
        "findings": findings,
    }


def impact_analysis(ir, failed):
    ir = normalize_ir(ir)
    if failed not in {n["id"] for n in ir["nodes"]}:
        raise ValueError(f"unknown node {failed!r}")
    adj = adjacency(ir)
    impacted, q = set(), deque([failed])
    paths = {failed: [failed]}
    while q:
        cur = q.popleft()
        for nxt, edge in adj.get(cur, []):
            if edge.get("properties", {}).get("isolates_failure"):
                continue
            if nxt not in impacted and nxt != failed:
                impacted.add(nxt)
                paths[nxt] = paths[cur] + [nxt]
                q.append(nxt)
    result = copy.deepcopy(ir)
    for n in result["nodes"]:
        if n["id"] == failed:
            n.setdefault("properties", {})["scenario_status"] = "failed"
            n["style"] = (
                "rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;strokeWidth=3;"
            )
        elif n["id"] in impacted:
            n.setdefault("properties", {})["scenario_status"] = "impacted"
            n["style"] = (
                "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;"
            )
    return {
        "failed": failed,
        "impacted": sorted(impacted),
        "paths": paths,
        "diagram": result,
    }


def query(ir, kind=None, owner=None, boundary=None, source=None, target=None):
    ir = normalize_ir(ir)
    nodes = ir["nodes"]
    if kind:
        nodes = [n for n in nodes if n.get("kind") == kind]
    if owner:
        nodes = [n for n in nodes if n.get("properties", {}).get("owner") == owner]
    if boundary:
        nodes = [
            n
            for n in nodes
            if n.get("properties", {}).get("trust_boundary") == boundary
        ]
    result = {"nodes": nodes, "edges": []}
    if source and target:
        path = shortest_path(ir, source, target)
        selected = set(path)
        pairs = set(zip(path, path[1:]))
        result["nodes"] = [n for n in ir["nodes"] if n["id"] in selected]
        result["edges"] = [
            e for e in ir["edges"] if (e["source"], e["target"]) in pairs
        ]
        result["path"] = path
    else:
        selected = {n["id"] for n in nodes}
        result["edges"] = [
            e
            for e in ir["edges"]
            if e["source"] in selected and e["target"] in selected
        ]
    return result


def nodes_by_id(ir):
    return {n["id"]: n for n in ir["nodes"]}


def reconcile(existing_path, incoming_ir, output_path, prune=False):
    """Patch the first uncompressed page, preserving matching geometry/style."""
    incoming_ir = normalize_ir(incoming_ir)
    tree = ET.parse(existing_path)
    page = (tree.getroot().findall("diagram") or [tree.getroot()])[0]
    model = page.find("mxGraphModel")
    root = model.find("root") if model is not None else None
    if root is None:
        raise ValueError("reconcile requires an uncompressed draw.io page")
    rows = list(iter_cells(model))
    by_model, holders = {}, {}
    parent_ids = {cell.get("parent") for _, cell in rows if cell.get("parent")}
    for holder, cell in rows:
        cid = holder.get("id") or cell.get("id")
        mid = holder.get("data-model-id") or cell.get("data-model-id") or cid
        if (
            cell.get("vertex") == "1"
            and mid
            and cid not in parent_ids
            and "edgeLabel" not in (cell.get("style") or "")
        ):
            by_model[mid] = cell
            holders[mid] = holder
    incoming_nodes = {n["id"]: n for n in incoming_ir["nodes"]}
    existing_ids = set(by_model)
    added, changed, removed, conflicts = (
        [],
        [],
        sorted(existing_ids - set(incoming_nodes) - {"0", "1"}),
        [],
    )
    # Place additions below the current diagram; neighbour-aware horizontal offset.
    max_y = 0.0
    for cell in by_model.values():
        g = cell.find("mxGeometry")
        if g is not None:
            try:
                max_y = max(max_y, float(g.get("y", 0)) + float(g.get("height", 70)))
            except ValueError:
                pass
    id_to_cell_id = {
        mid: (holders[mid].get("id") or cell.get("id"))
        for mid, cell in by_model.items()
    }
    for i, (nid, n) in enumerate(incoming_nodes.items()):
        if nid in by_model:
            cell, holder = by_model[nid], holders[nid]
            old_label = holder.get("label") if holder is not cell else cell.get("value")
            prior_label = holder.get("data-source-label") or cell.get(
                "data-source-label"
            )
            if clean_label(old_label) != n["label"]:
                changed.append(nid)
                if (
                    prior_label is not None
                    and clean_label(old_label) != prior_label
                    and n["label"] != prior_label
                ):
                    conflicts.append(
                        {
                            "id": nid,
                            "field": "label",
                            "manual": clean_label(old_label),
                            "incoming": n["label"],
                        }
                    )
                    holder.set("data-conflict", "label")
                elif holder is cell:
                    cell.set("value", n["label"])
                else:
                    holder.set("label", n["label"])
            cell.set("data-model-id", nid)
            cell.set("data-kind", n.get("kind", "service"))
            incoming_props = n.get("properties", {})
            current_props = _json_attr(holder, "data-properties") or _json_attr(
                cell, "data-properties"
            )
            prior_props = _json_attr(holder, "data-source-properties") or _json_attr(
                cell, "data-source-properties"
            )
            merged = dict(incoming_props)
            conflict_keys = []
            if prior_props:
                for key, value in current_props.items():
                    if (
                        prior_props.get(key) != value
                        and incoming_props.get(key) != prior_props.get(key)
                        and incoming_props.get(key) != value
                    ):
                        merged[key] = value
                        conflict_keys.append(key)
            if conflict_keys:
                conflicts.append(
                    {"id": nid, "field": "properties", "keys": sorted(conflict_keys)}
                )
                holder.set("data-conflict-properties", ",".join(sorted(conflict_keys)))
            props_text = json.dumps(merged, ensure_ascii=False, separators=(",", ":"))
            source_props_text = json.dumps(
                incoming_props, ensure_ascii=False, separators=(",", ":")
            )
            holder.set("data-properties", props_text)
            holder.set("data-source-properties", source_props_text)
            holder.set("data-source-label", n["label"])
            if n.get("provenance"):
                cell.set(
                    "data-provenance",
                    json.dumps(
                        n["provenance"], ensure_ascii=False, separators=(",", ":")
                    ),
                )
            continue
        cid = stable_id(nid, set(id_to_cell_id.values()))
        id_to_cell_id[nid] = cid
        added.append(nid)
        cell = ET.Element(
            "mxCell",
            {
                "id": cid,
                "value": n["label"],
                "vertex": "1",
                "parent": "1",
                "style": n.get("style")
                or KIND_STYLE.get(n.get("kind"), DEFAULT_NODE_STYLE),
                "data-model-id": nid,
                "data-kind": n.get("kind", "service"),
                "data-status": "added",
                "data-properties": json.dumps(
                    n.get("properties", {}), ensure_ascii=False, separators=(",", ":")
                ),
                "data-source-properties": json.dumps(
                    n.get("properties", {}), ensure_ascii=False, separators=(",", ":")
                ),
                "data-source-label": n["label"],
            },
        )
        if n.get("provenance"):
            cell.set(
                "data-provenance",
                json.dumps(n["provenance"], ensure_ascii=False, separators=(",", ":")),
            )
        ET.SubElement(
            cell,
            "mxGeometry",
            {
                "x": str(60 + (i % 4) * 220),
                "y": str(max_y + 100 + (i // 4) * 130),
                "width": str(n.get("width", 160)),
                "height": str(n.get("height", 70)),
                "as": "geometry",
            },
        )
        root.append(cell)
        by_model[nid] = cell
        holders[nid] = cell
    for nid in removed:
        holder, cell = holders[nid], by_model[nid]
        if prune:
            root.remove(holder)
        else:
            cell.set("data-status", "removed")
            style = cell.get("style") or DEFAULT_NODE_STYLE
            cell.set("style", style + "dashed=1;opacity=45;strokeColor=#b85450;")
    # Reconcile edges by semantic id, then endpoint signature.
    edge_rows = []
    for holder, cell in list(iter_cells(model)):
        if cell.get("edge") == "1":
            mid = (
                holder.get("data-model-id")
                or cell.get("data-model-id")
                or holder.get("id")
                or cell.get("id")
            )
            edge_rows.append((mid, holder, cell))
    edge_by_id = {mid: (holder, cell) for mid, holder, cell in edge_rows}
    used_cell_ids = {c.get("id") for _, c in rows if c.get("id")}
    incoming_edge_ids, changed_edges = set(), []
    for i, e in enumerate(incoming_ir["edges"]):
        if e["source"] not in id_to_cell_id or e["target"] not in id_to_cell_id:
            continue
        incoming_edge_ids.add(e["id"])
        if e["id"] in edge_by_id:
            holder, cell = edge_by_id[e["id"]]
            cell.set("source", id_to_cell_id[e["source"]])
            cell.set("target", id_to_cell_id[e["target"]])
            old_label = (
                holder.get("label") if holder is not cell else cell.get("value", "")
            )
            prior_label = holder.get("data-source-label") or cell.get(
                "data-source-label"
            )
            incoming_label = e.get("label", "")
            if clean_label(old_label) != incoming_label:
                changed_edges.append(e["id"])
                if (
                    prior_label is not None
                    and clean_label(old_label) != prior_label
                    and incoming_label != prior_label
                ):
                    conflicts.append(
                        {
                            "id": e["id"],
                            "field": "edge-label",
                            "manual": clean_label(old_label),
                            "incoming": incoming_label,
                        }
                    )
                    holder.set("data-conflict", "edge-label")
                elif holder is cell:
                    cell.set("value", incoming_label)
                else:
                    holder.set("label", incoming_label)
            properties = json.dumps(
                e.get("properties", {}), ensure_ascii=False, separators=(",", ":")
            )
            cell.set("data-properties", properties)
            cell.set("data-source-properties", properties)
            cell.set("data-source-label", incoming_label)
        else:
            cid = stable_id(f"edge-{e['id']}", used_cell_ids)
            used_cell_ids.add(cid)
            cell = ET.Element(
                "mxCell",
                {
                    "id": cid,
                    "value": e.get("label", ""),
                    "edge": "1",
                    "parent": "1",
                    "source": id_to_cell_id[e["source"]],
                    "target": id_to_cell_id[e["target"]],
                    "style": e.get("style") or DEFAULT_EDGE_STYLE,
                    "data-model-id": e["id"],
                    "data-kind": e.get("kind", "relation"),
                    "data-status": "added",
                    "data-properties": json.dumps(
                        e.get("properties", {}),
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                    "data-source-properties": json.dumps(
                        e.get("properties", {}),
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                    "data-source-label": e.get("label", ""),
                },
            )
            ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})
            root.append(cell)
    for mid, holder, cell in edge_rows:
        if mid not in incoming_edge_ids:
            if prune:
                root.remove(holder)
            else:
                cell.set("data-status", "removed")
                cell.set(
                    "style",
                    (cell.get("style") or DEFAULT_EDGE_STYLE)
                    + "dashed=1;opacity=35;strokeColor=#b85450;",
                )
    tree.getroot().set("modified", utc_now())
    ET.indent(tree.getroot(), space="  ")
    tree.write(output_path, encoding="unicode", xml_declaration=False)
    # pi-lens-ignore: ast-grep:unchecked-throwing-call-python
    with open(output_path, "a", encoding="utf-8") as fh:
        fh.write("\n")
    return {
        "added": added,
        "changed": changed,
        "removed": removed,
        "changed_edges": changed_edges,
        "conflicts": conflicts,
        "output": output_path,
    }


def accessible_description(ir):
    ir = normalize_ir(ir)
    kinds = defaultdict(int)
    for n in ir["nodes"]:
        kinds[n.get("kind", "service")] += 1
    kind_text = ", ".join(f"{v} {k}" for k, v in sorted(kinds.items()))
    return f"{ir['metadata'].get('title', 'Diagram')}: {len(ir['nodes'])} components ({kind_text}) and {len(ir['edges'])} relationships."


def story_html(ir, title=None, scenario=None):
    ir = normalize_ir(ir)
    title = title or ir["metadata"].get("title") or "Architecture Story"
    nodes = ir["nodes"]
    edges = ir["edges"]
    # pi-lens-ignore: ast-grep:unchecked-throwing-call-python
    cols = max(1, int(math.ceil(math.sqrt(max(1, len(nodes))))))
    positions = {
        n["id"]: (100 + (i % cols) * 240, 90 + (i // cols) * 150)
        for i, n in enumerate(nodes)
    }
    width = max(640, cols * 240 + 120)
    rows = math.ceil(max(1, len(nodes)) / cols)
    height = rows * 150 + 100
    svg_edges = []
    for e in edges:
        if e["source"] in positions and e["target"] in positions:
            x1, y1 = positions[e["source"]]
            x2, y2 = positions[e["target"]]
            svg_edges.append(
                f'<line class="edge" data-source="{html.escape(e["source"])}" data-target="{html.escape(e["target"])}" x1="{x1 + 75}" y1="{y1 + 25}" x2="{x2 + 75}" y2="{y2 + 25}" marker-end="url(#arrow)"/><text x="{(x1 + x2) / 2 + 75}" y="{(y1 + y2) / 2 + 18}">{html.escape(e.get("label", ""))}</text>'
            )
    svg_nodes, steps, languages = [], [], set()
    for i, n in enumerate(nodes):
        x, y = positions[n["id"]]
        status = n.get("properties", {}).get("scenario_status", "")
        svg_nodes.append(
            f'<g class="node {html.escape(status)}" id="node-{html.escape(slug(n["id"]))}" data-id="{html.escape(n["id"])}" tabindex="0" role="button" aria-label="{html.escape(n["label"] + ", " + n.get("kind", "service"))}"><rect x="{x}" y="{y}" width="150" height="55" rx="10"/><text x="{x + 75}" y="{y + 33}" text-anchor="middle">{html.escape(n["label"])}</text></g>'
        )
        owner = n.get("properties", {}).get("owner")
        boundary = n.get("properties", {}).get("trust_boundary")
        prov = n.get("provenance", {})
        source = prov.get("path")
        if source and prov.get("line"):
            source = f"{source}:{prov['line']}"
        detail = (
            f"{n.get('kind', 'service')}"
            + (f" · owner: {owner}" if owner else "")
            + (f" · boundary: {boundary}" if boundary else "")
            + (f" · source: {source}" if source else "")
        )
        labels = n.get("labels", {})
        languages.update(labels)
        steps.append(
            {"id": n["id"], "title": n["label"], "detail": detail, "labels": labels}
        )
    data = json.dumps(
        {"steps": steps, "scenario": scenario or {}, "languages": sorted(languages)},
        ensure_ascii=False,
    ).replace("</", "<\\/")
    desc = html.escape(accessible_description(ir))
    text_alternative = "".join(
        f"<li>{html.escape(s['title'])} — {html.escape(s['detail'])}</li>"
        for s in steps
    )
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title><style>
body{{font:16px system-ui;margin:0;background:#f7f8fa;color:#17202a}}header,main{{max-width:1200px;margin:auto;padding:18px}}.toolbar{{display:flex;gap:8px;align-items:center}}button{{padding:8px 14px}}svg{{background:white;border:1px solid #ccd2da;width:100%;height:auto}}.node rect{{fill:#dae8fc;stroke:#6c8ebf;stroke-width:2}}.node.failed rect{{fill:#f8cecc;stroke:#b85450}}.node.impacted rect{{fill:#ffe6cc;stroke:#d79b00}}.node.active rect{{stroke:#005fcc;stroke-width:5}}.edge{{stroke:#65717e;stroke-width:2}}svg text{{font:13px system-ui;fill:#17202a}}#narration{{padding:12px;background:#fff;border-left:4px solid #005fcc;margin:12px 0}}.sr-only{{position:absolute;left:-10000px}}@media(prefers-reduced-motion:no-preference){{.node{{transition:opacity .2s}}}}</style></head><body>
<header><h1>{html.escape(title)}</h1><p>{desc}</p><div class="toolbar"><button id="prev">Previous</button><button id="next">Next</button><button id="reset">Overview</button><label id="langWrap" hidden>Language <select id="language"><option value="">Default</option></select></label><span id="counter" aria-live="polite"></span></div><div id="narration" aria-live="polite">Use Next to walk through the architecture.</div></header><main><svg viewBox="0 0 {width} {height}" role="img" aria-labelledby="diagram-title diagram-desc"><title id="diagram-title">{html.escape(title)}</title><desc id="diagram-desc">{desc}</desc><defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#65717e"/></marker></defs>{"".join(svg_edges)}{"".join(svg_nodes)}</svg><details><summary>Text alternative</summary><ol>{text_alternative}</ol></details></main><script>
const DATA={data};let i=-1;const nodes=[...document.querySelectorAll('.node')];function titleOf(s){{return (language.value&&s.labels&&s.labels[language.value])||s.title}}function show(n){{i=n;nodes.forEach(x=>x.classList.remove('active'));if(i>=0&&i<DATA.steps.length){{const s=DATA.steps[i],el=nodes.find(x=>x.dataset.id===s.id);if(el)el.classList.add('active');narration.textContent=titleOf(s)+' — '+s.detail;counter.textContent=(i+1)+' / '+DATA.steps.length}}else{{narration.textContent='Overview: all components and relationships.';counter.textContent='Overview'}}}}function setLanguage(){{DATA.steps.forEach(s=>{{const el=nodes.find(x=>x.dataset.id===s.id);if(el)el.querySelector('text').textContent=titleOf(s)}});show(i)}}if(DATA.languages.length){{langWrap.hidden=false;DATA.languages.forEach(x=>language.add(new Option(x,x)));language.onchange=setLanguage}}nodes.forEach(el=>{{el.onclick=()=>show(DATA.steps.findIndex(s=>s.id===el.dataset.id));el.onkeydown=e=>{{if(e.key==='Enter'||e.key===' ')el.click()}}}});prev.onclick=()=>show(Math.max(-1,i-1));next.onclick=()=>show(Math.min(DATA.steps.length-1,i+1));reset.onclick=()=>show(-1);document.addEventListener('keydown',e=>{{if(e.key==='ArrowRight')next.click();if(e.key==='ArrowLeft')prev.click()}});show(-1);
</script></body></html>"""
