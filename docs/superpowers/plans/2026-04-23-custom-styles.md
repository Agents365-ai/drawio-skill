# Custom Styles Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add named style-preset support to drawio-skill so users can teach the skill a visual style from a `.drawio` file or an image, save it, and have future diagrams generated in that style.

**Architecture:** Pure prompt-layer change — no runtime code. Ships a JSON schema, three built-in presets, and a reference doc with extraction + sample-render recipes. Edits `SKILL.md` to (a) resolve the active preset at the start of the workflow, (b) fully replace the built-in palette/shape/edge conventions when a preset is active, and (c) add a new "Style Presets" section covering the learn and management flows.

**Tech Stack:** Markdown (SKILL.md + reference doc), JSON (schema + preset files), draw.io desktop CLI (already used), the agent's own vision capability (already used for self-check).

**Spec:** `docs/superpowers/specs/2026-04-23-custom-styles-design.md`

---

## File structure

**New files:**
- `styles/schema.json` — JSON Schema for preset files (draft-07).
- `styles/built-in/default.json` — mirrors the current `SKILL.md` color table; `confidence: "high"`, `default: false`.
- `styles/built-in/corporate.json` — muted professional palette, sharp corners (`rounded=0`).
- `styles/built-in/handdrawn.json` — warm palette, `extras.sketch: true`, curved edges.
- `references/style-extraction.md` — single reference doc the agent loads on demand during the learn flow. Contains: sample-render XML skeleton, XML extraction algorithm, image extraction algorithm, approval-flow checklist.
- `docs/superpowers/plans/2026-04-23-custom-styles.md` — this plan (already being written).

**Modified files:**
- `SKILL.md` — three edits, in order:
  1. Insert new workflow step **0.5 Resolve active preset** between step 0 and step 1.
  2. Insert a new subsection **Applying a preset** before the existing `### Color palette (fillColor / strokeColor)` subsection, and prepend a "No preset active / Preset active" conditional wrapper to the palette table's intro.
  3. Add a new top-level section `## Style Presets` after the `## Workflow` section, covering the learn flow and the management-operations table.
- `SKILL.md` frontmatter — bump `metadata.author.version` from `1.2.0` to `1.3.0`.

**Unchanged:** everything else — auto-update mechanism, diagram-type presets (ERD/UML/Sequence/etc.), self-check loop, export commands, browser fallback.

**Verification:** no unit-test harness (the skill is a prompt). Final task runs the nine scenario checks from the spec's "Verification checklist" section manually.

---

## Task 1: Create the preset JSON schema

**Files:**
- Create: `styles/schema.json`

- [ ] **Step 1: Write `styles/schema.json`**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://github.com/Agents365-ai/drawio-skill/styles/schema.json",
  "title": "drawio-skill preset",
  "type": "object",
  "required": ["name", "version", "palette", "roles", "shapes", "font", "edges"],
  "additionalProperties": false,
  "properties": {
    "$schema":    { "type": "string" },
    "name":       { "type": "string", "pattern": "^[a-z0-9][a-z0-9_-]*$" },
    "version":    { "type": "integer", "const": 1 },
    "default":    { "type": "boolean" },
    "confidence": { "type": "string", "enum": ["low", "medium", "high"] },
    "source": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "type":          { "type": "string", "enum": ["xml", "image", "built-in", "hand-authored"] },
        "path":          { "type": "string" },
        "extracted_at":  { "type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$" }
      }
    },
    "palette": {
      "type": "object",
      "additionalProperties": false,
      "required": ["primary", "success", "warning", "accent", "danger", "neutral", "secondary"],
      "properties": {
        "primary":   { "$ref": "#/$defs/colorPair" },
        "success":   { "$ref": "#/$defs/colorPair" },
        "warning":   { "$ref": "#/$defs/colorPair" },
        "accent":    { "$ref": "#/$defs/colorPair" },
        "danger":    { "$ref": "#/$defs/colorPair" },
        "neutral":   { "$ref": "#/$defs/colorPair" },
        "secondary": { "$ref": "#/$defs/colorPair" }
      }
    },
    "roles": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "service":  { "$ref": "#/$defs/slotName" },
        "database": { "$ref": "#/$defs/slotName" },
        "queue":    { "$ref": "#/$defs/slotName" },
        "gateway":  { "$ref": "#/$defs/slotName" },
        "error":    { "$ref": "#/$defs/slotName" },
        "external": { "$ref": "#/$defs/slotName" },
        "security": { "$ref": "#/$defs/slotName" }
      }
    },
    "shapes": {
      "type": "object",
      "additionalProperties": { "type": "string" },
      "properties": {
        "service":   { "type": "string" },
        "database":  { "type": "string" },
        "queue":     { "type": "string" },
        "decision":  { "type": "string" },
        "external":  { "type": "string" },
        "container": { "type": "string" }
      }
    },
    "font": {
      "type": "object",
      "additionalProperties": false,
      "required": ["fontFamily", "fontSize"],
      "properties": {
        "fontFamily":    { "type": "string" },
        "fontSize":      { "type": "integer", "minimum": 8, "maximum": 36 },
        "titleFontSize": { "type": "integer", "minimum": 8, "maximum": 48 },
        "titleBold":     { "type": "boolean" }
      }
    },
    "edges": {
      "type": "object",
      "additionalProperties": false,
      "required": ["style", "arrow"],
      "properties": {
        "style":      { "type": "string" },
        "arrow":      { "type": "string" },
        "dashedFor":  { "type": "array", "items": { "type": "string" } }
      }
    },
    "extras": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "sketch":            { "type": "boolean" },
        "globalStrokeWidth": { "type": "number", "minimum": 0.5, "maximum": 6 }
      }
    }
  },
  "$defs": {
    "colorPair": {
      "oneOf": [
        { "type": "null" },
        {
          "type": "object",
          "additionalProperties": false,
          "required": ["fillColor", "strokeColor"],
          "properties": {
            "fillColor":   { "type": "string", "pattern": "^#[0-9A-Fa-f]{6}$" },
            "strokeColor": { "type": "string", "pattern": "^#[0-9A-Fa-f]{6}$" }
          }
        }
      ]
    },
    "slotName": {
      "type": "string",
      "enum": ["primary", "success", "warning", "accent", "danger", "neutral", "secondary"]
    }
  }
}
```

- [ ] **Step 2: Verify JSON parses cleanly**

Run: `python3 -c "import json; json.load(open('styles/schema.json')); print('ok')"`
Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add styles/schema.json
git commit -m "feat: add preset JSON schema for custom styles"
```

