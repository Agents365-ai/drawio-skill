# Changelog

All notable changes to **drawio-skill** are documented here. The format is based
on [Keep a Changelog](https://keepachangelog.com/), and the project follows
semantic-ish versioning (the `version:` field in `skills/drawio-skill/SKILL.md`).

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
