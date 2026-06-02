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
- If `extras.sketch=true`, append `;sketch=1` to every vertex style AND every edge style.
- If `extras.globalStrokeWidth !== 1` (i.e., any value other than the drawio default of 1, including `0.5`), append `;strokeWidth=<n>` to every vertex style AND every edge style.

The edge style is built as:
`<edges.style>;<edges.arrow>`
- Per-edge routing keys (`exitX/entryX/...`) are added as literals below.
- Edge 15 exercises `edges.dashedFor`:
  - If `edges.dashedFor` is **non-empty**, use its first entry as the edge's `value` (label) AND append `;dashed=1` to the edge style.
  - If `edges.dashedFor` is empty (`[]`), use the label `cross-call` and do NOT append `;dashed=1` — the preset has no dashed convention, so the sample must not fake one.

**Placeholder expansion (applied when filling the XML):**
- `{{VSTYLE:<role>}}` expands to the vertex-style formula above with `R = <role>`. Write the result as a literal string; do not URL-encode.
- `{{ESTYLE}}` expands to the edge-style formula above.
- `{{EDGE15_LABEL}}` and `{{EDGE15_DASH}}` follow the Edge-15 rule above.

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
        <mxCell id="15" value="{{EDGE15_LABEL}}" style="{{ESTYLE}}{{EDGE15_DASH}};exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0" edge="1" parent="1" source="4" target="8">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

### Rendering the sample

