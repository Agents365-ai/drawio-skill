#!/usr/bin/env python3
"""Dependency-free regression tests for the bundled scripts.

Run from the repo root:
    python3 -m unittest discover -s tests -v

Uses only the standard library (unittest). Pure-function behaviour is tested by
importing the scripts directly; CLI/exit-code behaviour (validate, importers) is
tested via subprocess against tiny temp fixtures. No Graphviz/draw.io needed —
auto-layout is exercised through to_drawio() with synthetic node positions.
"""
import base64
import gzip
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
import urllib.parse
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "skills", "drawio-skill", "scripts")
DATA = os.path.join(ROOT, "skills", "drawio-skill", "data")


def load(name):
    """Import a bundled script module by file path."""
    path = os.path.join(SCRIPTS, name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run(script, *args, **kw):
    """Run a script as a subprocess; return CompletedProcess."""
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, script), *args],
                          capture_output=True, text=True, **kw)


class TestShapeSearch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load("shapesearch")
        with gzip.open(os.path.join(DATA, "shape-index.json.gz"), "rt", encoding="utf-8") as f:
            cls.shapes = json.load(f)
        cls.tm = cls.m.build_tag_map(cls.shapes)

    def search(self, q, n=5):
        return self.m.search(self.shapes, self.tm, q, n)

    def test_soundex(self):
        self.assertEqual(self.m.soundex("Robert"), "R163")
        self.assertEqual(self.m.soundex("Jackson"), "J250")

    def test_index_loaded(self):
        self.assertGreater(len(self.shapes), 10000)
        self.assertTrue(self.tm)

    def test_known_shapes(self):
        self.assertIn("Lambda", self.search("aws lambda")[0]["title"])
        self.assertIn("Actor", self.search("uml actor")[0]["title"])

    def test_title_exact_ranking(self):
        # The v1.11.1 fix: the shape literally titled "DynamoDB" ranks first,
        # above tag-only neighbours like "Attribute".
        self.assertEqual(self.search("aws dynamodb")[0]["title"], "DynamoDB")

    def test_no_match_is_empty(self):
        self.assertEqual(self.search("zzzznotashape"), [])