---

## Task 2: Create the three built-in presets

**Files:**
- Create: `styles/built-in/default.json`
- Create: `styles/built-in/corporate.json`
- Create: `styles/built-in/handdrawn.json`

- [ ] **Step 1: Write `styles/built-in/default.json`** (mirrors the current SKILL.md color table)

```json
{
  "$schema": "../schema.json",
  "name": "default",
  "version": 1,
  "default": false,
  "source": { "type": "built-in" },
  "confidence": "high",
  "palette": {
    "primary":   { "fillColor": "#dae8fc", "strokeColor": "#6c8ebf" },
    "success":   { "fillColor": "#d5e8d4", "strokeColor": "#82b366" },
    "warning":   { "fillColor": "#fff2cc", "strokeColor": "#d6b656" },
    "accent":    { "fillColor": "#ffe6cc", "strokeColor": "#d79b00" },
    "danger":    { "fillColor": "#f8cecc", "strokeColor": "#b85450" },
    "neutral":   { "fillColor": "#f5f5f5", "strokeColor": "#666666" },
    "secondary": { "fillColor": "#e1d5e7", "strokeColor": "#9673a6" }
  },
  "roles": {
    "service":  "primary",
    "database": "success",
    "queue":    "warning",
    "gateway":  "accent",
    "error":    "danger",
    "external": "neutral",
    "security": "secondary"
  },
  "shapes": {
    "service":   "rounded=1",
    "database":  "shape=cylinder3",
    "queue":     "rounded=1",
    "decision":  "rhombus",
    "external":  "rounded=1;dashed=1",
    "container": "swimlane;startSize=30"
  },
  "font": {
    "fontFamily": "Helvetica",
    "fontSize": 12,
    "titleFontSize": 14,
    "titleBold": true
  },
  "edges": {
    "style": "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1",
    "arrow": "endArrow=classic;endFill=1",
    "dashedFor": []
  },
  "extras": {
    "sketch": false,
    "globalStrokeWidth": 1
  }
}
```

- [ ] **Step 2: Write `styles/built-in/corporate.json`** (muted professional palette, sharp corners)

```json
{
  "$schema": "../schema.json",
  "name": "corporate",
  "version": 1,
  "default": false,
  "source": { "type": "built-in" },
  "confidence": "high",
  "palette": {
    "primary":   { "fillColor": "#e3f2fd", "strokeColor": "#1565c0" },
    "success":   { "fillColor": "#e8f5e9", "strokeColor": "#2e7d32" },
    "warning":   { "fillColor": "#fff9c4", "strokeColor": "#f57c00" },
    "accent":    { "fillColor": "#fff3e0", "strokeColor": "#e65100" },
    "danger":    { "fillColor": "#ffebee", "strokeColor": "#c62828" },
    "neutral":   { "fillColor": "#eceff1", "strokeColor": "#455a64" },
    "secondary": { "fillColor": "#f3e5f5", "strokeColor": "#6a1b9a" }
  },
  "roles": {
    "service":  "primary",
    "database": "success",
    "queue":    "warning",
    "gateway":  "accent",
    "error":    "danger",
    "external": "neutral",
    "security": "secondary"
  },
  "shapes": {
    "service":   "rounded=0",
    "database":  "shape=cylinder3",
    "queue":     "rounded=0",
    "decision":  "rhombus",
    "external":  "rounded=0;dashed=1",
    "container": "swimlane;startSize=30"
  },
  "font": {
    "fontFamily": "Arial",
    "fontSize": 11,
    "titleFontSize": 13,
    "titleBold": true
  },
  "edges": {
    "style": "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1",
    "arrow": "endArrow=classic;endFill=1",
    "dashedFor": ["optional", "async"]
  },
  "extras": {
    "sketch": false,
    "globalStrokeWidth": 1
  }
}
```

- [ ] **Step 3: Write `styles/built-in/handdrawn.json`** (warm palette, `sketch=1`, curved edges)

```json
{
  "$schema": "../schema.json",
  "name": "handdrawn",
  "version": 1,
  "default": false,
  "source": { "type": "built-in" },
  "confidence": "high",
  "palette": {
    "primary":   { "fillColor": "#ffe4b5", "strokeColor": "#b8651e" },
    "success":   { "fillColor": "#def0dc", "strokeColor": "#5c8a49" },
    "warning":   { "fillColor": "#fff4cc", "strokeColor": "#b8901a" },
    "accent":    { "fillColor": "#ffd9b3", "strokeColor": "#c25100" },
    "danger":    { "fillColor": "#ffcdbf", "strokeColor": "#a53d3d" },
    "neutral":   { "fillColor": "#f5e6d3", "strokeColor": "#8b7355" },
    "secondary": { "fillColor": "#e6d7e8", "strokeColor": "#7b4397" }
  },
  "roles": {
    "service":  "primary",
    "database": "success",
    "queue":    "warning",
    "gateway":  "accent",
    "error":    "danger",
    "external": "neutral",
    "security": "secondary"
  },
  "shapes": {
    "service":   "rounded=1",
    "database":  "shape=cylinder3",
    "queue":     "rounded=1",
    "decision":  "rhombus",
    "external":  "rounded=1;dashed=1",
    "container": "swimlane;startSize=30"
  },
  "font": {
    "fontFamily": "Helvetica",
    "fontSize": 12,
    "titleFontSize": 14,
    "titleBold": true
  },
  "edges": {
    "style": "edgeStyle=orthogonalEdgeStyle;curved=1;rounded=1;orthogonalLoop=1;jettySize=auto;html=1",
    "arrow": "endArrow=classic;endFill=1",
    "dashedFor": ["optional"]
  },
  "extras": {
    "sketch": true,
    "globalStrokeWidth": 2
  }
}
```

- [ ] **Step 4: Verify all three presets are valid JSON**

Run:
```bash
for f in styles/built-in/*.json; do
  python3 -c "import json; json.load(open('$f')); print('ok: $f')"
done
```
Expected: three `ok:` lines.

