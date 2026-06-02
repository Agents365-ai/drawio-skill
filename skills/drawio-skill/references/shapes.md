# Shape vocabulary & search

Read this when a diagram needs a **specific shape** — a cloud-provider icon
(AWS/Azure/GCP), a network/Cisco/Kubernetes symbol, a UML/BPMN/ER element, an
electrical or P&ID part — or any time you'd otherwise *guess* a `style=` string.

There are two ways to get a style:

1. **Search the official shape index** (`scripts/shapesearch.py`) — 10,446 real
   draw.io palette shapes with their exact `style`, `w`, `h`. Use this for
   branded/vendor icons and anything non-trivial. **Always prefer a searched
   style over a hand-written `shape=mxgraph.*` guess** — guessed stencil names
   silently render as a blank box if the name is wrong.
2. **The cheatsheet below** — the common built-in shapes whose style strings are
   short and stable enough to write by hand (rectangles, flowchart symbols,
   UML primitives, containers, edges).

## Searching shapes

```bash
python3 <this-skill-dir>/scripts/shapesearch.py "aws lambda" --limit 5
python3 <this-skill-dir>/scripts/shapesearch.py "uml actor" --json
```

- Query is space-separated keywords; matching is tag-based with Soundex
  fuzziness and `camelCase`/`digit` splitting (`"pid2valve"` → `pid valve`).
- Prints each match as `Title (WxH)` followed by its full `style=` string. With
  `--json`, emits `[{style,w,h,title}]` for programmatic use.
- Copy the `style` verbatim into an `mxCell`, and use the reported `w`/`h` as the
  `mxGeometry` width/height (vendor icons are drawn at a fixed aspect ratio).

```xml
<mxCell id="2" value="Lambda" style="<paste the searched style here>" vertex="1" parent="1">
  <mxGeometry x="40" y="40" width="78" height="78" as="geometry"/>
</mxCell>
```

Covered libraries: AWS (`aws3`/`aws4`), Azure, GCP, Cisco, Kubernetes, UML,
BPMN, ER, electrical, P&ID, mockup/wireframe, flowchart, network, and the
general/basic sets. The bundled index (`data/shape-index.json.gz`) is the
upstream draw.io shape data — see `data/SHAPE-INDEX-NOTICE.md` for attribution.

## Cheatsheet — hand-writable styles

These are stable enough to write without searching. Combine with `whiteSpace=wrap;html=1;`.

### Common shapes (`shape=` keyword)

| Need | style |
|---|---|
| Rectangle / rounded box | `rounded=0;` / `rounded=1;` |
| Circle / ellipse | `ellipse;` (`aspect=fixed;` for a true circle) |
| Diamond (decision) | `rhombus;` |
| Cylinder (database) | `shape=cylinder3;` |
| Cloud | `cloud;` |
| Cube (3D) | `shape=cube;` |
| Sticky note | `shape=note;` |
| Document (curled bottom) | `shape=document;` |
| Folder | `shape=folder;` |
| Card (cut corner) | `shape=card;` |
| Process (double border) | `shape=process;` |
| Step / chevron | `shape=step;` |
| Parallelogram (I/O) | `shape=parallelogram;perimeter=parallelogramPerimeter;` |
| Trapezoid | `shape=trapezoid;perimeter=trapezoidPerimeter;` |
| Hexagon | `shape=hexagon;perimeter=hexagonPerimeter2;` |
| Manual input | `shape=manualInput;` |
| Data storage | `shape=dataStorage;` |
| Off-page connector | `shape=offPageConnector;` |
| Delay | `shape=delay;` |
| OR / XOR gate | `shape=or;` / `shape=xor;` |
| Block arrow | `shape=singleArrow;` / `shape=doubleArrow;` |
| Callout (speech bubble) | `shape=callout;` |

### UML primitives

| Element | style |
|---|---|
| Actor (stick figure) | `shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;` |
| Boundary | `shape=umlBoundary;` |
| Control | `shape=umlControl;` |
| Entity | `shape=umlEntity;` |
| Lifeline | `shape=umlLifeline;perimeter=lifelinePerimeter;container=1;` |
| Frame | `shape=umlFrame;` |
| Provided interface (lollipop) | `shape=lollipop;direction=south;` |
| Required interface | `shape=requires;direction=north;` |
| Component | `shape=component;` |

### Containers (parent-child; children use relative coords)

| Type | style | When |
|---|---|---|
| Invisible group | `group;pointerEvents=0;` | No border, no own connections |
| Titled swimlane | `swimlane;startSize=30;` | Visible title bar / has connections |
| Any shape as container | append `container=1;pointerEvents=0;` | Box without own connections |

### Edges

| Need | add to style |
|---|---|
| Orthogonal routing | `edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;` |
| Curved | `curved=1;` |
| No arrowhead | `endArrow=none;` |
| Open/thin arrow | `endArrow=open;` / `endArrow=classicThin;` |
| Dashed | `dashed=1;` (pattern via `dashPattern=8 8;`) |
| Flow animation | `flowAnimation=1;` |
| Label background | `labelBackgroundColor=#ffffff;` |

### Useful property knobs

- `fontStyle` is a bitmask: `1`=bold, `2`=italic, `4`=underline (add to combine: `3`=bold+italic).
- `direction=north|south|east|west` rotates a shape in 90° steps; `rotation=<deg>` for free rotation.
- `gradientColor=#RRGGBB;` + `gradientDirection=north;` for a gradient fill.
- `sketch=1;` gives a hand-drawn look (set globally via a style preset instead when possible).

For richer per-shape detail, the upstream source is jgraph/drawio-mcp's
`shared/style-reference.md` (Apache-2.0).
