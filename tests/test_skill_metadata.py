#!/usr/bin/env python3
"""Regression tests for standard and distribution skill metadata."""

import json
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, "skills", "drawio-skill", "SKILL.md")


class TestSkillMetadata(unittest.TestCase):
    def test_declared_versions_match(self):
        with open(SKILL, encoding="utf-8") as f:
            text = f.read()

        metadata_match = re.search(r"^metadata:\s*(\{.*\})\s*$", text, re.M)
        self.assertIsNotNone(metadata_match, "metadata JSON is missing")
        assert metadata_match is not None
        metadata = json.loads(metadata_match.group(1))

        self.assertEqual("3.2.0", metadata.get("version"))
        self.assertEqual(
            "https://github.com/Agents365-ai/drawio-skill", metadata.get("homepage")
        )
        self.assertEqual(["macos", "linux", "windows"], metadata.get("platforms"))


if __name__ == "__main__":
    unittest.main()
