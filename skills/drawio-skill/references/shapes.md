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
- Results are ranked by tag relevance, with shapes whose **title** contains the
  query terms bubbled to the top of each score tier. Ranking is still a
  heuristic, though, and many shapes share a title (three `Lambda` variants:
  `aws3`/`aws4`/`aws3d`) — so run with `--limit 5` and pick the row whose title
  and size match what you actually want rather than blindly taking #1.

```xml
<mxCell id="2" value="Lambda" style="<paste the searched style here>" vertex="1" parent="1">
  <mxGeometry x="40" y="40" width="78" height="78" as="geometry"/>
</mxCell>
```

Covered libraries: AWS (`aws3`/`aws4`), Azure, GCP, Cisco, Kubernetes, UML,
BPMN, ER, electrical, P&ID, mockup/wireframe, flowchart, network, and the
general/basic sets. The bundled index (`data/shape-index.json.gz`) is the
upstream draw.io shape data — see `data/SHAPE-INDEX-NOTICE.md` for attribution.

## AI / LLM brand logos

draw.io's bundled libraries have **no** modern AI/LLM brand logos, so an "LLM app
architecture" otherwise renders as generic boxes. `scripts/aiicons.py` resolves a
brand name (OpenAI, Claude, Gemini, Mistral, Llama, HuggingFace, Ollama,
LangChain, …321 brands) to a draw.io `image` style backed by the
[lobe-icons](https://github.com/lobehub/lobe-icons) set (MIT).

```bash
python3 <this-skill-dir>/scripts/aiicons.py "claude" --json        # CDN reference
python3 <this-skill-dir>/scripts/aiicons.py "openai" --embed        # self-contained
python3 <this-skill-dir>/scripts/aiicons.py --list                  # all brands
```

- Picks the `-color` variant when it exists, else the mono logo (e.g. OpenAI is
  mono-only). Returns a square `image` style; use the reported `--size` (default
  48) for both width and height.
- **Default references the icon by CDN URL** — the SVG lives on unpkg, not in
  this repo, so **draw.io needs network access when the diagram is rendered or
  opened**; an offline export draws a blank box. Pass `--embed` to fetch the SVG
  once and inline it as a data URI (portable, renders offline, larger XML).
- Logos are trademarks of their respective owners, referenced for identification
  only — the same basis on which draw.io ships AWS/Azure icons.
- **Data stores** common in RAG/LLM apps that lobe lacks (Qdrant, Redis,
  Postgres, Mongo, Elasticsearch, Milvus, Supabase, Neo4j, ClickHouse, Kafka,
  Snowflake, Databricks, …) resolve via the [simple-icons](https://simpleicons.org)
  CDN (CC0) as an automatic fallback — same command, same output shape. A brand
  in neither set has no logo; use a cylinder (`shape=cylinder3;`, see below) or
  `scripts/shapesearch.py "<name> database"`.

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
