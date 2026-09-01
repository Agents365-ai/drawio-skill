---
name: drawio-skill
description: Create, edit, synchronize, inspect, test, and publish editable draw.io diagrams. Use when the user explicitly requests draw.io/diagrams.net, needs a polished architecture, ERD, UML, sequence, C4, SysML, BPMN, network, swimlane, ML, or infrastructure diagram, wants code/IaC/SQL/OpenAPI converted into a diagram, or wants an existing diagram queried, reviewed, diffed, restyled, kept in sync, or made interactive. Prefer Mermaid/PlantUML elsewhere when the requested artifact is diagrams-as-code rather than an editable draw.io file.
license: MIT
allowed-tools: [Bash, Read, Write, WebFetch]
metadata: {"openclaw":{"requires":{"anyBins":["python3"]},"emoji":"📐","os":["darwin","linux","win32"],"install":[{"id":"brew-drawio","kind":"brew","formula":"drawio","bins":["drawio"],"label":"Install draw.io for native exports","os":["darwin"],"optional":true},{"id":"brew-graphviz","kind":"brew","formula":"graphviz","bins":["dot"],"label":"Install Graphviz for automatic layout","os":["darwin"],"optional":true}]},"hermes":{"tags":["drawio","diagram","architecture","visualization","uml"],"category":"design","requires_tools":["python3"],"related_skills":["mermaid","excalidraw","plantuml"]},"author":"Agents365-ai","version":"3.2.0","homepage":"https://github.com/Agents365-ai/drawio-skill","compatibility":"Core IR, XML, sync, query, test, review, and Story workflows need Python 3 only; native export needs draw.io; Graphviz is optional.","platforms":["macos","linux","windows"]}
---

# Draw.io Architecture Studio

Produce editable `.drawio` artifacts, not flattened pictures. The preferred
entrypoint is `scripts/diagramctl.py`, which unifies generation, incremental
sync, multi-view projection, semantic queries/tests/reviews, failure analysis,
and accessible publishing over a shared Diagram IR.

## Choose the workflow

| Request | Route |
| --- | --- |
| Natural-language diagram with precise styling | Read `references/diagram-types.md`, then `references/xml-authoring.md` and author XML |
| Standard flowchart/mindmap/gantt/timeline/etc. with no special styling | If draw.io >=30, read `references/mermaid-authoring.md` and convert Mermaid to native `.drawio` |
| Code, Terraform, K8s, compose, SQL, OpenAPI, or CI source | Use `diagramctl.py build`; read `references/diagram-ir.md` |
| Update a generated diagram without losing manual layout | Use `diagramctl.py sync`; read `references/diagram-ir.md` |
| Executive/system/deployment/data-flow/security views | Use `diagramctl.py views`; read `references/diagram-ir.md` |
| Query, architecture policy, review, what-if, or guided walkthrough | Read `references/semantic-workflows.md` |
| MCP host (Claude Desktop, Cursor, VS Code, Codex) should call these workflows | Register `scripts/diagramctl_mcp.py`; read `references/mcp.md` |
| Prompt phrasing for a diagram type or semantic workflow | Read `references/cookbook.md` |
| Enforce architecture rules or visual diffs in GitHub Actions CI | Read `references/ci-gate.md` |
| Existing `.drawio` to HTML/PPTX/Mermaid/Markdown/animation/runbook | Read `references/toolbox.md`; `diagramctl.py transform` exposes the existing tools |
| Shape, cloud/vendor, AI, or Databricks icon | Read `references/shapes.md` or `references/databricks.md`; never guess shape names |
| Learn/apply/manage a visual style | Read `references/style-presets.md` |
| Export/platform problem | Read `references/troubleshooting.md`; for access/network questions read `references/security.md` |

## Unified CLI

Run from this skill directory, or replace `scripts/` with the absolute path to
this skill's scripts directory:

```bash
python3 scripts/diagramctl.py doctor
python3 scripts/diagramctl.py build model.json --from ir -o architecture.drawio
python3 scripts/diagramctl.py build ./infra --from terraform --group \
  --ir-output architecture.ir.json -o architecture.drawio
python3 scripts/diagramctl.py sync architecture.drawio ./infra --from terraform \
  -o architecture.next.drawio
python3 scripts/diagramctl.py views architecture.ir.json \
  --views executive,system,deployment,dataflow,security -o views.drawio
python3 scripts/diagramctl.py test architecture.drawio --rules policy.yml
python3 scripts/diagramctl.py review architecture.drawio -o review.md
python3 scripts/diagramctl.py query architecture.drawio --from internet --to orders-db
python3 scripts/diagramctl.py whatif architecture.ir.json --fail kafka \
  --drawio kafka-failure.drawio -o impact.json
python3 scripts/diagramctl.py story architecture.ir.json -o walkthrough.html
```

`doctor` does not launch GUI tools unless `--probe` is passed. Core semantic
commands are offline and stdlib-only.

## Creation workflow

1. Infer the diagram type, audience, scope, output format, and location from the
   request. Ask only when a missing choice materially changes the result;
   default to PNG plus `.drawio` in the working directory.
2. Select the authoring route from the table above. For a data-backed diagram,
   prefer Diagram IR and preserve provenance. For a large graph, use an importer
   or `autolayout.py`; do not hand-place more than roughly fifteen nodes.
3. Resolve an explicitly named style preset, or the user's default preset, as
   documented in `references/style-presets.md`. Structural diagram conventions
   and visual presets compose; they do not replace each other.
4. Generate the `.drawio`, then run structural validation:

   ```bash
   python3 scripts/validate.py diagram.drawio --score
   ```

   When semantic metadata or an architecture policy is in scope, also run
   `diagramctl.py test`. Do not present inferred semantic findings as verified
   runtime facts.
5. Export a draft PNG without embedded XML and inspect it visually. Fix obvious
   overlap, clipping, disconnected edges, edge-through-node routing, stacked
   edges, and unreadable labels. Stop automatic vision repair after two rounds.
6. Show the draft and apply targeted edits. Preserve existing geometry for
   local changes. Use `sync` for source-backed changes and write a reviewable
   output; use `--prune` only when deletion was requested.
7. After approval, create final requested formats and report both editable
   source and export paths.

## Export invariants

Resolve the available binary once (`drawio`, `draw.io`, the macOS app path, or
the Windows executable) and use that exact binary for the run.

```bash
# Draft for visual inspection: never use -e here
drawio -x -f png --width 2000 -o diagram.png diagram.drawio

# Final editable PNG
drawio -x -f png -e -s 2 -o diagram.drawio.png diagram.drawio
python3 scripts/repair_png.py diagram.drawio.png

# Final editable SVG/PDF
drawio -x -f svg -e --embed-svg-images -o diagram.svg diagram.drawio
drawio -x -f pdf -e -o diagram.pdf diagram.drawio
```

Do not combine `--width` and `-s`. Embedded PNG exports require
`repair_png.py`; draft PNGs used by vision must not use `-e`. On Linux headless,
follow `references/troubleshooting.md` rather than improvising Electron flags.
If the CLI crashes in a macOS sandbox, try one permitted escalated run, then use
`encode_drawio_url.py` or deliver XML; do not repeatedly launch it.

## Editing and identity

- Use stable semantic IDs and never reuse reserved IDs `0` or `1`.
- Every edge requires `<mxGeometry relative="1" as="geometry"/>`.
- For a local edit, change the matching cell only; for a global direction
  change, regenerate/re-layout the page.
- Keep provenance, `data-model-id`, semantic properties, manual geometry, and
  manual styles intact unless the user requests otherwise.
- When reconciling, retain removals as reviewable faded elements by default.
- For edges stacked at a boundary, run `edgeports.py`; add waypoints when an
  edge still crosses an unrelated shape. There is no CLI-only edge rerouter
  that preserves node positions.

## Quality and trust

An attractive diagram can still be wrong. Prefer source-backed relationships,
show provenance where useful, distinguish exact extraction from AI inference,
and keep architecture review findings framed as prompts. Story HTML must remain
self-contained, keyboard usable, and include a text alternative. Never include
secrets in node properties or provenance because they are embedded in outputs.

For all focused scripts and composition patterns, read `references/toolbox.md`;
load only the task-specific reference needed for the current request.