- [ ] **Step 5: Commit**

```bash
git add styles/built-in/
git commit -m "feat: add built-in presets (default, corporate, handdrawn)"
```

---

## Task 3: Create `references/style-extraction.md` — sample-render skeleton

**Files:**
- Create: `references/style-extraction.md`

- [ ] **Step 1: Write the initial reference doc with the sample-render skeleton**

Write `references/style-extraction.md` with this content:

````markdown
# Style Extraction — agent reference

Loaded on demand by `SKILL.md` when the user asks to learn a style ("learn my style from `<path>` as `<name>`") or when the agent needs to render a sample after extraction.

## Sample diagram (for approval render)

After extracting a candidate preset, render this seven-node sample using the candidate's palette/shapes/fonts/edges. Each role appears exactly once; six edges, one dashed, exercise `edges.arrow`, `edges.style`, and `edges.dashedFor`.

**Layout (TB):**
- Row 1 (y=40): `gateway` centered at x=340
- Row 2 (y=180): `security` (x=80), `service` (x=340), `queue` (x=600)
- Row 3 (y=340): `database` (x=80), `external` (x=340), `error` (x=600)

**Template — substitute `{{...}}` placeholders from the candidate preset.**

The vertex style for role `R` is built as:
`<shapes[R]>;whiteSpace=wrap;html=1;fillColor=<palette[roles[R]].fillColor>;strokeColor=<palette[roles[R]].strokeColor>;fontFamily=<font.fontFamily>;fontSize=<font.fontSize>`
- If `extras.sketch=true`, append `;sketch=1`.
- If `extras.globalStrokeWidth > 1`, append `;strokeWidth=<n>`.

The edge style is built as:
`<edges.style>;<edges.arrow>`
- Per-edge routing keys (`exitX/entryX/...`) are added as literals below.
- One edge is labeled `"optional"` and rendered with `;dashed=1` appended, so `edges.dashedFor` behavior is visible.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="drawio" version="26.0.0">
  <diagram name="Preset Sample">
    <mxGraphModel>
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />

        <!-- Row 1: gateway -->
        <mxCell id="2" value="Gateway" style="{{VSTYLE:gateway}}" vertex="1" parent="1">
          <mxGeometry x="340" y="40" width="160" height="60" as="geometry" />
        </mxCell>

        <!-- Row 2: security | service | queue -->
        <mxCell id="3" value="Auth" style="{{VSTYLE:security}}" vertex="1" parent="1">
          <mxGeometry x="80" y="180" width="160" height="60" as="geometry" />
        </mxCell>
        <mxCell id="4" value="Service" style="{{VSTYLE:service}}" vertex="1" parent="1">
          <mxGeometry x="340" y="180" width="160" height="60" as="geometry" />
        </mxCell>
        <mxCell id="5" value="Queue" style="{{VSTYLE:queue}}" vertex="1" parent="1">
          <mxGeometry x="600" y="180" width="160" height="60" as="geometry" />
        </mxCell>

        <!-- Row 3: database | external | error -->
        <mxCell id="6" value="Database" style="{{VSTYLE:database}}" vertex="1" parent="1">
          <mxGeometry x="80" y="340" width="160" height="70" as="geometry" />
        </mxCell>
        <mxCell id="7" value="External API" style="{{VSTYLE:external}}" vertex="1" parent="1">
          <mxGeometry x="340" y="340" width="160" height="60" as="geometry" />
        </mxCell>
        <mxCell id="8" value="Error Sink" style="{{VSTYLE:error}}" vertex="1" parent="1">
          <mxGeometry x="600" y="340" width="160" height="60" as="geometry" />
        </mxCell>

        <!-- Edges -->
        <mxCell id="10" value="" style="{{ESTYLE}};exitX=0.25;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0" edge="1" parent="1" source="2" target="3">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="11" value="" style="{{ESTYLE}};exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0" edge="1" parent="1" source="2" target="4">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="12" value="" style="{{ESTYLE}};exitX=0.75;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0" edge="1" parent="1" source="2" target="5">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="13" value="" style="{{ESTYLE}};exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0" edge="1" parent="1" source="4" target="7">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="14" value="" style="{{ESTYLE}};exitX=0;exitY=0.5;exitDx=0;exitDy=0;entryX=1;entryY=0.5;entryDx=0;entryDy=0" edge="1" parent="1" source="4" target="6">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="15" value="optional" style="{{ESTYLE}};dashed=1;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0" edge="1" parent="1" source="4" target="8">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

### Rendering the sample

