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
    {"id": "gw", "label": "API Gateway", "group": "edge", "groupLabel": "Edge tier"},
    {"id": "db", "label": "User DB", "style": "shape=cylinder3;whiteSpace=wrap;html=1;", "width": 120, "height": 80, "group": "data"}
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
| `nodes[].group` | no | none | Group key, or a `/`-delimited path (`"core/db"`) for **nested** containers — nodes sharing a path are boxed together (see **Containers / grouping**) |
| `nodes[].groupLabel` | no | last path segment | Title shown on the node's deepest container (first node with the path wins) |
| `edges[].source` / `target` | **yes** | — | Must match node ids |
| `edges[].label` | no | empty | Edge text |

## How it places things

- Node positions come from `dot` (hierarchical layered layout), converted to draw.io pixels and snapped to the grid (multiples of 10).
- Edges use `splines=ortho`: dot's orthogonal route is replayed as draw.io waypoints, so edges go **around** nodes instead of through them.
- Apply the active style preset by setting each node's `style` to the preset's role/shape values before calling the script — the script does not know about presets.

## Containers / grouping

Give nodes a `group` key and the script wraps each group in a labeled container (a dashed box with the group title at top) and tells dot to keep that group's nodes together via a Graphviz cluster. Grouped nodes become children of their container (`parent="<container>"`, relative coordinates); ungrouped nodes stay at the top level. This turns a flat hairball into a "boxes of related modules" architecture view.

**Nesting.** A `group` value with `/` separators builds nested containers: `"core/db"` puts the node inside a `db` box that itself sits inside a `core` box. Every path prefix becomes a container, so an arbitrarily deep package tree maps to nested boxes. A node can also sit *directly* in a parent box (`group: "core"`) alongside a sibling sub-box (`group: "core/db"`).

- Each container box is the bounding box of its members and child boxes plus a uniform padding. The dot cluster margin is set to that same padding, so each box equals dot's cluster box — which dot keeps non-overlapping at **any nesting depth**.
- The title sits in the top padding (`verticalAlign=top`); the box title is the path's last segment, or a member's `groupLabel`.
- Containers are visual only (no edges of their own). Edges still connect node→node and route across containers normally.
- If a container's top padding would cross the page origin, the whole diagram is shifted so nothing lands at a negative coordinate.

## Validate before previewing

`scripts/validate.py` is a deterministic structural linter — run it on the produced `.drawio` before the (slower, vision-based) self-check:

```bash
python3 <this-skill-dir>/scripts/validate.py diagram.drawio
```

It catches dangling edge endpoints, duplicate/reserved ids, broken parent references (errors), plus off-grid/negative geometry and overlapping sibling nodes (warnings) — without launching draw.io. Exit status is non-zero on any error (or any warning with `--strict`), so it can gate the workflow. Auto-layout output should always pass clean; a failure means a malformed input graph (e.g. an edge referencing a missing node id).

## Importers — visualize code structure

Bundled importers turn a codebase into a graph JSON ready for autolayout, so "visualize this project" is a two-step pipeline:

| Language | Script | Node = | Edge = |
|---|---|---|---|
| Python | `scripts/pyimports.py <dir>` | module / package (`ast`) | intra-project `import` / `from` |
| JS / TS | `scripts/jsimports.py <dir>` | source file (`.ts/.tsx/.js/.jsx/.mjs/.cjs`) | resolved relative `import`/`export from`/`require()`/`import()` |
| Go | `scripts/goimports.py <dir>` | package (directory, via `go.mod`) | intra-module package import |
| Python (classes) | `scripts/pyclasses.py <dir>` | class (`ast`) | subclass → base (inheritance) |

```bash
python3 <this-skill-dir>/scripts/pyimports.py myproject -o graph.json
python3 <this-skill-dir>/scripts/autolayout.py graph.json -o diagram.drawio
```

Each keeps only **intra-project** edges (third-party/stdlib imports are ignored), shortens node labels (drops the shared package/module/directory prefix; ids stay fully qualified), and shares the same flags: `--direction TB|LR` (default `TB`), `--group`, `--no-reduce`.

- **Python** (`pyimports.py`): if the directory is itself a package (`__init__.py` present), module names are package-qualified so the project's own absolute imports resolve; nested subpackages (`pkg.sub.mod`) are handled.
- **JS/TS** (`jsimports.py`): resolution is path-based (tries the source extensions and directory `index` files); `node_modules` and bare specifiers are skipped. Scanning is regex-based, not a full parser.
- **Go** (`goimports.py`): reads the `module` path from `go.mod`; each directory of `.go` files is one package; `*_test.go` and `vendor/` are skipped.
- **Python classes** (`pyclasses.py`): a finer granularity — one node per class, edges from each subclass to the project base classes it extends, so the result is an auto-generated class hierarchy. Bases are matched by name (preferring the same module); external bases (`object`, third-party) are ignored. With `--group`, classes are boxed by their module, so a deep package tree nests naturally. Inheritance only — function-level call graphs are out of scope (static call resolution in Python is unreliable).

**Density reduction is on by default** — this is the key to a readable result. Real import graphs are dense (asyncio: 33 modules / ~149 edges); without reduction they render as a hairball. Every importer applies **transitive reduction** (Graphviz `tred` — drops edges already implied by a longer path), which on asyncio cuts ~149 edges to ~46 and turns the hairball into a clean, traceable diagram. Pass `--no-reduce` to keep every edge.

**`--group`** assigns each node a container by its sub-package / directory path, so autolayout boxes related modules together — nested when the path has depth (see **Containers / grouping**). The fastest way to turn a large code graph into a tiered architecture view.

For any other language, produce the same graph JSON from any analyzer (e.g. `dependency-cruiser` for richer JS/TS resolution, `go-callvis` for Go call graphs) and feed it to autolayout the same way.

## Limitations

- **Placement is topological, not semantic** — dot minimises edge crossings, which may put a node in a different column than you'd choose by hand. Re-export with the other `direction`, or hand-tune the produced XML afterwards (it's a normal `.drawio`).
- **Import edges are static** — `pyimports`/`jsimports`/`goimports` read static import statements (not dynamic `importlib`, runtime `require`, or reflection); `pyclasses` resolves inheritance only, not method-level calls.
- **Parallel edges** between the same `(source, target)` pair share one route.
- **Containers don't add edges** — `group`/nesting only boxes nodes for layout; edges remain node→node. For hand-built swimlane/architecture containers with their own connections, see SKILL.md "Containers and groups".
