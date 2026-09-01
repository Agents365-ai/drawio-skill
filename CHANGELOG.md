# Changelog

All notable changes to **drawio-skill** are documented here. The format is based
on [Keep a Changelog](https://keepachangelog.com/), and the project follows
semantic-ish versioning (the `metadata.version` field in
`skills/drawio-skill/SKILL.md`).

## [3.2.0] — 2026-09-01

### Added

- **Semantic fidelity (v3.1 roadmap P0)** for code-backed diagrams:
  - **Source-kind profiles**: `diagramctl.py build --from python|js|go|rust|pyclasses`
    now labels source modules `module` / `library` / `command` from the file
    name (package roots `__init__.py`/`lib.rs` = library, entrypoints
    `__main__.py`/`main.rs`/`cli.py` = command) instead of a blanket
    `service`. Source importers also record per-file `provenance` (resolved to
    the real path), and Python edges carry the import statement line number.
  - **Architecture contracts stop misfiring on source modules**: ownership
    (`every-service-has-owner`) and observability
    (`production-has-observability`) rules no longer fire on ordinary
    `module`/`library`/`command` kinds.
  - **Profile reporting**: `diagramctl test` now reports a `profile` field
    (`code` vs `architecture`), so a CI gate can see what it is enforcing.
  - **View fallback reporting**: `views`/`build --views` emit per-view
    `fallback` / `fallback_reason` / `hint` when a projection had no metadata
    and fell back to the whole model, instead of failing silently.

### Changed

- Tests: 171 → 174 (source-profile build, view-fallback metadata gap, profile
  inference). Dogfood re-run against the repository's own toolbox now produces
  `module` kinds and zero ownership/observability noise.

## [3.1.0] — 2026-09-01

### Added

- **MCP server mode** (`scripts/diagramctl_mcp.py`) — a stdlib-only, offline
  Model Context Protocol stdio server exposing the semantic workflows as nine
  tools (`doctor`, `build`, `sync`, `views`, `architecture_test`, `review`,
  `query`, `whatif`, `story`) to any MCP host (Claude Desktop, Cursor,
  VS Code, Codex, Claude Code). No `mcp` package or network access; each call
  shells out to `diagramctl.py`, and `architecture_test` mirrors the CI exit
  code through `isError`. Host registration recipes in
  `references/mcp.md`; covered by 11 regression tests (suite 160 → 171).
- **Official GitHub Action: `drawio-architecture-test`**
  (`.github/actions/drawio-architecture-test/`) — runs the Diagram-as-Test
  architecture contract rules against Diagram IR files on every PR and
  reports via job summary + sticky comment + artifact, with a hard gate exit.
  Pure Python: no draw.io desktop, Xvfb, or Graphviz, so it runs on a stock
  runner in seconds. Usable cross-repo via
  `uses: Agents365-ai/drawio-skill/.github/actions/drawio-architecture-test@main`;
  ready-to-copy workflow template
  `.github/workflows/drawio-architecture-test.example.yml`; guide in
  `references/ci-gate.md`.
- **Prompt Cookbook** (`references/cookbook.md`) — tested prompt patterns for
  each workflow (architecture, sync, contracts, views, what-if, Story, C4,
  UML, ML, Mermaid-first) with the structural clauses that separate strong
  prompts from weak ones, plus anti-patterns. Routed from `SKILL.md`.

### Changed

- Scripts: 39 focused tools + 1 unified CLI + 1 IR module + 1 MCP server.
  Tests: 160 → 171.

## [3.0.0] — 2026-09-01

### Added

- **Versioned Diagram IR** (`drawio-skill/diagram-ir/v1`) with a published JSON
  Schema, stable semantic IDs, node/edge properties, provenance, multilingual
  labels, and readers for JSON plus compressed/uncompressed `.drawio` pages.
- **Unified `scripts/diagramctl.py`** with `doctor`, `build`, `inspect`, `query`,
  `test`, `review`, `sync`/`reconcile`, `views`, `whatif`, `story`, `publish`, and
  `transform` commands. It auto-detects common sources and orchestrates the 39
  existing focused tools without replacing their stable interfaces.
- **Incremental source reconciliation** — refresh labels, relations, semantic
  properties, and provenance while preserving matching cells' manual geometry
  and style. New elements are staged, retired elements remain reviewable by
  default, and destructive pruning is explicit.
- **Multi-view architecture projection** — executive, system, deployment,
  data-flow, and security pages from one model, with shared model IDs and
  click-through links between pages containing the same component.
- **Diagram-as-Test architecture contracts** — eight deterministic rules for
  direct Internet/database access, cycles, orphans, ownership, production
  observability, external timeouts, trust-boundary protocols, and WCAG-style
  text contrast. JSON/YAML policies and CI-friendly exit codes.
- **Architecture query/review** — kind/owner/boundary filtering, shortest-path
  queries, provenance/accessible summaries, dependency-cycle and articulation-
  point detection, coupling signals, and Markdown/JSON review reports.
- **What-if failure propagation** — deterministic downstream impact with
  isolation-edge support plus red/amber annotated `.drawio` output.
- **Accessible Story Mode** — a self-contained offline HTML walkthrough with
  clickable and keyboard-focusable nodes, arrow-key navigation, SVG title/desc,
  a full text alternative, provenance/ownership/boundary details, reduced-
  motion behavior, failure overlays, and multilingual label switching.
- **Codex UI metadata** in `agents/openai.yaml`, explicit `allowed-tools`
  disclosure, offline/security guidance, and allowlisted hosts for optional AI
  and Databricks icon fetching.
- **Maintained Architecture Studio showcase** covering code-to-IR generation,
  three-way sync conflicts, linked views, policy checks, what-if analysis, and
  offline Story publishing, with semantic regression tests.
- **Release evidence** from native draw.io E2E execution and a dogfood run
  against the repository's own script toolbox; observed gaps are tracked in the
  evidence-based 3.1 roadmap.

### Changed

- Reworked `SKILL.md` from a 355-line capability catalog into a 131-line
  progressive-disclosure router. Detailed semantic, IR, and security workflows
  now live in focused references.
- Native draw.io integration tests are now explicitly enabled with
  `DRAWIO_E2E=1`; an installed Electron binary is no longer mistaken for a
  usable renderer inside headless/macOS sandbox sessions.
- Scripts: 39 focused tools + 1 unified CLI + 1 internal IR module. Tests:
  146 → 157, including IR round-trip, compressed import, semantic rules,
  three-way reconcile invariants, multi-view, accessibility, host allowlists,
  and CLI workflows.

## [2.3.0] — 2026-08-27

### Added

- **Structured diagnostics in `scripts/validate.py`** — findings render as
  `error: [E-DANGLING-END] ... (fix: ...)` with 12 stable codes and a fix hint
  per finding, so an agent can act on lint output mechanically; `--json` emits
  the same findings as structured objects (`code`/`severity`/`subject`/
  `message`/`fix`). Message substrings are unchanged, so `--score` and existing
  consumers keep working.
- **`moved` (violet) and `rerouted` (orange) delta classes in
  `scripts/drawiodiff.py`** — a matched node with the same label at new
  coordinates is violet "moved", reported only when selective (if every matched
  node changed position, the files come from different layout runs and all stay
  "same"); an edge that re-points an old edge (one endpoint kept, the other
  swapped for a newly added node) or flips direction is orange "rerouted",
  shown once instead of a separate added/removed pair. (Both borrowed from the
  archify investigation, PR #107.)

## [2.2.0] — 2026-08-27

### Added

- **`scripts/dbxicons.py`** — Databricks product icon resolver, following the
  `aiicons.py` pattern. draw.io has no Databricks shape set, so lakehouse
  architectures rendered as generic boxes; only the bare Databricks logo
  resolved (via the `aiicons.py` simple-icons supplement, which is unchanged).
  Resolves 71 products from the community
  [databricks-architecture-icons](https://github.com/oieduardorabelo/databricks-architecture-icons)
  project (official Databricks artwork, referenced by URL — no artwork bundled,
  trademarks of Databricks, Inc.). Former product names resolve through aliases
  (DLT → `spark-declarative-pipelines`, Workflows → `lakeflow-jobs`, Vector
  Search → `ai-search`), `--variant color|tile|outline`, `--embed` inlines a
  marker-less base64 data URI fetched from a commit pinned in
  `data/databricks-icons.json`, and `--refresh-manifest` regenerates that
  manifest from the upstream catalog. Brand guidance (zone colors, category
  accents, capability-node style) in `references/databricks.md`.

## [2.1.1] — 2026-08-23

### Fixed

- **Embed images in SVG exports** (`--embed-svg-images` in `scripts/svgflow.py`,
  `scripts/drawiohtml.py`, and the documented export command in `SKILL.md`):
  without the flag draw.io wrote `file:///` references into its app bundle, so
  `img/lib/...` vendor icons (AWS/Azure/GCP, via `scripts/tfimports.py`) rendered
  only on the exporting machine. Adds a regression test asserting the flag in
  the `argv` of both Python call sites. (Thanks to @rjain21, PR #104.)

## [2.1.0] — 2026-07-25

### Added

- **`scripts/edgeports.py`** — deterministic edge port assignment, the real
  replacement for the `--layout libavoid` flag removed in 2.0.0. draw.io's
  floating connections attach every edge to the middle of whichever side faces
  the peer, so several edges leaving the same side stack into one line — the
  usual swimlane / cross-functional complaint (#96). The pass resolves each
  vertex to absolute coordinates (through swimlane parents), picks the side of
  each node facing the other endpoint, then spreads that side's edges over
  evenly-spaced slots **ordered by the far endpoint's position** so they keep
  their relative order instead of crossing at the boundary. Ends already pinned
  by hand are left alone and re-running is a no-op.

  It is a **port assigner, not a router**: it separates lines where they meet a
  shape, and does *not* stop an edge crossing an unrelated shape mid-run — add
  waypoints for that. Verified on a 3-lane swimlane (8 ends pinned, stacked
  handoffs separated); `validate.py --score` cannot measure the improvement,
  since it only scores edges carrying explicit waypoints.

## [2.0.0] — 2026-07-25

### Removed

- **`--layout libavoid` is gone from the documented interface.** It never
  worked; anyone who copied it from `SKILL.md` or `references/autolayout.md`
  hit a hang, not an error. There is **no CLI flag that reroutes edges without
  moving nodes** — route edges at authoring time instead (`exitX`/`entryX`
  pinning, `<Array as="points">` waypoints, node spacing), or open the file in
  draw.io desktop and use its editor-side obstacle-avoiding router.

### Fixed

- **Removed the non-existent `--layout libavoid` CLI flag from the docs**
  (regression from #95). draw.io desktop's `--layout` accepts only the ELK
  presets `verticalFlow`, `horizontalFlow`, `verticalTree`, `horizontalTree`,
  `radialTree`, `organic`, or a JSON layout array; `libavoid` is not among
  them and the string does not appear anywhere in draw.io desktop 30.2.6.
  Passing it opens a modal `Unknown layout: libavoid` dialog, which **hangs
  headless/CI runs** until the process is killed. `SKILL.md` and
  `references/autolayout.md` now state that no CLI flag reroutes edges without
  moving nodes, and point to authoring-side fixes (`exitX`/`entryX` pinning,
  `<Array as="points">` waypoints, node spacing) instead.
  `references/xml-authoring.md` already had this right; its unverifiable
  `libavoidRouting=1` style-stamp claim was dropped. Reported in #96.

## [1.34.0] — 2026-07-14

### Added

- **`scripts/tubemap.py`** — Tube-Map Mode: restyle a graph as a London-
  Underground-style metro map. From a metro JSON (coloured *lines* = ordered
  stations on an integer grid, shared stations = interchanges) it draws thick
  coloured line strokes with octilinear routing (horizontal / vertical / 45°,
  one automatic diagonal-then-straight bend when two stations aren't aligned),
  white-fill black-ring interchange circles, small station stops, and offset
  labels — an editable `.drawio`. Stdlib-only, no draw.io CLI or Graphviz
  needed; a line without a `color` is assigned one from a built-in tube palette.
  Schema + the one grid rule in `references/tubemap.md`. Scripts: 36 → 37;
  tests: 116 → 128 (`test_tubemap` 12). Routing rows in SKILL.md's resources
  table, toolbox (quick-guide + §1), and a README/README_CN example + demo image.

## [1.33.0] — 2026-07-14

### Added

- **`scripts/raster2drawio.py`** — image → editable `.drawio`. Converts a
  vision-extracted image graph (JSON: nodes with `x`/`y`/`shape`/`fill`, edges with
  `dashed`/`arrow`) — read off a whiteboard photo, legacy PNG, or Visio screenshot —
  into an editable `.drawio` honouring those coordinates; nodes missing positions fall
  back to shelling out to `autolayout.py`. Stdlib-only. Vision-extraction workflow in
  `references/derasterize.md`.
- **`scripts/buildup.py`** — turns ONE static `.drawio` into a self-contained HTML
  "build-up" player: reveals nodes/edges in topological (dependency) order, one PNG
  frame per step via the draw.io CLI, assembled into a base64-embedded
  play/pause/step/scrub viewer. `--gif` optionally exports an animated GIF (Pillow;
  skipped with a warning if absent — HTML still written). Distinct from `timelapse.py`
  (git-history animation); this animates a single diagram assembling itself.
- **`scripts/compress.py`** — big `.drawio` → boardroom executive summary. Clusters via
  deterministic pure-Python label propagation (no networkx dep), names each cluster by
  common label prefix / highest-degree member, aggregates cross-cluster edges, and emits
  a 2-page `.drawio` (exec view autolaid-out via `autolayout.py`, page 2 = the original
  diagram verbatim with `UserObject` drill-down links). Requires Graphviz `dot`.
- **`scripts/runbook.py`** — flowchart/decision-tree `.drawio` → self-contained
  click-through HTML runbook (current-step text, per-edge choice buttons, breadcrumb
  trail, Back/Restart, end-state on terminal nodes). Infers start/decision/io/process
  from shape style; start = the in-degree-0 start node. Pure XML parsing — no deps, no
  draw.io CLI needed.
- **`scripts/prdiff.py`** + **`.github/actions/drawio-diff/`** — PR diagram diff bot:
  for every `.drawio` changed between two git refs, exports base/head PNGs and a
  `drawiodiff.py`→`autolayout.py` colour-coded diff PNG via the draw.io CLI, and emits a
  pure, unit-testable Markdown report. Ships a composite GitHub Action plus an opt-in
  example workflow (`.github/workflows/drawio-pr-diff.example.yml`,
  `workflow_dispatch`-gated so it never auto-runs in this repo) that posts/updates a
  sticky PR comment. Needs git (fatal if missing); missing draw.io CLI degrades to a
  file-list-only report instead of failing. See `references/pr-bot.md`.
- Routing entries in SKILL.md's Bundled-resources table (5 rows), toolbox quick-guide
  (5 rows) + §1/§5/§6 bullets, README/README_CN example block, and 5 new per-feature
  test files. Scripts: 31 → 36; tests: 81 → 116 (`test_derasterize` 5, `test_buildup` 7,
  `test_prdiff` 8, `test_compress` 9, `test_runbook` 6).

## [1.32.0] — 2026-07-14

### Added

- **`scripts/ciimports.py`** — CI pipelines as diagrams. Reads GitHub Actions
  workflows (`.github/workflows/*.yml`, or a repo root) and/or `.gitlab-ci.yml`
  (auto-detected) and emits an autolayout graph: job nodes labeled with runner,
  `matrix ×N` size, and reusable-workflow targets (purple); `needs:` dependency
  edges; an `on:` trigger node per workflow feeding the root jobs; containers per
  workflow (GitHub) or per stage (GitLab, including the implicit previous-stage
  DAG for jobs without `needs`). Feeds `autolayout.py` like every other importer.
  Requires PyYAML. Extractors: 12 → 13; scripts: 30 → 31.
- Routing entries in SKILL.md step 3 + resources table, toolbox quick-guide/§3
  rows, README/README_CN examples + extractor row, a cross-reference in
  `docs/CI.md`/`CI_CN.md`, and 2 regression tests (81 total).

## [1.31.0] — 2026-07-13

### Added

- **`scripts/relabel.py`** — language variants / bulk text swaps of an existing
  `.drawio` with layout, styles, and ids untouched. `--extract` dumps every label
  (vertices, edges, UserObjects, page names) as an identity JSON map; translate the
  values, then `--map` applies them. Built for bilingual EN/CN twins of one diagram.
- **`scripts/restyle.py`** — re-theme an **existing** `.drawio` with a style preset
  ("make this dark", "apply my corporate style"). Every vertex fill/stroke is remapped
  to the preset palette by nearest hue (greys → neutral), so same-colored nodes stay
  grouped; applies font family and dark-theme extras (fontColor, edgeColor +
  `labelBackgroundColor=none`, page background, sketch, strokeWidth). Layout, shape
  keywords, and edge routing are never touched; default-white and `fillColor=none`
  cells keep readable text. Presets resolve like Step 0 (user dir → built-ins).
- Routing entries in SKILL.md, toolbox sections, a cross-reference in
  `style-presets.md`, and 6 new regression tests (79 total). Scripts: 28 → 30.

## [1.30.0] — 2026-07-13

### Added

- **Three new diagram-type presets** in `references/diagram-types.md`, filling gaps the
  frontmatter description already promised (same pattern as the 1.29.0 SysML preset):
  - **BPMN (Business Process)** — pools/lanes, `mxgraph.bpmn.task2` typed tasks
    (`taskMarker=user|service|...`), `mxgraph.bpmn.event` start/intermediate/end events,
    `mxgraph.bpmn.gateway2` gateways (`gwType=exclusive|parallel|inclusive|complex`),
    sequence vs conditional vs default vs message flows, data objects, annotations.
  - **Network Topology** — the `mxgraph.networks.*` device vocabulary (router, switch,
    firewall, LB, server, NAS, wireless, cloud) with a shared style prefix, subnet/DMZ
    zone containers, physical vs logical link styles; Cisco/rack/vendor icons routed
    through `shapesearch.py`.
  - **Cross-Functional Flowchart (Swimlane)** — pool + role-lane skeleton reusing the
    Flowchart node vocabulary, with lane-crossing orthogonal handoff edges.
- Trigger phrases ("BPMN", "business process", "network topology", "subnet",
  "swimlane diagram", "cross-functional flowchart", …) in the SKILL.md description and
  three new rows in the diagram-type dispatch table. Presets: 8 → 11.

## [1.29.0] — 2026-07-13

### Added

- **SysML diagram preset** ([#83](https://github.com/Agents365-ai/drawio-skill/issues/83)) —
  new SysML section in `references/diagram-types.md` covering the four SysML-unique
  diagram kinds: Block Definition (bdd, «block» compartments + composite/reference
  associations), Internal Block (ibd, parts + `mxgraph.sysml.port` ports + item flows),
  Requirement (req, id/text compartments + containment/satisfy/derive/verify/refine
  edges), and Parametric (par, constraint blocks + binding connectors). Behavioral
  SysML diagrams (activity, state machine, use case, sequence) reuse the UML presets;
  the shape index already ships ~60 native `mxgraph.sysml.*` shapes, discoverable via
  `shapesearch.py "sysml <keyword>"`.
- SysML / MBSE trigger phrases in the SKILL.md frontmatter description and a SysML row
  in the diagram-type dispatch table, so "SysML", "block definition diagram",
  "requirement diagram", "parametric diagram", "MBSE" requests route to the new preset.

## [1.28.1] — 2026-07-10

### Changed

- **Refreshed the `vs Other draw.io Skills & Tools` comparison** (README, README_CN,
  `docs/COMPARISON.md`, `docs/COMPARISON_CN.md`) to match the current state of the
  official [jgraph/drawio-mcp](https://github.com/jgraph/drawio-mcp), which has grown
  into a four-approach project. Corrected three now-stale cells that overclaimed in our
  favour: **Approach** (it now ships an official Claude Code plugin), **Multi-agent**
  (its MCP servers run in Claude, Cursor and VS Code — no longer "Claude apps only"),
  and **Browser fallback** (its Claude Code plugin now emits a diagrams.net `url`, not
  just an inline preview). Added a pointer to the official plugin's install command with
  a one-line statement of how drawio-skill stays complementary. Bumped the audit date.

### Added

- **libavoid routing note** in `references/xml-authoring.md` — documents draw.io's newer
  editor-side obstacle-avoiding connector router (`libavoidRouting=1`), clarifies it is
  not a headless CLI `--layout` flag (those are ELK node layouts), and gives the practical
  path for CLI-authored files. Also noted in the comparison's edge-routing row.

## [1.28.0] — 2026-07-04

### Added

- **Interactive HTML viewer** (`scripts/drawiohtml.py`) — publish a `.drawio` as
  ONE self-contained `.html`: every page exported to SVG via the draw.io CLI and
  inlined with page tabs, drag-pan, wheel-zoom (cursor-anchored), node search
  (matches glow, Enter cycles + centres) and **working links** — external links
  open normally, internal `data:page/id,…` links (e.g. a C4 model's drill-down)
  switch tabs inside the viewer. No server, no external requests; share the file
  with anyone, no draw.io needed.
  - Internal page links survive SVG export by being rewritten to `#page-<id>`
    fragments first (draw.io drops raw `data:page/id` links); search targets the
    `<g data-cell-id>` groups draw.io wraps every cell in.
  - Verified in a real browser (Playwright): C4 Context→Container→Component
    drill-down chain, search hit/centre, wheel zoom, tab switching. SKILL.md
    router + toolbox.md + READMEs updated; script count 27 → 28. Suite now 73.

## [1.27.0] — 2026-07-04

### Added

- **OpenAPI / Swagger → API diagram** (`scripts/openapiimports.py`) — turn an
  OpenAPI 3 or Swagger 2 spec (JSON, or YAML with PyYAML) into a graph for
  autolayout: one node per operation **coloured by HTTP method** (GET blue, POST
  green, PUT/PATCH orange, DELETE red) plus one node per component schema, with
  edges from each operation to the schemas it references (request/response
  bodies) and between schemas that nest one another. `--group` boxes operations
  by tag; `--no-schemas` shows just the endpoint surface. `$ref`s resolve to
  their final name; only schemas under `components`/`definitions` become nodes.
- **Metric heat map** (`scripts/heatmap.py`) — recolour an existing `.drawio` by
  data: pass a metrics file (CSV `key,value` or JSON `{key: value}`) and each
  node is matched by cell id or label and shaded along a gradient from the
  lowest value to the highest — a cost / latency / traffic / error-rate heat map
  over any architecture diagram. `--palette heat|cool|warm`, `--reverse`,
  `--size` (scale nodes by value), and an auto legend placed clear of the
  content. Unmatched nodes keep their style; post-processes any diagram, export
  as usual.
  - Both verified end-to-end (spec → grouped API PNG; architecture + latency CSV
    → heat map PNG with legend + sizing). SKILL.md router + toolbox.md + READMEs
    updated; script count 25 → 27. Suite now 69.

## [1.26.1] — 2026-07-04

### Added

- **`references/toolbox.md`** — a use-case map of all 25 bundled scripts
  (author / import code / import IaC / live infra / compare / reverse-export /
  utilities) with an "I have X, I want Y → use Z" decision guide and the shared
  extractor → autolayout → validate → export pipeline. Docs only; SKILL.md
  resource table points to it as the "not sure which script fits" entry.

## [1.26.0] — 2026-07-04

### Added

- **Diagram → Mermaid** (`scripts/drawio2mermaid.py`) — convert a `.drawio` into
  a Mermaid `flowchart` you can paste into Markdown and have GitHub / GitLab /
  docs render natively (diagrams-as-code). Containers become `subgraph`s, edge
  labels are kept, and a few shapes map to Mermaid node forms (cylinder →
  database `[( )]`, rhombus → decision `{ }`). `--fenced` wraps each graph in a
  ```` ```mermaid ```` block; multi-page files emit one flowchart per page.
  - `drawio2mermaid.py diagram.drawio` (to stdout) or `--fenced -o out.md`.
  - Structural conversion only — styling/colours/vendor icons don't survive
    (Mermaid has no equivalent); keep the `.drawio` for a faithful diagram.
  - Output validated against the Mermaid renderer + a draw.io round-trip.
    SKILL.md router + READMEs updated. Suite now 63.

## [1.25.0] — 2026-07-03

### Added

- **Animated data-flow SVG** (`scripts/svgflow.py`) — export a `.drawio` to SVG
  and turn every edge into a marching-ants animation (dashes travel along each
  connector in the arrow's direction), so the diagram shows data/flow moving
  through it. Self-contained looping `.svg` that renders on GitHub and any
  browser — good for a README, docs page, or slide background.
  - `svgflow.py diagram.drawio -o flow.svg` (also takes an `.svg` directly);
    `--speed` (seconds/cycle), `--dash` (pattern), `--reverse` (flow to source).
  - Only real edges animate: draw.io marks connector lines with
    `pointer-events="stroke"` (shape outlines / arrowheads use `="all"`), so
    arrowheads and shapes stay static. SKILL.md router + READMEs updated.
    Suite now 61.

## [1.24.0] — 2026-07-03

### Added

- **Diagram → PowerPoint** (`scripts/drawio2pptx.py`) — export a (multi-page)
  `.drawio` to a 16:9 `.pptx`, one page per slide, the page name as the slide
  title and the diagram centred + scaled to fit. A C4 model
  (Context / Container / Component) becomes a ready-to-present deck.
  - `drawio2pptx.py c4.drawio -o c4.pptx`.
  - Needs the draw.io CLI (page PNG export, `--page-index` is 1-based) and the
    optional `python-pptx` package (graceful error if absent, same pattern as
    PyYAML). Verified openable via LibreOffice + python-pptx.
  - SKILL.md router + READMEs updated. Suite now 59.

## [1.23.0] — 2026-07-03

### Added

- **Diagram → Markdown** (`scripts/explain.py`) — the inverse of the generators:
  read a `.drawio` and describe it as structured Markdown. Lists components
  grouped by their container / swimlane / tier, relations (`A —label→ B`, the
  edge label becomes the verb), and a section per page for multi-page / C4
  files. A handful of common shapes are named (data store, actor, decision,
  queue, cloud, AWS/Azure/GCP/Kubernetes). Handy for dropping an architecture
  summary into a README or PR, or a text-only read-out of a handed-over diagram.
  - `explain.py diagram.drawio` (Markdown to stdout) or `-o out.md`.
  - SKILL.md router + READMEs updated. Suite now 56.

## [1.22.0] — 2026-07-03

### Added

- **Architecture time-lapse** (`scripts/timelapse.py`) — animate how a codebase's
  structure grew across git history. Walks a directory's commits, re-runs a
  bundled importer at each sampled commit (tree pulled with `git archive`; the
  working copy is never touched), lays out + exports a PNG per commit, and
  assembles **one self-contained HTML player** (frames embedded as base64,
  play / step / scrub controls, no external files or CDNs).
  - `timelapse.py <dir> --importer pyimports` → `architecture-evolution.html`.
  - Works with any bundled extractor (`pyimports`/`jsimports`/`goimports`/
    `rustimports`/`pyclasses`/`tfimports`/`k8simports`/`composeimports`/`sqlerd`);
    `--importer-args` passes extra flags. Commits are sampled evenly to
    `--max-frames` (first + last always kept); commits where the path did not
    exist yet are skipped.
  - Documented in `references/autolayout.md`; SKILL.md router + READMEs updated.
    Suite now 54.

## [1.21.0] — 2026-07-03

### Added

- **Diagram diff** (`scripts/drawiodiff.py`) — compare two `.drawio` files into a
  single colour-coded "what changed" graph for autolayout: nodes/edges **added**
  (green), **removed** (red, dashed), **changed** (orange — a matched node whose
  label moved), **unchanged** (grey).
  - Matches by cell **id** by default (stable for importer/live-snapshot output,
    so *snapshot → change → snapshot → diff* shows **drift** directly — pairs with
    the v1.20 live importers); `--by-label` matches on visible text for
    hand-drawn diagrams. Leaf vertices + their edges only; multi-page flattened.
  - `drawiodiff.py old.drawio new.drawio -o diff.json` → `autolayout.py diff.json`.
  - Documented in `references/autolayout.md`; SKILL.md router + READMEs updated.
    Suite now 52.

## [1.20.0] — 2026-07-03

### Added

- **Live-infrastructure importers** — draw what's *actually running / deployed*,
  not just the declared config:
  - `scripts/tfstate.py` — `terraform show -json | tfstate.py -` renders the
    **deployed** state (provider-agnostic; `count`/`for_each` instances expanded,
    module nesting preserved, `depends_on` edges). Reuses tfimports' icon
    resolver, so the same official AWS/Azure/GCP icons and `--no-icons` fallback
    apply. The actually-deployed counterpart to tfimports' `.tf` view.
  - `scripts/dockerimports.py` — `docker inspect $(docker ps -q) | dockerimports.py -`
    renders the **running** containers, the user networks they attach to (green
    ellipses) and the named volumes they mount (cylinders); edges from `links`
    and the compose `depends_on` label. Built-in `bridge`/`host`/`none`/`ingress`
    networks and bind mounts are dropped as noise. The running counterpart to
    composeimports.
- **`k8simports.py` now reads a live cluster from stdin** (`-`):
  `kubectl get all,ing,cm,secret,pvc -o json | k8simports.py -`.
- New `references/live-infra.md` recipe (the three `terraform`/`docker`/`kubectl`
  one-liners + caveats); router + autolayout reference updated. Suite now 50.

## [1.19.0] — 2026-07-03

### Added

- **Accessibility built-in presets**: `colorblind-safe` (Okabe-Ito palette —
  all seven role colors distinguishable under color-vision deficiency, plus
  `strokeWidth=2`) and `dark` (dark fills + dark page background, light
  strokes/text) join `default` / `corporate` / `handdrawn`.
- **Schema + application-rule support for dark palettes**: optional
  `extras.background` / `extras.fontColor` / `extras.edgeColor` (backwards
  compatible); `style-presets.md` documents how each maps to styles and why
  dark exports must not use `-t` (transparent PNG).
- **Legend guidance**: `references/xml-authoring.md` gains a
  "Legend (auto-generate from the palette)" section — mechanical swatch +
  role-label recipe for diagrams using 3+ semantic colors.
- Built-in preset conformance test (suite now 46).

## [1.18.0] — 2026-07-03

### Added

- **Mermaid authoring path** (draw.io CLI ≥ 30, discovered via
  jgraph/drawio-mcp): for standard diagram types with no custom styling/icon
  needs, write Mermaid text and convert natively —
  `drawio -x -f xml -o out.drawio in.mmd` — 28 types incl. **mindmap, gantt,
  timeline, journey, pie, sankey, kanban** that previously required painful
  hand placement. New `references/mermaid-authoring.md` covers
  when-to-prefer, draw.io-parser quirks (condensed from drawio-mcp's
  reference, Apache-2.0), and the version gate.
- **ELK `--layout` pass** (CLI ≥ 30): `verticalFlow` / `horizontalFlow` /
  `verticalTree` / `horizontalTree` / `radialTree` / `organic` (or custom ELK
  JSON) as a Graphviz-free alternative to autolayout.py, and the better
  engine for organic/radial topologies.
- **Version gating in step 1**: the CLI major version now decides feature
  availability — on ≤ 29, `.mmd` input fails and `--layout` corrupts
  argument parsing, so both paths are skipped (verified 29.7.8 vs 30.2.6).

## [1.17.0] — 2026-07-03

### Added

- **`c4.py` — C4 model diagrams with drill-down.** Levels JSON (System
  Context → Containers → Components, any depth) in, one multi-page `.drawio`
  out: official C4 shapes/colors (`mxgraph.c4.person2`, c4model.com
  palette), standard three-line labels (`Name` / `[Type: Tech]` / desc),
  Graphviz placement per page, and **click-to-drill-down** — an element with
  `"children"` links to that level's page (`data:page/id,…`).
- `autolayout.py`: node-level `link` support (wraps the cell in a
  `UserObject`) and a reusable `page_cells`/`wrap_page` split so multi-page
  generators can share its layout pipeline.
- `validate.py`: understands `UserObject`/`object` wrappers — linked cells
  no longer produce false dangling-edge errors (also fixes linting of
  hand-authored diagrams that use links/metadata).
- `references/diagram-types.md`: C4 Model section (styles, label format,
  drill-down recipe); SKILL.md routes "C4", "container diagram", etc. to it.

### Fixed

- SKILL.md export flags: `--page-index` is **1-based** in current
  drawio-desktop (verified on 29.7.8) — previously documented as 0-based.
- Tests: 45.

## [1.16.0] — 2026-07-02

### Added

- **`seqlayout.py` — deterministic sequence diagrams.** Participants +
  messages JSON in, finished `.drawio` out: lifeline, activation-bar and
  arrow geometry are computed (not hand-placed), with automatic activation
  tracking (sync opens a bar on the target, return closes the sender's),
  self-messages, notes, actor lifelines, and the official umlLifeline styles
  from `diagram-types.md`. No Graphviz needed.
- **`composeimports.py`** — docker-compose → autolayout graph: services as
  name+image boxes, named volumes as cylinders; edges from `depends_on` /
  `links` / `volumes_from` / volume mounts. `--group` by network.
- **`sqlerd.py`** — SQL DDL → ER diagram: parses `CREATE TABLE` (inline and
  table-level PK/FK, quoted identifiers, schema prefixes) into per-table
  nodes with PK/FK-marked column lists and crow's-foot FK edges.
- **Layout auto-tuning.** `autolayout.py --tune` lays out in both directions
  and keeps the more readable one; `validate.py --score` prints the matching
  readability score (through-vertex ×20, crossings ×10, overlaps ×5).
- `autolayout.py` honours per-edge `style` in the graph JSON (used by
  sqlerd's ER edges).

### Changed

- **SKILL.md slimmed 488 → 313 lines**: the XML-authoring tutorial (skeleton,
  shape/edge cells, containers, connection distribution, palette, layout
  tips) moved to `references/xml-authoring.md`, read on demand before
  hand-writing XML — generator-driven flows no longer pay for it.
- Tests: 42 (new coverage for seqlayout, composeimports, sqlerd, edge-style
  passthrough).

## [1.15.0] — 2026-07-02

### Added

- **IaC → architecture diagram.** Two new importers feed autolayout:
  - `tfimports.py` parses Terraform `.tf` files (regex + brace matching, no
    HCL dependency) into a resource-reference graph. Each resource type is
    resolved to its **official cloud icon** via the bundled shape index —
    AWS `aws4`, Azure `azure2`, GCP icon sets — with a ~45-entry curated
    query table and strict tag-AND matching (a partial match falls back to a
    plain box rather than another vendor's icon). `--group` boxes resources
    by service; `--no-icons` for plain boxes.
  - `k8simports.py` parses Kubernetes manifests (JSON incl. `kind: List`
    stdlib-only; YAML via PyYAML) and derives Ingress→Service,
    Service→workload (selector match), workload→ConfigMap/Secret/PVC and
    HPA→target edges, with official `mxgraph.kubernetes` kind icons
    (25 kinds). `--group` boxes objects by namespace.
- `autolayout.py`: graph-level `ranksep`/`nodesep` passthrough (icon labels
  render below the shape and need wider spacing — the IaC importers emit
  these automatically) and `\n` in labels now renders as a line break.
- Test coverage for both importers and the autolayout additions (suite now 38).

## [1.14.0] — 2026-06-03

### Added

- `aiicons.py` resolves common RAG/LLM **data-store brands** (Qdrant, Redis,
  Postgres, Mongo, Elasticsearch, Milvus, Supabase, Neo4j, … 18 total) via the
  [simple-icons](https://simpleicons.org) (CC0) CDN when lobe-icons lacks them;
  lobe stays the default for AI/LLM brands. Unmatched brands get a
  cylinder/`shapesearch` suggestion.
- Test coverage for `jsimports` / `goimports` / `rustimports` (suite now 21).
- `docs/` USAGE + COMPARISON sub-pages document codebase visualization, shape
  search, and AI logos.

## [1.13.1] — 2026-06-03

### Added

- Dependency-free `unittest` regression suite (`tests/`) + GitHub Actions CI.

### Fixed

- Unclosed file handle in `autolayout.load_palette()`.

## [1.13.0] — 2026-06-03

### Added

- **Palette-based group colouring** in auto-layout: grouped code-visualization
  diagrams now tint each top-level group with a distinct colour from the skill's
  own palette (`styles/built-in/default.json`), with matching container borders —
  so related modules read as a coloured cluster instead of monochrome boxes.
- `autolayout.py --mono` to opt out and keep the previous monochrome look.
- README example images for Shape Search and AI/LLM brand logos.

### Changed

- `pyclasses.py` no longer hard-codes a node colour; its grouped output is
  coloured by module. Styleless nodes are tinted by group; an explicit node
  `style` always wins. Ungrouped output is unchanged.

## [1.12.0] — 2026-06-03

### Added

- **AI / LLM brand logos** via `aiicons.py` — resolves a brand (OpenAI, Claude,
  Gemini, Mistral, Llama, Ollama, LangChain, … 321 brands) to a draw.io image
  style backed by [lobe-icons](https://github.com/lobehub/lobe-icons) (MIT).
  References icons from the unpkg CDN by default; `--embed` inlines a
  self-contained data URI for offline use. draw.io ships none of these logos.

## [1.11.1] — 2026-06-03

### Changed

- Shape search ranks **title-exact matches above tag-only neighbours** (e.g.
  `dynamodb` now returns *DynamoDB*, not *Attribute*). Scoring/candidate set is
  unchanged; only the within-score-tier order changes.

### Added

- READMEs document shape search, the editable browser URL, and WSL2 support.

## [1.11.0] — 2026-06-02

Ideas adapted from [jgraph/drawio-mcp](https://github.com/jgraph/drawio-mcp) (Apache-2.0).

### Added

- **Shape search** across 10,000+ official draw.io shapes (`shapesearch.py`) —
  resolves the exact `style` for AWS/Azure/GCP/Cisco/Kubernetes/UML/BPMN/ER/
  electrical/P&ID instead of guessing `shape=mxgraph.*` names.
- **WSL2 / Windows** CLI detection + browser-open guidance (the `.url`-file
  fragment workaround).
- `encode_drawio_url.py --edit` for an editable `app.diagrams.net` URL.

### Fixed

- Browser-URL encoder now `encodeURIComponent`s before deflate, so URLs no
  longer throw "URI malformed" on a literal `%` or non-ASCII (e.g. CJK) label.

## [1.10.0] — 2026-06-02

### Added

- **Rust** module-use importer (`rustimports.py`) — intra-crate `use` graph.

## [1.9.0] — 2026-06-02

### Added

- **Nested containers** in auto-layout (deep `/`-delimited group paths).
- **Python class-inheritance** graph (`pyclasses.py`) — one node per class,
  edges from subclass to base, boxed by module with `--group`.

## [1.8.0] — 2026-06-02

### Added

- **Structural validator** (`validate.py`) — deterministic `.drawio` lint
  (dangling edges, duplicate/reserved ids, broken parents, overlaps).
- **JS/TS** (`jsimports.py`) and **Go** (`goimports.py`) import-graph importers.
- Container / cluster layout (`--group`) in auto-layout.

## [1.7.0] — 2026-06-02

### Added

- **Python** import-graph importer (`pyimports.py`) — intra-project module graph,
  transitive-reduced.

## [1.6.0] — 2026-06-02

### Added

- **Graphviz auto-layout** (`autolayout.py`) — places nodes and routes
  orthogonal edges for medium/large graphs, removing the manual-coordinate
  ceiling.

## [1.5.3] — 2026-06-02

### Changed

- Finalize the `drawio` binary rename and sync reference docs.
- Major docs/landing-page overhaul (comparison tables, hero, sub-doc split),
  `sync-365-skills` CI, macOS sandbox-isolation notes.

## [1.5.2] — 2026-05-17

### Fixed

- Add a top-level `version` field for ClawHub compatibility.

## [1.5.1] — 2026-05-06

### Added

- Claude Code **plugin marketplace** support; restructure for the 365-skills
  umbrella submodule.

## [1.5.0] — 2026-05-06

### Changed

- Split `SKILL.md` into modular references + scripts.

## [1.4.0] — 2026-04-23

### Added

- Custom output directory support.

### Fixed

- Browser fallback fix; repair truncated IEND chunk in `-e` PNG export (issues #8/#9).

## [1.3.0] — 2026-04-23

### Added

- **Style presets** — learn a visual style from a `.drawio`/image and reuse it.

## [1.2.0] — 2026-04-19

### Added

- Auto-update check; Opencode support.

## [1.1.1] — 2026-04-06

### Added

- GitHub Pages landing page.

### Fixed

- Security flag fixes.

## [1.1.0] — 2026-04-06

### Added

- Diagram-type presets, ML/Deep-Learning model support, and quality-of-life
  enhancements.

[1.14.0]: https://github.com/Agents365-ai/drawio-skill/releases/tag/v1.14.0
[1.13.1]: https://github.com/Agents365-ai/drawio-skill/releases/tag/v1.13.1
[1.13.0]: https://github.com/Agents365-ai/drawio-skill/releases/tag/v1.13.0
[1.12.0]: https://github.com/Agents365-ai/drawio-skill/releases/tag/v1.12.0
[1.11.1]: https://github.com/Agents365-ai/drawio-skill/releases/tag/v1.11.1
[1.11.0]: https://github.com/Agents365-ai/drawio-skill/releases/tag/v1.11.0
[1.10.0]: https://github.com/Agents365-ai/drawio-skill/releases/tag/v1.10.0
[1.9.0]: https://github.com/Agents365-ai/drawio-skill/releases/tag/v1.9.0
[1.8.0]: https://github.com/Agents365-ai/drawio-skill/releases/tag/v1.8.0
[1.7.0]: https://github.com/Agents365-ai/drawio-skill/releases/tag/v1.7.0
[1.6.0]: https://github.com/Agents365-ai/drawio-skill/releases/tag/v1.6.0
[1.5.3]: https://github.com/Agents365-ai/drawio-skill/releases/tag/v1.5.3
[1.5.2]: https://github.com/Agents365-ai/drawio-skill/releases/tag/v1.5.2
[1.5.1]: https://github.com/Agents365-ai/drawio-skill/releases/tag/v1.5.1
[1.5.0]: https://github.com/Agents365-ai/drawio-skill/releases/tag/v1.5.0
[1.4.0]: https://github.com/Agents365-ai/drawio-skill/releases/tag/v1.4.0
[1.3.0]: https://github.com/Agents365-ai/drawio-skill/releases/tag/v1.3.0
[1.2.0]: https://github.com/Agents365-ai/drawio-skill/releases/tag/v1.2.0
[1.1.1]: https://github.com/Agents365-ai/drawio-skill/releases/tag/v1.1.1
[1.1.0]: https://github.com/Agents365-ai/drawio-skill/releases/tag/v1.1.0
