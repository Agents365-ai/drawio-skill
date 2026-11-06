#!/usr/bin/env python3
"""Tests for scripts/drawio_cli.py — locating the draw.io desktop CLI.

Run from the repo root:
    python3 -m unittest tests.test_drawio_cli -v
"""
import importlib.util
import os
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "skills", "drawio-skill", "scripts")


def load(name):
    """Import a bundled script module by file path."""
    path = os.path.join(SCRIPTS, name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class TestResolveDrawio(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load("drawio_cli")

    def resolve(self, on_path, installed=(), env=None):
        """resolve_drawio() with a fake PATH and fake filesystem."""
        with mock.patch.object(self.m.shutil, "which",
                               side_effect=lambda name: on_path.get(name)), \
             mock.patch.object(self.m.os.path, "isfile",
                               side_effect=lambda path: path in installed), \
             mock.patch.dict(self.m.os.environ, env or {}):
            return self.m.resolve_drawio()

    def test_prefers_undotted_name_on_path(self):
        found = self.resolve({"drawio": "/usr/local/bin/drawio",
                              "draw.io": "/usr/local/bin/draw.io"})
        self.assertEqual(found, "/usr/local/bin/drawio")

    def test_accepts_dotted_name_on_path(self):
        # Windows: the installer ships draw.io.exe, so `drawio` never resolves.
        found = self.resolve({"draw.io": "/opt/draw.io"})
        self.assertEqual(found, "/opt/draw.io")

    def test_macos_app_bundle_fallback(self):
        path = "/Applications/draw.io.app/Contents/MacOS/draw.io"
        self.assertEqual(self.resolve({}, installed={path}), path)

    def test_windows_program_files_fallback(self):
        base = os.path.join(os.sep, "fake", "ProgramFiles")
        expected = os.path.join(base, "draw.io", "draw.io.exe")
        found = self.resolve({}, installed={expected}, env={"ProgramFiles": base})
        self.assertEqual(found, expected)

    def test_windows_localappdata_fallback(self):
        base = os.path.join(os.sep, "fake", "LocalAppData")
        expected = os.path.join(base, "Programs", "draw.io", "draw.io.exe")
        found = self.resolve({}, installed={expected}, env={"LOCALAPPDATA": base})
        self.assertEqual(found, expected)

    def test_missing_returns_none(self):
        self.assertIsNone(self.resolve({}))

    def test_path_hit_skips_install_locations(self):
        # A CLI on PATH wins even when an app bundle also exists.
        found = self.resolve({"drawio": "/custom/drawio"},
                             installed={"/Applications/draw.io.app/Contents/MacOS/draw.io"})
        self.assertEqual(found, "/custom/drawio")


if __name__ == "__main__":
    unittest.main()
