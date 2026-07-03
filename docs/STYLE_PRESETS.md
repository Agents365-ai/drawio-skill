# Style Presets

[中文](STYLE_PRESETS_CN.md)

Style presets let you capture and reuse a visual style across diagrams. When a preset is active, it replaces the built-in color palette, shape vocabulary, fonts, and edge defaults.

## Built-in presets

| Name | Description |
|------|-------------|
| `default` | Clean blue/green/yellow palette matching the built-in conventions |
| `corporate` | Muted, professional palette suited for business presentations |
| `handdrawn` | Sketch-style strokes for informal or whiteboard-style diagrams |
| `colorblind-safe` | Okabe-Ito palette — all seven roles distinguishable under color-vision deficiency; thicker strokes |
| `dark` | Dark fills + dark page background, light strokes/text — for dark-mode docs and slides |

## Apply a preset to a diagram

```
Draw a microservices architecture using my "corporate" style
```

Or set a default so all future diagrams use it automatically:

```
Make "corporate" my default style
```

## Learn your style from a file

Point the skill at any `.drawio` file or flat image:

```
Learn my style from ~/diagrams/brand.drawio as "mybrand"
Learn my style from ~/diagrams/screenshot.png as "mybrand"
```

The skill extracts colors, shapes, fonts, and edge style, renders a sample diagram for preview, and saves to `~/.drawio-skill/styles/mybrand.json` only after you approve.

## Manage presets

| What you say | What happens |
|---|---|
| "list my styles" | Shows all user and built-in presets in a table |
| "show my `<name>` style" | Pretty-prints the preset JSON |
| "make `<name>` the default" | Sets it as the active default for all diagrams |
| "remove default" | Clears the default (reverts to built-in conventions) |
| "delete `<name>`" | Deletes the user preset (prompts for confirmation) |
| "rename `<a>` to `<b>`" | Renames a user preset |
