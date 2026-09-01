#!/usr/bin/env python3
"""Tests for the unified Diagram IR and diagramctl workflows."""

import base64
import json
import os
import subprocess
import sys
import tempfile
import unittest
import urllib.parse
import zlib
import xml.etree.ElementTree as ET


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "skills", "drawio-skill", "scripts")
sys.path.insert(0, SCRIPTS)
import diagram_ir as d  # noqa: E402 - path injection loads the bundled module


def sample_ir():
    return d.normalize_ir(
        {
            "schema": d.SCHEMA,
            "metadata": {"title": "Checkout"},
            "nodes": [
                {
                    "id": "internet",
                    "label": "Internet",
                    "kind": "external",
                    "owner": "edge",
                },
                {
                    "id": "api",
                    "label": "API",
                    "kind": "gateway",
                    "owner": "platform",
                    "environment": "production",
                    "observability": "otel",
                    "trust_boundary": "public",
                },
                {
                    "id": "orders",
                    "label": "Orders",
                    "kind": "service",
                    "owner": "orders",
                    "trust_boundary": "private",
                    "importance": 9,
                    "provenance": {"path": "services/orders.py", "line": 12},
                },
                {
                    "id": "db",
                    "label": "Orders DB",
                    "kind": "database",
                    "owner": "orders",
                    "trust_boundary": "data",
                },
            ],
            "edges": [
                {
                    "id": "e1",
                    "source": "internet",
                    "target": "api",
                    "label": "HTTPS",
                    "protocol": "HTTPS",
                },
                {
                    "id": "e2",
                    "source": "api",
                    "target": "orders",
                    "label": "HTTP",
                    "protocol": "HTTP",
                },
                {
                    "id": "e3",
                    "source": "orders",
                    "target": "db",
                    "label": "SQL",
                    "protocol": "TLS",
                },
            ],
        }
    )