1. Write the filled XML to `/tmp/drawio-preset-<name>.drawio`.
2. Run the same `drawio -x -f png -e -s 2 -o <preset-name>-sample.png <tmp>.drawio` command the main workflow uses (substitute the binary name you resolved in SKILL.md Step 1 if it isn't `drawio`).
3. Repair the IEND chunk: `python3 <this-skill-dir>/scripts/repair_png.py <preset-name>-sample.png` — the `-e` flag truncates the PNG the same way the main workflow's step 7 does, so the sample needs the same fix to be readable.
4. Save the PNG as `./preset-<name>-sample.png` (the user's working directory).
5. Show the user: preset summary table + PNG path + provenance/confidence line.

### Approval loop

- "save" / "looks good" → write candidate to `~/.drawio-skill/styles/<name>.json`; delete tempfile and sample PNG.
- "change <field> to <value>" → edit the in-memory candidate; re-render; re-ask.
- "cancel" → delete tempfile and sample PNG; no save.

### If sample render fails (draw.io CLI missing / export error)

Still show the summary table and the provenance line. Note: *"Could not render sample PNG (CLI unavailable). Save anyway on your OK."* Do not block.

## XML extraction path

Input: a `.drawio` file path. Output: candidate preset JSON. Deterministic, no LLM inference.

### Steps

1. **Parse the file.** Read the XML, collect every `<mxCell>` with a `style=` attribute, split into vertices (`vertex="1"`) and edges (`edge="1"`).
2. **Tokenize each `style=` string** on `;`. Each element is either `key=value` or a bare keyword (e.g., `rhombus`, `ellipse`, `rounded=1`).
3. **Extract palette.** For every vertex, take the `(fillColor, strokeColor)` pair (skip vertices with neither). Count frequency. Keep the top ≤7 pairs.
4. **Extract shape vocabulary + role mapping.** For each vertex determine a shape class by precedence:
   `cylinder3 > ellipse > rhombus > swimlane > rounded=1 > rounded=0`.
   Then infer the semantic role from the vertex's shape class and its `value` (label) attribute. **Evaluate the rules below in order; first match wins.**
   - `cylinder3` → `database`
   - `rhombus` → `decision`
   - `swimlane` → `container`
   - `dashed=1` present + **grey-family fill** (hex where the R, G, and B channels all fall within ±16 of each other, i.e., near-achromatic) → `external`
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

   Record the shape class string used per role in `shapes[role]`. The six named shape keys are `service`, `database`, `queue`, `decision`, `external`, `container` — `gateway`, `error`, and `security` roles inherit `shapes.service` and do not get their own `shapes[...]` entry. Example: `shapes.database = "shape=cylinder3"`.

5. **Extract fonts.** Compute modal `fontFamily` and `fontSize` across vertices; emit them as `font.fontFamily` and `font.fontSize`. Also track `fontStyle` per vertex as a **working variable** (not an output field — the schema has no top-level `font.fontStyle`). If a distinguishable subset of vertices uses a larger `fontSize` combined with `fontStyle=1` (bold), treat that subset as titles: set `font.titleFontSize` to their modal size and `font.titleBold: true`. Otherwise omit both title fields.

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
| Non-standard `shape=` keywords (e.g., `shape=mxgraph.aws4.*`) | These do not match the Step 4 precedence ladder, so the vertex falls through to `rounded=0` for shape-class purposes. Iconography is lost; color, label, and edge style are still captured. Role inference still runs via the label-regex rules. Summary notes: *"Non-standard shape library detected — iconography not preserved in preset (color and label captured)."* |
| Non-English labels | The English-keyword regexes in step 4 will mostly miss; most vertices collapse to `service`. Palette/shapes/font/edges still captured correctly (they don't depend on label text). `confidence` stays `"high"`. Summary notes: *"Role labels not in English — `service`/`database`/`decision`/`container`/`external` inferred from shape class; other roles not mapped."* |
| File has no `<mxCell vertex="1">` at all | Stop. Refuse to save. Message: *"Nothing to learn from — source file has no shapes."* |

## Image extraction path

Input: path to a PNG/JPG (or any vision-readable image format). Output: candidate preset JSON. Inference-based; `confidence: "medium"` at best.

**Prerequisite:** the agent's vision capability must be available (same mechanism the main workflow's self-check uses). If vision is not available, stop and tell the user:
*"Image-based learning needs a vision-enabled model (Claude Sonnet or Opus). Re-run on such a model, or provide the `.drawio` source file instead."*

### Steps

1. **Read the image.** Use the agent's vision input — the same path the main workflow's step 5 uses to read exported PNGs during self-check.

2. **Extract palette by visual inspection.** Identify distinct fill-color regions on shape bodies.

   For each distinct fill:
   - `fillColor` — quantize each RGB channel to the nearest multiple of 16. If the resulting HSL lightness is below 0.75, raise it to 0.85 (keep hue and saturation; set L=0.85; HSL→RGB round-trip). Emit as `#RRGGBB`. Drawio-standard pastels occupy L≈0.85–0.96; below 0.75 reads as "too dark for a fill color" and this step lifts it back into that range.
   - `strokeColor` — read the matching border. If unreadable, derive from fill by darkening ~25% (match HSL, drop L by 0.25).

   Map each `(fillColor, strokeColor)` pair to a named slot using this decision order:

   1. **Grey check first.** If the fill has R, G, and B channels all within ±16 of each other (same definition as the XML path's grey-family rule), OR HSL saturation < 0.20, classify as `neutral`. This check wins regardless of hue angle.
   2. **Hue band otherwise.** Use these explicit HSL hue ranges:
      - 180°–260° → `primary` (blue)
      - 80°–170° → `success` (green)
      - 45°–65° → `warning` (yellow)
      - 20°–44° → `accent` (orange)
      - 0°–19° or 320°–360° → `danger` (red/pink)
      - 260°–320° → `secondary` (purple)
   3. **No band matched** (gap regions at 65°–80° or 170°–180°) → spill to the nearest band by angular distance.

   **Collision rule.** If ≥2 distinct fills land in the same slot, sort them by total pixel area covered in the image (descending). The largest keeps the canonical slot. Remaining fills spill to the **nearest empty slot** measured by hue-band angular distance — first to adjacent bands on either side, then farther out. If every slot is already filled, drop the extras and warn in the summary.

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
   - Image path stays at `"medium"` by default. The only path to `"high"` is a strictly-verifiable signal: the source image was exported from drawio itself (recognizable drawio default chrome, grid, or a visible drawio watermark), **and** all seven palette slots are filled, **and** all seven roles are labeled. This preserves the semantic gap between inference-based (image) and parse-based (XML) provenance.

### Image edge cases

| Situation | Behavior |
|---|---|
| Vision unavailable | Stop as described above — do not fall back to guessing. |
| Image has <3 identifiable shapes | Continue; mark `confidence: "low"`; summary explicitly warns the user that the preset is a loose approximation. |
| Image has no visible labels | Role assignment collapses to shape-class only: cylinders → `database`, diamonds → `decision`, swimlanes → `container`, dashed-bordered rectangles with grey fill → `external`, everything else → `service`. Palette/font/edges still captured. Summary notes: *"No labels readable — semantic roles beyond shape-class not inferred."* |
| Two palette slots would land in the same hue family | Keep the more frequent one in its canonical slot; spill the other to the adjacent empty slot (rule in step 2). |
| Image has more than 7 distinct fills | Keep the 7 most area-covering fills per the Step 2 collision rule. Summary warns that some colors were dropped. |
