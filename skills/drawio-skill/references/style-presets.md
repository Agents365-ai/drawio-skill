# Style Presets — Learn, Apply, Manage

A **style preset** is a named JSON file capturing a user's visual preferences — palette, shape vocabulary, fonts, edge style. When a preset is active, it fully replaces the built-in conventions in SKILL.md's color/shape/edge tables.

Read this file when:
- The user asks to "learn", "save", "remember", or "extract" a style from a file
- The user wants to manage existing presets (list, set default, delete, rename)
- You've resolved an active preset in Step 0 and need the application rules
- You need to validate a preset file before loading it

## Locations and lookup order

1. `~/.drawio-skill/styles/<name>.json` — user presets (survive `git pull`).
2. `<this-skill-dir>/styles/built-in/<name>.json` — built-ins shipped with the skill (`default`, `corporate`, `handdrawn`).

A user preset shadows a built-in of the same name.

Only user presets can have `"default": true`. When the user says *"make `<built-in-name>` my default"*, copy the built-in JSON to `~/.drawio-skill/styles/<name>.json` first, then set `default: true` on the copy — leave the shipped built-in untouched.

**Name normalisation:** always lowercase the user-provided name before writing or looking up files (the preset schema enforces lowercase; uppercase names will fail validation).

## Applying a preset

When SKILL.md's Step 0 identified a preset, it fully replaces the built-in palette, shape keywords, edge defaults, and font for this diagram — do not mix values from the built-in color table.

**Color lookup.** For each role a shape plays (service / database / queue / gateway / error / external / security), resolve `preset.roles[role]` to a slot name, then `preset.palette[<slot>]` to the `(fillColor, strokeColor)` pair. If `roles[role]` is unset or the resolved slot is `null`, follow this fallback ladder:

1. Try the role's canonical slot (`service→primary`, `database→success`, `queue→warning`, `gateway→accent`, `error→danger`, `external→neutral`, `security→secondary`).
2. If that slot is also empty, pick the most-populated non-null slot in the preset.
3. Never reach into the built-in color table — the preset is authoritative.

**Decision and container shapes** are not in `preset.roles` — they have shape vocabulary (`preset.shapes.decision`, `preset.shapes.container`) but no role-to-slot mapping. Pick their colors as follows:
- **Decision** (rhombus) → use `preset.palette.warning` (the canonical yellow slot in the built-in conventions). If `warning` is empty, apply the slot-fallback ladder above starting from `warning`.
- **Container** (swimlane) → use the palette slot matching the tier/grouping the container represents (e.g. a "Services" tier container uses `primary`; a "Data" tier uses `success`). If no tier signal is available, default to `primary`.

**Shape keywords.** Use `preset.shapes[role]` as the **prefix** of the vertex style string (before `whiteSpace=wrap;html=1;...`). Example: for a database role, if `preset.shapes.database = "shape=cylinder3"`, the vertex style starts `shape=cylinder3;whiteSpace=wrap;html=1;fillColor=...`. The six named shape keys are `service`, `database`, `queue`, `decision`, `external`, `container`. Roles `gateway`, `error`, and `security` reuse `preset.shapes.service` unless the preset explicitly populates a key with their name.