class TestAiIcons(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load("aiicons")
        with open(os.path.join(DATA, "lobe-icons.json"), encoding="utf-8") as fh:
            manifest = json.load(fh)
        cls.fam = cls.m.families(manifest["icons"])

    def test_families_group_variants(self):
        self.assertIn("claude", self.fam)
        self.assertIn("claude-color", self.fam["claude"])

    def test_search_matches_brand(self):
        self.assertEqual(self.m.search(self.fam, "claude", 1)[0], "claude")
        # token matching: a brand word inside a phrase still matches
        self.assertEqual(self.m.search(self.fam, "use the openai logo", 1)[0], "openai")

    def test_variant_preference(self):
        # claude has a colour variant; openai is mono-only -> falls back.
        self.assertEqual(self.m.pick_variant("claude", self.fam["claude"], "color"), "claude-color")
        self.assertEqual(self.m.pick_variant("openai", self.fam["openai"], "color"), "openai")

    def test_unknown_brand(self):
        self.assertEqual(self.m.search(self.fam, "definitelynotabrand", 3), [])


class TestEncodeUrl(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load("encode_drawio_url")

    @staticmethod
    def decode(b64):
        # Reverse the encoder: inflate, then decodeURIComponent.
        inflated = zlib.decompress(base64.b64decode(b64), -zlib.MAX_WBITS).decode("utf-8")
        return urllib.parse.unquote(inflated)

    def test_roundtrip_cjk_and_percent(self):
        # The v1.11.0 fix: encodeURIComponent before deflate keeps % and CJK safe.
        xml = '<mxGraphModel><root><mxCell value="登录 100% &amp; ok"/></root></mxGraphModel>'
        b64 = self.m._deflate_b64(xml)
        self.assertEqual(self.decode(b64), xml)

    def test_viewer_and_editor_urls(self):
        xml = "<mxGraphModel><root/></mxGraphModel>"
        self.assertIn("viewer.diagrams.net", self.m.encode(xml))
        self.assertIn("#R", self.m.encode(xml))
        self.assertIn("app.diagrams.net", self.m.edit_url(xml))
        self.assertIn("#create=", self.m.edit_url(xml))


class TestAutolayoutColor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load("autolayout")
        cls.pal = cls.m.load_palette()

    def test_palette_from_design_file(self):
        # Sourced from styles/built-in/default.json, not the inline fallback.
        self.assertNotEqual(self.pal, self.m._FALLBACK_PALETTE)
        self.assertEqual(self.pal[0], ("#dae8fc", "#6c8ebf"))   # primary

    def _render(self, color):
        graph = {"direction": "TB", "nodes": [
            {"id": "a", "label": "A", "group": "mod1"},
            {"id": "b", "label": "B", "group": "mod2"},
            {"id": "c", "label": "C", "style": "fillColor=#ff0000;"},
            {"id": "d", "label": "D"},
        ], "edges": []}
        pos = {"a": (1, 4), "b": (3, 4), "c": (5, 4), "d": (7, 4)}
        return self.m.to_drawio(graph, 5, pos, {}, color=color)

    def test_grouped_nodes_coloured(self):
        out = self._render(color=True)
        self.assertIn("fillColor=#d5e8d4", out)   # b tinted by mod2 (success/green)
        self.assertIn("strokeColor=#82b366", out)  # mod2 container border colour
        self.assertIn("fillColor=#ff0000", out)    # explicit style preserved

    def test_mono_disables_colour(self):
        out = self._render(color=False)
        self.assertIn("strokeColor=#999999", out)  # grey container
        self.assertNotIn("fillColor=#d5e8d4", out)  # no group tint
        self.assertIn("fillColor=#ff0000", out)     # explicit style still wins


class TestValidateCli(unittest.TestCase):
    GOOD = ('<mxfile><diagram name="P1"><mxGraphModel><root>'
            '<mxCell id="0"/><mxCell id="1" parent="0"/>'
            '<mxCell id="2" value="A" vertex="1" parent="1">'
            '<mxGeometry x="0" y="0" width="80" height="40" as="geometry"/></mxCell>'
            '<mxCell id="3" value="B" vertex="1" parent="1">'
            '<mxGeometry x="200" y="0" width="80" height="40" as="geometry"/></mxCell>'
            '<mxCell id="4" edge="1" parent="1" source="2" target="3">'
            '<mxGeometry relative="1" as="geometry"/></mxCell>'
            '</root></mxGraphModel></diagram></mxfile>')
    BAD = ('<mxfile><diagram name="P1"><mxGraphModel><root>'
           '<mxCell id="0"/><mxCell id="1" parent="0"/>'
           '<mxCell id="2" value="A" vertex="1" parent="1">'
           '<mxGeometry x="0" y="0" width="80" height="40" as="geometry"/></mxCell>'
           '<mxCell id="4" edge="1" parent="1" source="2" target="nope">'
           '<mxGeometry relative="1" as="geometry"/></mxCell>'
           '</root></mxGraphModel></diagram></mxfile>')
    # Edge label: a relative-positioned vertex that legitimately omits width/height.
    EDGE_LABEL = ('<mxfile><diagram name="P1"><mxGraphModel><root>'
                  '<mxCell id="0"/><mxCell id="1" parent="0"/>'
                  '<mxCell id="2" value="A" vertex="1" parent="1">'
                  '<mxGeometry x="0" y="0" width="80" height="40" as="geometry"/></mxCell>'
                  '<mxCell id="3" value="B" vertex="1" parent="1">'
                  '<mxGeometry x="200" y="0" width="80" height="40" as="geometry"/></mxCell>'
                  '<mxCell id="4" edge="1" parent="1" source="2" target="3">'
                  '<mxGeometry relative="1" as="geometry"/></mxCell>'
                  '<mxCell id="5" value="lbl" style="edgeLabel;html=1;" vertex="1" '
                  'connectable="0" parent="1">'
                  '<mxGeometry x="0.5" y="0" relative="1" as="geometry">'
                  '<mxPoint as="offset"/></mxGeometry></mxCell>'
                  '</root></mxGraphModel></diagram></mxfile>')

    def _check(self, xml):
        with tempfile.NamedTemporaryFile("w", suffix=".drawio", delete=False) as f:
            f.write(xml)
            path = f.name
        try:
            return run("validate.py", path)
        finally:
            os.unlink(path)

    def test_good_passes(self):
        self.assertEqual(self._check(self.GOOD).returncode, 0)

    def test_dangling_edge_fails(self):
        r = self._check(self.BAD)
        self.assertEqual(r.returncode, 1)
        self.assertIn("error", r.stdout)

    def test_edge_label_passes(self):
        # edgeLabel vertices have no width/height; they must not be flagged
        # as missing/invalid geometry (issue #35).
        r = self._check(self.EDGE_LABEL)
        self.assertEqual(r.returncode, 0)
        self.assertNotIn("error:", r.stdout)


class TestImportersCli(unittest.TestCase):
    @staticmethod
    def _write(path, text):
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

    def test_pyimports_edge(self):
        with tempfile.TemporaryDirectory() as d:
            self._write(os.path.join(d, "a.py"), "import b\n")
            self._write(os.path.join(d, "b.py"), "x = 1\n")
            r = run("pyimports.py", d)
            graph = json.loads(r.stdout)
            ids = {n["id"] for n in graph["nodes"]}
            self.assertEqual(ids, {"a", "b"})
            self.assertIn({"source": "a", "target": "b"}, graph["edges"])

    def test_pyclasses_inheritance(self):
        with tempfile.TemporaryDirectory() as d:
            self._write(os.path.join(d, "m.py"), "class A: pass\nclass B(A): pass\n")
            r = run("pyclasses.py", d)
            graph = json.loads(r.stdout)
            self.assertEqual(len(graph["nodes"]), 2)
            self.assertEqual(graph["edges"], [{"source": "m.B", "target": "m.A"}])
            # No hard-coded colour anymore (coloured by group in autolayout).
            self.assertNotIn("style", graph["nodes"][0])

    def test_jsimports_edge(self):
        # Node ids are the module basename without extension: a, b.
        with tempfile.TemporaryDirectory() as d:
            self._write(os.path.join(d, "a.js"), "import './b.js';\n")
            self._write(os.path.join(d, "b.js"), "export const x = 1;\n")
            r = run("jsimports.py", d)
            graph = json.loads(r.stdout)
            ids = {n["id"] for n in graph["nodes"]}
            self.assertEqual(len(graph["nodes"]), 2)
            self.assertEqual(ids, {"a", "b"})
            self.assertEqual(len(graph["edges"]), 1)
            self.assertEqual(graph["edges"][0], {"source": "a", "target": "b"})

    def test_goimports_edge(self):
        # Node ids are full import paths: example.com/m/<pkg>.
        with tempfile.TemporaryDirectory() as d:
            self._write(os.path.join(d, "go.mod"), "module example.com/m\n\ngo 1.21\n")
            os.mkdir(os.path.join(d, "a"))
            os.mkdir(os.path.join(d, "b"))
            self._write(os.path.join(d, "a", "a.go"),
                        'package a\n\nimport _ "example.com/m/b"\n')
            self._write(os.path.join(d, "b", "b.go"), "package b\n")
            r = run("goimports.py", d)
            graph = json.loads(r.stdout)
            ids = {n["id"] for n in graph["nodes"]}
            self.assertEqual(len(graph["nodes"]), 2)
            self.assertEqual(ids, {"example.com/m/a", "example.com/m/b"})
            self.assertEqual(len(graph["edges"]), 1)
            self.assertEqual(graph["edges"][0],
                             {"source": "example.com/m/a", "target": "example.com/m/b"})

    def test_rustimports_edge(self):
        # Node ids are module paths (no crate-root file, so just a, b).
        with tempfile.TemporaryDirectory() as d:
            self._write(os.path.join(d, "Cargo.toml"), '[package]\nname = "m"\n')
            os.mkdir(os.path.join(d, "src"))
            self._write(os.path.join(d, "src", "a.rs"), "use crate::b;\n")
            self._write(os.path.join(d, "src", "b.rs"), "pub fn f() {}\n")
            r = run("rustimports.py", d)
            graph = json.loads(r.stdout)
            ids = {n["id"] for n in graph["nodes"]}
            self.assertEqual(len(graph["nodes"]), 2)
            self.assertEqual(ids, {"a", "b"})
            self.assertEqual(len(graph["edges"]), 1)
            self.assertEqual(graph["edges"][0], {"source": "a", "target": "b"})


if __name__ == "__main__":
    unittest.main()