class TestDiagramIR(unittest.TestCase):
    def test_normalize_query_review_and_impact(self):
        ir = sample_ir()
        self.assertEqual(
            ["internet", "api", "orders", "db"], d.shortest_path(ir, "internet", "db")
        )
        self.assertEqual(
            4, len(d.query(ir, source="internet", target="db")["nodes"])
        )
        self.assertEqual(
            ["db"], [n["id"] for n in d.query(ir, kind="database")["nodes"]]
        )
        self.assertIn("api", d.articulation_points(ir))
        self.assertEqual(
            ["api", "db", "orders"], d.impact_analysis(ir, "internet")["impacted"]
        )
        report = d.review(ir)
        self.assertEqual(4, report["summary"]["nodes"])

    def test_review_finds_long_sync_chain_and_residency(self):
        ir = d.normalize_ir(
            {
                "nodes": [
                    {
                        "id": f"n{i}",
                        "kind": "service",
                        "region": "eu" if i < 4 else "us",
                    }
                    for i in range(6)
                ],
                "edges": [
                    {
                        "id": f"e{i}",
                        "source": f"n{i}",
                        "target": f"n{i + 1}",
                        "kind": "sync",
                        "data_classification": "pii" if i == 3 else "public",
                    }
                    for i in range(5)
                ],
            }
        )
        rules = {f["rule"] for f in d.review(ir)["findings"]}
        self.assertIn("long-synchronous-chain", rules)
        self.assertIn("sensitive-data-region-crossing", rules)

    def test_semantic_contracts(self):
        ir = sample_ir()
        clean = d.semantic_findings(
            ir, ["no-direct-internet-to-database", "every-service-has-owner"]
        )
        self.assertEqual([], clean)
        ir["edges"].append(
            {
                "id": "bad",
                "source": "internet",
                "target": "db",
                "label": "",
                "kind": "relation",
                "properties": {},
            }
        )
        findings = d.semantic_findings(ir, ["no-direct-internet-to-database"])
        self.assertEqual("error", findings[0]["severity"])

    def test_drawio_roundtrip_and_provenance(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "out.drawio")
            d.write_drawio(sample_ir(), path)
            out = d.load_ir(path)
            self.assertEqual(4, len(out["nodes"]))
            orders = next(n for n in out["nodes"] if n["id"] == "orders")
            self.assertEqual("services/orders.py", orders["provenance"]["path"])
            self.assertEqual("orders", orders["properties"]["owner"])

    def test_compressed_drawio_import(self):
        model = '<mxGraphModel><root><mxCell id="0"/><mxCell id="1" parent="0"/><mxCell id="a" value="A" vertex="1" parent="1"><mxGeometry x="10" y="20" width="100" height="50" as="geometry"/></mxCell></root></mxGraphModel>'
        encoded = base64.b64encode(
            zlib.compress(urllib.parse.quote(model).encode())[2:-4]
        ).decode()
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "compressed.drawio")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(f'<mxfile><diagram name="Page-1">{encoded}</diagram></mxfile>')
            self.assertEqual("A", d.load_ir(path)["nodes"][0]["label"])

    def test_reconcile_preserves_manual_geometry_and_style(self):
        with tempfile.TemporaryDirectory() as td:
            old = os.path.join(td, "old.drawio")
            out = os.path.join(td, "new.drawio")
            d.write_drawio(sample_ir(), old)
            tree = ET.parse(old)
            cell = next(
                c for c in tree.iter("mxCell") if c.get("data-model-id") == "orders"
            )
            cell.set("style", "rounded=1;fillColor=#123456;")
            cell.find("mxGeometry").set("x", "777")
            tree.write(old, encoding="unicode")
            incoming = sample_ir()
            next(n for n in incoming["nodes"] if n["id"] == "orders")["label"] = (
                "Order Service"
            )
            incoming["nodes"].append(
                {
                    "id": "worker",
                    "label": "Worker",
                    "kind": "service",
                    "properties": {"owner": "orders"},
                }
            )
            incoming["edges"].append(
                {
                    "id": "e4",
                    "source": "orders",
                    "target": "worker",
                    "label": "jobs",
                    "kind": "async",
                    "properties": {},
                }
            )
            result = d.reconcile(old, incoming, out)
            self.assertEqual(["worker"], result["added"])
            self.assertEqual(["orders"], result["changed"])
            tree = ET.parse(out)
            cell = next(
                c for c in tree.iter("mxCell") if c.get("data-model-id") == "orders"
            )
            self.assertEqual("777", cell.find("mxGeometry").get("x"))
            self.assertIn("#123456", cell.get("style"))
            self.assertEqual("Order Service", cell.get("value"))

    def test_reconcile_reports_three_way_label_conflict(self):
        with tempfile.TemporaryDirectory() as td:
            old = os.path.join(td, "old.drawio")
            out = os.path.join(td, "new.drawio")
            d.write_drawio(sample_ir(), old)
            tree = ET.parse(old)
            cell = next(
                c for c in tree.iter("mxCell") if c.get("data-model-id") == "orders"
            )
            cell.set("value", "Manual Orders Label")
            tree.write(old, encoding="unicode")
            incoming = sample_ir()
            next(n for n in incoming["nodes"] if n["id"] == "orders")["label"] = (
                "Order Service v2"
            )
            result = d.reconcile(old, incoming, out)
            self.assertEqual("label", result["conflicts"][0]["field"])
            tree = ET.parse(out)
            cell = next(
                c for c in tree.iter("mxCell") if c.get("data-model-id") == "orders"
            )
            self.assertEqual("Manual Orders Label", cell.get("value"))

    def test_views_and_story_are_accessible(self):
        ir = sample_ir()
        views = d.project_views(ir)
        self.assertEqual(5, len(views))
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "views.drawio")
            d.write_drawio(ir, path, views=views[:2])
            self.assertTrue(
                any(
                    x.get("link", "").startswith("data:page/id,")
                    for x in ET.parse(path).getroot().iter("UserObject")
                )
            )
        page = d.story_html(ir)
        self.assertIn('role="img"', page)
        self.assertIn("Text alternative", page)
        self.assertIn("ArrowRight", page)
        self.assertNotIn("https://", page)


