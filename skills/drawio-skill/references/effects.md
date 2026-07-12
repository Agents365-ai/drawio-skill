# Effects — soft shadows and theme tokens

## Soft shadows (academic, subtle)

draw.io's native `shadow=1` is a hard grey offset — dated for publication work, and its
appearance is not tunable from the style string. This skill synthesizes soft shadows
deterministically instead: 2-3 stacked backing cells behind the card (same rounded
geometry, black fill, no stroke, opacity ~6/4/2, offsets growing per layer), which
renders identically in PNG/SVG/PDF export and needs no Electron/CSS support.

- Generator use: `poster.py` emits them automatically for cards/bands.
- Hand-authored diagrams: `python3 scripts/theme.py shadow --style soft --canvas 1600 --x 100 --y 200 --w 400 --h 150 --rx 12` prints the backing cells — paste them **before** the card cell (draw.io paints in document order), keep `--rx` equal to the card's `arcSize`.
- `--canvas` scales offsets linearly (reference 1600 px): a 4800 px poster gets 3x offsets so shadows stay proportionate.
- Styles: `soft` (3 layers) and `softer` (2 layers, fainter).

When NOT to shadow: dense many-node diagrams (visual noise), diagrams destined for
small-size print (shadow bands fall below print resolution), or any diagram where the
style preset carries `sketch=1` (hand-drawn look + drop shadow reads wrong).

## Theme tokens (one-hex rebrand)

draw.io style strings hold literal hex — there are no runtime variables — so theming is
generation-time plus a deterministic remap:

1. `theme.py derive "#BRAND" --name myname [--override deep=... tint=... ink=... gray=... hair=...]`
   writes a schema-valid preset (`myname.json`, usable by the normal Step-0 preset flow)
   plus an extended theme file (`myname.theme.json`) carrying tokens the preset schema
   has no slot for: `ink` (text), `hair` (hairlines), `deep` (emphasis).
2. Generators write a per-file sidecar (`<figure>.theme.json`) mapping the file's colors.
3. `retheme.py <figure>.drawio --to "#NEWBRAND"` swaps every occurrence — style attributes,
   HTML label spans (`color:#hex` inside `value` overrides cell `fontColor`; the swap covers
   both), and url-encoded SVG data-URIs (where `#` is spelled `%23`) — then rewrites the
   sidecar so the file stays re-themeable. `--dry-run` prints the swap table first.
