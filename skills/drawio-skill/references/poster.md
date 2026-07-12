# Poster mode — page-exact academic posters

Read this when the user asks for an academic/conference poster (48x36, A0, custom size) or when `poster.py` / `posterqa.py` is in play.

## Page math (empirically pinned, drawio desktop 26.x)

- The PDF exporter maps model px to PDF pt at **0.72 pt/px** and honors `pageWidth`/`pageHeight` exactly with plain `-x -f pdf` (no flags).
- 48x36 in at 100 px/in → `pageWidth="4800" pageHeight="3600"` → PDF page **3456 x 2592 pt exactly** (= 48x36 in at 72 pt/in).
- **Do not pass `--crop`** for posters: it crops to the content bbox + ~1 px border (e.g. 3456.96x2592.96 pt) — off-spec for print.
- **Overflow is silent**: any cell outside the page rect makes the export **tile onto extra PDF pages** (a one-cell overflow turns a poster into a 4-page PDF). `posterqa.py` fails on `Pages != 1` for exactly this reason.

## Workflow

1. Write a config JSON (start from `examples/poster-demo.json`; full knob reference in the `poster.py` docstring).
2. Generate the skeleton: `python3 <this-skill-dir>/scripts/poster.py config.json -o poster.drawio` (writes `poster.theme.json` sidecar too).
3. Fill section bodies: each `c<COL>s<ROW>-body` cell is a `group` — children set `parent="c1s1-body"` and use coordinates **relative to the group**. Same for `fw-slot<N>` framework slots.
4. Export: `drawio -x -f pdf -o poster.pdf poster.drawio`.
5. Gate: `python3 <this-skill-dir>/scripts/posterqa.py poster.drawio --pdf poster.pdf --preview preview.png`, then vision-read `preview.png` (never the `-e` variant).
6. Rebrand later: `python3 <this-skill-dir>/scripts/retheme.py poster.drawio --to "#NEWBRAND"`.

## Font floors (viewing-distance, 100 px/in; 1 px = 0.72 pt)

| Role | Floor px | ≈ pt |
|---|---|---|
| title | 100 | 72 |
| section header | 64 | 46 |
| body | 33 | 24 |
| caption | 25 | 18 |

`poster.py` warns at generation; `posterqa.py` hard-fails any text cell below `--min-font` (default 25 px) and warns per-class on poster ids. Always put `fontSize` in the **cell style**, not only inside an HTML span — draw.io vertically centers using the style value (span-only sizes sag low).

## Icons and theme in posters

- Section headers take a concept icon: config `"icon": "<phosphor-name>"` (fetched + baked in brand ink) or a pre-built `"icon_style": "<style>"` from `concepticons.py`. `--no-icons` (or offline) emits dashed placeholder slots — generation never blocks on network.
- All colors flow from the theme (see `theme.py`); the sidecar keeps the poster re-themeable in one command.
- Preview for vision QA: `--width 2000`, no `-e` (the 2576px vision ceiling and the `-e` zTXt 400 both apply to posters like any diagram).
- When comparing a render against a reference image, autocrop both to content bbox first — the export's white canvas margin otherwise reads as fake vertical drift.
