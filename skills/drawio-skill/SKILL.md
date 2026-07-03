---
name: drawio-skill
version: 1.18.0
description: Use when the user requests diagrams, flowcharts, architecture diagrams, ER diagrams, UML / sequence / class diagrams, network topology, cloud architecture from Terraform or Kubernetes manifests, ML/DL model figures (Transformer/CNN/LSTM), mind maps, or any visualization. Also use proactively when explaining systems with 3+ components, complex data flows, or relationships that benefit from visual representation. Best suited when the diagram needs custom styling, rich shape vocabulary, swimlanes, or exportable images (PNG/SVG/PDF/JPG). Generates .drawio XML and exports locally via the native draw.io desktop CLI.
license: MIT
homepage: https://github.com/Agents365-ai/drawio-skill
compatibility: Requires draw.io desktop app CLI on PATH (macOS/Linux/Windows). Self-check step requires a vision-enabled model (e.g., Claude Sonnet/Opus); gracefully skipped if unavailable. Optional auto-layout (scripts/autolayout.py) needs Graphviz (dot).
platforms: [macos, linux, windows]
metadata: {"openclaw":{"requires":{"anyBins":["draw.io","drawio"]},"emoji":"📐","os":["darwin","linux","win32"],"install":[{"id":"brew-drawio","kind":"brew","formula":"drawio","bins":["drawio"],"label":"Install draw.io via Homebrew","os":["darwin"]},{"id":"brew-graphviz","kind":"brew","formula":"graphviz","bins":["dot"],"label":"Install Graphviz for optional autolayout.py","os":["darwin"],"optional":true}]},"hermes":{"tags":["drawio","diagram","flowchart","architecture","visualization","uml"],"category":"design","requires_tools":["drawio","draw.io"],"related_skills":["mermaid","excalidraw","plantuml"]},"author":"Agents365-ai","version":"1.18.0"}
---

# Draw.io Diagrams

## Overview

Generate `.drawio` XML files and export to PNG/SVG/PDF/JPG locally using the native draw.io desktop app CLI.

**Supported formats:** PNG, SVG, PDF, JPG — no browser automation needed.

PNG, SVG, and PDF exports support `--embed-diagram` (`-e`) — the exported file contains the full diagram XML, so opening it in draw.io recovers the editable diagram. Use double extensions (`name.drawio.png`) to signal embedded XML.

## When to use / when NOT to use

**Use this skill for:** polished, precise diagrams (architecture, network, strict UML, ERD), anything needing solid opaque fills, 10,000+ stock/branded shapes, swimlanes, or custom geometry, exported as editable PNG/SVG/PDF.

**Do NOT use it — route elsewhere — for:**
- A casual hand-drawn / whiteboard look → **excalidraw** or **tldraw**.
- Diagrams-as-code that live in git / render in Markdown → **mermaid** (general) or **plantuml** (UML).
- Freeform infinite-canvas sketching or freehand strokes → **tldraw**.

## Bundled resources

When the workflow references one of these, read it on demand — none of them need to be in context up front.

