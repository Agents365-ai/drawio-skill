# Mermaid authoring → native .drawio

Read this when the diagram is a **standard type with no custom styling needs** and the draw.io CLI is **version ≥ 30** — writing Mermaid text and letting the CLI convert it is faster and safer than hand-placing XML: you only get the *structure* right, layout comes free.

```bash
# .mmd in → laid-out, editable, native .drawio out (draw.io desktop ≥ 30)
drawio -x -f xml -o diagram.drawio diagram.mmd
# then continue the normal workflow (validate → preview PNG → self-check → …)
```

**Version gate (critical):** on draw.io ≤ 29 the `.mmd` input fails with `Export failed`, and the `--layout` flag corrupts argument parsing entirely (like the `-w` pitfall). Resolve the CLI version in workflow step 1 (`drawio --version`); if it prints < 30, skip both this path and `--layout`, and author XML instead (optionally suggest `brew upgrade --cask drawio`).

## When to prefer which authoring mode

| Author as | Best for | Why |
|---|---|---|
| **Mermaid → CLI convert** | flowchart, state, gantt, timeline, journey, pie, quadrant, sankey, gitGraph, **mindmap**, kanban, requirement, block, xychart, radar, wardley, C4 sketches | structure-only input, free layout, 28 types |
| **XML (this skill's core path)** | anything needing **official vendor icons** (shapesearch/aiicons), **style presets**, swimlanes, precise positions, edge waypoint control, multi-page/drill-down | Mermaid can't express draw.io styles/shapes |
| **Bundled generators** | code/IaC/SQL imports, sequence (seqlayout), C4 with drill-down (c4.py) | deterministic, data-driven |

Routing note: this converts Mermaid **into a `.drawio` deliverable**. If the user wants Mermaid text that lives in git / renders in Markdown, route to the **mermaid** skill instead (see "When to use / when NOT to use").

## Mermaid quirks that matter for draw.io's parser

Condensed from the upstream reference (jgraph/drawio-mcp `shared/mermaid-reference.md`, Apache-2.0):

- The **first non-directive line's keyword selects the type** — a misspelled header yields a blank diagram. Common: `flowchart TD`, `sequenceDiagram`, `classDiagram`, `stateDiagram-v2`, `erDiagram`, `gantt`, `mindmap`, `timeline`, `journey`, `pie`, `gitGraph`, `quadrantChart`, `sankey-beta`, `kanban`, `c4Context`.
- **Node IDs are identifiers** (`A`, `node_1`) — no spaces, no trailing punctuation, avoid reserved words (`end`, `class`, `subgraph`). Display text goes in brackets/quotes: `A["User's Account"]`.
- **One statement per line**; quote labels containing `:`, `-`, parentheses, or non-ASCII (use `"`, not `'`).
- Only `<br>`, `<b>`, `<i>`, `<u>` are reliable HTML in labels; hex colors only (`#fff`, never `rgb()`).
- Styling: `style A fill:#f9f,stroke:#333`, reusable `classDef x fill:#dfd` + `A:::x`, edge `linkStyle 0 stroke:#f00`.
- **Never apply `--layout` to a Mermaid-converted file** — it is already laid out.
- Match label language to the user's language.

After converting, treat the `.drawio` as the artifact (delete the `.mmd`) and continue at the **validate → export draft** steps as usual. The converted file uses `UserObject`-wrapped cells — `validate.py` handles those.

## ELK `--layout` pass (XML-authored diagrams, CLI ≥ 30)

For XML you authored with rough (or all-zero) positions, the CLI can run the editor's ELK layouts — an alternative to `autolayout.py` when Graphviz is unavailable, and the better choice for **organic/radial** shapes (networks, mind-map-like graphs) that `dot` lays out poorly:

```bash
# in-place re-layout (reading and overwriting the same path is supported)
drawio -x -f xml --layout verticalFlow -o diagram.drawio diagram.drawio
# or layout + export in one call
drawio -x -f png -e -b 10 --layout verticalFlow -o diagram.drawio.png diagram.drawio
```

| Preset | Layout |
|---|---|
| `verticalFlow` / `horizontalFlow` | layered — flowcharts, pipelines |
| `verticalTree` / `horizontalTree` / `radialTree` | trees — hierarchies, org charts |
| `organic` | force-directed — networks, mind maps |

Finer control: pass a JSON array instead of a preset — `--layout '[{"layout":"elkLayered","config":{"elk.direction":"RIGHT","elk.spacing.nodeNode":40}}]'` (algorithms: `elkLayered`, `elkTree`, `elkRadial`, `elkOrganic`, `elkStress`, `elkBox`).

Choosing between layout engines: `autolayout.py` (Graphviz) understands this skill's graph-JSON pipeline (importers, groups→clusters, `--tune`, palette tinting) — prefer it when that pipeline is in play. Use `--layout` when Graphviz is missing, when re-laying-out an existing `.drawio`, or for organic/radial topologies.