1. Write the filled XML to `/tmp/drawio-preset-<name>.drawio`.
2. Run the same `draw.io -x -f png -e -s 2 -o <preset-name>-sample.png <tmp>.drawio` command the main workflow uses.
3. Save the PNG as `./preset-<name>-sample.png` (the user's working directory).
4. Show the user: preset summary table + PNG path + provenance/confidence line.

### Approval loop

- "save" / "looks good" → write candidate to `~/.drawio-skill/styles/<name>.json`; delete tempfile and sample PNG.
- "change <field> to <value>" → edit the in-memory candidate; re-render; re-ask.
- "cancel" → delete tempfile and sample PNG; no save.

### If sample render fails (draw.io CLI missing / export error)

Still show the summary table and the provenance line. Note: *"Could not render sample PNG (CLI unavailable). Save anyway on your OK."* Do not block.
````

- [ ] **Step 2: Verify the file parses as markdown and the XML block is well-formed**

Run:
```bash
python3 -c "
import re
doc = open('references/style-extraction.md').read()
xml_blocks = re.findall(r'\`\`\`xml\n(.*?)\n\`\`\`', doc, re.DOTALL)
print(f'found {len(xml_blocks)} xml block(s)')
import xml.etree.ElementTree as ET
# Strip {{...}} placeholders before parse
cleaned = re.sub(r'\{\{[^}]+\}\}', 'placeholder', xml_blocks[0])
ET.fromstring(cleaned)
print('xml well-formed')
"
```
Expected: `found 1 xml block(s)` then `xml well-formed`.

- [ ] **Step 3: Commit**

```bash
git add references/style-extraction.md
git commit -m "feat: add style-extraction reference with sample-render skeleton"
```

---

## Task 4: Append XML extraction algorithm to the reference

**Files:**
- Modify: `references/style-extraction.md` (append new section)

- [ ] **Step 1: Append the XML extraction section**

Append this content to the end of `references/style-extraction.md`:

````markdown

## XML extraction path

Input: a `.drawio` file path. Output: candidate preset JSON. Deterministic, no LLM inference.

### Steps

1. **Parse the file.** Read the XML, collect every `<mxCell>` with a `style=` attribute, split into vertices (`vertex="1"`) and edges (`edge="1"`).
2. **Tokenize each `style=` string** on `;`. Each element is either `key=value` or a bare keyword (e.g., `rhombus`, `ellipse`, `rounded=1`).
3. **Extract palette.** For every vertex, take the `(fillColor, strokeColor)` pair (skip vertices with neither). Count frequency. Keep the top ≤7 pairs.
4. **Extract shape vocabulary + role mapping.** For each vertex determine a shape class by precedence:
   `cylinder3 > ellipse > rhombus > swimlane > rounded=1 > rounded=0`.
   Then infer the semantic role:
   - `cylinder3` → `database`
   - `rhombus` → `decision`
   - `swimlane` → `container`
   - `dashed=1` present + grey-family fill → `external`
   - label matches `/queue|bus|kafka|rabbit/i` → `queue`
   - label matches `/gateway|api|lb|load/i` → `gateway`
   - label matches `/auth|login|jwt|oauth/i` → `security`
   - label matches `/error|fail|alert/i` → `error`
   - everything else → `service`

   For each **role that has a canonical palette slot** — `service`, `database`, `queue`, `gateway`, `error`, `external`, `security` — the most frequent `(role, color-pair)` mapping wins. The pair goes into the role's canonical palette slot:
   `service→primary, database→success, queue→warning, gateway→accent, error→danger, external→neutral, security→secondary`.
   Set `roles[role]` to that slot name.

   **Decision and container shapes do not get a `roles[...]` entry** — they are recorded only in `shapes.decision` and `shapes.container`. Any color pairs observed on decision/container vertices still participate in the palette (they can fill leftover slots) but are not tied to a semantic role.

   Leftover color pairs (not claimed by any role-slot mapping) fill remaining empty palette slots in descending-frequency order.

   Record the shape class string used per role in `shapes[role]` (e.g., `shapes.database = "shape=cylinder3"`). This applies to all nine shape roles: `service`, `database`, `queue`, `decision`, `external`, `container`, plus `gateway`, `error`, `security` where their modal shape differs from `service`.

5. **Extract fonts.** Modal `fontFamily`, `fontSize`, `fontStyle` across vertices.
   If a distinguishable subset uses a larger size + `fontStyle=1` (bold), treat that as titles: set `titleFontSize` and `titleBold: true`.

6. **Extract edge defaults.** Take the modal edge style string, but strip these per-edge coordinate keys before counting: `entryX`, `entryY`, `exitX`, `exitY`, `entryDx`, `entryDy`, `exitDx`, `exitDy`. Record arrow style from `endArrow`/`endFill` separately in `edges.arrow`.
   If any edges have `dashed=1`, collect their `value` (label) attributes. If ≥2 share a common token (e.g., all are labeled "async" or "optional"), add that token to `edges.dashedFor`.

7. **Extract extras.** `sketch=1` seen on any vertex or edge → `extras.sketch = true`. Modal `strokeWidth` across vertices → `extras.globalStrokeWidth` (default `1`).

8. **Set provenance.**
   ```json
   {
     "source": { "type": "xml", "path": "<input absolute path>", "extracted_at": "YYYY-MM-DD" },
     "confidence": "high"
   }
   ```

### XML edge cases

| Situation | Behavior |
|---|---|
| Source has <3 distinct color pairs | Leave unfilled slots as `null`. Downgrade `confidence` to `"medium"`. Summary warns the user. |
| Source has >7 color pairs | Keep the top 7 by frequency. Summary warns that some colors were dropped. |
| Non-standard `shape=` keywords (e.g., `shape=mxgraph.aws4.*`) | Record the literal string under the closest role. Note in summary. |
| Non-English labels | The English-keyword regexes in step 4 will mostly miss; most vertices collapse to `service`. Palette/shapes/font/edges still captured correctly (they don't depend on label text). `confidence` stays `"high"`. Summary notes: *"Role labels not in English — `service`/`database`/`decision`/`container`/`external` inferred from shape class; other roles not mapped."* |
| File has no `<mxCell vertex="1">` at all | Stop. Refuse to save. Message: *"Nothing to learn from — source file has no shapes."* |
````

- [ ] **Step 2: Verify the file still parses**

Run: `wc -l references/style-extraction.md`
Expected: line count has increased by at least 50.

- [ ] **Step 3: Commit**

```bash
git add references/style-extraction.md
git commit -m "feat: add XML extraction algorithm to style-extraction reference"
```

---

## Task 5: Append image extraction algorithm to the reference

**Files:**
- Modify: `references/style-extraction.md` (append new section)

- [ ] **Step 1: Append the image extraction section**

Append this content to the end of `references/style-extraction.md`:

````markdown

## Image extraction path

Input: path to a PNG/JPG (or any vision-readable image format). Output: candidate preset JSON. Inference-based; `confidence: "medium"` at best.

**Prerequisite:** the agent's vision capability must be available (same mechanism the main workflow's self-check uses). If vision is not available, stop and tell the user:
*"Image-based learning needs a vision-enabled model (Claude Sonnet or Opus). Re-run on such a model, or provide the `.drawio` source file instead."*

### Steps

1. **Read the image.** Use the agent's vision input — the same path the main workflow's step 5 uses to read exported PNGs during self-check.

2. **Extract palette by visual inspection.** Identify distinct fill-color regions on shape bodies.

   For each distinct fill:
   - `fillColor` — quantize: round each RGB channel to the nearest multiple of 16, harmonize lightness to ~85% (drawio-standard pastel look). Emit as `#RRGGBB`.
   - `strokeColor` — read the matching border. If unreadable, derive from fill by darkening ~25% (match HSL, drop L by 0.25).

   Map each `(fillColor, strokeColor)` pair to a named slot by hue of the fill:
   - blue family → `primary`
   - green family → `success`
   - yellow family → `warning`
   - orange family → `accent`
   - red/pink family → `danger`
   - grey family → `neutral`
   - purple family → `secondary`

   Two distinct colors in the same hue family: keep the more frequently-used one in its canonical slot; the other spills to the nearest empty slot (adjacent hue).

3. **Extract shape vocabulary.** Classify every visible shape by silhouette:
   - rounded rectangle → `rounded=1`
   - sharp rectangle → `rounded=0`
   - circle / oval → `ellipse`
   - diamond → `rhombus`
   - cylinder (rectangle with curved top/bottom) → `shape=cylinder3`
   - titled container (header bar + nested children inside) → `swimlane;startSize=30`
   - dashed-bordered rectangle → `rounded=1;dashed=1`

   Role assignment uses the **same label-text + shape rules as the XML path step 4**. Visible labels are read via vision.

4. **Extract fonts.** Best-effort. Distinguishable categories:
   - clearly serif → `fontFamily: "Georgia"`
   - clearly monospaced → `fontFamily: "Courier New"`
   - otherwise → `fontFamily: "Helvetica"`

   Size by relative appearance:
   - small → `fontSize: 11`
   - medium → `fontSize: 12`
   - large → `fontSize: 14`

   If titles/container headers are distinctly larger or bolder → set `titleFontSize` accordingly and `titleBold: true`.

5. **Extract edge defaults.**
   - Right-angle orthogonal arrows → `edges.style = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1"`.
   - Curved arrows → append `;curved=1` to `edges.style`.
   - Filled triangle arrowheads → `edges.arrow = "endArrow=classic;endFill=1"`.
   - Open V-shaped arrowheads → `edges.arrow = "endArrow=open;endFill=0"`.
   - Any dashed arrows near labels like "optional", "async", "fallback", "secondary" → add those label tokens to `edges.dashedFor`.

6. **Extract extras.**
   - Visibly hand-drawn / rough / sketch look (wavy strokes, uneven fills) → `extras.sketch = true`.
   - Heavy strokes (clearly >1.5× normal) → `extras.globalStrokeWidth = 2`.
   - Otherwise default: `extras = { "sketch": false, "globalStrokeWidth": 1 }`.

7. **Set provenance and confidence.**
   ```json
   {
     "source": { "type": "image", "path": "<input absolute path>", "extracted_at": "YYYY-MM-DD" },
     "confidence": "medium"
   }
   ```
   Adjustments:
   - <3 distinct shapes identifiable → `confidence: "low"`.
   - Very clean image, ≥5 roles confidently mapped, all seven palette slots filled → may upgrade to `"high"`.

### Image edge cases

| Situation | Behavior |
|---|---|
| Vision unavailable | Stop as described above — do not fall back to guessing. |
| Image has <3 identifiable shapes | Continue; mark `confidence: "low"`; summary explicitly warns the user that the preset is a loose approximation. |
| Image has no visible labels | Role assignment collapses to shape-class only: cylinders → `database`, diamonds → `decision`, swimlanes → `container`, everything else → `service`. Palette/font/edges still captured. Summary notes: *"No labels readable — semantic roles beyond shape-class not inferred."* |
| Two palette slots would land in the same hue family | Keep the more frequent one in its canonical slot; spill the other to the adjacent empty slot (rule in step 2). |
````

- [ ] **Step 2: Verify the file still parses**

Run: `wc -l references/style-extraction.md`
Expected: line count has increased further.

- [ ] **Step 3: Commit**

```bash
git add references/style-extraction.md
git commit -m "feat: add image extraction algorithm to style-extraction reference"
```

---

## Task 6: Edit SKILL.md — insert workflow step 0.5 (resolve active preset)

**Files:**
- Modify: `SKILL.md` (insert between step 0 and step 1)

- [ ] **Step 1: Insert step 0.5 into the Workflow section**

We insert step 0.5 as a **non-list paragraph** between ordered-list items 0 and 1. This avoids renumbering the existing 1–7 steps (which are referenced by name elsewhere in SKILL.md, e.g., `### Step 5: Self-Check`).

Use the Edit tool. Find the existing text:

```
   If the pull fails (offline, conflict, not a git checkout, etc.), ignore the error and continue normally. Do not mention the update to the user unless they ask.
1. **Check deps** — verify `draw.io --version` succeeds; note platform for correct CLI path
```

Replace with:

```
   If the pull fails (offline, conflict, not a git checkout, etc.), ignore the error and continue normally. Do not mention the update to the user unless they ask.

**Step 0.5 — Resolve active preset.** Determine which (if any) user-defined style preset applies to this generation.

- Scan the user's message for a named preset reference: "use my `<name>` style", "with `<name>`", "in `<name>` mode". If found → active preset = `<name>`.
- Else, check `~/.drawio-skill/styles/` for any file with `"default": true`. If found → active preset = that one.
- Else → no preset active; fall through to the built-in color/shape/edge conventions for the rest of the workflow.

Load the preset JSON from `~/.drawio-skill/styles/<name>.json`, falling back to `<skill-dir>/styles/built-in/<name>.json`. If the named preset exists in neither location, tell the user the name is unknown, list the available presets (user dir + built-in), and stop — do **not** silently fall back to defaults.

When a preset loads successfully, mention it in the first line of the reply: *"Using preset `<name>` (confidence: `<level>`)."* See the **Applying a preset** subsection below for how the preset changes color/shape/edge/font decisions.

1. **Check deps** — verify `draw.io --version` succeeds; note platform for correct CLI path
```

(Note the blank line before `**Step 0.5 — ...**` and the blank line before `1. **Check deps**`. The blank line after step 0.5 is required to close the ordered list so that `1.` starts a **new** ordered list at `1` rather than being treated as `2` of the prior list.)

- [ ] **Step 2: Verify the edit rendered correctly**

Run: `grep -n "Resolve active preset" SKILL.md`
Expected: one match line with the bold heading.

Run: `grep -nE "^1\.[[:space:]]+\*\*Check deps" SKILL.md`
Expected: one match — step 1 is still numbered `1.` in the source. (Markdown will render it as item 1 of the new list after the step 0.5 paragraph.)

Run: `grep -nE "^### Step [0-9]+:" SKILL.md`
Expected: still three matches — `### Step 5: Self-Check`, `### Step 6: Review Loop`, `### Step 7: Final Export`. These must not have been renumbered.

- [ ] **Step 3: Commit**

```bash
git add SKILL.md
git commit -m "feat(skill): add workflow step to resolve active style preset"
```

---

## Task 7: Edit SKILL.md — add "Applying a preset" subsection + wrap palette table

**Files:**
- Modify: `SKILL.md` (insert before `### Color palette (fillColor / strokeColor)`)

- [ ] **Step 1: Insert the new subsection and wrap the palette table**

Use the Edit tool. Find the existing text:

```
### Color palette (fillColor / strokeColor)

| Color name | fillColor | strokeColor | Use for |
|-----------|-----------|-------------|---------|
| Blue | `#dae8fc` | `#6c8ebf` | services, clients |
```

Replace with:

```
### Applying a preset

When the Workflow's step *Resolve active preset* identified a preset, it fully replaces the built-in palette, shape keywords, edge defaults, and font for this diagram — do not mix values from the built-in color table below.

**Color lookup.** For each role a shape plays (service / database / queue / gateway / error / external / security), resolve `preset.roles[role]` to a slot name, then `preset.palette[<slot>]` to the `(fillColor, strokeColor)` pair. If `roles[role]` is unset or the resolved slot is `null`, follow this fallback ladder:

1. Try the role's canonical slot (`service→primary`, `database→success`, `queue→warning`, `gateway→accent`, `error→danger`, `external→neutral`, `security→secondary`).
2. If that slot is also empty, pick the most-populated non-null slot in the preset.
3. Never reach into the built-in color table below — the preset is authoritative.

**Decision and container shapes** are not in `preset.roles` — they have shape vocabulary (`preset.shapes.decision`, `preset.shapes.container`) but no role-to-slot mapping. Pick their colors as follows:
- **Decision** (rhombus) → use `preset.palette.warning` (the canonical yellow slot in the built-in conventions). If `warning` is empty, apply the slot-fallback ladder above starting from `warning`.
- **Container** (swimlane) → use the palette slot matching the tier/grouping the container represents (e.g., a "Services" tier container uses `primary`; a "Data" tier uses `success`). If no tier signal is available, default to `primary`.

**Shape keywords.** Use `preset.shapes[role]` as the **prefix** of the vertex style string (before `whiteSpace=wrap;html=1;...`). Example: for a database role, if `preset.shapes.database = "shape=cylinder3"`, the vertex style starts `shape=cylinder3;whiteSpace=wrap;html=1;fillColor=...`.

**Edges.** Use `preset.edges.style` as the base edge style string. Append `preset.edges.arrow`. Per-edge routing keys (`exitX/exitY/entryX/entryY/...`) are still added by the usual routing rules in the rest of this document. If the flow between two shapes matches a token from `preset.edges.dashedFor` (either because the user's prompt used that word, or because one end of the edge plays a role whose typical relation is "optional"), append `;dashed=1` to the edge style.

**Fonts.** Append `fontFamily=<preset.font.fontFamily>;fontSize=<preset.font.fontSize>` to every vertex style. Container headers and swimlane titles additionally get `fontSize=<preset.font.titleFontSize>;fontStyle=1` when `preset.font.titleBold` is `true`.

**Extras.**
- `preset.extras.sketch === true` → append `sketch=1` to every vertex style and every edge style.
- `preset.extras.globalStrokeWidth > 1` → append `strokeWidth=<n>` to every vertex style and every edge style.

**Interaction with diagram-type presets (ERD / UML / Sequence / ML / Flowchart).** Diagram-type presets earlier in this document set structural style keywords that the user preset must preserve (e.g., ERD tables rely on `shape=table;startSize=30;container=1;childLayout=tableLayout;...`). The rule: keep the diagram-type preset's structural keywords, then layer the user preset's color / font / edge / extras on top. When a diagram-type preset hardcodes a color (`fillColor=#dae8fc`, etc.) that conflicts with the user preset, the user preset's color wins.

### Color palette (fillColor / strokeColor)

*Used only when no preset is active (see "Applying a preset" above).*

| Color name | fillColor | strokeColor | Use for |
|-----------|-----------|-------------|---------|
| Blue | `#dae8fc` | `#6c8ebf` | services, clients |
```

- [ ] **Step 2: Verify the edit**

Run: `grep -n "^### Applying a preset" SKILL.md`
Expected: one match.

Run: `grep -n "^### Color palette" SKILL.md`
Expected: still one match, now preceded by the conditional note.

Run: `grep -n "Used only when no preset is active" SKILL.md`
Expected: one match.

- [ ] **Step 3: Commit**

```bash
git add SKILL.md
git commit -m "feat(skill): document how an active preset overrides built-in styling"
```

---

## Task 8: Edit SKILL.md — add the "Style Presets" section (learn flow + management)

**Files:**
- Modify: `SKILL.md` (insert new top-level section between `## Workflow` end and `## Draw.io XML Structure`)

- [ ] **Step 1: Insert the new section**

Use the Edit tool. Find the last paragraph of the Workflow section — the end of `### Step 7: Final Export`. The exact line to insert after is:

```
- Confirm files are saved and ready to use
```

…which is the last bullet of Step 7, immediately before `## Draw.io XML Structure`.

Replace:

```
- Confirm files are saved and ready to use

## Draw.io XML Structure
```

With:

```
- Confirm files are saved and ready to use

## Style Presets

A **style preset** is a named JSON file that captures a user's visual preferences — palette, shape vocabulary, fonts, edge style. When a preset is active, it fully replaces the built-in conventions in `## Draw.io XML Structure` below (see `### Applying a preset`).

**Locations, in lookup order:**
1. `~/.drawio-skill/styles/<name>.json` — user presets (survive `git pull`).
2. `<skill-dir>/styles/built-in/<name>.json` — built-ins shipped with the skill (`default`, `corporate`, `handdrawn`).

A user preset shadows a built-in of the same name.

Only user presets can have `"default": true`. When the user says *"make `<built-in-name>` my default"*, copy the built-in JSON to `~/.drawio-skill/styles/<name>.json` first, then set `default: true` on the copy — leave the shipped built-in untouched.

### Learn flow

**Triggers:** "learn my style from `<path>` as `<name>`", "save this as `<name>` style", "remember this style as `<name>`".

**Dispatch by file extension:**
- `.drawio`, `.xml` → XML path
- `.png`, `.jpg`, `.jpeg`, `.svg` (rasterized) → image path

**Steps:**

1. **Load the extraction reference.** Read `references/style-extraction.md` into context (the algorithms below live there, not in this file).
2. **Extract** following the XML path or image path procedure.
3. **Build a candidate preset** and write it to `/tmp/drawio-preset-<name>.json`. Do **not** save to `~/.drawio-skill/styles/<name>.json` yet.
4. **Render a sample** using the sample-diagram skeleton in the reference, parameterized by the candidate preset. Export PNG to `./preset-<name>-sample.png` using the same `draw.io -x -f png ...` command the main workflow uses.
5. **Show the user:**
   - Preset summary table (palette hex values, shapes per role, font, edge style, extras).
   - The sample PNG path (and embed the image if the environment supports it).
   - Provenance line: `source.type`, `source.path`, `extracted_at`, `confidence`.
6. **Wait for approval:**
   - "save" / "looks good" → write candidate to `~/.drawio-skill/styles/<name>.json`. Create `~/.drawio-skill/styles/` if it doesn't exist. Delete tempfile and sample PNG.
   - "change `<field>` to `<value>`" → edit the in-memory candidate, re-render, re-ask.
   - "cancel" / "abort" / "no" → delete tempfile and sample PNG; nothing saved.

**Error behavior (match the spec's error table):**

| Failure | Behavior |
|---|---|
| Source path does not exist | Stop; report path not found. |
| XML parse fails | Stop; report the parse error; suggest opening the file in drawio desktop to repair. |
| Image vision unavailable | Stop; tell user to re-run on a vision-capable model or provide the `.drawio` file. |
| Extraction yields 0 vertices / shapes | Stop; refuse to save. |
| Extraction yields <3 distinct color pairs | Continue; mark `confidence` as `"low"` (image) or `"medium"` (XML); warn in the summary. |
| Preset name collides with existing user preset | Ask: overwrite, or pick a new name. |
| Preset name collides with a built-in preset | Save to user dir (shadows the built-in); warn once. |
| Sample render fails (CLI missing / export error) | Still show the summary; note "could not render sample — saving on your OK anyway". Do not block. |

### Management operations

All operations are natural language — no slash commands. Match intent from these phrasings:

| User says | Agent does |
|---|---|
| "list my styles", "what styles do I have", "show me my style presets" | Read `~/.drawio-skill/styles/` and `<skill-dir>/styles/built-in/`. Print a table: `name`, `location` (user/built-in), `source.type`, `confidence`, `default` flag. Built-ins that are shadowed by a user preset of the same name are marked so. |
| "show my `<name>` style", "what's in `<name>`" | Print the preset JSON (pretty-printed) + a one-line summary (source, confidence, is-default). |
| "make `<name>` the default", "set `<name>` as default" | If `<name>` is a user preset: set `default: true` on it; clear `default` on any other user preset that had it; save both files. If `<name>` is a built-in: first copy `<skill-dir>/styles/built-in/<name>.json` → `~/.drawio-skill/styles/<name>.json`, then set `default: true` on the copy. The shipped built-in is never mutated. |
| "remove default", "unset default" | Clear `default: true` from whichever user preset has it. |
| "delete `<name>`", "remove `<name>`" | Confirm first. Then `rm ~/.drawio-skill/styles/<name>.json`. Refuse to delete files under `<skill-dir>/styles/built-in/` — suggest shadowing with a user preset of the same name instead. |
| "rename `<a>` to `<b>`" | `mv ~/.drawio-skill/styles/<a>.json ~/.drawio-skill/styles/<b>.json`, then update the `name` field inside. Fails if `<a>` is a built-in (cannot rename built-ins; offer to copy-then-rename instead). |
| "learn my style from `<path>` as `<name>`" | Dispatch to the Learn flow above. |

### Preset file validation

When loading any preset (for generation or management), the agent does a lightweight structural check:
- required top-level fields present (`name`, `version`, `palette`, `roles`, `shapes`, `font`, `edges`);
- `version === 1`;
- every populated palette slot has both `fillColor` and `strokeColor` as `#RRGGBB`;
- `confidence` ∈ {`"low"`, `"medium"`, `"high"`}.

On validation failure:
- **During generation:** warn the user, fall back to built-in conventions for this one diagram, do not mutate the file.
- **During learn:** refuse to save the candidate; report which field failed.

## Draw.io XML Structure
```

- [ ] **Step 2: Verify the edit**

Run: `grep -n "^## Style Presets" SKILL.md`
Expected: one match.

Run: `grep -n "^### Learn flow" SKILL.md`
Expected: one match, inside the Style Presets section.

Run: `grep -n "^### Management operations" SKILL.md`
Expected: one match.

Run: `grep -c "^## " SKILL.md`
Expected: one more top-level section than before.

- [ ] **Step 3: Commit**

```bash
git add SKILL.md
git commit -m "feat(skill): add Style Presets section with learn flow and management ops"
```

---

## Task 9: Bump SKILL.md version and update README

**Files:**
- Modify: `SKILL.md` (frontmatter `metadata.author.version`)
- Modify: `README.md` (add feature mention)
- Modify: `README_CN.md` (add feature mention)

- [ ] **Step 1: Bump version in SKILL.md frontmatter**

Use the Edit tool on `SKILL.md`. Replace `"version":"1.2.0"` with `"version":"1.3.0"` (the version field is inside the `metadata` JSON on one line).

Verify:
```bash
grep -o '"version":"[^"]*"' SKILL.md
```
Expected: `"version":"1.3.0"`.

- [ ] **Step 2: Add a short feature mention to README.md**

Read `README.md` to find the Features section. Add one bullet under Features (or create a new "What's new in 1.3" line near the top):

> - **Style presets (new in 1.3)** — teach the skill your visual style from a `.drawio` file or an image, save it under a name, and use it on future diagrams. See the `## Style Presets` section in SKILL.md for details.

- [ ] **Step 3: Add the same mention to README_CN.md in Chinese**

Add equivalent bullet to `README_CN.md`:

> - **样式预设（v1.3 新增）** — 用一个 `.drawio` 文件或一张图片"教会"Skill 你喜欢的风格，命名保存后可在后续图表中复用。详见 SKILL.md 的 `## Style Presets` 小节。

- [ ] **Step 4: Commit**

```bash
git add SKILL.md README.md README_CN.md
git commit -m "chore: bump to v1.3.0 and document style presets in READMEs"
```

---

## Task 10: Run the nine verification scenarios

**Files:** no files changed unless a scenario fails and requires a fix.

This is the only test the skill gets. Each scenario exercises one aspect of the design. Document pass/fail for each. If any fails, fix and re-run — don't mark the task complete with known failures.

- [ ] **Step 1: Scenario 1 — XML learn round-trip**

In a fresh session with the drawio-skill available, run:

> "Learn my style from `assets/demo-layered.drawio` as `demo-xml`."

Expected:
- Agent reads `references/style-extraction.md` (or follows its rules internally).
- Candidate preset captures at least 5 of the 7 palette slots with colors matching `demo-layered.drawio` (`#dae8fc/#6c8ebf`, `#d5e8d4/#82b366`, `#f5f5f5/#666666`, `#ffe6cc/#d79b00`, `#e1d5e7/#9673a6`, `#f8cecc/#b85450`).
- `confidence: "high"`.
- A sample PNG is rendered showing the same palette visually.
- After user says "save", `~/.drawio-skill/styles/demo-xml.json` exists and validates against `styles/schema.json`.

- [ ] **Step 2: Scenario 2 — Image learn round-trip**

Run:

> "Learn my style from `assets/demo-layered.png` as `demo-img`."

Expected:
- Agent uses vision to read the PNG.
- Candidate preset is in the same ballpark as scenario 1 (colors may be quantized slightly differently).
- `confidence: "medium"`.
- Sample PNG rendered.
- On save, `~/.drawio-skill/styles/demo-img.json` exists.

- [ ] **Step 3: Scenario 3 — Apply (explicit)**

Run:

> "Draw an architecture diagram with a browser, an API gateway, two services, and a database, using my `demo-xml` style."

Expected:
- First reply line: *"Using preset `demo-xml` (confidence: high)."*
- Exported PNG uses the `demo-xml` palette (not a different palette).
- Shapes use the preset's `shapes.service` / `shapes.database` prefix.

- [ ] **Step 4: Scenario 4 — Default fallback**

Run:

> "Make `demo-xml` my default style."

Then in a fresh conversation:

> "Draw a simple three-tier architecture."

Expected:
- First reply line still mentions `demo-xml`.
- Output uses the `demo-xml` palette even without an explicit reference.

- [ ] **Step 5: Scenario 5 — No preset active**

Remove the default (`"Unset my default style"` then verify no user preset has `default: true`). Ensure no user preset is referenced.

Run:

> "Draw a flowchart with start, two steps, a decision, and end."

Expected:
- No preset mentioned in the reply.
- Output uses the built-in `SKILL.md` palette (blue services, green DBs, etc.) — unchanged from pre-1.3 behavior.

- [ ] **Step 6: Scenario 6 — Missing preset**

Run:

> "Draw an ERD using my `nonexistent` style."

Expected:
- Agent does **not** silently fall back.
- Reply lists the available presets (user dir + built-ins) and asks the user to pick one.

- [ ] **Step 7: Scenario 7 — Sparse preset**

Hand-author `~/.drawio-skill/styles/sparse.json` with only `primary` and `success` populated (the other 5 palette slots set to `null`). Run:

> "Draw a diagram with a client, an API gateway, a queue, a database, and an error sink, using my `sparse` style."

Expected:
- All 5 shapes use only the two populated colors (rotating between `primary` and `success` per the fallback ladder).
- No color from the built-in palette appears.

- [ ] **Step 8: Scenario 8 — Built-in shadowing**

Save a user preset named `corporate` (e.g., copy `styles/built-in/corporate.json` to `~/.drawio-skill/styles/corporate.json` and change `palette.primary.fillColor` to a distinct value like `#FF00FF`). Run:

> "Draw a two-service architecture using my `corporate` style."

Expected:
- The purple `#FF00FF` color appears in the output (user preset won).
- Reply mentions the preset source is "user" not "built-in".

- [ ] **Step 9: Scenario 9 — Diagram-type layering**

Ensure `demo-xml` is saved (from scenario 1). Run:

> "Draw an ERD with `users`, `orders`, and `products` tables, using my `demo-xml` style."

Expected:
- Tables render as drawio ERD tables (structural keywords from the ERD preset preserved — `shape=table;startSize=30;container=1;childLayout=tableLayout`).
- Fill colors come from the `demo-xml` preset.
- The `demo-xml` font is applied.

- [ ] **Step 10: Record results**

If all nine pass, commit a simple verification note:

```bash
# Create a tiny verification log
cat > docs/superpowers/specs/2026-04-23-custom-styles-verification.md <<'EOF'
# Custom Styles — Verification Log

**Date:** <today>
**Implementer:** <name>

| # | Scenario | Result |
|---|---|---|
| 1 | XML learn round-trip | PASS |
| 2 | Image learn round-trip | PASS |
| 3 | Apply (explicit) | PASS |
| 4 | Default fallback | PASS |
| 5 | No preset active | PASS |
| 6 | Missing preset | PASS |
| 7 | Sparse preset | PASS |
| 8 | Built-in shadowing | PASS |
| 9 | Diagram-type layering | PASS |

All scenarios from the spec's verification checklist pass.
EOF

git add docs/superpowers/specs/2026-04-23-custom-styles-verification.md
git commit -m "docs: verification log for custom-styles implementation"
```

If any scenario fails, do not commit a PASS log — instead, open a sub-task to fix the failing scenario, re-run, then write the log.

---

## Scope fences (from spec)

These are explicit non-goals for this plan. Do not add tasks for them:
- Preset versioning / migration UI.
- Style diffing.
- Automatic/implicit style detection during generation.
- Web UI.
- Sharing/export format beyond the JSON file.
- Slash commands for preset operations.