| File | Read it when |
|---|---|
| `references/xml-authoring.md` | You're about to **hand-write `.drawio` XML** (workflow step 3) — file skeleton, shape/edge cells, containers, connection distribution, palette, spacing/grid rules. Not needed when a bundled generator writes the XML |
| `references/mermaid-authoring.md` | The diagram is a **standard type with no custom styling/icon needs** (flowchart, state, gantt, mindmap, timeline, journey, pie, …) and the CLI is **≥ v30** — author it as Mermaid text and let the CLI convert to native `.drawio` (structure only, layout free). Also documents the CLI's ELK `--layout` pass for XML |
| `references/diagram-types.md` | The user names a specific diagram type (ERD, UML class, sequence, C4, architecture, ML/DL, flowchart) |
| `references/shapes.md` + `scripts/shapesearch.py` | The diagram needs a **specific shape** — a cloud icon (AWS/Azure/GCP), Cisco/Kubernetes/network symbol, UML/BPMN/ER/electrical/P&ID element — or any time you'd otherwise guess a `style=` string. `shapesearch.py "<keywords>"` returns the exact official style for 10k+ shapes |
| `scripts/aiicons.py` | The diagram involves an **AI/LLM brand** (OpenAI, Claude, Gemini, Mistral, Llama, HuggingFace, Ollama, LangChain, …) — `aiicons.py "<brand>"` returns a draw.io `image` style for the brand logo (lobe-icons via CDN; `--embed` to inline). draw.io has no built-in AI logos. See `references/shapes.md` → "AI / LLM brand logos" |
| `references/style-presets.md` | The user asks to learn / save / list / set-default / delete a style preset, or you've resolved an active preset and need the application rules |
| `references/style-extraction.md` | You're inside the Learn flow and need the extraction procedure (called from `style-presets.md`) |
| `references/troubleshooting.md` | An export fails, vision rejects a PNG, or a rendering looks wrong |
| `scripts/repair_png.py` | After every `-e` PNG export — fixes draw.io's truncated IEND chunk (issue #8) |
| `scripts/encode_drawio_url.py` | The CLI is unavailable and you need a browser-fallback diagrams.net URL (`--edit` for an editable editor URL) |
| `references/autolayout.md` | The diagram is large or layout-heavy (dependency/call graph, code structure, >~15 nodes) and you want Graphviz to place nodes + route edges instead of hand-placing coordinates |
| `scripts/pyimports.py` · `jsimports.py` · `goimports.py` · `rustimports.py` | The user wants to visualize a **Python, JS/TS, Go, or Rust project** structure — extracts the import graph (transitive-reduced, optional `--group` containers, nested by sub-package) for autolayout |
| `scripts/pyclasses.py` | The user wants a **Python class hierarchy / class diagram** — extracts classes + inheritance edges (boxed by module with `--group`) for autolayout |
| `scripts/tfimports.py` · `k8simports.py` · `composeimports.py` | The user wants to visualize **Terraform, Kubernetes, or docker-compose infrastructure** — extracts the resource/service reference graph (official AWS/Azure/GCP/K8s icons for tf/k8s; service boxes + volume cylinders for compose) for autolayout |
| `scripts/sqlerd.py` | The user wants an **ER diagram from SQL DDL** — parses `CREATE TABLE` statements into per-table nodes (columns with PK/FK markers) and crow's-foot FK edges for autolayout |
| `scripts/seqlayout.py` | The user wants a **sequence diagram** — describe participants + messages as JSON and the script computes all lifeline/activation/arrow geometry deterministically (no hand-placed coordinates, no Graphviz needed) |
| `scripts/c4.py` | The user wants a **C4 model** (System Context / Container / Component) — levels JSON in, one multi-page `.drawio` out with official C4 shapes/colors and **click-to-drill-down** links between levels |
| `scripts/validate.py` | You generated a `.drawio` (especially via autolayout or for a large hand-placed diagram) and want a fast deterministic structural lint (dangling edges, dup/reserved ids, broken parents, overlaps) before the vision self-check. `--score` prints a readability score for comparing layout variants |

## Prerequisites

The draw.io desktop app must be installed and the CLI accessible:

**macOS sandbox / sandbox isolation note (e.g., codex.app):** In some sandboxed macOS environments, invoking the draw.io desktop CLI (even `drawio --version`) can crash the draw.io process or produce no output. If that happens, treat the CLI as **unavailable in this sandbox isolation** — do not keep retrying inside the sandbox. Prefer a **non-sandboxed host environment** (outside sandbox isolation) for any CLI export work, or use the browser fallback / XML-only outputs.

```bash
# macOS (Homebrew — recommended; CLI binary is `drawio`, not `draw.io`)
brew install --cask drawio
drawio --version

# macOS (full path if not in PATH)
/Applications/draw.io.app/Contents/MacOS/draw.io --version

# Windows
"C:\Program Files\draw.io\draw.io.exe" --version

# Linux
drawio --version
```

