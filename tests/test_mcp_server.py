#!/usr/bin/env python3
"""Tests for the diagramctl MCP stdio server (scripts/diagramctl_mcp.py)."""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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

    def test_non_object_request_is_invalid_request(self):
        for payload in ("[]", "null", "42", '"ping"'):
            resp = mcp.handle(payload)
            self.assertEqual(-32600, resp["error"]["code"], payload)
            self.assertIsNone(resp["id"])

    def test_invalid_version_is_invalid_request(self):
        resp = mcp.handle(json.dumps({"jsonrpc": "1.0", "id": 7, "method": "ping"}))
        self.assertEqual(-32600, resp["error"]["code"])
        self.assertEqual(7, resp["id"])

    def test_missing_or_non_string_method_is_invalid_request(self):
        resp = mcp.handle(json.dumps({"jsonrpc": "2.0", "id": 1}))
        self.assertEqual(-32600, resp["error"]["code"])
        self.assertEqual(1, resp["id"])
        resp = mcp.handle(json.dumps({"jsonrpc": "2.0", "id": 2, "method": ["ping"]}))
        self.assertEqual(-32600, resp["error"]["code"])
        self.assertEqual(2, resp["id"])

    def test_non_object_params_is_invalid_params(self):
        for params in ([], "ping", 3, True):
            line = json.dumps(
                {"jsonrpc": "2.0", "id": 1, "method": "ping", "params": params}
            )
            resp = mcp.handle(line)
            self.assertEqual(-32602, resp["error"]["code"], params)

    def test_unknown_notification_is_silent(self):
        line = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "notifications/cancelled",
                "params": {"requestId": 3},
            }
        )
        self.assertIsNone(mcp.handle(line))

    def test_notification_with_invalid_params_is_silent(self):
        # A message without an id is a notification: invalid params must not
        # produce an error response.
        line = json.dumps({"jsonrpc": "2.0", "method": "ping", "params": []})
        self.assertIsNone(mcp.handle(line))

    def test_notification_with_invalid_tool_arguments_is_silent(self):
        line = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": "build", "arguments": {}},
            }
        )
        self.assertIsNone(mcp.handle(line))

    def test_invalid_request_without_id_is_still_answered(self):
        # Only the invalid-params path is notification-suppressed; an invalid
        # request is answered even without an id.
        resp = mcp.handle(json.dumps({"jsonrpc": "2.0", "method": ["ping"]}))
        self.assertEqual(-32600, resp["error"]["code"])
        self.assertIsNone(resp["id"])

    def test_invalid_id_shapes_are_rejected(self):
        for bad_id in ([1], {"a": 1}, True, False):
            line = json.dumps(
                {"jsonrpc": "2.0", "id": bad_id, "method": "ping", "params": {}}
            )
            resp = mcp.handle(line)
            self.assertEqual(-32600, resp["error"]["code"], bad_id)
            self.assertIsNone(resp["id"], bad_id)

    def test_supported_ids_are_echoed(self):
        for good_id in ("abc", 7, 2.5, None):
            line = json.dumps(
                {"jsonrpc": "2.0", "id": good_id, "method": "ping", "params": {}}
            )
            resp = mcp.handle(line)
            self.assertIsNone(resp.get("error"), good_id)
            self.assertEqual({}, resp["result"], good_id)
            self.assertEqual(good_id, resp["id"], good_id)


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

    def test_build_schema_requires_only_source_and_output(self):
        tools = rpc("tools/list")["result"]["tools"]
        build = next(t for t in tools if t["name"] == "build")
        self.assertEqual(["source", "output"], build["inputSchema"]["required"])
        self.assertEqual(
            "string", build["inputSchema"]["properties"]["ir_output"]["type"]
        )

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
                        "ir_output": str(ir),
                    },
                },
            )
            self.assertFalse(resp["result"]["isError"], resp["result"]["content"])
            report = json.loads(resp["result"]["content"][0]["text"])
            self.assertEqual(2, report["nodes"])
            self.assertEqual(1, report["edges"])
            self.assertEqual(str(ir), report["ir"])
            self.assertTrue(out.exists())
            self.assertTrue(ir.exists())
            document = json.loads(ir.read_text(encoding="utf-8"))
            self.assertEqual("drawio-skill/diagram-ir/v1", document["schema"])
            self.assertEqual(["web", "db"], [n["id"] for n in document["nodes"]])
            self.assertEqual(
                [["web", "db"]],
                [[e["source"], e["target"]] for e in document["edges"]],
            )

            resp = rpc(
                "tools/call",
                {"name": "architecture_test", "arguments": {"input": str(ir)}},
            )
            result = resp["result"]
            self.assertFalse(result["isError"], result["content"])
            findings = json.loads(result["content"][0]["text"])
            self.assertEqual(0, findings["errors"])
            self.assertEqual(0, findings["warnings"])
            self.assertEqual([], findings["findings"])

    def test_build_without_ir_output_writes_only_drawio(self):
        with tempfile.TemporaryDirectory() as td:
            graph = Path(td) / "graph.json"
            graph.write_text(json.dumps(GRAPH))
            out = Path(td) / "out.drawio"
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
            report = json.loads(resp["result"]["content"][0]["text"])
            self.assertIsNone(report["ir"])
            self.assertTrue(out.exists())
            self.assertEqual([], sorted(Path(td).glob("*.ir.json")))

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


