#!/usr/bin/env python3
"""Tests for scripts/prdiff.py — the PR diagram diff bot.

Run from the repo root:
    python3 -m unittest tests.test_prdiff -v
"""
import importlib.util
import os
import shutil
import subprocess
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


def make_repo(tmp):
    """Init a throwaway git repo (local config only) in tmp."""
    subprocess.run(["git", "init", "-q", tmp], check=True)
    subprocess.run(["git", "-C", tmp, "config", "user.email", "t@example.com"], check=True)
    subprocess.run(["git", "-C", tmp, "config", "user.name", "Test"], check=True)


def write_commit(tmp, name, content, message):
    with open(os.path.join(tmp, name), "w", encoding="utf-8") as f:
        f.write(content)
    subprocess.run(["git", "-C", tmp, "add", name], check=True)
    subprocess.run(["git", "-C", tmp, "commit", "-q", "-m", message], check=True)


V1 = """<mxfile>
  <diagram id="p1" name="Page-1">
    <mxGraphModel dx="800" dy="600" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="850" pageHeight="1100" math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <mxCell id="n1" value="A" style="rounded=1;whiteSpace=wrap;html=1;" vertex="1" parent="1">
          <mxGeometry x="40" y="40" width="120" height="60" as="geometry"/>
        </mxCell>
        <mxCell id="n2" value="B" style="rounded=1;whiteSpace=wrap;html=1;" vertex="1" parent="1">
          <mxGeometry x="240" y="40" width="120" height="60" as="geometry"/>
        </mxCell>
        <mxCell id="e1" style="html=1;" edge="1" parent="1" source="n1" target="n2">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
"""

V2 = V1.replace('value="B"', 'value="B2"')


class TestChangedDrawios(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load("prdiff")

    def test_modified(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_repo(tmp)
            write_commit(tmp, "a.drawio", V1, "v1")
            write_commit(tmp, "a.drawio", V2, "v2")
            self.assertEqual(self.m.changed_drawios("HEAD~1", "HEAD", tmp), [("a.drawio", "modified")])

    def test_added(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_repo(tmp)
            write_commit(tmp, "a.drawio", V1, "v1")
            write_commit(tmp, "b.drawio", V1, "add b")
            self.assertEqual(self.m.changed_drawios("HEAD~1", "HEAD", tmp), [("b.drawio", "added")])

    def test_removed(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_repo(tmp)
            write_commit(tmp, "a.drawio", V1, "v1")
            os.remove(os.path.join(tmp, "a.drawio"))
            subprocess.run(["git", "-C", tmp, "add", "-A"], check=True, cwd=tmp)
            subprocess.run(["git", "-C", tmp, "commit", "-q", "-m", "remove a"], check=True)
            self.assertEqual(self.m.changed_drawios("HEAD~1", "HEAD", tmp), [("a.drawio", "removed")])

    def test_non_drawio_files_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_repo(tmp)
            write_commit(tmp, "a.drawio", V1, "v1")
            write_commit(tmp, "notes.txt", "hello", "add notes")
            self.assertEqual(self.m.changed_drawios("HEAD~1", "HEAD", tmp), [])


class TestRenderMarkdown(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load("prdiff")

    def test_sections_statuses_and_links(self):
        entries = [
            {"path": "a.drawio", "status": "modified",
             "base_png": "/out/a.base.png", "head_png": "/out/a.head.png", "diff_png": "/out/a.diff.png"},
            {"path": "b.drawio", "status": "added", "head_png": "/out/b.head.png"},
            {"path": "c.drawio", "status": "removed", "base_png": "/out/c.base.png"},
        ]
        md = self.m.render_markdown(entries, "/out")
        self.assertIn("## a.drawio (modified)", md)
        self.assertIn("## b.drawio (added)", md)
        self.assertIn("## c.drawio (removed)", md)
        self.assertIn("![base](a.base.png)", md)
        self.assertIn("![head](a.head.png)", md)
        self.assertIn("![diff](a.diff.png)", md)
        self.assertIn("![head](b.head.png)", md)
        self.assertIn("![base](c.base.png)", md)
        self.assertIn("3 file(s) changed", md)
        self.assertIn("+1 added", md)
        self.assertIn("-1 removed", md)
        self.assertIn("~1 modified", md)

    def test_no_changes(self):
        md = self.m.render_markdown([], "/out")
        self.assertIn("No `.drawio` files changed", md)

    def test_skipped_cli_note(self):
        entries = [{"path": "a.drawio", "status": "modified", "skipped": True}]
        md = self.m.render_markdown(entries, "/out")
        self.assertIn("## a.drawio (modified)", md)
        self.assertIn("images skipped", md)
        self.assertNotIn("![", md)


class TestFullPipeline(unittest.TestCase):
    """Exercises the real draw.io CLI (and Graphviz, via drawiodiff+autolayout)."""

    @classmethod
    def setUpClass(cls):
        cls.m = load("prdiff")

    def test_build_entry_exports_base_head_diff_pngs(self):
        if os.environ.get("DRAWIO_E2E") != "1":
            self.skipTest("set DRAWIO_E2E=1 to launch the desktop CLI")
        if shutil.which("drawio") is None:
            self.skipTest("draw.io CLI not installed")
        if shutil.which("dot") is None:
            self.skipTest("Graphviz `dot` not installed (needed by drawiodiff -> autolayout)")
        with tempfile.TemporaryDirectory() as tmp:
            repo = os.path.join(tmp, "repo")
            os.makedirs(repo)
            make_repo(repo)
            write_commit(repo, "a.drawio", V1, "v1")
            write_commit(repo, "a.drawio", V2, "v2")
            out_dir = os.path.join(tmp, "out")
            os.makedirs(out_dir)
            entry = self.m.build_entry(repo, "HEAD~1", "HEAD", "a.drawio", "modified", out_dir, True)
            self.assertTrue(os.path.exists(entry["base_png"]))
            self.assertTrue(os.path.exists(entry["head_png"]))
            self.assertTrue(os.path.exists(entry["diff_png"]))


if __name__ == "__main__":
    unittest.main()
