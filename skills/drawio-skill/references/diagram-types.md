# Diagram Type Presets

When the user requests a specific diagram type, apply the matching preset below for shapes, styles, and layout conventions. These presets set **structural** style keywords (e.g. ERD's `shape=table;childLayout=tableLayout`); a user style preset (see `references/style-presets.md`) layers color/font/edge/extras on top.

Read this file when:
- The user names one of these diagram types (ERD, UML class, sequence, C4, architecture, ML/DL model, flowchart, SysML)
- You're choosing shape vocabulary or layout direction for a new diagram

## ERD (Entity-Relationship Diagram)

**From SQL DDL, don't hand-build**: `python3 scripts/sqlerd.py schema.sql -o graph.json` parses `CREATE TABLE` into per-table nodes (PK/FK-marked column lists) + crow's-foot FK edges for autolayout. Hand-build with the styles below when there's no DDL to parse.

| Element | Style | Notes |
|---------|-------|-------|
| Table | `shape=table;startSize=30;container=1;collapsible=1;childLayout=tableLayout;fixedRows=1;rowLines=0;fontStyle=1;strokeColor=#6c8ebf;fillColor=#dae8fc;` | Each table is a container |
| Row (column) | `shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;collapsible=0;dropTarget=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontSize=12;` | Child of table, `parent=tableId` |
| PK column | Bold text: `fontStyle=1` on the row | Mark with `PK` prefix or key icon |
| FK relationship | Dashed edge: `dashed=1;endArrow=ERmandOne;startArrow=ERmandOne;` | Use ER notation arrows |
| Layout | TB, tables spaced 300px apart | Group related tables vertically |

## UML Class Diagram

| Element | Style | Notes |
|---------|-------|-------|
| Class box | `swimlane;fontStyle=1;align=center;startSize=26;html=1;` | 3-section: title / attributes / methods |
| Separator | `line;strokeWidth=1;fillColor=none;align=left;verticalAlign=middle;spacingTop=-1;spacingLeft=3;spacingRight=10;rotatable=0;labelPosition=left;points=[];portConstraint=eastwest;` | Between sections |
| Inheritance | `endArrow=block;endFill=0;` | Hollow triangle arrow |
| Implementation | `endArrow=block;endFill=0;dashed=1;` | Dashed + hollow triangle |
| Composition | `endArrow=diamondThin;endFill=1;` | Filled diamond |
| Aggregation | `endArrow=diamondThin;endFill=0;` | Hollow diamond |
| Layout | TB, classes 250px apart | Interfaces above implementations |

## Sequence Diagram

**Don't hand-place sequence geometry** — `python3 scripts/seqlayout.py seq.json -o out.drawio` computes all lifeline/activation-bar/arrow coordinates deterministically from a participants + messages JSON (schema in the script docstring), using exactly the styles below. Hand-edit the output only for fragments (alt/loop frames), which are out of its scope.

| Element | Style | Notes |
|---------|-------|-------|
| Actor/Object | `shape=umlLifeline;perimeter=lifelinePerimeter;whiteSpace=wrap;html=1;container=1;collapsible=0;recursiveResize=0;outlineConnect=0;portConstraint=eastwest;` | Lifeline with dashed vertical line |
| Sync message | `html=1;verticalAlign=bottom;endArrow=block;` | Solid line, filled arrowhead |
| Async message | `html=1;verticalAlign=bottom;endArrow=open;dashed=1;` | Dashed line, open arrowhead |
| Return message | `html=1;verticalAlign=bottom;endArrow=open;dashed=1;strokeColor=#999999;` | Grey dashed |
| Activation box | `shape=umlFrame;whiteSpace=wrap;` on the lifeline | Narrow rectangle on lifeline |
| Layout | LR, lifelines spaced 200px apart | Time flows top to bottom |

## C4 Model (System Context / Container / Component)

**Don't hand-build** — `python3 scripts/c4.py c4.json -o out.drawio` generates the whole multi-page set (one page per level, drill-down links from parent elements to child pages, Graphviz placement; schema in the script docstring). The styles below are what it emits — for hand-tweaks afterwards:

| Element | Style | Notes |
|---------|-------|-------|
| Person | `shape=mxgraph.c4.person2;html=1;whiteSpace=wrap;fontColor=#ffffff;fillColor=#083F75;strokeColor=#06315C;` | Dark-blue person shape, 200×180 |
| Software System | `rounded=1;arcSize=10;html=1;whiteSpace=wrap;fontColor=#ffffff;fillColor=#1061B0;strokeColor=#0D5091;` | 240×120 |
| External System | same, `fillColor=#8C8496;strokeColor=#736782;` | Grey = outside your control |
| Container | same, `fillColor=#23A2D9;strokeColor=#0E7DAD;` | Mid-blue |
| Component | same, `fillColor=#63BEF2;strokeColor=#2086C9;` | Light-blue |
| Database | `shape=cylinder3;size=15;boundedLbl=1;` + Container colors | Cylinder |
| Relationship | `endArrow=blockThin;endFill=1;html=1;fontSize=11;fontColor=#404040;strokeColor=#828282;labelBackgroundColor=#ffffff;` | Grey thin arrow, label = protocol/action |
| Label format | `Name` ⏎ `[Type: Tech]` ⏎ `description` | The standard three-line C4 label |
| Drill-down | wrap the element in `<UserObject link="data:page/id,<pageId>">` | Click jumps to the child page in draw.io / viewer |
| Layout | TB, one `<diagram>` page per level | Export a single page with `--page-index <n>` (1-based) |

## Architecture Diagram

| Element | Style | Notes |
|---------|-------|-------|
| Layer/tier | `swimlane;startSize=30;` | Containers for grouping: Client / API / Service / Data |
| Service | `rounded=1;whiteSpace=wrap;html=1;` + tier color | Use color palette by tier |
| Database | `shape=cylinder3;whiteSpace=wrap;html=1;` | Green palette |
| Queue/Bus | `rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;` | Yellow — place centrally for hub pattern |
| Gateway/LB | `shape=mxgraph.aws4.resourceIcon;` or `rounded=1;` with orange | Orange palette |
| External | `rounded=1;dashed=1;fillColor=#f5f5f5;strokeColor=#666666;` | Dashed border for external systems |
| Layout | TB or LR by tier count; ≥4 tiers → TB | Hub nodes centered |

## ML / Deep Learning Model Diagram

For neural network architecture diagrams — ideal for papers targeting NeurIPS, ICML, ICLR.

| Element | Style | Notes |
|---------|-------|-------|
| Layer block | `rounded=1;whiteSpace=wrap;html=1;` + type color | Main building block |
| Input/Output | `fillColor=#d5e8d4;strokeColor=#82b366;` | Green |
| Conv / Pooling | `fillColor=#dae8fc;strokeColor=#6c8ebf;` | Blue |
| Attention / Transformer | `fillColor=#e1d5e7;strokeColor=#9673a6;` | Purple |
| RNN / LSTM / GRU | `fillColor=#fff2cc;strokeColor=#d6b656;` | Yellow |
| FC / Linear | `fillColor=#ffe6cc;strokeColor=#d79b00;` | Orange |
| Loss / Activation | `fillColor=#f8cecc;strokeColor=#b85450;` | Red/Pink |
| Skip connection | `dashed=1;endArrow=block;curved=1;` | Dashed curved arrow |
| Tensor shape label | Add shape annotation as secondary label: `value="Conv2D&#xa;(B, 64, 32, 32)"` | Use `&#xa;` for multi-line |
| Layout | TB (data flows top→bottom), layers 150px apart | Group encoder/decoder as swimlanes |

**Tensor shape convention:** annotate each layer with input/output tensor dimensions in `(B, C, H, W)` or `(B, T, D)` format. Place dimensions as the second line of the label using `&#xa;`.

## SysML (Block Definition / Internal Block / Requirement / Parametric)

draw.io ships a native SysML 1.x shape library (`mxgraph.sysml.*`, ~60 shapes) — run `python3 scripts/shapesearch.py "sysml <keyword>"` for any element not listed below. Stereotype labels use guillemets as the first label line: `&#171;block&#187;` (HTML entities for « »). SysML behavioral diagrams (activity, state machine, use case, sequence) reuse the UML presets above; search `shapesearch.py "sysml activity"` / `"sysml state"` for the SysML-specific variants.

### Block Definition Diagram (bdd)

| Element | Style | Notes |
|---------|-------|-------|
| Block | `swimlane;fontStyle=1;align=center;startSize=40;html=1;` | Label `&#171;block&#187;&#xa;Name`; compartments (values / parts / operations) like UML class |
| Compartment separator | same `line;...` style as UML Class | Between compartments |
| Composite association | `html=1;endArrow=none;startArrow=diamondThin;startFill=1;` | Filled diamond at the whole (owner) end |
| Reference association | `html=1;endArrow=none;startArrow=diamondThin;startFill=0;` | Hollow diamond |
| Generalization | `edgeStyle=none;html=1;endArrow=block;endFill=0;endSize=12;` | Hollow triangle pointing at the parent block |
| Multiplicity | edge labels `1`, `0..1`, `1..*` near the ends | Offset with edge label geometry |
| Layout | TB, whole block on top, part blocks below, 250px apart | Same convention as UML class |

### Internal Block Diagram (ibd)

| Element | Style | Notes |
|---------|-------|-------|
| Frame | `rounded=0;html=1;verticalAlign=top;align=left;spacingLeft=10;fontStyle=1;container=1;` | Label `ibd [block] Name`; parts are children |
| Part | `rounded=0;whiteSpace=wrap;html=1;` | Label `partName : BlockType` |
| Port | `html=1;shape=mxgraph.sysml.port;sysMLPortType=flowN;` 20×20 | Child of the part, relative geometry pinned to its border |
| Connector | `html=1;endArrow=none;` | Solid line port-to-port |
| Item flow direction | `shape=triangle;fillColor=strokeColor;` 10×10 on the connector + item label | Triangle points along the flow |

### Requirement Diagram (req)

| Element | Style | Notes |
|---------|-------|-------|
| Requirement | `swimlane;fontStyle=1;align=center;startSize=26;html=1;` | Title `&#171;requirement&#187;&#xa;Name`; body compartment `id="R1.1"&#xa;text="..."` |
| Containment | `edgeStyle=none;html=1;startArrow=sysMLPackCont;startSize=12;endArrow=none;` | Crosshair-circle at the parent end |
| deriveReqt / satisfy / verify / refine | `html=1;endArrow=open;endSize=12;dashed=1;` + edge label `&#171;satisfy&#187;` | Dashed open arrow pointing at the requirement |
| Trace | same dashed style, label `&#171;trace&#187;` | |
| Layout | TB, parent requirements above children, 200px apart | Satisfy/verify sources (blocks, test cases) at the bottom |

### Parametric Diagram (par)

| Element | Style | Notes |
|---------|-------|-------|
| Constraint block | `rounded=1;whiteSpace=wrap;html=1;` | Label `&#171;constraint&#187;&#xa;{F = m · a}` |
| Parameter port | `rounded=0;html=1;fontSize=10;` 20×20 on the border | Label = parameter name (`m`, `a`, `F`) |
| Binding connector | `html=1;endArrow=none;` | Solid, no arrows |
| Value property | `rounded=0;whiteSpace=wrap;html=1;` | Label `name : Type` |
| Layout | LR, value properties on the outside, constraints centered | |

## Flowchart (enhanced)

| Element | Style | Notes |
|---------|-------|-------|
| Start/End | `ellipse;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;` | Green oval |
| Process | `rounded=0;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;` | Blue rectangle |
| Decision | `rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;` | Yellow diamond |
| I/O | `shape=parallelogram;perimeter=parallelogramPerimeter;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;` | Orange parallelogram |
| Subprocess | `rounded=0;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;` + double border | Purple |
| Yes/No labels | `value="Yes"` / `value="No"` on decision edges | Always label decision branches |
| Layout | TB, 200px vertical gap | Decisions branch LR, merge back to center |
