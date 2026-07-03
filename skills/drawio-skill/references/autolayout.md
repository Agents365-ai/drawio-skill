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
| `nodes[].style` | no | group colour, else blue | Any draw.io style string — reuse the role/shape styles from `diagram-types.md` and the active preset. A styleless node is tinted by its group (see **Containers / grouping**); an explicit style always wins |
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

- **Colour by group.** Each top-level group is assigned a colour from the skill's own palette (`styles/built-in/default.json`, cycled in role order: blue → green → orange → purple → yellow → red → grey). A node with no `style` of its own is tinted with its group's colour, and the container's border + title match — so related modules read as a coloured cluster instead of monochrome boxes. A node that carries its own `style` (e.g. from an applied preset) is left untouched. Pass `--mono` to turn colouring off (dashed grey boxes, default-blue nodes — the previous look). Ungrouped graphs are unaffected.
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

## Importers — visualize code & infrastructure

Bundled importers turn a codebase or an IaC configuration into a graph JSON ready for autolayout, so "visualize this project" is a two-step pipeline:

| Source | Script | Node = | Edge = |
|---|---|---|---|
| Python | `scripts/pyimports.py <dir>` | module / package (`ast`) | intra-project `import` / `from` |
| JS / TS | `scripts/jsimports.py <dir>` | source file (`.ts/.tsx/.js/.jsx/.mjs/.cjs`) | resolved relative `import`/`export from`/`require()`/`import()` |
| Go | `scripts/goimports.py <dir>` | package (directory, via `go.mod`) | intra-module package import |
| Rust | `scripts/rustimports.py <dir>` | module (`.rs` file / `mod`) | intra-crate `use crate::` / `super::` / `self::` |
| Python (classes) | `scripts/pyclasses.py <dir>` | class (`ast`) | subclass → base (inheritance) |
| Terraform | `scripts/tfimports.py <dir>` | `resource` / `module` block, rendered as its **official AWS/Azure/GCP icon** | cross-resource reference (`aws_iam_role.x.arn`, `${...}`, `depends_on`) |
| Kubernetes | `scripts/k8simports.py <dir>` | manifest object (kind/name), rendered as its **official K8s kind icon** | Ingress→Service, Service→workload (selector), workload→ConfigMap/Secret/PVC, HPA→target |
| docker-compose | `scripts/composeimports.py <file-or-dir>` | service (name + image box) / named volume (cylinder) | `depends_on` / `links` / `volumes_from` / named-volume mounts |
| Terraform state (**live**) | `terraform show -json \| scripts/tfstate.py -` | **deployed** resource instance, rendered as its **official cloud icon** | recorded dependency (`depends_on` in state) |
| Docker (**live**) | `docker inspect $(docker ps -q) \| scripts/dockerimports.py -` | running container (name + image) / user network (ellipse) / named volume (cylinder) | container→network, container→volume, `links` / compose `depends_on` |
| SQL DDL | `scripts/sqlerd.py <file-or-dir>` | table (column list with PK/FK markers) | foreign key (crow's-foot, labeled with the FK column) |

```bash
python3 <this-skill-dir>/scripts/pyimports.py myproject -o graph.json
python3 <this-skill-dir>/scripts/autolayout.py graph.json -o diagram.drawio
```

Each code importer keeps only **intra-project** edges (third-party/stdlib imports are ignored), shortens node labels (drops the shared package/module/directory prefix; ids stay fully qualified), and shares the same flags: `--direction TB|LR` (default `TB`), `--group`, `--no-reduce`. The IaC importers share `--direction` and `--group` and add `--no-icons`.

- **Python** (`pyimports.py`): if the directory is itself a package (`__init__.py` present), module names are package-qualified so the project's own absolute imports resolve; nested subpackages (`pkg.sub.mod`) are handled.
- **JS/TS** (`jsimports.py`): resolution is path-based (tries the source extensions and directory `index` files); `node_modules` and bare specifiers are skipped. Scanning is regex-based, not a full parser.
- **Go** (`goimports.py`): reads the `module` path from `go.mod`; each directory of `.go` files is one package; `*_test.go` and `vendor/` are skipped.
- **Rust** (`rustimports.py`): each `.rs` file is a module (`mod.rs`/`main.rs`/`lib.rs` name the enclosing module); edges come from `use` paths rooted at `crate::`/`super::`/`self::` (brace groups expanded). `std`/external crates and `target/` are skipped. Regex-based — inline `mod { … }` blocks aren't split out, and 2015-edition bare intra-crate paths aren't resolved.
- **Python classes** (`pyclasses.py`): a finer granularity — one node per class, edges from each subclass to the project base classes it extends, so the result is an auto-generated class hierarchy. Bases are matched by name (preferring the same module); external bases (`object`, third-party) are ignored. With `--group`, classes are boxed by their module, so a deep package tree nests naturally. Inheritance only — function-level call graphs are out of scope (static call resolution in Python is unreliable).
- **Terraform** (`tfimports.py`): parses `.tf` files directly (regex + brace matching, no HCL library). Each resource type is resolved to its official icon through the bundled shape index — AWS `aws4` set, Azure `azure2` set, GCP icon set — with a curated query table for the ~45 most common types and strict tag-AND matching so a partial match never lands on the wrong vendor's icon; unresolvable types fall back to a plain box labeled `name` + type (`--no-icons` forces boxes for all). `--group` boxes resources by service (`aws_s3_* → s3`). Data sources, variables, locals and providers are ignored; heredocs with unbalanced braces are the known parse limit.
- **Kubernetes** (`k8simports.py`): accepts one or more manifest files or a directory. JSON (including `kind: List`, i.e. `kubectl get ... -o json` output) parses with the stdlib alone; `.yaml`/`.yml` needs PyYAML. Kind icons come from the official `mxgraph.kubernetes` set (25 kinds mapped). Edges land only on objects present in the manifest set, matched within the same namespace. `--group` boxes objects by namespace. No `--no-reduce` flag — reference edges are sparse and never reduced.
- **docker-compose** (`composeimports.py`): needs PyYAML. Services become rounded boxes labeled `name` + image (or `build:` context); named volumes declared in the top-level `volumes:` section become cylinders. `--group` boxes services by their first network.
- **Terraform state — live** (`tfstate.py`): reads the JSON that `terraform show -json` prints (live state, or a saved plan) from a file or `-` (stdin). Provider-agnostic; `count`/`for_each` instances are expanded (labeled `name[0]`, `name[1]`, …) and module nesting is preserved. Reuses tfimports' icon resolver, so the same official AWS/Azure/GCP icons and `--no-icons` fallback apply. Edges come from the dependencies Terraform recorded in state (`depends_on`); data sources are skipped. `--group` boxes resources by module; shares `--direction` / `--no-reduce`. This is the **actually-deployed** counterpart to tfimports' declared-config view.
- **Docker — live** (`dockerimports.py`): reads the JSON array `docker inspect` prints (file or `-`). Containers become rounded boxes (name + image) matching the compose look; the user networks they attach to become green ellipses and the named volumes they mount become cylinders (Docker's built-in `bridge`/`host`/`none`/`ingress` networks and bind mounts are ignored as noise). Edges: container→network, container→volume, plus container→container from `links` and the compose `depends_on` label. `--group` boxes containers by compose project (falling back to first network). The **actually-running** counterpart to composeimports' declared view.
- **SQL DDL** (`sqlerd.py`): regex + paren matching, no SQL library. Handles inline and table-level `PRIMARY KEY`/`FOREIGN KEY ... REFERENCES`, quoted identifiers, `schema.table` prefixes (`--group` boxes by schema). Column lines carry `PK`/`FK` markers and types (`--no-types` to hide). Unknown dialect clauses are skipped, never mis-parsed into edges.

The tf/k8s importers emit `ranksep`/`nodesep` in the graph JSON automatically (icon labels render *below* the shape, so rows need extra separation).

**`--tune` (autolayout flag)**: lays the graph out in both directions (TB and LR), scores each (through-vertex routes ×20 + edge crossings ×10 + total edge length as tiebreak), and keeps the better one — report on stderr. `validate.py --score` prints the same style of readability score for a finished `.drawio`, for comparing variants.

**Density reduction is on by default** — this is the key to a readable result. Real import graphs are dense (asyncio: 33 modules / ~149 edges); without reduction they render as a hairball. Every importer applies **transitive reduction** (Graphviz `tred` — drops edges already implied by a longer path), which on asyncio cuts ~149 edges to ~46 and turns the hairball into a clean, traceable diagram. Pass `--no-reduce` to keep every edge.

**`--group`** assigns each node a container by its sub-package / directory path, so autolayout boxes related modules together — nested when the path has depth (see **Containers / grouping**). The fastest way to turn a large code graph into a tiered architecture view.

For any other language, produce the same graph JSON from any analyzer (e.g. `dependency-cruiser` for richer JS/TS resolution, `go-callvis` for Go call graphs) and feed it to autolayout the same way.

## Limitations

- **Placement is topological, not semantic** — dot minimises edge crossings, which may put a node in a different column than you'd choose by hand. Re-export with the other `direction`, or hand-tune the produced XML afterwards (it's a normal `.drawio`).
- **Import edges are static** — `pyimports`/`jsimports`/`goimports` read static import statements (not dynamic `importlib`, runtime `require`, or reflection); `pyclasses` resolves inheritance only, not method-level calls.
- **Parallel edges** between the same `(source, target)` pair share one route.
- **Containers don't add edges** — `group`/nesting only boxes nodes for layout; edges remain node→node. For hand-built swimlane/architecture containers with their own connections, see `references/xml-authoring.md` "Containers and groups".
