#!/usr/bin/env python3
"""Tests for the diagramctl MCP stdio server (scripts/diagramctl_mcp.py)."""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "skills" / "drawio-skill" / "scripts"

_spec = importlib.util.spec_from_file_location(
    "diagramctl_mcp", SCRIPTS / "diagramctl_mcp.py"
)
assert _spec is not None and _spec.loader is not None
mcp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mcp)

GRAPH = {
    "nodes": [
        {"id": "web", "label": "Web", "kind": "service"},
        {"id": "db", "label": "Orders DB", "kind": "database"},
    ],
    "edges": [{"source": "web", "target": "db", "label": "SQL"}],
}


def rpc(method, params=None, id=1):
    line = json.dumps(
        {"jsonrpc": "2.0", "id": id, "method": method, "params": params or {}}
    )
    return mcp.handle(line)


class TestMcpProtocol(unittest.TestCase):
    def test_initialize(self):
        resp = rpc("initialize")
        self.assertEqual(resp["result"]["serverInfo"]["name"], "drawio-skill")
        self.assertIn("protocolVersion", resp["result"])

    def test_notification_returns_none(self):
        self.assertIsNone(
            mcp.handle(
                json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"})
            )
        )

    def test_ping(self):
        self.assertEqual(rpc("ping")["result"], {})

    def test_unknown_method(self):
        resp = rpc("nope/nope")
        self.assertEqual(resp["error"]["code"], -32601)

    def test_parse_error(self):
        resp = mcp.handle("{broken")
        self.assertEqual(resp["error"]["code"], -32700)

    def test_unknown_tool(self):
        resp = rpc("tools/call", {"name": "bogus"})
        self.assertEqual(resp["error"]["code"], -32602)


class TestMcpTools(unittest.TestCase):
    def test_tools_list(self):
        tools = rpc("tools/list")["result"]["tools"]
        names = {t["name"] for t in tools}
        self.assertTrue(
            {
                "doctor",
                "build",
                "sync",
                "views",
                "architecture_test",
                "review",
                "query",
                "whatif",
                "story",
            }
            <= names
        )
        for tool in tools:
            self.assertEqual(tool["inputSchema"]["type"], "object")
            self.assertIn("description", tool)

    def test_doctor_call(self):
        resp = rpc("tools/call", {"name": "doctor"})
        result = resp["result"]
        self.assertFalse(result["isError"])
        self.assertIn("python", result["content"][0]["text"])

    def test_build_and_test_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            graph = Path(td) / "graph.json"
            graph.write_text(json.dumps(GRAPH))
            out = Path(td) / "out.drawio"
            ir = Path(td) / "out.ir.json"
            resp = rpc(
                "tools/call",
                {
                    "name": "build",
                    "arguments": {
                        "source": str(graph),
                        "output": str(out),
                        "source_type": "graph",
                    },
                },
            )
            self.assertFalse(resp["result"]["isError"], resp["result"]["content"])
            self.assertTrue(out.exists())
            self.assertTrue(ir.exists() is False)  # ir-output not requested
            report = json.loads(resp["result"]["content"][0]["text"])
            self.assertEqual(report["nodes"], 2)

            resp = rpc(
                "tools/call",
                {
                    "name": "architecture_test",
                    "arguments": {"input": str(ir if ir.exists() else graph)},
                },
            )
            # graph is not IR; the call must fail cleanly with isError, not crash
            if not resp["result"]["isError"]:
                self.assertIn("errors", resp["result"]["content"][0]["text"])

    def test_bad_arguments_is_clean_error(self):
        resp = rpc(
            "tools/call",
            {
                "name": "build",
                "arguments": {
                    "source": "/nonexistent/xyz",
                    "output": "/tmp/xyz.drawio",
                },
            },
        )
        self.assertTrue(resp["result"]["isError"])


class TestMcpStdioProcess(unittest.TestCase):
    def test_end_to_end_stdio(self):
        msgs = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        ]
        payload = "\n".join(json.dumps(m) for m in msgs) + "\n"
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / "diagramctl_mcp.py")],
            input=payload,
            capture_output=True,
            text=True,
            timeout=60,
        )
        lines = [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
        self.assertEqual(len(lines), 2)  # notifications produce no response
        self.assertEqual(lines[0]["result"]["serverInfo"]["name"], "drawio-skill")
        self.assertIn("tools", lines[1]["result"])


if __name__ == "__main__":
    unittest.main()
