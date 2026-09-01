#!/usr/bin/env python3
"""Regenerate the drawio-skill 3.0 showcase artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DIAGRAMCTL = ROOT / "skills" / "drawio-skill" / "scripts" / "diagramctl.py"
VALIDATE = ROOT / "skills" / "drawio-skill" / "scripts" / "validate.py"


def run(*args: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(DIAGRAMCTL), *(str(arg) for arg in args)],
        check=True,
        text=True,
        capture_output=True,
    )


def manually_tune(path: Path) -> None:
    tree = ET.parse(path)
    holder = next(
        cell for cell in tree.getroot().iter() if cell.get("data-model-id") == "orders"
    )
    cell = holder.find("mxCell") if holder.tag == "UserObject" else holder
    if cell is None:
        raise RuntimeError("orders cell has no mxCell")
    holder.set("value" if holder.tag == "mxCell" else "label", "Orders (manual)")
    holder.set("data-properties", json.dumps({"owner": "platform-ops"}))
    cell.set("style", (cell.get("style") or "") + "shadow=1;strokeWidth=3;")
    geometry = cell.find("mxGeometry")
    if geometry is None:
        raise RuntimeError("orders cell has no geometry")
    geometry.set("x", "720")
    geometry.set("y", "210")
    ET.indent(tree.getroot(), space="  ")
    tree.write(path, encoding="unicode", xml_declaration=False)
    with path.open("a", encoding="utf-8") as stream:
        stream.write("\n")


def validate(path: Path) -> None:
    subprocess.run(
        [sys.executable, str(VALIDATE), str(path), "--strict"],
        check=True,
        text=True,
        capture_output=True,
    )


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=HERE / "generated")
    args = parser.parse_args()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    run(
        "build",
        HERE / "codebase",
        "--from",
        "python",
        "--group",
        "--title",
        "Checkout codebase",
        "--ir-output",
        out / "codebase.ir.json",
        "-o",
        out / "codebase.drawio",
    )
    code_ir_path = out / "codebase.ir.json"
    code_ir = json.loads(code_ir_path.read_text(encoding="utf-8"))
    code_ir["metadata"]["created"] = "2026-09-01T00:00:00+00:00"
    code_ir["metadata"]["source"] = "examples/architecture-studio/codebase"
    for node in code_ir["nodes"]:
        node.get("provenance", {})["path"] = "examples/architecture-studio/codebase"
    write_json(code_ir_path, code_ir)
    run(
        "build",
        code_ir_path,
        "--from",
        "ir",
        "-o",
        out / "codebase.drawio",
    )

    run(
        "build",
        HERE / "sync-baseline.ir.json",
        "--from",
        "ir",
        "-o",
        out / "manual-layout.drawio",
    )
    manually_tune(out / "manual-layout.drawio")
    result = run(
        "sync",
        out / "manual-layout.drawio",
        HERE / "sync-source-v2.ir.json",
        "--from",
        "ir",
        "-o",
        out / "reconciled.drawio",
    )
    sync_result = json.loads(result.stdout)
    sync_result["output"] = "generated/reconciled.drawio"
    write_json(out / "sync-result.json", sync_result)

    model = HERE / "checkout.ir.json"
    run(
        "views",
        model,
        "--views",
        "executive,system,deployment,dataflow,security",
        "-o",
        out / "checkout-views.drawio",
    )
    run(
        "test",
        model,
        "--rules",
        HERE / "policy.yml",
        "-o",
        out / "policy-result.json",
    )
    run(
        "whatif",
        model,
        "--fail",
        "orders",
        "--drawio",
        out / "checkout-failure.drawio",
        "-o",
        out / "impact.json",
    )
    impact_path = out / "impact.json"
    impact = json.loads(impact_path.read_text(encoding="utf-8"))
    impact["drawio"] = "generated/checkout-failure.drawio"
    write_json(impact_path, impact)
    run(
        "story",
        model,
        "--fail",
        "orders",
        "--title",
        "Checkout failure walkthrough",
        "-o",
        out / "checkout-story.html",
    )

    for path in out.glob("*.drawio"):
        validate(path)
    print(f"generated showcase in {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
