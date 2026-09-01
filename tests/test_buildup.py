#!/usr/bin/env python3
"""Tests for scripts/buildup.py — the build-up "video" HTML player.

Run from the repo root:
    python3 -m unittest tests.test_buildup -v
"""
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "skills", "drawio-skill", "scripts")


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


# a, b -> c: two independent sources feeding one sink.
PAGE = (
    '<mxCell id="0"/><mxCell id="1" parent="0"/>'
    '<mxCell id="a" value="A" vertex="1" parent="1" style="rounded=1;">'
    '<mxGeometry x="0" y="0" width="80" height="40" as="geometry"/></mxCell>'
    '<mxCell id="b" value="B" vertex="1" parent="1" style="rounded=1;">'
    '<mxGeometry x="200" y="0" width="80" height="40" as="geometry"/></mxCell>'
    '<mxCell id="c" value="C" vertex="1" parent="1" style="rounded=1;">'
    '<mxGeometry x="400" y="0" width="80" height="40" as="geometry"/></mxCell>'
    '<mxCell id="e1" value="" edge="1" parent="1" source="a" target="c">'
    '<mxGeometry relative="1" as="geometry"/></mxCell>'
    '<mxCell id="e2" value="" edge="1" parent="1" source="b" target="c">'
    '<mxGeometry relative="1" as="geometry"/></mxCell>'
)
DOC = f'<mxfile><diagram name="P1"><mxGraphModel><root>{PAGE}</root></mxGraphModel></diagram></mxfile>'


class TestParseClassify(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load("buildup")

    def _write(self, path, text):
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

    def test_classify_leaves_and_edges(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "diagram.drawio")
            self._write(path, DOC)
            _, cells = self.m.parse_page(path)
            leaves, containers, edges = self.m.classify(cells)
            self.assertEqual(leaves, ["a", "b", "c"])
            self.assertEqual(containers, set())
            self.assertEqual(edges, [("e1", "a", "c"), ("e2", "b", "c")])

    def test_bounding_box_from_full_diagram(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "diagram.drawio")
            self._write(path, DOC)
            _, cells = self.m.parse_page(path)
            width, height = self.m.bounding_box(cells)
            # rightmost cell C: x=400,w=80 -> 480 + 40 margin; tallest: 0+40+40
            self.assertEqual(width, 520)
            self.assertEqual(height, 80)


class TestRevealOrder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load("buildup")

    def test_sources_precede_targets(self):
        # diamond: a,b -> c -> d
        order = self.m.reveal_order(["a", "b", "c", "d"],
                                    [("a", "c"), ("b", "c"), ("c", "d")])
        self.assertEqual(set(order), {"a", "b", "c", "d"})
        self.assertLess(order.index("a"), order.index("c"))
        self.assertLess(order.index("b"), order.index("c"))
        self.assertLess(order.index("c"), order.index("d"))

    def test_cycle_falls_back_to_document_order(self):
        order = self.m.reveal_order(["x", "y"], [("x", "y"), ("y", "x")])
        self.assertEqual(order, ["x", "y"])            # no crash, no infinite loop

    def test_edge_step_is_at_or_after_both_endpoints(self):
        order = self.m.reveal_order(["a", "b", "c", "d"],
                                    [("a", "c"), ("b", "c"), ("c", "d")])
        edges = [("e1", "a", "c"), ("e2", "b", "c"), ("e3", "c", "d")]
        node_step, edge_step = self.m.reveal_steps(order, edges)
        for eid, s, t in edges:
            self.assertGreaterEqual(edge_step[eid], node_step[s])
            self.assertGreaterEqual(edge_step[eid], node_step[t])
        # e3 (c->d) can't reveal before c does
        self.assertGreaterEqual(edge_step["e3"], node_step["c"])


class TestBuildHtml(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load("buildup")

    def test_build_html_self_contained(self):
        frames = [(b"\x89PNG-1", "A", 1, 3),
                  (b"\x89PNG-2", "B", 2, 3),
                  (b"\x89PNG-3", "C", 3, 3)]
        html = self.m.build_html(frames, "Test Buildup")
        self.assertEqual(html.count("data:image/png;base64,"), 3)
        self.assertNotIn("http://", html)
        self.assertNotIn("https://", html)              # no CDN/external refs
        for ctl in ('id="play"', 'id="scrub"', 'id="bar"'):
            self.assertIn(ctl, html)
        self.assertIn('"label": "C"', html)
        self.assertIn('"step": 3', html)
        self.assertIn('"total": 3', html)


class TestBuildupCli(unittest.TestCase):
    def test_full_run_produces_one_frame_per_node(self):
        if os.environ.get("DRAWIO_E2E") != "1":
            self.skipTest("set DRAWIO_E2E=1 to launch the desktop CLI")
        if not shutil.which("drawio"):
            self.skipTest("draw.io CLI not installed")
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "diagram.drawio")
            with open(src, "w", encoding="utf-8") as f:
                f.write(DOC)
            out = os.path.join(d, "out.html")
            r = run("buildup.py", src, "-o", out)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue(os.path.exists(out))
            with open(out, encoding="utf-8") as f:
                html = f.read()
            self.assertEqual(html.count("data:image/png;base64,"), 3)   # a, b, c


if __name__ == "__main__":
    unittest.main()
