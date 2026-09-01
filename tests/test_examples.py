#!/usr/bin/env python3
"""Regression tests for the checked Architecture Studio showcase."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAMPLE = os.path.join(ROOT, "examples", "architecture-studio")


class TestArchitectureStudioExamples(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.out = cls.temp.name
        result = subprocess.run(
            [
                sys.executable,
                os.path.join(EXAMPLE, "generate.py"),
                "--output-dir",
                cls.out,
            ],
            text=True,
            capture_output=True,
        )
        if result.returncode:
            raise AssertionError(result.stderr or result.stdout)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def load(self, name):
        with open(os.path.join(self.out, name), encoding="utf-8") as stream:
            return json.load(stream)

    def test_code_to_ir_to_drawio(self):
        ir = self.load("codebase.ir.json")
        self.assertEqual(5, len(ir["nodes"]))
        self.assertGreaterEqual(len(ir["edges"]), 4)
        self.assertEqual("python", ir["metadata"]["importer"])
        root = ET.parse(os.path.join(self.out, "codebase.drawio")).getroot()
        self.assertEqual("mxfile", root.tag)

    def test_three_way_sync_preserves_manual_changes(self):
        result = self.load("sync-result.json")
        self.assertEqual(["events"], result["added"])
        fields = {conflict["field"] for conflict in result["conflicts"]}
        self.assertEqual({"label", "properties"}, fields)
        orders = next(
            cell
            for cell in ET.parse(os.path.join(self.out, "reconciled.drawio"))
            .getroot()
            .iter()
            if cell.get("data-model-id") == "orders"
        )
        self.assertEqual("Orders (manual)", orders.get("value"))
        self.assertEqual("720", orders.find("mxGeometry").get("x"))
        self.assertIn("shadow=1", orders.get("style"))

    def test_views_policy_failure_and_story(self):
        pages = (
            ET.parse(os.path.join(self.out, "checkout-views.drawio"))
            .getroot()
            .findall("diagram")
        )
        self.assertEqual(5, len(pages))
        policy = self.load("policy-result.json")
        self.assertEqual((0, 0), (policy["errors"], policy["warnings"]))
        impact = self.load("impact.json")
        self.assertEqual("orders", impact["failed"])
        self.assertIn("orders-db", impact["impacted"])
        self.assertNotIn("inventory", impact["impacted"])
        with open(
            os.path.join(self.out, "checkout-story.html"), encoding="utf-8"
        ) as stream:
            story = stream.read()
        self.assertIn('role="img"', story)
        self.assertIn("Text alternative", story)
        self.assertNotIn("https://", story)


if __name__ == "__main__":
    unittest.main()