Install draw.io desktop if missing:
- macOS: `brew install --cask drawio` or download from https://github.com/jgraph/drawio-desktop/releases
- Windows: download installer from https://github.com/jgraph/drawio-desktop/releases
- Linux: download `.deb`/`.rpm` from https://github.com/jgraph/drawio-desktop/releases — **do not use snap** (AppArmor sandbox denies secrets/keyring on servers, causes crash)

## Workflow

Before starting the workflow, assess whether the user's request is specific enough. If key details are missing, ask 1-3 focused questions:
- **Diagram type** — which preset? (ERD, UML, Sequence, Architecture, ML/DL, Flowchart, or general)
- **Output format** — PNG (default), SVG, PDF, or JPG?
- **Output location** — default is the user's working dir; honor any explicit path the user gives (e.g. "put it in `./artifacts/`"). Don't ask if they didn't mention one.
- **Scope/fidelity** — how many components? Any specific technologies or labels?

Skip clarification if the request already specifies these details or is clearly simple (e.g., "draw a flowchart of X").

**Step 0 — Resolve active preset.** Determine which (if any) user-defined style preset applies to this generation.

- Scan the user's message for a phrase that clearly names a style preset: "use my `<name>` style", "with my `<name>` style", "in `<name>` mode", "in the style of `<name>`". A bare `with <name>` does **not** count — "draw a diagram with redis" names a component, not a style. If a clear match is found → active preset = `<name>`.
- Else, check `~/.drawio-skill/styles/` for any file with `"default": true`. If found → active preset = that one.
- Else → no preset active; fall through to the built-in color/shape/edge conventions for the rest of the workflow.

Load the preset JSON from `~/.drawio-skill/styles/<name>.json`, falling back to `<this-skill-dir>/styles/built-in/<name>.json`. If the named preset exists in neither location, tell the user the name is unknown, list the available presets (user dir + built-in), and stop — do **not** silently fall back to defaults.

When a preset loads successfully, mention it in the first line of the reply: *"Using preset `<name>` (confidence: `<level>`)."* See `references/style-presets.md` → "Applying a preset" for how the preset changes color/shape/edge/font decisions.

