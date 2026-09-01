#!/usr/bin/env python3
"""Unified command surface for drawio-skill 3.x.

The existing focused scripts remain stable public building blocks.  This CLI
adds orchestration and the semantic Diagram IR used for build/sync/views/test/
query/review/what-if/story workflows.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from diagram_ir import (
    DEFAULT_RULES,
    accessible_description,
    impact_analysis,
    infer_profile,
    load_ir,
    normalize_ir,
    project_views,
    reconcile,
    review,
    save_ir,
    semantic_findings,
    story_html,
    write_drawio,
)
from diagram_ir import (
    query as query_ir,
)

HERE = Path(__file__).resolve().parent
IMPORTERS = {
    "python": "pyimports.py",
    "javascript": "jsimports.py",
    "js": "jsimports.py",
    "go": "goimports.py",
    "rust": "rustimports.py",
    "pyclasses": "pyclasses.py",
    "terraform": "tfimports.py",
    "kubernetes": "k8simports.py",
    "k8s": "k8simports.py",
    "compose": "composeimports.py",
    "sql": "sqlerd.py",
    "openapi": "openapiimports.py",
    "ci": "ciimports.py",
}
CODE_IMPORTERS = {"python", "javascript", "js", "go", "rust", "pyclasses"}
TRANSFORMS = {
    "restyle": "restyle.py",
    "heatmap": "heatmap.py",
    "relabel": "relabel.py",
    "mermaid": "drawio2mermaid.py",
    "pptx": "drawio2pptx.py",
    "viewer": "drawiohtml.py",
    "animate": "svgflow.py",
    "compress": "compress.py",
    "runbook": "runbook.py",
    "buildup": "buildup.py",
    "explain": "explain.py",
}


def emit(value, output=None):
    text = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)


def detect_source(path):
    p = Path(path)
    if p.is_dir():
        if list(p.rglob("*.tf")):
            return "terraform"
        if (p / "Cargo.toml").exists():
            return "rust"
        if (p / "go.mod").exists():
            return "go"
        if (p / "package.json").exists():
            return "javascript"
        if (p / ".github" / "workflows").exists() or (p / ".gitlab-ci.yml").exists():
            return "ci"
        return "python"
    suffix = p.suffix.lower()
    if suffix == ".sql":
        return "sql"
    if suffix in {".tf", ".tfvars"}:
        return "terraform"
    if suffix == ".drawio":
        return "drawio"
    if suffix == ".json":
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if data.get("schema") == "drawio-skill/diagram-ir/v1":
                return "ir"
            if "openapi" in data or "swagger" in data:
                return "openapi"
        except (OSError, ValueError):
            pass
        return "graph"
    if suffix in {".yaml", ".yml"}:
        text = p.read_text(encoding="utf-8", errors="ignore")[:10000]
        if "openapi:" in text or "swagger:" in text:
            return "openapi"
        if "services:" in text:
            return "compose"
        return "kubernetes"
    return "graph"


def code_kind(prov_path, importer):
    """Semantic kind for a code-source node (v3.2 P0 source profiles).

    Package roots become `library`, entrypoints become `command`, everything
    else is an ordinary `module`. Go packages are library units by definition.
    """
    base = os.path.basename(prov_path or "")
    stem = base.rsplit(".", 1)[0].lower()
    if importer == "go" or stem in {"__init__", "lib"}:
        return "library"
    if stem in {"__main__", "main", "cli"}:
        return "command"
    return "module"


def _resolve_provenance(ir, root_abs):
    """Resolve importer-relative provenance paths against the scanned root."""
    for node in ir["nodes"]:
        prov = node.setdefault("provenance", {})
        rel = prov.get("path")
        if rel and not os.path.isabs(rel):
            prov["path"] = os.path.normpath(os.path.join(root_abs, rel))
        elif not rel:
            prov["path"] = root_abs
    for edge in ir["edges"]:
        prov = edge.get("provenance")
        if prov and prov.get("path") and not os.path.isabs(prov["path"]):
            prov["path"] = os.path.normpath(os.path.join(root_abs, prov["path"]))


def importer_ir(source, source_type, group=False):
    script = HERE / IMPORTERS[source_type]
    with tempfile.TemporaryDirectory(prefix="drawio-skill-") as td:
        graph_path = Path(td) / "graph.json"
        cmd = [sys.executable, str(script), source, "-o", str(graph_path)]
        if group and source_type in {
            "python",
            "javascript",
            "js",
            "go",
            "rust",
            "pyclasses",
            "openapi",
        }:
            cmd.insert(-2, "--group")
        proc = subprocess.run(cmd, text=True, capture_output=True)
        if proc.returncode:
            raise RuntimeError(
                proc.stderr.strip() or proc.stdout.strip() or f"{script.name} failed"
            )
        # pi-lens-ignore: ast-grep:unchecked-throwing-call-python
        raw = json.loads(graph_path.read_text(encoding="utf-8"))
    ir = normalize_ir(raw, source_path=source)
    ir["metadata"]["importer"] = source_type
    root_abs = os.path.abspath(source)
    _resolve_provenance(ir, root_abs)
    is_code = source_type in CODE_IMPORTERS
    for node in ir["nodes"]:
        prov = node.setdefault("provenance", {})
        prov["importer"] = source_type
        if is_code:
            # Source profile: real file kinds instead of a blanket "service".
            node["kind"] = code_kind(prov.get("path", ""), source_type)
    return ir


def source_ir(source, source_type="auto", group=False):
    source_type = detect_source(source) if source_type == "auto" else source_type
    if source_type in {"graph", "ir", "drawio"}:
        return load_ir(source), source_type
    if source_type not in IMPORTERS:
        raise ValueError(f"unsupported source type {source_type!r}")
    return importer_ir(source, source_type, group=group), source_type


def cmd_doctor(args):
    drawio = shutil.which("drawio") or shutil.which("draw.io")
    if not drawio and Path("/Applications/draw.io.app/Contents/MacOS/draw.io").exists():
        drawio = "/Applications/draw.io.app/Contents/MacOS/draw.io"
    checks = {
        "python": {
            "status": "ok",
            "path": sys.executable,
            "version": sys.version.split()[0],
        },
        "drawio": {
            "status": "available" if drawio else "missing",
            "path": drawio,
            "note": "not executed unless --probe is passed; safe in macOS sandboxes",
        },
        "graphviz": {
            "status": "available" if shutil.which("dot") else "missing",
            "path": shutil.which("dot"),
        },
        "git": {
            "status": "available" if shutil.which("git") else "missing",
            "path": shutil.which("git"),
        },
    }
    for mod in ("yaml", "pptx", "PIL"):
        try:
            available = importlib.util.find_spec(mod) is not None
            if not available:
                raise ModuleNotFoundError(mod)
            checks[mod] = {"status": "available"}
        except (ImportError, ModuleNotFoundError, ValueError):
            checks[mod] = {"status": "optional-missing"}
    if args.probe and drawio:
        try:
            p = subprocess.run(
                [drawio, "--version"], capture_output=True, text=True, timeout=8
            )
            checks["drawio"].update(
                {
                    "probe": "ok" if p.returncode == 0 else "failed",
                    "version": (p.stdout or p.stderr).strip(),
                }
            )
        except (subprocess.TimeoutExpired, OSError) as exc:
            checks["drawio"].update({"probe": "failed", "error": str(exc)})
    checks["capabilities"] = {
        "xml_generation": True,
        "semantic_ir": True,
        "sync": True,
        "native_export": bool(drawio),
        "auto_layout": bool(shutil.which("dot")),
        "network_required": False,
    }
    emit(checks, args.output)


def cmd_build(args):
    ir, source_type = source_ir(args.source, args.source_type, group=args.group)
    ir["metadata"]["title"] = args.title or ir["metadata"].get("title")
    views = project_views(ir, args.views.split(",")) if args.views else None
    write_drawio(ir, args.output, views=views, direction=args.direction)
    if args.ir_output:
        save_ir(ir, args.ir_output)
    emit(
        {
            "output": args.output,
            "ir": args.ir_output,
            "source_type": source_type,
            "nodes": len(ir["nodes"]),
            "edges": len(ir["edges"]),
            "views": [
                {
                    "name": v["name"],
                    "nodes": len(v["nodes"]),
                    "fallback": v.get("fallback", False),
                    "fallback_reason": v.get("fallback_reason"),
                }
                for v in views
            ]
            if views
            else ["System"],
        }
    )


def cmd_inspect(args):
    ir = load_ir(args.input)
    kinds, owners, sources = {}, {}, set()
    for n in ir["nodes"]:
        kinds[n["kind"]] = kinds.get(n["kind"], 0) + 1
        owner = n.get("properties", {}).get("owner")
        if owner:
            owners[owner] = owners.get(owner, 0) + 1
        prov = n.get("provenance", {})
        if prov.get("path"):
            sources.add(prov["path"])
    emit(
        {
            "title": ir["metadata"].get("title"),
            "nodes": len(ir["nodes"]),
            "edges": len(ir["edges"]),
            "kinds": kinds,
            "owners": owners,
            "sources": sorted(sources),
            "alt_text": accessible_description(ir),
        },
        args.output,
    )


def cmd_query(args):
    if bool(args.source) != bool(args.target):
        raise ValueError("path queries require both --from and --to")
    emit(
        query_ir(
            load_ir(args.input),
            kind=args.kind,
            owner=args.owner,
            boundary=args.boundary,
            source=args.source,
            target=args.target,
        ),
        args.output,
    )


def load_rules(path):
    if not path:
        return DEFAULT_RULES
    text = Path(path).read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    # pi-lens-ignore: ast-grep:unchecked-throwing-call-python
    # pi-lens-ignore: ast-grep:no-boolean-in-except
    except ValueError:
        try:
            import yaml

            data = yaml.safe_load(text)
        # pi-lens-ignore: ast-grep:unchecked-throwing-call-python
        # pi-lens-ignore: ast-grep:no-boolean-in-except
        except ImportError:
            rules, in_rules = [], False
            for line in text.splitlines():
                if line.strip() == "rules:":
                    in_rules = True
                    continue
                if in_rules and line.strip().startswith("-"):
                    rules.append(line.split("-", 1)[1].strip())
            data = {"rules": rules}
    rules = data.get("rules", data) if isinstance(data, dict) else data
    out = []
    for rule in rules or []:
        out.append(rule.get("id") if isinstance(rule, dict) else str(rule))
    return out


def cmd_test(args):
    ir = load_ir(args.input)
    findings = semantic_findings(ir, load_rules(args.rules))
    result = {
        "profile": infer_profile(ir),
        "errors": sum(f["severity"] == "error" for f in findings),
        "warnings": sum(f["severity"] == "warning" for f in findings),
        "findings": findings,
    }
    emit(result, args.output)
    if result["errors"] or (args.strict and result["warnings"]):
        return 1
    return 0


def review_markdown(report):
    lines = [
        "# Architecture Review",
        "",
        f"- Nodes: {report['summary']['nodes']}",
        f"- Edges: {report['summary']['edges']}",
        f"- Errors: {report['summary']['errors']}",
        f"- Warnings: {report['summary']['warnings']}",
        "",
        "## Findings",
        "",
    ]
    for f in report["findings"]:
        lines += [
            f"- **{f['severity'].upper()} · {f['rule']} · {f['subject']}** — {f['message']}",
            f"  - Suggested action: {f['fix']}",
        ]
    if not report["findings"]:
        lines.append("No findings.")
    return "\n".join(lines) + "\n"


def cmd_review(args):
    report = review(load_ir(args.input))
    if args.format == "markdown":
        text = review_markdown(report)
        if args.output:
            Path(args.output).write_text(text, encoding="utf-8")
        else:
            sys.stdout.write(text)
    else:
        emit(report, args.output)


def cmd_sync(args):
    ir, source_type = source_ir(args.source, args.source_type, group=args.group)
    result = reconcile(args.diagram, ir, args.output, prune=args.prune)
    result["source_type"] = source_type
    emit(result)


def cmd_views(args):
    ir = load_ir(args.input)
    views = project_views(ir, args.views.split(",") if args.views else None)
    write_drawio(ir, args.output, views=views, direction=args.direction)
    emit(
        {
            "output": args.output,
            "views": [
                {
                    "name": v["name"],
                    "nodes": len(v["nodes"]),
                    "fallback": v.get("fallback", False),
                    "fallback_reason": v.get("fallback_reason"),
                    "hint": v.get("hint"),
                }
                for v in views
            ],
        }
    )


def cmd_whatif(args):
    result = impact_analysis(load_ir(args.input), args.fail)
    if args.drawio:
        write_drawio(result.pop("diagram"), args.drawio)
        result["drawio"] = args.drawio
    elif not args.include_ir:
        result.pop("diagram")
    emit(result, args.output)


def cmd_story(args):
    ir = load_ir(args.input)
    scenario = None
    if args.fail:
        impact = impact_analysis(ir, args.fail)
        ir, scenario = (
            impact["diagram"],
            {"failed": impact["failed"], "impacted": impact["impacted"]},
        )
    Path(args.output).write_text(
        story_html(ir, title=args.title, scenario=scenario), encoding="utf-8"
    )
    emit(
        {
            "output": args.output,
            "nodes": len(ir["nodes"]),
            "accessible": True,
            "offline": True,
            "scenario": scenario,
        }
    )


def cmd_transform(args):
    script = HERE / TRANSFORMS[args.operation]
    extra = list(args.arguments)
    if extra[:1] == ["--"]:
        extra.pop(0)
    cmd = [sys.executable, str(script), args.input] + extra
    proc = subprocess.run(cmd)
    return proc.returncode


def cmd_publish(args):
    if args.format == "story" or not args.input.lower().endswith(".drawio"):
        ir = load_ir(args.input)
        Path(args.output).write_text(story_html(ir, title=args.title), encoding="utf-8")
        emit({"output": args.output, "format": "story", "offline": True})
        return 0
    proc = subprocess.run(
        [sys.executable, str(HERE / "drawiohtml.py"), args.input, "-o", args.output]
    )
    return proc.returncode


def parser():
    ap = argparse.ArgumentParser(
        prog="diagramctl",
        description="Build, sync, test, query, review and publish draw.io architecture models.",
    )
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser(
        "doctor", help="report local capabilities without launching GUI tools"
    )
    p.add_argument(
        "--probe",
        action="store_true",
        help="execute draw.io --version with an 8 second timeout",
    )
    p.add_argument("-o", "--output")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser(
        "build", help="build a draw.io from IR, graph JSON, code, IaC, SQL or OpenAPI"
    )
    p.add_argument("source")
    p.add_argument("-o", "--output", required=True)
    p.add_argument(
        "--from",
        dest="source_type",
        default="auto",
        choices=["auto", "graph", "ir", "drawio"] + sorted(IMPORTERS),
    )
    p.add_argument("--group", action="store_true")
    p.add_argument("--direction", choices=["TB", "LR"], default="TB")
    p.add_argument(
        "--views", help="comma-separated executive,system,deployment,dataflow,security"
    )
    p.add_argument("--title")
    p.add_argument("--ir-output")
    p.set_defaults(func=cmd_build)

    p = sub.add_parser(
        "inspect", help="summarize structure, owners, provenance and accessible text"
    )
    p.add_argument("input")
    p.add_argument("-o", "--output")
    p.set_defaults(func=cmd_inspect)
    p = sub.add_parser("query", help="query nodes or find a directed path")
    p.add_argument("input")
    p.add_argument("--kind")
    p.add_argument("--owner")
    p.add_argument("--boundary")
    p.add_argument("--from", dest="source")
    p.add_argument("--to", dest="target")
    p.add_argument("-o", "--output")
    p.set_defaults(func=cmd_query)
    p = sub.add_parser("test", help="run semantic architecture rules")
    p.add_argument("input")
    p.add_argument("--rules")
    p.add_argument("--strict", action="store_true")
    p.add_argument("-o", "--output")
    p.set_defaults(func=cmd_test)
    p = sub.add_parser(
        "review",
        help="review ownership, resilience, trust boundaries and accessibility",
    )
    p.add_argument("input")
    p.add_argument("--format", choices=["json", "markdown"], default="markdown")
    p.add_argument("-o", "--output")
    p.set_defaults(func=cmd_review)
    for name in ("sync", "reconcile"):
        p = sub.add_parser(
            name,
            help="incrementally update a diagram while preserving manual geometry/style",
        )
        p.add_argument("diagram")
        p.add_argument("source")
        p.add_argument("-o", "--output", required=True)
        p.add_argument(
            "--from",
            dest="source_type",
            default="auto",
            choices=["auto", "graph", "ir"] + sorted(IMPORTERS),
        )
        p.add_argument("--group", action="store_true")
        p.add_argument("--prune", action="store_true")
        p.set_defaults(func=cmd_sync)
    p = sub.add_parser(
        "views", help="project one model into linked audience/concern views"
    )
    p.add_argument("input")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--views")
    p.add_argument("--direction", choices=["TB", "LR"], default="TB")
    p.set_defaults(func=cmd_views)
    p = sub.add_parser("whatif", help="simulate failure propagation")
    p.add_argument("input")
    p.add_argument("--fail", required=True)
    p.add_argument("--drawio")
    p.add_argument("--include-ir", action="store_true")
    p.add_argument("-o", "--output")
    p.set_defaults(func=cmd_whatif)
    p = sub.add_parser("story", help="publish an accessible offline guided walkthrough")
    p.add_argument("input")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--title")
    p.add_argument("--fail")
    p.set_defaults(func=cmd_story)
    p = sub.add_parser(
        "publish", help="publish as an interactive viewer or semantic story"
    )
    p.add_argument("input")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--format", choices=["viewer", "story"], default="viewer")
    p.add_argument("--title")
    p.set_defaults(func=cmd_publish)
    p = sub.add_parser(
        "transform", help="unified access to existing diagram transformations"
    )
    p.add_argument("operation", choices=sorted(TRANSFORMS))
    p.add_argument("input")
    p.add_argument("arguments", nargs=argparse.REMAINDER)
    p.set_defaults(func=cmd_transform)
    return ap


def main():
    args = parser().parse_args()
    try:
        return args.func(args) or 0
    except (ValueError, RuntimeError, OSError, json.JSONDecodeError) as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