**Edges.** Use `preset.edges.style` as the base edge style string. Append `preset.edges.arrow`. Per-edge routing keys (`exitX/exitY/entryX/entryY/...`) are still added by the usual routing rules in SKILL.md. If the flow between two shapes matches a token from `preset.edges.dashedFor` (either because the user's prompt used that word, or because one end of the edge plays a role whose typical relation is "optional"), append `;dashed=1` to the edge style.

**Fonts.** Append `fontFamily=<preset.font.fontFamily>;fontSize=<preset.font.fontSize>` to every vertex style. Container headers and swimlane titles additionally get `fontSize=<preset.font.titleFontSize>;fontStyle=1` when `preset.font.titleBold` is `true`.

**Extras.**
- `preset.extras.sketch === true` → append `sketch=1` to every vertex style and every edge style.
- `preset.extras.globalStrokeWidth !== 1` (any value other than the drawio default of 1, including `0.5`) → append `strokeWidth=<n>` to every vertex style and every edge style.

**Interaction with diagram-type presets** (ERD / UML / Sequence / ML / Flowchart). Diagram-type presets set structural style keywords that the user preset must preserve (e.g. ERD tables rely on `shape=table;startSize=30;container=1;childLayout=tableLayout;...`). The rule: keep the diagram-type preset's structural keywords, then layer the user preset's color / font / edge / extras on top. When a diagram-type preset hardcodes a color (`fillColor=#dae8fc`, etc.) that conflicts with the user preset, the user preset's color wins. Exception: `fillColor=none` is structural — do not replace it with a palette color.

## Learn flow

**Triggers:** "learn my style from `<path>` as `<name>`", "save this as `<name>` style", "remember this style as `<name>`".

**Dispatch by file extension:**
- `.drawio`, `.xml` → XML path
- `.png`, `.jpg`, `.jpeg`, `.svg` (rasterized flat image) → image path

**Steps:**

1. **Load the extraction reference.** Read `references/style-extraction.md` into context.
2. **Extract** following the XML path or image path procedure in the reference.
3. **Normalize and build candidate.** Convert the user-provided preset name to lowercase. Use this normalized name for ALL file paths in this flow. Build the candidate preset JSON and write it to `/tmp/drawio-preset-<name>.json` (where `<name>` is the already-normalized name). Do **not** save to `~/.drawio-skill/styles/<name>.json` yet.
4. **Render a sample** using the sample-diagram skeleton in `references/style-extraction.md`, parameterized by the candidate preset. Export PNG to `./preset-<name>-sample.png` using the same `drawio -x -f png -e -s 2 -o ./preset-<name>-sample.png /tmp/drawio-preset-<name>.drawio` command the main workflow uses, then run `repair_png.py` on it (see the Rendering the sample steps in `style-extraction.md`).
5. **Show the user:**
   - Preset summary table (palette hex values, shapes per role, font, edge style, extras).
   - The sample PNG path (and embed the image if the environment supports it).
   - Provenance line: `source.type`, `source.path`, `extracted_at`, `confidence`.
6. **Wait for approval:**
   - "save" / "looks good" → write candidate to `~/.drawio-skill/styles/<name>.json`. Create `~/.drawio-skill/styles/` if it doesn't exist. Delete tempfile and sample PNG.
   - "change `<field>` to `<value>`" → edit the in-memory candidate, re-render, re-ask.
   - "cancel" / "abort" / "no" → delete tempfile and sample PNG; nothing saved.

**Error behavior:**

| Failure | Behavior |
|---|---|
| Source path does not exist | Stop; report path not found. |
| XML parse fails | Stop; report the parse error; suggest opening the file in drawio desktop to repair. |
| Image vision unavailable | Stop; tell user to re-run on a vision-capable model or provide the `.drawio` file. |
| Extraction yields 0 vertices / shapes | Stop; refuse to save. |
| Extraction yields <3 distinct color pairs | Continue; mark `confidence: "low"` (image) or `"medium"` (XML); warn in summary. |
| Preset name collides with existing user preset | Ask: overwrite, or pick a new name. |
| Preset name collides with a built-in preset | Save to user dir (shadows the built-in); warn once. |
| Sample render fails | Still show summary; note "could not render sample — saving on your OK anyway". Do not block. |

## Management operations

All operations are natural language — no slash commands.

*Apply name normalisation (lowercase) to all `<name>`, `<a>`, `<b>` arguments before any file operation.*

| User says | Agent does |
|---|---|
| "list my styles", "what styles do I have", "show me my style presets" | Read `~/.drawio-skill/styles/` and `<this-skill-dir>/styles/built-in/`. Print a table: `name`, `location` (user/built-in), `source.type`, `confidence`, `default` flag. Built-ins shadowed by a user preset are marked so. |
| "show my `<name>` style", "what's in `<name>`" | Print the preset JSON (pretty-printed) + a one-line summary (source, confidence, is-default). |
| "make `<name>` the default", "set `<name>` as default" | If `<name>` is a user preset: set `default: true` on it; clear `default` on any other user preset that had it; save both files. If `<name>` is a built-in: copy `<this-skill-dir>/styles/built-in/<name>.json` → `~/.drawio-skill/styles/<name>.json` first, then set `default: true` on the copy. Never mutate the shipped built-in. |
| "remove default", "unset default" | Clear `default: true` from whichever user preset has it. |
| "delete `<name>`", "remove `<name>`" | Confirm first. Then `rm ~/.drawio-skill/styles/<name>.json`. Refuse to delete files under `<this-skill-dir>/styles/built-in/` — suggest shadowing with a user preset of the same name. |
| "rename `<a>` to `<b>`" | `mv ~/.drawio-skill/styles/<a>.json ~/.drawio-skill/styles/<b>.json`, then update the `name` field inside. Fails if `<a>` is a built-in (offer to copy-then-rename instead). |
| "learn my style from `<path>` as `<name>`" | Dispatch to the Learn flow above. |

## Preset file validation

When loading any preset (for generation or management), do a lightweight structural check:
- Required top-level fields present (`name`, `version`, `palette`, `roles`, `shapes`, `font`, `edges`).
- `version === 1`.
- Every populated palette slot has both `fillColor` and `strokeColor` as `#RRGGBB`.
- `confidence` ∈ {`"low"`, `"medium"`, `"high"`} if present.

On validation failure:
- **During generation:** warn the user, fall back to built-in conventions for this one diagram, do not mutate the file.
- **During learn:** refuse to save the candidate; report which field failed.
