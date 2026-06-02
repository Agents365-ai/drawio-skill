# Auto-layout (Graphviz)

Read this when a diagram is **large or layout-heavy** — dependency/call graphs, code/module structure, or roughly **more than ~15 nodes** — where hand-placing `x`/`y` coordinates is slow, error-prone, and overlap-prone.

Instead of computing coordinates by hand in the Generate step, describe the graph as JSON and let `scripts/autolayout.py` place the nodes and route the edges with Graphviz, then continue the normal workflow (Export draft → Self-check → …) on the produced `.drawio`.

For small or carefully-styled diagrams, keep hand-placing — auto-layout trades fine control for scale.

## Dependency

Requires Graphviz `dot` on PATH:

```bash
# macOS
brew install graphviz
# Debian/Ubuntu
sudo apt install graphviz
```

The script exits with a clear message if `dot` is missing — fall back to hand-placed coordinates in that case.

## Usage

```bash
python3 <this-skill-dir>/scripts/autolayout.py graph.json -o diagram.drawio
```

It prints `wrote diagram.drawio (N nodes, M edges)` to stderr and writes a normal `.drawio` file. From there, continue at the **Export draft** step of the main workflow (preview PNG with `--width 2000`, self-check, review loop, final export with `-e` + `repair_png.py`).

## Input format

```json
{
  "direction": "TB",
  "nodes": [
    {"id": "client", "label": "Web Client", "style": "rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;"},
    {"id": "gw", "label": "API Gateway"},
    {"id": "db", "label": "User DB", "style": "shape=cylinder3;whiteSpace=wrap;html=1;", "width": 120, "height": 80}
  ],
  "edges": [
    {"source": "client", "target": "gw", "label": "HTTPS"},
    {"source": "gw", "target": "db"}
  ]
}
```

**Fields**

| Field | Required | Default | Notes |
|---|---|---|---|
| `direction` | no | `TB` | `TB` (top→bottom) or `LR` (left→right) — the layout rank direction |
| `nodes[].id` | **yes** | — | Unique; must not be `0` or `1` (reserved for draw.io root cells) |
| `nodes[].label` | no | the `id` | Display text; auto XML-escaped |
| `nodes[].style` | no | blue rounded box | Any draw.io style string — reuse the role/shape styles from `diagram-types.md` and the active preset |
| `nodes[].width` / `height` | no | `120` / `60` | Pixels; dot lays out at this real size |
| `edges[].source` / `target` | **yes** | — | Must match node ids |
| `edges[].label` | no | empty | Edge text |

## How it places things

- Node positions come from `dot` (hierarchical layered layout), converted to draw.io pixels and snapped to the grid (multiples of 10).
- Edges use `splines=ortho`: dot's orthogonal route is replayed as draw.io waypoints, so edges go **around** nodes instead of through them.
- Apply the active style preset by setting each node's `style` to the preset's role/shape values before calling the script — the script does not know about presets.

## Importers — visualize code structure

`scripts/pyimports.py` turns a **Python project/package** into a graph JSON ready for autolayout, so "visualize this codebase" is a two-step pipeline:

```bash
python3 <this-skill-dir>/scripts/pyimports.py myproject -o graph.json
python3 <this-skill-dir>/scripts/autolayout.py graph.json -o diagram.drawio
```

It walks the directory, parses each module with `ast`, and builds the **intra-project** module-import edges (third-party/stdlib imports are ignored). If the directory is itself a package (`__init__.py` present), module names are package-qualified so the project's own absolute imports resolve; nested subpackages (`pkg.sub.mod`) are handled.

**Density reduction is on by default** — this is the key to a readable result. Real import graphs are dense (asyncio: 33 modules / ~149 edges); without reduction they render as a hairball. `pyimports.py` applies **transitive reduction** (Graphviz `tred` — drops edges already implied by a longer path), which on asyncio cuts ~149 edges to ~46 and turns the hairball into a clean, traceable diagram. Pass `--no-reduce` to keep every edge.

Flags: `--direction TB|LR` (default `TB`), `--no-reduce`. Node labels are shortened (the shared package prefix is dropped); ids stay fully qualified.

For other languages, produce the same graph JSON from any analyzer (e.g. `dependency-cruiser` for JS/TS, `go-callvis` for Go) and feed it to autolayout the same way.

## Limitations

- **Placement is topological, not semantic** — dot minimises edge crossings, which may put a node in a different column than you'd choose by hand. Re-export with the other `direction`, or hand-tune the produced XML afterwards (it's a normal `.drawio`).
- **`pyimports.py` is module-level** — it maps module→module imports, not function/class call graphs, and resolves static `import`/`from` statements (not dynamic `importlib` calls).
- **Parallel edges** between the same `(source, target)` pair share one route.
- **No containers/swimlanes** — this MVP lays out a flat node/edge graph. For nested architecture diagrams, hand-place containers (see SKILL.md "Containers and groups").