class TestDiagramCtl(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, os.path.join(SCRIPTS, "diagramctl.py"), *args],
            text=True,
            capture_output=True,
        )

    def test_end_to_end_commands(self):
        with tempfile.TemporaryDirectory() as td:
            src = os.path.join(td, "model.json")
            drawio = os.path.join(td, "model.drawio")
            with open(src, "w", encoding="utf-8") as fh:
                json.dump(sample_ir(), fh)
            r = self.run_cli("build", src, "-o", drawio, "--from", "ir")
            self.assertEqual(0, r.returncode, r.stderr)
            self.assertTrue(os.path.exists(drawio))
            r = self.run_cli("query", src, "--from", "internet", "--to", "db")
            self.assertEqual(
                ["internet", "api", "orders", "db"], json.loads(r.stdout)["path"]
            )
            story = os.path.join(td, "story.html")
            r = self.run_cli("story", src, "-o", story, "--fail", "api")
            self.assertEqual(0, r.returncode, r.stderr)
            with open(story, encoding="utf-8") as fh:
                self.assertIn("impacted", fh.read())

    def test_doctor_does_not_probe_by_default(self):
        r = self.run_cli("doctor")
        self.assertEqual(0, r.returncode, r.stderr)
        data = json.loads(r.stdout)
        self.assertIn("not executed", data["drawio"]["note"])

    def test_build_python_gets_source_profile_and_provenance(self):
        # v3.2 P0: a code build must produce module/library/command kinds (not
        # a blanket "service"), precise per-file provenance, and no
        # ownership/observability noise on source modules.
        with tempfile.TemporaryDirectory() as td:
            pkg = os.path.join(td, "pkg")
            sub = os.path.join(pkg, "sub")
            os.makedirs(sub)
            for rel, text in (
                (os.path.join("pkg", "__init__.py"), "from .cli import main\n"),
                (os.path.join("pkg", "cli.py"), "from . import util\n"),
                (os.path.join("pkg", "util.py"), "x = 1\n"),
                (os.path.join("pkg", "__main__.py"), "from .cli import main\n"),
                (os.path.join("pkg", "sub", "mod.py"), "from .. import util\n"),
            ):
                with open(os.path.join(td, rel), "w", encoding="utf-8") as fh:
                    fh.write(text)
            ir_json = os.path.join(td, "out.ir.json")
            out = os.path.join(td, "out.drawio")
            r = self.run_cli(
                "build", os.path.join(td, "pkg"), "--from", "python",
                "--ir-output", ir_json, "-o", out,
            )
            self.assertEqual(0, r.returncode, r.stderr)
            with open(ir_json, encoding="utf-8") as fh:
                ir = json.load(fh)
            by_id = {n["id"]: n for n in ir["nodes"]}
            # source profile: package root library, entrypoint command, rest module
            self.assertEqual(by_id["pkg"]["kind"], "library")
            self.assertEqual(by_id["pkg.cli"]["kind"], "command")
            self.assertEqual(by_id["pkg.util"]["kind"], "module")
            self.assertEqual(by_id["pkg.sub.mod"]["kind"], "module")
            # precise provenance: real file path (absolute) + importer tag
            self.assertEqual(
                os.path.basename(by_id["pkg.cli"]["provenance"]["path"]), "cli.py"
            )
            self.assertEqual(by_id["pkg.cli"]["provenance"]["importer"], "python")
            # line-level edge provenance survived the build
            edge = next(e for e in ir["edges"] if e["source"] == "pkg.cli")
            self.assertEqual(edge["provenance"]["line"], 1)

    def test_view_fallback_reports_metadata_gap(self):
        # A model with no deployment/security/data metadata must say so, with a
        # hint, instead of silently falling back to the whole graph.
        bare = d.normalize_ir({"nodes": [
            {"id": "a", "label": "A", "kind": "module"},
            {"id": "b", "label": "B", "kind": "module"},
        ], "edges": [{"source": "a", "target": "b"}]})
        views = d.project_views(bare, ["deployment", "dataflow", "system"])
        dep = next(v for v in views if v["name"] == "Deployment")
        self.assertTrue(dep["fallback"])
        self.assertIn("no deployment metadata", dep["fallback_reason"])
        self.assertIn("properties.environment", dep["hint"])
        flow = next(v for v in views if v["name"] == "Dataflow")
        self.assertTrue(flow["fallback"])
        self.assertIn("data-flow", flow["fallback_reason"])
        syst = next(v for v in views if v["name"] == "System")
        self.assertFalse(syst.get("fallback", False))

    def test_infer_profile(self):
        code = d.normalize_ir({"nodes": [{"id": "a", "kind": "module"}]})
        self.assertEqual(d.infer_profile(code), "code")
        arch = d.normalize_ir(
            {"nodes": [{"id": "a", "kind": "service"},
                        {"id": "b", "kind": "database"}]}
        )
        self.assertEqual(d.infer_profile(arch), "architecture")


if __name__ == "__main__":
    unittest.main()
