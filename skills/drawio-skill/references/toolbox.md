# Toolbox — every bundled script, by use-case

A map of the 39 focused tools, the unified `diagramctl.py` orchestrator
(and its MCP server wrapper), and its
internal `diagram_ir.py` model grouped by what you're trying to do. The
per-task routing table in `SKILL.md` says *when* to reach for each; this says
*how they fit together*. Read it when you're not sure which script a request
maps to, or you want to chain several.

The recurring backbone is one pipeline — an **extractor** emits graph JSON, then
`autolayout.py` places it, then `validate.py` lints it, then the draw.io CLI
exports it:

```text
<extractor> → graph.json → autolayout.py → diagram.drawio → validate.py → (export PNG/SVG/PDF)
```

For new workflows, prefer the semantic backbone. It retains provenance and
supports incremental updates instead of one-shot regeneration:

```text
source → diagramctl build → Diagram IR → views/test/review/story
                              ↕
                       diagramctl sync ↔ existing .drawio
```

Use focused scripts directly when you need their narrow interface; use
`diagramctl.py` when a task crosses several stages.

## Quick decision guide

| I have… | I want… | Use |
| --- | --- | --- |
| a description in words | a styled diagram | hand-write XML (`references/xml-authoring.md`) or `autolayout.py` |
| code/IaC/spec/IR | one command that detects, builds, and records provenance | `diagramctl build` |
| a source-backed `.drawio` + changed source | update it without losing manual layout/style | `diagramctl sync` |
| one architecture model | executive/system/deployment/data/security pages | `diagramctl views` |
| a diagram or IR | queries, policy tests, architecture review, failure impact | `diagramctl query/test/review/whatif` |
| a diagram or IR | an accessible guided offline walkthrough | `diagramctl story` |
| a big/complex graph | it laid out for me | `autolayout.py` (`--tune` picks direction) |
| a Python/JS/Go/Rust project | its module/class structure | `pyimports` · `jsimports` · `goimports` · `rustimports` · `pyclasses` |
| Terraform/K8s/compose files | the **declared** architecture | `tfimports` · `k8simports` · `composeimports` |
| a running cluster/stack/cloud | what's **actually deployed** | `tfstate` · `dockerimports` · `k8simports -` |
| a SQL schema | an ER diagram | `sqlerd` |
| an OpenAPI / Swagger spec | an API diagram (by method) | `openapiimports` |
| CI workflows (GH Actions / GitLab) | the pipeline as a DAG | `ciimports` |
| a diagram + a metrics file | it coloured by the data | `heatmap` |
| a sequence of interactions | a UML sequence diagram | `seqlayout` |
| a system at 3 zoom levels | a C4 model with drill-down | `c4` |
| two diagrams / two snapshots | what changed (drift) | `drawiodiff` |
| a repo's git history | how its architecture grew | `timelapse` |
| a `.drawio` | a shareable interactive viewer | `drawiohtml` (→ HTML: pan/zoom/search/tabs) |
| a `.drawio` | a written description | `explain` (→ Markdown) |
| a `.drawio` | a slide deck | `drawio2pptx` (→ PPTX) |
| a `.drawio` | an animated data-flow | `svgflow` (→ SVG) |
| a `.drawio` | diagrams-as-code | `drawio2mermaid` (→ Mermaid) |
| a `.drawio` | the same diagram in another language | `relabel` (extract → translate → apply) |
| a `.drawio` | it re-themed (dark / corporate preset) | `restyle` |
| a shape/icon need | the exact style string | `shapesearch` · `aiicons` (AI/LLM logos) · `dbxicons` (Databricks products) |
| a photo/screenshot of a diagram | an editable `.drawio` | `raster2drawio` (your vision → JSON → draw.io) |
| ONE `.drawio` | it building itself, as a video/GIF | `buildup` (→ HTML player; `--gif`) |
| a big/sprawling diagram | a boardroom exec summary + drill-down | `compress` |
| a decision-tree flowchart | a click-through triage app | `runbook` (→ HTML, no CLI) |
| a PR touching `.drawio` | rendered before/after/diff for reviewers | `prdiff` (+ GitHub Action) |
| a pipeline / journey / subsystem map | it drawn as a metro / subway map | `tubemap` (coloured lines, octilinear, interchanges) |

## 1. Author & place

- **`autolayout.py`** — graph JSON → placed `.drawio` (Graphviz `dot`; orthogonal routing, `--group` containers, `--tune` best direction). The hub every extractor feeds. See `references/autolayout.md`.
- **`seqlayout.py`** — participants + messages JSON → sequence diagram with computed lifelines/activation bars (no Graphviz).
- **`c4.py`** — levels JSON → one multi-page `.drawio` (Context→Container→Component) with click-to-drill-down links.
- **`tubemap.py`** — metro JSON (coloured lines + grid-placed stations) → a London-Underground-style **tube map**: octilinear (H/V/45°) routing, white interchange circles, station stops. No Graphviz. See `references/tubemap.md`.
- **`shapesearch.py`** — search 10k+ official shapes for their exact `style=` string. **`aiicons.py`** — draw.io `image` styles for AI/LLM brand logos. **`dbxicons.py`** — draw.io `image` styles for Databricks product icons (see `references/databricks.md`).
- **`raster2drawio.py`** — a vision-extracted image graph JSON (from a whiteboard photo / legacy PNG / Visio screenshot) → editable `.drawio` honouring the read coordinates; missing positions fall back to `autolayout.py`. See `references/derasterize.md`.

