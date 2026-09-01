# MCP server mode

`scripts/diagramctl_mcp.py` exposes the skill's semantic workflows as an MCP
(Model Context Protocol) server over stdio, so MCP hosts (Claude Desktop,
Cursor, VS Code, Codex, any MCP client) can drive them directly. It is
stdlib-only: no `mcp` package, no network access, no GUI launch. Every tool
call shells out to `scripts/diagramctl.py`, the same CLI the skill uses.

## Register with a host

```json
{
  "mcpServers": {
    "drawio-skill": {
      "command": "python3",
      "args": ["/path/to/drawio-skill/skills/drawio-skill/scripts/diagramctl_mcp.py"]
    }
  }
}
```

- Claude Desktop / Cursor / VS Code: add the snippet above to the host's MCP
  config (`claude_desktop_config.json`, `mcp.json`, `.vscode/mcp.json`, ...).
- Claude Code: `claude mcp add drawio-skill -- python3 <path>/scripts/diagramctl_mcp.py`.
- Paths in tool arguments are resolved against the server's working directory
  (whatever the host launches it with), so prefer absolute paths.

## Tools

| Tool | Maps to | Purpose |
| --- | --- | --- |
| `doctor` | `diagramctl doctor` | Check python/draw.io/Graphviz availability without launching anything |
| `build` | `build` | Code / IaC / SQL / OpenAPI / graph / IR → editable `.drawio` (+ optional IR) |
| `sync` | `sync` | Incremental re-sync of a diagram from its changed source, preserving manual layout |
| `views` | `views` | Project an IR file into linked executive/system/deployment/dataflow/security pages |
| `architecture_test` | `test` | Deterministic architecture contract rules (policy YAML/JSON); `isError` mirrors the CI exit code |
| `review` | `review` | Ownership / resilience / trust-boundary / accessibility report (Markdown or JSON) |
| `query` | `query` | Filter nodes by kind/owner/boundary; directed path between two components |
| `whatif` | `whatif` | Failure-propagation simulation with optional red/amber annotated `.drawio` |
| `story` | `story` | Accessible offline HTML walkthrough (keyboard navigation, text alternative) |

Outputs are files (`.drawio`, `.html`, `.json`); tool results return the JSON
report or report text plus the written paths, so the host can open or attach
them.

## Behavior and safety

- Offline by default: no tool performs network access; native PNG export is
  deliberately not exposed (it launches the Electron GUI) — export from the
  CLI or the draw.io desktop app when needed.
- `architecture_test` failing rules are reported as a normal tool result with
  `isError: true`, so CI-style gating survives the MCP hop.
- Errors from bad paths/arguments come back as readable text, never as
  crashes; the server process itself never exits on a tool failure.
- Protocol: newline-delimited JSON-RPC 2.0, `initialize` / `tools/list` /
  `tools/call` / `ping`; notifications produce no response.