1. **Check deps** — **resolve which name the binary has on this system** and use that name verbatim in every subsequent command in this workflow. Try in order: (a) `drawio --version` (the canonical name for Homebrew cask, jgraph `.deb`/`.rpm`, Arch AUR), (b) `draw.io --version` (older builds, some custom symlinks, some distro packages), (c) macOS `.app` direct: `/Applications/draw.io.app/Contents/MacOS/draw.io --version`, (d) Windows: `"C:\Program Files\draw.io\draw.io.exe" --version`. The first one that prints a version is your binary; remember the exact path/name and substitute it for `drawio` in every export command below. **Do not copy the example commands verbatim if your binary is named differently** — the examples use `drawio` only because it's the most common. On macOS-Homebrew, `drawio` is just a thin wrapper script that execs `/Applications/draw.io.app/Contents/MacOS/draw.io` — they run the same engine, so candidate (c) is only needed when the `drawio` wrapper is absent (e.g. the app was installed by drag-and-drop without the cask). **Also note the major version** the command printed: **≥ 30** unlocks Mermaid→`.drawio` conversion and the ELK `--layout` pass (see `references/mermaid-authoring.md`); on **≤ 29** both are unavailable — `.mmd` input fails and `--layout` corrupts argument parsing — so never emit those flags there.
2. **Plan** — identify shapes, relationships, layout (LR or TB), group by tier/layer
3. **Generate** — produce the `.drawio` file, choosing the authoring mode: **(a) Mermaid → CLI convert** when the diagram is a standard type with no custom styling/icon needs **and** the CLI is ≥ v30 — write a `.mmd` and run `drawio -x -f xml -o <name>.drawio <name>.mmd`, see `references/mermaid-authoring.md` (structure only; layout comes free; never `--layout` afterwards). **(b) Hand-written XML** for custom styling, vendor icons, swimlanes, precise geometry — **read `references/xml-authoring.md` first** (skeleton, cell forms, palette, spacing rules). **(c) A bundled generator** for the data-driven cases below. **For large or layout-heavy diagrams (dependency/call graphs, code structure, >~15 nodes), don't hand-place** — describe the graph as JSON and run `python3 <this-skill-dir>/scripts/autolayout.py graph.json -o <name>.drawio` to compute node positions + orthogonal edge routing via Graphviz (see `references/autolayout.md`; add `--tune` to auto-pick the more readable direction). For a **Python / JS-TS / Go / Rust project**, the matching importer (`scripts/pyimports.py`, `jsimports.py`, `goimports.py`, or `rustimports.py`) extracts the import graph (transitive-reduced; add `--group` to box modules by sub-package, nested for deep trees) ready for autolayout; for a **Python class hierarchy**, `scripts/pyclasses.py` extracts classes + inheritance instead; for **Terraform / Kubernetes / docker-compose** (`scripts/tfimports.py`, `k8simports.py`, `composeimports.py`), the importer extracts the resource/service reference graph — tf/k8s nodes resolve to their official cloud icons automatically; for an **ER diagram from SQL DDL**, `scripts/sqlerd.py` parses `CREATE TABLE` into table nodes + crow's-foot FK edges. For a **sequence diagram**, skip autolayout entirely — describe participants + messages as JSON and run `python3 <this-skill-dir>/scripts/seqlayout.py seq.json -o <name>.drawio` (deterministic lifeline/activation/arrow geometry; see the script docstring for the JSON schema). For a **C4 model**, `python3 <this-skill-dir>/scripts/c4.py c4.json -o <name>.drawio` emits the full multi-page Context→Container→Component set with drill-down links (schema in the script docstring). For complex architecture diagrams with many visible edge labels, give labels `labelBackgroundColor=#ffffff;fontSize=11` and use edge geometry `x`/`y` offsets plus `<mxPoint as="offset" />` to move long labels into nearby whitespace instead of relying on draw.io's default midpoint placement. After generating any `.drawio`, run `python3 <this-skill-dir>/scripts/validate.py <name>.drawio` for a fast structural lint (dangling edges, dup ids, overlaps) before exporting. Default output dir is the user's working dir; if the user specified an output path or directory (e.g. `./artifacts/`, `docs/images/`), use that instead — `mkdir -p` the target dir first. Apply the same dir choice to PNG/SVG/PDF exports in steps 4 and 7.
4. **Export draft** — run CLI to produce a preview PNG. **Do NOT pass `-e`** at this step — the embedded `zTXt mxGraphModel` chunk it adds causes vision APIs (Claude included) to return 400 "Could not process image" in step 5. **Cap the preview width with `--width 2000` (not `-s 2`)** — Claude's vision API rejects images larger than 2576×2576px with "Unable to resize image — dimensions exceed the 2576x2576px limit", and `-s 2` on a medium-or-larger diagram easily overshoots that ceiling. Save the clean preview as `<name>.png` (single extension). Embedding and full-resolution scale are for the final export only (step 7).
5. **Self-check** — use the agent's built-in vision capability to read the exported PNG, catch obvious issues, auto-fix before showing user (requires a vision-enabled model such as Claude Sonnet/Opus). If reading the PNG returns a 400 / "Could not process image" error, you almost certainly exported with `-e` by mistake — re-export without `-e` and retry once. If it still fails, skip self-check and continue to step 6.
6. **Review loop** — show image to user, collect feedback, apply targeted XML edits, re-export, repeat until approved
7. **Final export** — re-export the approved version to all requested formats. Use `-e` here (PNG/SVG/PDF) so the deliverable stays editable in draw.io; save as `<name>.drawio.png` to signal embedded XML. **For PNG with `-e`, run `python3 <this-skill-dir>/scripts/repair_png.py <name>.drawio.png` immediately after** — draw.io's CLI truncates the IEND chunk in `-e` PNG output (8 bytes missing), producing a corrupt file that vision APIs and strict PNG decoders reject (issue #8). Report file paths.