## 2. Code → diagram

- **`pyimports` · `jsimports` · `goimports` · `rustimports`** — a project's intra-module import graph (transitive-reduced; `--group` boxes by sub-package).
- **`pyclasses.py`** — a Python class-inheritance graph.

All emit graph JSON → `autolayout.py`.

## 3. Infrastructure → diagram (declared config)

- **`tfimports.py`** — Terraform `.tf` → resources as official AWS/Azure/GCP icons.
- **`k8simports.py`** — K8s manifests → objects as official kind icons (edges: Ingress→Service→workload→ConfigMap/Secret/PVC).
- **`composeimports.py`** — docker-compose → service boxes + volume cylinders.
- **`sqlerd.py`** — SQL DDL (`CREATE TABLE`) → ERD with crow's-foot FK edges.
- **`ciimports.py`** — GitHub Actions (`.github/workflows/*.yml`) and/or `.gitlab-ci.yml` -> pipeline DAG: job nodes (runner, `matrix xN`, reusable-workflow calls in purple), `needs:` edges, an `on:` trigger node per workflow, jobs boxed per workflow / per GitLab stage.
- **`openapiimports.py`** — OpenAPI 3 / Swagger 2 spec → API diagram: one node per operation (coloured by HTTP method) + one per component schema, with edges to the schemas each operation uses and between nested schemas. `--group` by tag.

## 4. Live infrastructure → diagram (actually running)

The **actual** counterpart to §3 — see `references/live-infra.md`.

- **`tfstate.py`** — `terraform show -json | tfstate.py -` → deployed resources (provider-agnostic; expands `count`/`for_each`).
- **`dockerimports.py`** — `docker inspect $(docker ps -q) | dockerimports.py -` → running containers + networks + volumes.
- **`k8simports.py -`** — `kubectl get all,ing,cm,secret,pvc -o json | k8simports.py -` → live cluster.

## 5. Compare & evolve

- **`drawiodiff.py`** — diff two `.drawio` (or two live snapshots) → colour-coded graph (added=green, removed=red, changed=orange, moved=violet, rerouted edges=orange). Pairs with §4 for drift.
- **`timelapse.py`** — re-run an extractor across git history → a self-contained HTML player of how the architecture grew.
- **`heatmap.py`** — recolour any `.drawio` by a metrics file (CSV/JSON): each node shaded low→high on a gradient by its value (`--palette`, optional `--size`, auto legend). Turns a static architecture into a cost / latency / traffic / error-rate heat map.
- **`buildup.py`** — reveal ONE diagram's cells in dependency order (topological over its edges) → self-contained HTML player (embedded PNG frames, play/pause/step/scrub); optional `--gif`. Needs the draw.io CLI.
- **`compress.py`** — big `.drawio` → 2-page executive summary. Pure-Python label-propagation clustering (no networkx), one auto-named node per cluster with a drill-down link to the full original on page 2, aggregated cross-cluster edges. Needs Graphviz.
- **`prdiff.py`** — for every `.drawio` changed between two git refs, render base/head/`drawiodiff`-diff PNGs + a Markdown report for a PR comment; ships a composite GitHub Action (`.github/actions/drawio-diff/`). See `references/pr-bot.md`.

## 6. Diagram → other formats (reverse / interop)

The skill runs both directions — these turn a `.drawio` back into something else:

- **`drawiohtml.py`** — → a self-contained **interactive HTML viewer**: every page inlined as SVG with tabs, drag-pan, wheel-zoom, node search, and working drill-down links (C4 `data:page/id` links switch tabs). Share one file; no draw.io, no server.
- **`explain.py`** — → structured **Markdown** (components by tier, relations, per-page C4).
- **`drawio2pptx.py`** — → a 16:9 **PowerPoint** deck, one page per slide (needs `python-pptx`).
- **`svgflow.py`** — → an **animated SVG** (edges flow as marching ants); renders on GitHub.
- **`drawio2mermaid.py`** — → **Mermaid** `flowchart` text (diagrams-as-code GitHub renders).
- **`runbook.py`** — a flowchart/decision-tree → a self-contained **click-through HTML runbook** (current-step text, per-edge choice buttons, breadcrumb, Back/Restart). Reads the XML directly — no draw.io CLI needed.

## 7. Utilities & quality

- **`relabel.py`** — swap every label via a JSON map, layout untouched — `--extract` dumps an identity map of all labels (vertices, edges, UserObjects, page names), translate the values, `--map` applies them. Built for bilingual (EN/CN) variants of one diagram.
- **`restyle.py`** — apply a style preset (user or built-in, e.g. `dark`) to an existing `.drawio`: palette remap by hue, font, dark-theme extras, page background. Layout, shapes, and edge routing stay put.
- **`validate.py`** — deterministic structural lint (dangling edges, dup/reserved ids, overlaps; `--score` for layout readability). Findings render as `error: [E-DANGLING-END] ... (fix: ...)` — stable codes + fix hints; `--json` for structured output. Run before exporting.
- **`repair_png.py`** — fix draw.io's truncated IEND chunk after every `-e` PNG export (issue #8).
- **`encode_drawio_url.py`** — encode a `.drawio` into a diagrams.net browser URL when the CLI is unavailable (`--edit` for an editable editor URL).
