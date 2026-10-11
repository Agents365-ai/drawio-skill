#!/usr/bin/env python3
"""Minimal MCP (Model Context Protocol) stdio server for diagramctl.

Stdlib-only JSON-RPC 2.0 over newline-delimited stdin/stdout, so any MCP host
(Claude Desktop, Cursor, VS Code, ...) can run the skill's semantic workflows
without installing the `mcp` package. Each tool call shells out to
`diagramctl.py`, the same stable CLI surface agents use directly. No tool in
this server performs network access.

Run:  python3 scripts/diagramctl_mcp.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIAGRAMCTL = HERE / "diagramctl.py"
PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "drawio-skill", "version": "3.1.0"}
CALL_TIMEOUT_SECONDS = 180

# Every tool maps 1:1 to a diagramctl subcommand. Paths are resolved relative
# to the server process CWD (whatever the host launched it from).


def _schema(props, required):
    return {
        "type": "object",
        "properties": props,
        "required": required,
        "additionalProperties": False,
    }


TOOLS = [
    {
        "name": "doctor",
        "description": (
            "Check the local drawio-skill environment: python version, draw.io CLI, "
            "Graphviz, optional packages, and capability flags. Safe, nothing is "
            "launched."
        ),
        "inputSchema": _schema(
            {"probe": {"type": "boolean", "description": "Also run drawio --version"}},
            [],
        ),
        "argv": lambda a: ["doctor"] + (["--probe"] if a.get("probe") else []),
    },
    {
        "name": "build",
        "description": (
            "Build an editable .drawio diagram from code, IaC, SQL, OpenAPI, "
            "AsyncAPI, Protobuf, GraphQL, compose, a graph JSON, or an existing IR "
            "file. "
            "Auto-detects the "
            "source type. Returns a JSON report and writes the .drawio (and "
            "optionally the IR JSON)."
        ),
        "inputSchema": _schema(
            {
                "source": {"type": "string", "description": "Path to source dir/file"},
                "output": {"type": "string", "description": "Output .drawio path"},
                "ir_output": {
                    "type": "string",
                    "description": "Optional Diagram IR JSON output path",
                },
                "source_type": {
                    "type": "string",
                    "description": "Override auto-detection "
                    "(python|javascript|go|rust|pyclasses|terraform|kubernetes|"
                    "compose|sql|openapi|asyncapi|proto|graphql|ci|graph|ir|drawio)",
                },
                "group": {
                    "type": "boolean",
                    "description": "Group nodes by module/namespace",
                },
                "views": {
                    "type": "string",
                    "description": "Comma-separated views: executive,system,deployment,dataflow,security",
                },
                "title": {"type": "string"},
            },
            ["source", "output"],
        ),
        "argv": lambda a: ["build", a["source"], "-o", a["output"]]
        + (["--ir-output", a["ir_output"]] if a.get("ir_output") else [])
        + (["--from", a["source_type"]] if a.get("source_type") else [])
        + (["--group"] if a.get("group") else [])
        + (["--views", a["views"]] if a.get("views") else [])
        + (["--title", a["title"]] if a.get("title") else []),
    },
    {
        "name": "sync",
        "description": (
            "Incrementally update an existing .drawio from its (changed) source "
            "while preserving manual geometry and styling. Removals are staged "
            "for review unless prune is set."
        ),
        "inputSchema": _schema(
            {
                "diagram": {"type": "string", "description": "Existing .drawio file"},
                "source": {
                    "type": "string",
                    "description": "Fresh source to sync from",
                },
                "output": {"type": "string", "description": "Updated .drawio path"},
                "prune": {
                    "type": "boolean",
                    "description": "Explicitly remove elements gone from the source",
                },
            },
            ["diagram", "source", "output"],
        ),
        "argv": lambda a: ["sync", a["diagram"], a["source"], "-o", a["output"]]
        + (["--prune"] if a.get("prune") else []),
    },
    {
        "name": "views",
        "description": (
            "Project one Diagram IR file into linked audience/concern views "
            "(executive, system, deployment, dataflow, security) as a multi-page "
            ".drawio."
        ),
        "inputSchema": _schema(
            {
                "input": {"type": "string", "description": "Diagram IR JSON path"},
                "output": {"type": "string", "description": "Output .drawio path"},
                "views": {
                    "type": "string",
                    "description": "Comma-separated view names (default: all five)",
                },
                "direction": {"type": "string", "enum": ["TB", "LR"]},
            },
            ["input", "output"],
        ),
        "argv": lambda a: ["views", a["input"], "-o", a["output"]]
        + (["--views", a["views"]] if a.get("views") else [])
        + (["--direction", a["direction"]] if a.get("direction") else []),
    },
    {
        "name": "architecture_test",
        "description": (
            "Run deterministic architecture contract rules (direct "
            "Internet-to-database access, cycles, orphans, ownership, production "
            "observability, external timeouts, trust-boundary protocols, contrast) "
            "against a Diagram IR file. Exit is reflected in isError."
        ),
        "inputSchema": _schema(
            {
                "input": {"type": "string", "description": "Diagram IR JSON path"},
                "rules": {
                    "type": "string",
                    "description": "Optional JSON/YAML policy path (default: all rules)",
                },
                "strict": {"type": "boolean", "description": "Fail on warnings too"},
            },
            ["input"],
        ),
        "argv": lambda a: ["test", a["input"]]
        + (["--rules", a["rules"]] if a.get("rules") else [])
        + (["--strict"] if a.get("strict") else []),
    },
    {
        "name": "review",
        "description": (
            "Review an architecture model for ownership, resilience, trust "
            "boundaries, and accessibility; returns a Markdown or JSON report."
        ),
        "inputSchema": _schema(
            {
                "input": {"type": "string", "description": "Diagram IR JSON path"},
                "format": {"type": "string", "enum": ["markdown", "json"]},
            },
            ["input"],
        ),
        "argv": lambda a: [
            "review",
            a["input"],
            "--format",
            a.get("format", "markdown"),
        ],
    },
    {
        "name": "query",
        "description": (
            "Query a Diagram IR: filter nodes by kind/owner/boundary, or find the "
            "directed path between two components."
        ),
        "inputSchema": _schema(
            {
                "input": {"type": "string", "description": "Diagram IR JSON path"},
                "kind": {"type": "string"},
                "owner": {"type": "string"},
                "boundary": {"type": "string"},
                "from": {"type": "string", "description": "Path query: start node id"},
                "to": {"type": "string", "description": "Path query: end node id"},
            },
            ["input"],
        ),
        "argv": lambda a: ["query", a["input"]]
        + sum(
            (
                [f"--{k.replace('_', '-')}", a[k]]
                for k in ("kind", "owner", "boundary", "from", "to")
                if a.get(k)
            ),
            [],
        ),
    },
    {
        "name": "whatif",
        "description": (
            "Simulate failure propagation from one component: downstream impact, "
            "isolation points, and an optional red/amber annotated .drawio."
        ),
        "inputSchema": _schema(
            {
                "input": {"type": "string", "description": "Diagram IR JSON path"},
                "fail": {"type": "string", "description": "Node id or label to fail"},
                "drawio": {
                    "type": "string",
                    "description": "Optional annotated .drawio output path",
                },
            },
            ["input", "fail"],
        ),
        "argv": lambda a: ["whatif", a["input"], "--fail", a["fail"]]
        + (["--drawio", a["drawio"]] if a.get("drawio") else []),
    },
    {
        "name": "story",
        "description": (
            "Publish an accessible, self-contained offline HTML walkthrough of "
            "the model (keyboard navigation, text alternative, multilingual "
            "labels)."
        ),
        "inputSchema": _schema(
            {
                "input": {"type": "string", "description": "Diagram IR JSON path"},
                "output": {"type": "string", "description": "Output .html path"},
                "title": {"type": "string"},
                "fail": {
                    "type": "string",
                    "description": "Optional failure-scenario node",
                },
            },
            ["input", "output"],
        ),
        "argv": lambda a: ["story", a["input"], "-o", a["output"]]
        + (["--title", a["title"]] if a.get("title") else [])
        + (["--fail", a["fail"]] if a.get("fail") else []),
    },
]


def call_tool(name, arguments):
    tool = next((t for t in TOOLS if t["name"] == name), None)
    if tool is None:
        raise KeyError(f"unknown tool {name!r}")
    argv = [sys.executable, str(DIAGRAMCTL)] + tool["argv"](arguments or {})
    proc = subprocess.run(
        argv, capture_output=True, text=True, timeout=CALL_TIMEOUT_SECONDS
    )
    text = (proc.stdout or proc.stderr).strip()
    if proc.returncode == 2:  # usage/argument error from diagramctl
        raise ValueError(f"diagramctl rejected the arguments: {text}")
    return proc.returncode, text


def validate_arguments(tool, arguments):
    """Validate tool arguments against the tool's flat input schema.

    Returns the arguments unchanged, or raises MethodError(-32602) with a
    readable diagnostic. Without this check a missing key reaches argv
    construction and surfaces as a misleading unknown-tool error.
    """
    if arguments is None:
        arguments = {}
    name = tool["name"]
    if not isinstance(arguments, dict):
        raise MethodError(
            -32602, f"invalid params: arguments for tool {name!r} must be an object"
        )
    schema = tool["inputSchema"]
    missing = [key for key in schema["required"] if key not in arguments]
    if missing:
        raise MethodError(
            -32602,
            f"invalid params: missing required argument(s) "
            f"{', '.join(missing)} for tool {name!r}",
        )
    for key, value in arguments.items():
        spec = schema["properties"].get(key)
        if spec is None:
            raise MethodError(
                -32602, f"invalid params: unknown argument {key!r} for tool {name!r}"
            )
        expected = spec["type"]
        if expected == "boolean" and not isinstance(value, bool):
            raise MethodError(
                -32602,
                f"invalid params: argument {key!r} for tool {name!r} "
                f"must be a {expected}",
            )
        if expected == "string" and not isinstance(value, str):
            raise MethodError(
                -32602,
                f"invalid params: argument {key!r} for tool {name!r} "
                f"must be a {expected}",
            )
        allowed = spec.get("enum")
        if allowed is not None and value not in allowed:
            raise MethodError(
                -32602,
                f"invalid params: argument {key!r} for tool {name!r} "
                f"must be one of {', '.join(str(a) for a in allowed)}",
            )
    return arguments


def dispatch(method, params):
    if method == "initialize":
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": SERVER_INFO,
        }
    if method == "ping":
        return {}
    if method == "tools/list":
        return {
            "tools": [
                {
                    "name": t["name"],
                    "description": t["description"],
                    "inputSchema": t["inputSchema"],
                }
                for t in TOOLS
            ]
        }
    if method == "tools/call":
        name = params.get("name", "")
        if not isinstance(name, str):
            raise MethodError(-32602, "invalid params: tool name must be a string")
        tool = next((t for t in TOOLS if t["name"] == name), None)
        if tool is None:
            raise MethodError(-32602, f"unknown tool {name!r}")
        arguments = validate_arguments(tool, params.get("arguments"))
        try:
            code, text = call_tool(name, arguments)
        except ValueError as exc:
            return {"content": [{"type": "text", "text": str(exc)}], "isError": True}
        except subprocess.TimeoutExpired:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"{name} timed out after {CALL_TIMEOUT_SECONDS}s",
                    }
                ],
                "isError": True,
            }
        return {
            "content": [{"type": "text", "text": text}],
            "isError": code != 0,
        }
    raise MethodError(-32601, f"method not found: {method}")


class MethodError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def error_response(id_value, code, message):
    return {
        "jsonrpc": "2.0",
        "id": id_value,
        "error": {"code": code, "message": message},
    }


def handle(line):
    """Handle one JSON-RPC message; returns a response dict or None (notification)."""
    try:
        msg = json.loads(line)
    except ValueError:
        return error_response(None, -32700, "parse error")
    if not isinstance(msg, dict):
        return error_response(None, -32600, "invalid request: expected a JSON object")
    method = msg.get("method")
    if isinstance(method, str) and method.startswith("notifications/"):
        # Legacy notification-method suppression (MCP names such as
        # notifications/initialized): never answered, valid or not.
        return None
    if "id" in msg:
        id_value = msg["id"]
        is_valid_id = id_value is None or (
            not isinstance(id_value, bool)
            and isinstance(id_value, (str, int, float))
        )
        if not is_valid_id:
            return error_response(
                None,
                -32600,
                "invalid request: id must be a string, number, or null",
            )
    if msg.get("jsonrpc") != "2.0":
        return error_response(
            msg.get("id"), -32600, "invalid request: jsonrpc must be '2.0'"
        )
    if not isinstance(method, str):
        return error_response(
            msg.get("id"), -32600, "invalid request: method must be a string"
        )
    is_notification = "id" not in msg
    params = msg.get("params")
    if params is not None and not isinstance(params, dict):
        if is_notification:
            return None
        return error_response(
            msg.get("id"), -32602, "invalid params: expected an object"
        )
    try:
        result = dispatch(method, params or {})
        return (
            None
            if is_notification
            else {"jsonrpc": "2.0", "id": msg["id"], "result": result}
        )
    except MethodError as exc:
        return (
            None
            if is_notification
            else {
                "jsonrpc": "2.0",
                "id": msg.get("id"),
                "error": {"code": exc.code, "message": exc.message},
            }
        )


def main():
    for line in sys.stdin:
        response = handle(line)
        if response is not None:
            sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