**If `drawio --version` crashes or prints nothing (common in restricted macOS sandbox isolation like codex.app):**
- Do not keep retrying CLI invocations inside the sandbox.
- Skip steps 4, 5, 6, and 7 (CLI export + PNG-based review) and use **Browser fallback** (`scripts/encode_drawio_url.py`) or deliver the `.drawio` XML only.
- If the user needs PNG/SVG/PDF outputs, ask them to run the export commands in a **non-sandboxed host environment** (outside sandbox isolation) and share the resulting files.

Escalation rule:
- If the binary exists on PATH (or known app path exists) but execution fails with abnormal exit, empty output, Electron startup failure, display/session error, or likely sandbox restriction, prefer one escalated retry before falling back.
- If the binary is missing entirely, do not escalate just to search more aggressively; go to install guidance or fallback.

### Step 5: Self-Check

After exporting the draft PNG, use the agent's vision capability (e.g., Claude's image input) to read the image and check for these issues before showing the user. If the agent does not support vision, skip self-check and show the PNG directly.

**Important:** the draft PNG read here must have been exported **without** `-e`. Draw.io's `-e` flag emits a PNG with a truncated IEND chunk (8 bytes of type+CRC missing) that the Anthropic vision API rejects with 400 "Could not process image" (issue #8). The simplest fix for the preview step is to skip `-e` entirely; the final export in step 7 keeps `-e` and runs the repair snippet. If you see the 400 error here, re-export without `-e` and retry once; if it still fails (any other reason), skip self-check and proceed to step 6.

| Check | What to look for | Auto-fix action |
|-------|-----------------|-----------------|
| Overlapping shapes | Two or more shapes stacked on top of each other | Shift shapes apart by ≥200px |
| Clipped labels | Text cut off at shape boundaries | Increase shape width/height to fit label |
| Missing connections | Arrows that don't visually connect to shapes | Verify `source`/`target` ids match existing cells |
| Off-canvas shapes | Shapes at negative coordinates or far from the main group | Move to positive coordinates near the cluster |
| Edge-shape overlap | An edge/arrow visually crosses through an unrelated shape | Add waypoints (`<Array as="points">`) to route around the shape, or increase spacing between shapes |
| Stacked edges | Multiple edges overlap each other on the same path | Distribute entry/exit points across the shape perimeter (use different exitX/entryX values) |
| Edge-label overlap | Edge text overlaps another label, line, or node in the exported PNG | Keep the label on the edge, add a white label background, and move it locally with edge geometry `x`/`y` offsets into adjacent whitespace |

- Max **2 self-check rounds** — if issues remain after 2 fixes, show the user anyway
- Re-export after each fix and re-read the new PNG

### Step 6: Review Loop

After self-check, show the exported image and ask the user for feedback.

**Targeted edit rules** — for each type of feedback, apply the minimal XML change:

| User request | XML edit action |
|-------------|----------------|
| Change color of X | Find `mxCell` by `value` matching X, update `fillColor`/`strokeColor` in `style` |
| Add a new node | Append a new `mxCell` vertex with next available `id`, position near related nodes |
| Remove a node | Delete the `mxCell` vertex and any edges with matching `source`/`target` |
| Move shape X | Update `x`/`y` in the `mxGeometry` of the matching `mxCell` |
| Resize shape X | Update `width`/`height` in the `mxGeometry` of the matching `mxCell` |
| Add arrow from A to B | Append a new `mxCell` edge with `source`/`target` matching A and B ids |
| Change label text | Update the `value` attribute of the matching `mxCell` |
| Change layout direction | **Full regeneration** — rebuild XML with new orientation |