class TestMcpToolArgumentValidation(unittest.TestCase):
    def test_missing_required_arguments_is_invalid_params(self):
        resp = rpc("tools/call", {"name": "build", "arguments": {"source": "x"}})
        self.assertEqual(-32602, resp["error"]["code"])
        self.assertIn("output", resp["error"]["message"])
        self.assertIn("build", resp["error"]["message"])
        self.assertNotIn("unknown tool", resp["error"]["message"])

    def test_all_missing_required_arguments_are_listed(self):
        resp = rpc("tools/call", {"name": "sync"})
        self.assertEqual(-32602, resp["error"]["code"])
        for key in ("diagram", "source", "output"):
            self.assertIn(key, resp["error"]["message"])

    def test_wrong_type_argument_is_invalid_params(self):
        resp = rpc(
            "tools/call",
            {"name": "build", "arguments": {"source": 3, "output": "x"}},
        )
        self.assertEqual(-32602, resp["error"]["code"])
        self.assertIn("source", resp["error"]["message"])
        resp = rpc("tools/call", {"name": "doctor", "arguments": {"probe": "yes"}})
        self.assertEqual(-32602, resp["error"]["code"])
        self.assertIn("probe", resp["error"]["message"])

    def test_wrong_type_ir_output_is_invalid_params(self):
        for value in (5, ["out.ir.json"], True):
            with mock.patch.object(mcp.subprocess, "run") as run:
                resp = rpc(
                    "tools/call",
                    {
                        "name": "build",
                        "arguments": {
                            "source": "s.json",
                            "output": "o.drawio",
                            "ir_output": value,
                        },
                    },
                )
            self.assertEqual(-32602, resp["error"]["code"], value)
            self.assertIn("ir_output", resp["error"]["message"])
            run.assert_not_called()

    def test_unknown_argument_is_invalid_params(self):
        resp = rpc(
            "tools/call",
            {"name": "doctor", "arguments": {"probe": True, "verbose": True}},
        )
        self.assertEqual(-32602, resp["error"]["code"])
        self.assertIn("verbose", resp["error"]["message"])

    def test_enum_argument_is_invalid_params(self):
        resp = rpc(
            "tools/call",
            {"name": "review", "arguments": {"input": "m.json", "format": "xml"}},
        )
        self.assertEqual(-32602, resp["error"]["code"])
        self.assertIn("format", resp["error"]["message"])
        resp = rpc(
            "tools/call",
            {
                "name": "views",
                "arguments": {"input": "m.json", "output": "o.drawio", "direction": "up"},
            },
        )
        self.assertEqual(-32602, resp["error"]["code"])

    def test_arguments_must_be_an_object(self):
        resp = rpc("tools/call", {"name": "doctor", "arguments": []})
        self.assertEqual(-32602, resp["error"]["code"])

    def test_unknown_tool_stays_distinct(self):
        resp = rpc("tools/call", {"name": "bogus", "arguments": {"source": "x"}})
        self.assertEqual(-32602, resp["error"]["code"])
        self.assertIn("unknown tool", resp["error"]["message"])


