#!/usr/bin/env python3
"""Extract a CI pipeline (GitHub Actions / GitLab CI) as autolayout graph JSON.

GitHub Actions: every job becomes a node (label: name, runner, matrix size,
reusable-workflow target), `needs:` become edges, and each workflow gets a
trigger node (its `on:` events) feeding the jobs that have no `needs`. Given a
repo root, all of `.github/workflows/*.yml|yaml` are read and each workflow is
boxed in its own container.

GitLab CI (`.gitlab-ci.yml`, auto-detected): jobs become nodes grouped by
stage; edges come from `needs:`, and jobs without `needs` inherit the stage
DAG (every job of the previous stage), matching GitLab's execution order.

  python3 ciimports.py .                          # repo root -> all workflows
  python3 ciimports.py .github/workflows/ci.yml -o graph.json
  python3 autolayout.py graph.json -o pipeline.drawio

Requires PyYAML (pip install pyyaml).

Usage: python3 ciimports.py <repo-root | workflow.yml ...> [-o graph.json]
       [--direction TB|LR]
"""
import argparse
import json
import os
import sys

JOB_STYLE = "rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;"
REUSE_STYLE = "rounded=1;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;"
TRIGGER_STYLE = "ellipse;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;"

GITLAB_RESERVED = {"stages", "variables", "workflow", "default", "include", "image",
                   "services", "before_script", "after_script", "cache", "pages"}


def find_workflows(path):
    """Workflow files for a path: file(s) as-is, a repo root via .github/workflows."""
    if os.path.isfile(path):
        return [path]
    wfdir = os.path.join(path, ".github", "workflows")
    files = sorted(os.path.join(wfdir, f) for f in os.listdir(wfdir)
                   if f.endswith((".yml", ".yaml"))) if os.path.isdir(wfdir) else []
    gitlab = os.path.join(path, ".gitlab-ci.yml")
    if os.path.isfile(gitlab):
        files.append(gitlab)
    if not files:
        sys.exit(f"error: no workflow files under {path}")
    return files


def matrix_size(strategy):
    n = 1
    matrix = (strategy or {}).get("matrix") or {}
    if not isinstance(matrix, dict):
        return 0                                # dynamic (fromJSON) — unknown
    for key, vals in matrix.items():
        if key not in ("include", "exclude") and isinstance(vals, list):
            n *= len(vals)
    n += len(matrix.get("include") or []) - len(matrix.get("exclude") or [])
    return max(n, 1)


def parse_actions(spec, wf_id, wf_name, group):
    """One GitHub Actions workflow -> (nodes, edges)."""
    nodes, edges = [], []
    # YAML 1.1 quirk: bare `on:` parses as boolean True
    on = spec.get("on", spec.get(True, {}))
    events = sorted(on) if isinstance(on, dict) else \
        ([on] if isinstance(on, str) else sorted(on or []))
    trig_id = f"{wf_id}//trigger"
    nodes.append({"id": trig_id, "label": "on: " + (", ".join(events) or "?"),
                  "style": TRIGGER_STYLE, "width": 160, "height": 50, "group": group})
    jobs = spec.get("jobs") or {}
    for jid, job in jobs.items():
        job = job or {}
        lines = [job.get("name") or jid]
        if job.get("uses"):
            lines.append("uses: " + os.path.basename(str(job["uses"])))
            style = REUSE_STYLE
        else:
            style = JOB_STYLE
            runner = job.get("runs-on")
            if runner:
                lines.append(str(runner if isinstance(runner, str) else ", ".join(runner)))
        n = matrix_size(job.get("strategy"))
        if n > 1:
            lines.append(f"matrix ×{n}")
        elif n == 0:
            lines.append("matrix (dynamic)")
        nodes.append({"id": f"{wf_id}//{jid}", "label": "\n".join(lines),
                      "style": style, "width": 180, "height": 60, "group": group})
        needs = job.get("needs") or []
        needs = [needs] if isinstance(needs, str) else needs
        for dep in needs:
            if dep in jobs:
                edges.append({"source": f"{wf_id}//{dep}", "target": f"{wf_id}//{jid}"})
        if not needs:
            edges.append({"source": trig_id, "target": f"{wf_id}//{jid}"})
    return nodes, edges


def parse_gitlab(spec, wf_id, group_prefix):
    """A .gitlab-ci.yml -> (nodes, edges); jobs grouped by stage."""
    stages = spec.get("stages") or ["build", "test", "deploy"]
    jobs = {k: v for k, v in spec.items()
            if isinstance(v, dict) and k not in GITLAB_RESERVED and not k.startswith(".")
            and ("script" in v or "trigger" in v or "extends" in v or "stage" in v)}
    nodes, edges = [], []
    by_stage = {}
    for jid, job in jobs.items():
        stage = job.get("stage") or "test"
        by_stage.setdefault(stage, []).append(jid)
        nodes.append({"id": f"{wf_id}//{jid}", "label": jid, "style": JOB_STYLE,
                      "width": 160, "height": 50,
                      "group": f"{group_prefix}{stage}"})
    order = [s for s in stages if s in by_stage]
    for jid, job in jobs.items():
        needs = [(n.get("job") if isinstance(n, dict) else n) for n in job.get("needs") or []]
        needs = [n for n in needs if n in jobs]
        if needs:
            edges.extend({"source": f"{wf_id}//{n}", "target": f"{wf_id}//{jid}"} for n in needs)
        else:                                   # stage DAG: all jobs of the previous stage
            stage = job.get("stage") or "test"
            i = order.index(stage) if stage in order else 0
            if i > 0:
                edges.extend({"source": f"{wf_id}//{p}", "target": f"{wf_id}//{jid}"}
                             for p in by_stage[order[i - 1]])
    return nodes, edges


def main():
    ap = argparse.ArgumentParser(description="CI pipeline -> autolayout graph JSON.")
    ap.add_argument("paths", nargs="+",
                    help="repo root, or workflow file(s) (.github/workflows/*.yml, .gitlab-ci.yml)")
    ap.add_argument("-o", "--output", help="output JSON path (default: stdout)")
    ap.add_argument("--direction", default="LR", choices=["TB", "LR"])
    args = ap.parse_args()

    try:
        import yaml
    except ImportError:
        sys.exit("error: PyYAML is required (pip install pyyaml)")

    files = [f for p in args.paths for f in find_workflows(p)]
    nodes, edges = [], []
    for path in files:
        with open(path, encoding="utf-8") as f:
            try:
                spec = yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                sys.stderr.write(f"warning: skipping {path}: {e}\n")
                continue
        wf_id = os.path.splitext(os.path.basename(path))[0]
        if os.path.basename(path) == ".gitlab-ci.yml" or (
                "jobs" not in spec and "stages" in spec):
            n, e = parse_gitlab(spec, wf_id, "stage: " if len(files) == 1
                                else f"{wf_id} / stage: ")
        elif spec.get("jobs"):
            wf_name = spec.get("name") or wf_id
            group = wf_name if len(files) > 1 else None
            n, e = parse_actions(spec, wf_id, wf_name, group)
        else:
            sys.stderr.write(f"warning: {path} has no jobs — skipped\n")
            continue
        nodes.extend(n)
        edges.extend(e)
    if not nodes:
        sys.exit("error: no CI jobs found")

    graph = {"direction": args.direction, "nodes": nodes, "edges": edges}
    text = json.dumps(graph, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        sys.stderr.write(f"wrote {args.output}\n")
    else:
        sys.stdout.write(text)
    sys.stderr.write(f"{len(nodes)} nodes, {len(edges)} edges from {len(files)} file(s)\n")


if __name__ == "__main__":
    main()