**Rules:**
- For single-element changes: edit existing XML in place — preserves layout tuning from prior iterations
- For layout-wide changes (e.g., swap LR↔TB, "start over"): regenerate full XML
- Overwrite the same `{name}.png` (no `-e`) each iteration — do not create `v1`, `v2`, `v3` files. `-e` is reserved for the final export in step 7.
- After applying edits, re-export and show the updated image
- Loop continues until user says approved / done / LGTM
- **Safety valve:** after 5 iteration rounds, suggest the user open the `.drawio` file in draw.io desktop for fine-grained adjustments

### Step 7: Final Export

Once the user approves:
- Export to all requested formats (PNG, SVG, PDF, JPG) — default to PNG if not specified
- Report file paths for both the `.drawio` source file and exported image(s)
- **Auto-launch:** offer to open the `.drawio` file in draw.io desktop for fine-tuning — `open diagram.drawio` (macOS), `xdg-open` (Linux), `start` (Windows)
- Confirm files are saved and ready to use

## Style Presets

A **style preset** is a named JSON file capturing a user's visual preferences (palette, shapes, font, edges). When active, it fully replaces the built-in color/shape conventions in this skill.

**Lookup order** when SKILL.md's Step 0 resolves a preset name:
1. `~/.drawio-skill/styles/<name>.json` — user presets (survive `git pull`)
2. `<this-skill-dir>/styles/built-in/<name>.json` — shipped built-ins (`default`, `corporate`, `handdrawn`)

Always lowercase the user-provided name before any file operation — the schema enforces lowercase.

**For everything else — Learn flow (extracting a preset from a file), management ops (list/default/delete/rename), application rules (color lookup, shape keywords, edges, fonts, extras, interaction with diagram-type presets), and validation — read `references/style-presets.md`.** It's only needed when the user invokes those flows or when an active preset must be applied to the current generation.

## Authoring .drawio XML

**Before hand-writing any `.drawio` XML (step 3), read `references/xml-authoring.md`** — file skeleton, shape/edge cell forms, containers, connection-point distribution, color palette, and spacing/grid rules all live there. Skip it only when a bundled generator writes the XML for you (`autolayout.py` + importers, `seqlayout.py`).

Two rules worth stating even here: never reuse ids `0`/`1` (reserved root cells), and every edge `mxCell` needs a `<mxGeometry relative="1" as="geometry" />` child — self-closing edge cells do not render.

## Export

### Commands

There are **two** export modes:

- **Preview / self-check** (step 4 of the workflow) — no `-e`. Output `diagram.png`. Required for vision self-check; using `-e` here triggers a 400 "Could not process image" error from the vision API (issue #8).
- **Final / deliverable** (step 7) — pass `-e`. Output `diagram.drawio.png`. The embedded XML keeps the file editable in draw.io.

> All commands below write `drawio` as a placeholder for the binary you resolved in Step 1. If your binary is on PATH as `draw.io` (with dot — some older or distro-packaged installs), substitute `draw.io` throughout. If only the macOS `.app` or Windows `.exe` is available, use the full path variant shown a few lines down.

```bash
# Preview PNG (use this in step 4, before self-check) — NO -e, width-capped to stay under vision's 2576px ceiling
drawio -x -f png --width 2000 -o diagram.png input.drawio

# Final PNG (step 7, after user approval) — WITH -e, double extension
drawio -x -f png -e -s 2 -o diagram.drawio.png input.drawio

# macOS — full path (if not in PATH); preview / final variants
/Applications/draw.io.app/Contents/MacOS/draw.io -x -f png --width 2000 -o diagram.png input.drawio
/Applications/draw.io.app/Contents/MacOS/draw.io -x -f png -e -s 2 -o diagram.drawio.png input.drawio

# Windows
"C:\Program Files\draw.io\draw.io.exe" -x -f png -e -s 2 -o diagram.drawio.png input.drawio

# Linux (headless — requires xvfb-run; on servers add HOME and --disable-gpu)
export HOME=${HOME:-/tmp}
xvfb-run -a --server-args="-screen 0 1280x1024x24" \
  drawio -x -f png -e -s 2 -o diagram.drawio.png input.drawio --disable-gpu
# Running as root (CI / Docker)? Append --no-sandbox AT THE END (placing it earlier makes drawio treat it as the input filename)

# SVG export (final — -e is safe; SVG is text)
drawio -x -f svg -e -o diagram.svg input.drawio

# PDF export (final)
drawio -x -f pdf -e -o diagram.pdf input.drawio

# Custom output directory (e.g. CI artifacts dir) — create if missing, then export there
mkdir -p ./artifacts && drawio -x -f png -e -s 2 -o ./artifacts/diagram.drawio.png input.drawio
```

### Post-export PNG repair (required after `-e` PNG export)

draw.io CLI truncates the IEND chunk when emitting `-e` PNGs — the file ends with the 4-byte IEND length field but the `IEND` type + CRC (8 bytes) are missing. Result: vision APIs return 400 "Could not process image" and strict PNG decoders error out. SVG/PDF are unaffected.

Run this immediately after every `-e` PNG export:

```bash
python3 <this-skill-dir>/scripts/repair_png.py diagram.drawio.png
```

The script's `endswith(IEND)` guard makes it a no-op once draw.io fixes the bug upstream — safe to run unconditionally.

**Key flags:**
- `-x` — export mode (required)
- `-f` — format: `png`, `svg`, `pdf`, `jpg`
- `-e` — embed diagram XML in output (PNG, SVG, PDF) — exported file remains editable in draw.io. **Skip for the preview PNG used in step 5 self-check** — `-e` PNGs have a truncated IEND chunk that vision APIs reject (issue #8). For final PNG export, keep `-e` and run `scripts/repair_png.py` (see Post-export PNG repair). SVG/PDF unaffected.
- `-s` — scale: `1`, `2`, `3` (2 recommended for final PNG; do NOT use for the step-4 preview — see `--width`)
- `--width <px>` — target width in pixels (no short form; `-w` does **not** exist and silently breaks the input-file parser). Use `--width 2000` for the step-4 preview to keep the PNG under Claude's 2576×2576 vision ceiling. There's also a `--height <px>` flag for tall-narrow diagrams. Don't combine `--width` with `-s`.
- `-o` — output file path; accepts any directory (e.g. `./artifacts/diagram.drawio.png`) — `mkdir -p` the target dir first. Use `.drawio.png` double extension when embedding.
- `--layout <preset|json>` — **CLI ≥ v30 only** — ELK auto-layout pass on XML input (`verticalFlow`, `horizontalFlow`, `verticalTree`, `horizontalTree`, `radialTree`, `organic`, or a custom ELK JSON array). Alternative to `autolayout.py` when Graphviz is missing; never combine with Mermaid-converted files (already laid out). On ≤ 29 this flag breaks argument parsing — don't emit it. See `references/mermaid-authoring.md`
- `-b` — border width around diagram (default: 0, recommend 10)
- `-t` — transparent background (PNG only)
- `--page-index <n>` — export one page of a multi-page file. **1-based** in current drawio-desktop (verified on 29.7.8: `--page-index 2` exports the second page; older docs claimed 0-based). Default: first page. `--page-range 2..3` also works

### Browser fallback (no CLI needed)

When the draw.io desktop CLI is unavailable, generate a client-side URL:

```bash
python3 <this-skill-dir>/scripts/encode_drawio_url.py input.drawio          # read-only viewer
python3 <this-skill-dir>/scripts/encode_drawio_url.py --edit input.drawio    # opens in the editor
```

Default prints a `https://viewer.diagrams.net/...#R…` viewer URL; `--edit` prints a `https://app.diagrams.net/...#create=…` URL that opens straight into the editable editor. Either way the diagram XML is `encodeURIComponent`-encoded, deflate-compressed, and base64'd into the URL fragment — the fragment (after `#`) is never sent to the server, so nothing is uploaded. The `encodeURIComponent` step is mandatory: without it, any diagram containing a literal `%` or non-ASCII (e.g. CJK) label makes the browser throw "URI malformed" and the diagram never opens.

Open the URL with `open "$URL"` (macOS) / `xdg-open "$URL"` (Linux). On **WSL2 / Windows**, `cmd.exe` drops the `#fragment` — write a `.url` shortcut file and open that instead (see `references/troubleshooting.md` → "WSL2 / Windows specifics").

### Fallback chain

When tools are unavailable, degrade gracefully:

| Scenario | Behavior |
|----------|----------|
| draw.io CLI missing, Python available | Use browser fallback (diagrams.net URL) |
| draw.io CLI missing, Python missing | Generate `.drawio` XML only; instruct user to open in draw.io desktop or diagrams.net manually |
| draw.io CLI crashes / no output in macOS sandbox isolation | Treat CLI as unavailable in-sandbox; use browser fallback / XML-only; ask user to run CLI exports in a non-sandboxed host environment |
| Vision unavailable for self-check | Skip self-check (step 5); proceed directly to showing user the exported PNG |
| Export fails (Chromium/display issues) | On Linux, retry with `xvfb-run -a`; if still failing, deliver `.drawio` XML and suggest manual export |
| Export fails on Linux server (headless) | Try in order: (1) `xvfb-run -a`, (2) append `--no-sandbox` at the very end if root, (3) add `--disable-gpu`, (4) `export HOME=/tmp`, (5) install apt deps (`libgtk-3-0 libnotify4 libnss3 libgbm1 libasound2t64` etc.), (6) fall back to [tomkludy/drawio-renderer](https://hub.docker.com/r/tomkludy/drawio-renderer) Docker (REST API for headless export) |

### Checking if drawio is in PATH

```bash
# Prefer the Homebrew / Linux-package binary name (no dot)
if command -v drawio &>/dev/null; then
  DRAWIO="drawio"
# Fall back to the dot-named binary (older installs, manual symlinks)
elif command -v draw.io &>/dev/null; then
  DRAWIO="draw.io"
# macOS .app bundle (binary inside the bundle keeps the dot)
elif [ -f "/Applications/draw.io.app/Contents/MacOS/draw.io" ]; then
  DRAWIO="/Applications/draw.io.app/Contents/MacOS/draw.io"
# WSL2: the CLI is the Windows desktop exe, reached via /mnt/c (note the space)
elif grep -qi microsoft /proc/version 2>/dev/null && [ -f "/mnt/c/Program Files/draw.io/draw.io.exe" ]; then
  DRAWIO="/mnt/c/Program Files/draw.io/draw.io.exe"
else
  echo "drawio not found — install from https://github.com/jgraph/drawio-desktop/releases (Homebrew: brew install --cask drawio)"
fi
```

On **WSL2 / native Windows**, opening exported files and browser-fallback URLs needs path conversion + a `.url`-file workaround (`cmd.exe` drops URL `#fragment`s) — see the "WSL2 / Windows specifics" section in `references/troubleshooting.md`.

## Common Mistakes

When something looks wrong (export fails, vision rejects a PNG, layout broken, edges misroute), see `references/troubleshooting.md` for a row-by-row mistake → fix table.

## Diagram Type Presets

When the user requests a specific diagram type, read `references/diagram-types.md` for the matching preset (shapes, edges, layout direction). Pick by user phrasing:

| User says | Section in `references/diagram-types.md` |
|---|---|
| "ER diagram", "schema diagram", "data model" | ERD |
| "UML class diagram", "class diagram" | UML Class |
| "sequence diagram", "interaction diagram", "lifeline" | Sequence |
| "architecture", "system diagram", "service diagram" | Architecture |
| "neural network", "model architecture", "ML diagram", "deep learning" | ML / Deep Learning Model |
| "flowchart", "decision tree", "process flow" | Flowchart |
| "C4", "system context diagram", "container diagram", "component diagram" | C4 Model |

The diagram-type preset sets **structural** style keywords. If a user style preset is also active (see `## Style Presets`), keep the structural keywords and layer color/font/edge/extras on top — read `references/style-presets.md` → "Interaction with diagram-type presets" for the merge rules.