class TestMcpExitCodeMapping(unittest.TestCase):
    """A nonzero diagramctl exit must surface as isError; exit 1 is a
    contract failure or a strict-warning failure, not success."""

    @staticmethod
    def _write(td, name, payload):
        path = Path(td) / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    @staticmethod
    def _clean_model():
        return {
            "nodes": [
                {"id": "api", "label": "API", "kind": "service"},
                {"id": "orders", "label": "Orders", "kind": "service"},
            ],
            "edges": [
                {"id": "e1", "source": "api", "target": "orders", "label": "HTTP"}
            ],
        }

    def test_contract_failure_exit_one_reports_iserror(self):
        with tempfile.TemporaryDirectory() as td:
            graph = self._write(
                td,
                "violating.json",
                {
                    "nodes": [
                        {"id": "internet", "label": "Internet", "kind": "external"},
                        {"id": "db", "label": "Orders DB", "kind": "database"},
                    ],
                    "edges": [
                        {"id": "e1", "source": "internet", "target": "db", "label": "SQL"}
                    ],
                },
            )
            resp = rpc(
                "tools/call",
                {"name": "architecture_test", "arguments": {"input": str(graph)}},
            )
            result = resp["result"]
            self.assertTrue(result["isError"])
            report = json.loads(result["content"][0]["text"])
            self.assertEqual(1, report["errors"])

    def test_clean_run_exit_zero_is_not_error(self):
        with tempfile.TemporaryDirectory() as td:
            graph = self._write(td, "clean.json", self._clean_model())
            resp = rpc(
                "tools/call",
                {"name": "architecture_test", "arguments": {"input": str(graph)}},
            )
            result = resp["result"]
            self.assertFalse(result["isError"])
            self.assertEqual(0, json.loads(result["content"][0]["text"])["errors"])

    def test_strict_warning_exit_one_reports_iserror(self):
        graph = self._clean_model()
        graph["nodes"].append({"id": "lonely", "label": "Lonely", "kind": "service"})
        with tempfile.TemporaryDirectory() as td:
            path = self._write(td, "warning.json", graph)
            resp = rpc(
                "tools/call",
                {"name": "architecture_test", "arguments": {"input": str(path)}},
            )
            result = resp["result"]
            self.assertFalse(result["isError"])
            self.assertEqual(1, json.loads(result["content"][0]["text"])["warnings"])
            resp = rpc(
                "tools/call",
                {
                    "name": "architecture_test",
                    "arguments": {"input": str(path), "strict": True},
                },
            )
            result = resp["result"]
            self.assertTrue(result["isError"])
            report = json.loads(result["content"][0]["text"])
            self.assertEqual(0, report["errors"])
            self.assertEqual(1, report["warnings"])


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
        self.assertEqual(0, proc.returncode, proc.stderr)
        self.assertEqual("", proc.stderr)
        lines = [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
        self.assertEqual(2, len(lines))  # notifications produce no response
        self.assertEqual([1, 2], [line["id"] for line in lines])
        self.assertEqual(["2.0", "2.0"], [line["jsonrpc"] for line in lines])
        for line in lines:
            self.assertIn("result", line)
        self.assertEqual("drawio-skill", lines[0]["result"]["serverInfo"]["name"])
        self.assertEqual("2024-11-05", lines[0]["result"]["protocolVersion"])
        self.assertEqual(
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
            },
            {t["name"] for t in lines[1]["result"]["tools"]},
        )

    def test_malformed_requests_do_not_stop_the_server(self):
        msgs = [
            "[]",
            "null",
            json.dumps({"jsonrpc": "1.0", "id": 1, "method": "ping"}),
            json.dumps({"jsonrpc": "2.0", "id": 2, "method": 5, "params": {}}),
            json.dumps({"jsonrpc": "2.0", "id": 3, "method": "ping", "params": []}),
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            # notifications (no id) with invalid params: silent
            json.dumps({"jsonrpc": "2.0", "method": "ping", "params": []}),
            {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": "build", "arguments": {}},
            },
            # invalid id shape: rejected with a null id, never echoed
            json.dumps({"jsonrpc": "2.0", "id": [4], "method": "ping"}),
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {"name": "build", "arguments": {}},
            },
            {"jsonrpc": "2.0", "id": 5, "method": "ping"},
        ]
        payload = "\n".join(
            m if isinstance(m, str) else json.dumps(m) for m in msgs
        ) + "\n"
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / "diagramctl_mcp.py")],
            input=payload,
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(0, proc.returncode, proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)
        lines = [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
        self.assertEqual(
            [-32600, -32600, -32600, -32600, -32602, -32600, -32602, None],
            [line.get("error", {}).get("code") for line in lines],
        )
        self.assertEqual(
            [None, None, 1, 2, 3, None, 4, 5], [line["id"] for line in lines]
        )
        self.assertEqual({}, lines[-1]["result"])


if __name__ == "__main__":
    unittest.main()
