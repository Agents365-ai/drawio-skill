---
name: drawio
description: Use when user requests diagrams, flowcharts, architecture charts, or visualizations. Also use proactively when explaining systems with 3+ components, complex data flows, or relationships that benefit from visual representation. Generates .drawio XML files and exports to PNG/SVG/PDF locally using the native draw.io desktop CLI.
---

# Draw.io Diagrams

## Overview

Generate `.drawio` XML files and export to PNG/SVG/PDF/JPG locally using the native draw.io desktop app CLI.

**Supported formats:** PNG, SVG, PDF, JPG — no browser automation needed.

## When to Use

**Explicit triggers:** user says "画图", "diagram", "visualize", "flowchart", "draw", "架构图", "流程图"

**Proactive triggers:**
- Explaining a system with 3+ interacting components
- Describing a multi-step process or decision tree
- Comparing architectures or approaches side by side

**Skip when:** a simple list or table suffices, or user is in a quick Q&A flow

## Prerequisites

The draw.io desktop app must be installed and the CLI accessible:

```bash
# macOS (Homebrew — recommended)
brew install --cask drawio
draw.io --version

# macOS (full path if not in PATH)
/Applications/draw.io.app/Contents/MacOS/draw.io --version

# Windows
"C:\Program Files\draw.io\draw.io.exe" --version

# Linux
draw.io --version
```

Install draw.io desktop if missing:
- macOS: `brew install --cask drawio` or download from https://github.com/jgraph/drawio-desktop/releases
- Windows: download installer from https://github.com/jgraph/drawio-desktop/releases
- Linux: download `.deb`/`.rpm` from https://github.com/jgraph/drawio-desktop/releases

## Workflow

1. **Check deps** — verify `draw.io --version` succeeds; note platform for correct CLI path
2. **Plan** — identify shapes, relationships, layout (LR or TB), group by tier/layer
3. **Generate** — write `.drawio` XML file to disk (output dir same as user's working dir)
4. **Export** — run CLI to produce PNG, SVG, or PDF
5. **Report** — tell user the output file paths (source + image)

## Draw.io XML Structure

### File skeleton

```xml
<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="drawio" version="26.0.0">
  <diagram name="Page-1">
    <mxGraphModel>
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <!-- user shapes start at id="2" -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

**Rules:**
- `id="0"` and `id="1"` are required root cells — never omit them
- User shapes start at `id="2"` and increment sequentially
- All shapes have `parent="1"`
- All text uses `html=1` in style for proper rendering

### Shape types (vertex)

| Style keyword | Use for |
|--------------|---------|
| `rounded=0` | plain rectangle (default) |
| `rounded=1` | rounded rectangle — services, modules |
| `ellipse;` | circles/ovals — start/end, databases |
| `rhombus;` | diamond — decision points |
| `shape=mxgraph.aws4.resourceIcon;` | AWS icons |
| `shape=cylinder3;` | cylinder — databases |
| `swimlane;` | group/container with title bar |

### Required properties

```xml
<!-- Rectangle / rounded box -->
<mxCell id="2" value="Label" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="160" height="60" as="geometry" />
</mxCell>

<!-- Cylinder (database) -->
<mxCell id="3" value="DB" style="shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontColor=#333333;" vertex="1" parent="1">
  <mxGeometry x="350" y="100" width="120" height="80" as="geometry" />
</mxCell>

<!-- Diamond (decision) -->
<mxCell id="4" value="Check?" style="rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;" vertex="1" parent="1">
  <mxGeometry x="100" y="220" width="160" height="80" as="geometry" />
</mxCell>
```

### Connector (edge)

```xml
<!-- Directed arrow between shapes -->
<mxCell id="10" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;" edge="1" parent="1" source="2" target="3">
  <mxGeometry relative="1" as="geometry" />
</mxCell>

<!-- Arrow with label -->
<mxCell id="11" value="HTTP/REST" style="edgeStyle=orthogonalEdgeStyle;html=1;" edge="1" parent="1" source="2" target="4">
  <mxGeometry relative="1" as="geometry" />
</mxCell>
```

### Color palette (fillColor / strokeColor)

| Color name | fillColor | strokeColor | Use for |
|-----------|-----------|-------------|---------|
| Blue | `#dae8fc` | `#6c8ebf` | services, clients |
| Green | `#d5e8d4` | `#82b366` | success, databases |
| Yellow | `#fff2cc` | `#d6b656` | queues, decisions |
| Orange | `#ffe6cc` | `#d79b00` | gateways, APIs |
| Red/Pink | `#f8cecc` | `#b85450` | errors, alerts |
| Grey | `#f5f5f5` | `#666666` | external/neutral |
| Purple | `#e1d5e7` | `#9673a6` | security, auth |

### Layout tips

- Allocate ~200px per node horizontally, ~150px vertically to avoid overlaps
- Plan a grid before assigning x/y coordinates
- Group related nodes in the same horizontal or vertical band
- Use `swimlane` cells for logical grouping with visible borders

## Export

### Commands

```bash
# macOS — Homebrew (draw.io in PATH)
draw.io -x -f png -s 2 -o diagram.png input.drawio

# macOS — full path (if not in PATH)
/Applications/draw.io.app/Contents/MacOS/draw.io -x -f png -s 2 -o diagram.png input.drawio

# Windows
"C:\Program Files\draw.io\draw.io.exe" -x -f png -s 2 -o diagram.png input.drawio

# Linux (headless — requires xvfb-run)
xvfb-run -a draw.io -x -f png -s 2 -o diagram.png input.drawio

# SVG export
draw.io -x -f svg -o diagram.svg input.drawio

# PDF export
draw.io -x -f pdf -o diagram.pdf input.drawio
```

**Key flags:**
- `-x` — export mode (required)
- `-f` — format: `png`, `svg`, `pdf`, `jpg`
- `-s` — scale: `1`, `2`, `3` (2 recommended for PNG)
- `-o` — output file path
- `--page-index 0` — export specific page (default: all)

### Checking if draw.io is in PATH

```bash
# Try short command first
if command -v draw.io &>/dev/null; then
  DRAWIO="draw.io"
elif [ -f "/Applications/draw.io.app/Contents/MacOS/draw.io" ]; then
  DRAWIO="/Applications/draw.io.app/Contents/MacOS/draw.io"
else
  echo "draw.io not found — install from https://github.com/jgraph/drawio-desktop/releases"
fi
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Missing `id="0"` and `id="1"` root cells | Always include both at the top of `<root>` |
| Shapes not connected | `source` and `target` on edge must match existing shape `id` values |
| Export command not found on macOS | Try full path `/Applications/draw.io.app/Contents/MacOS/draw.io` |
| Linux: blank/error output headlessly | Prefix command with `xvfb-run -a` |
| PDF export fails | Ensure Chromium is available (draw.io bundles it on desktop) |
| Background color wrong in CLI export | Known CLI bug; add `--transparent` flag or set background via style |
| Overlapping shapes | Plan a 200px grid before placing x/y coordinates |
| Special characters in `value` | Use XML entities: `&amp;` `&lt;` `&gt;` `&quot;` |
