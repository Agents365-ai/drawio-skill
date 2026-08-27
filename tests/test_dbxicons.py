"""Tests for scripts/dbxicons.py (Databricks product icon resolver).

Pure-function tests against the committed manifest plus one CLI --json check.
No network — the data-URI builder is fed literal SVG bytes.
"""
import importlib.util
import json
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "skills", "drawio-skill", "scripts")
DATA = os.path.join(ROOT, "skills", "drawio-skill", "data")


def load(name):
    path = os.path.join(SCRIPTS, name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run(script, *args, **kw):
    return subprocess.run(
        [sys.executable, os.path.join(SCRIPTS, script), *args],
        capture_output=True, text=True, **kw)


class TestDbxIcons(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load("dbxicons")
        with open(os.path.join(DATA, "databricks-icons.json"), encoding="utf-8") as fh:
            cls.manifest = json.load(fh)
        cls.products = cls.manifest["products"]

    def test_manifest_loads(self):
        slugs = [p["slug"] for p in self.products]
        self.assertEqual(len(slugs), 71)
        self.assertEqual(len(slugs), len(set(slugs)))
        self.assertRegex(self.manifest["pinnedRef"], r"^[0-9a-f]{40}$")

    def test_every_category_exists(self):
        for p in self.products:
            self.assertIn(p["category"], self.manifest["categories"])
            self.assertEqual(p["categoryColor"],
                             self.manifest["categories"][p["category"]]["color"])

    def test_manifest_carries_facts_only(self):
        for p in self.products:
            self.assertEqual(sorted(p), ["aliases", "category", "categoryColor",
                                         "name", "slug"])

    def test_exact_slug(self):
        hits = self.m.resolve(self.products, "unity-catalog", 8)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["slug"], "unity-catalog")

    def test_alias_resolution(self):
        # Renamed products resolve by their former names, case-insensitively.
        self.assertEqual(self.m.resolve(self.products, "DLT", 8)[0]["slug"],
                         "spark-declarative-pipelines")
        self.assertEqual(self.m.resolve(self.products, "delta live tables", 8)[0]["slug"],
                         "spark-declarative-pipelines")
        self.assertEqual(self.m.resolve(self.products, "Workflows", 8)[0]["slug"],
                         "lakeflow-jobs")

    def test_search_ranks_substring(self):
        hits = self.m.search(self.products, "vector", 8)
        self.assertTrue(hits)
        self.assertEqual(hits[0]["slug"], "ai-search")

    def test_unknown_product(self):
        self.assertEqual(self.m.search(self.products, "definitelynotaproduct", 3), [])

    def test_url_style(self):
        p = self.m.resolve(self.products, "unity-catalog", 1)[0]
        style = self.m.STYLE + f"{self.manifest['hostedBase']}/{self.m.icon_path(p, 'color')}"
        self.assertTrue(style.startswith("shape=image"))
        self.assertIn("image=https://oieduardorabelo.github.io/", style)
        self.assertTrue(style.endswith("icons/svg/unity-catalog.svg"))
        self.assertTrue(self.m.icon_path(p, "tile").startswith("icons/svg-tile/"))
        self.assertTrue(self.m.icon_path(p, "outline").startswith("icons/svg-outline/"))

    def test_data_uri_has_no_base64_marker(self):
        # draw.io splits style values on ';' — a ';base64,' marker would
        # truncate the image= value (issue #80).
        uri = self.m.data_uri(b'<svg xmlns="http://www.w3.org/2000/svg"></svg>')
        self.assertTrue(uri.startswith("data:image/svg+xml,"))
        self.assertNotIn(";base64", uri)
        self.assertNotIn(";", uri)

    def test_parse_aka(self):
        self.assertEqual(
            self.m.parse_aka("Lakeflow Declarative Pipelines. Formerly Delta Live Tables (DLT)"),
            ["Lakeflow Declarative Pipelines", "Delta Live Tables (DLT)"])
        self.assertEqual(self.m.parse_aka("formerly A / B"), ["A", "B"])
        self.assertEqual(self.m.parse_aka(None), [])

    def test_cli_json(self):
        cp = run("dbxicons.py", "DLT", "--json")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        results = json.loads(cp.stdout)
        self.assertEqual(results[0]["product"], "spark-declarative-pipelines")
        self.assertTrue(results[0]["style"].startswith("shape=image"))


if __name__ == "__main__":
    unittest.main()
