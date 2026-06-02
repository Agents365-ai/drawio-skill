# drawio-skill — From Text to Professional Diagrams

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/Agents365-ai/drawio-skill?style=flat&logo=github)](https://github.com/Agents365-ai/drawio-skill/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/Agents365-ai/drawio-skill?style=flat&logo=github)](https://github.com/Agents365-ai/drawio-skill/network/members)
[![Latest Release](https://img.shields.io/github/v/release/Agents365-ai/drawio-skill?logo=github)](https://github.com/Agents365-ai/drawio-skill/releases/latest)
[![Last Commit](https://img.shields.io/github/last-commit/Agents365-ai/drawio-skill?logo=github)](https://github.com/Agents365-ai/drawio-skill/commits/main)

[![SkillsMP](https://img.shields.io/badge/SkillsMP-listed-1f6feb)](https://skillsmp.com/skills/agents365-ai-drawio-skill-skills-drawio-skill-skill-md)
[![ClawHub](https://img.shields.io/badge/ClawHub-listed-ff6b35)](https://clawhub.ai/agents365-ai/drawio-pro-skill)
[![Claude Code Plugin](https://img.shields.io/badge/Claude%20Code-plugin-8a2be2)](https://github.com/Agents365-ai/365-skills)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-compatible-2ea44f)](https://agentskills.io)
[![Discord](https://img.shields.io/badge/Discord-Join-5865F2?logo=discord&logoColor=white)](https://discord.gg/79JF5Atuk)

**English** · [中文](README_CN.md) · [📖 Online Docs](https://agents365-ai.github.io/drawio-skill/)

A skill that turns natural-language descriptions into `.drawio` XML and exports them to PNG / SVG / PDF / JPG via the native draw.io desktop CLI. It can also turn an **existing codebase** (Python / JS-TS / Go / Rust) into an auto-laid-out structure diagram. Works with **Claude Code, Cursor, Copilot, OpenClaw, Codex, Hermes**, and any agent compatible with the [Agent Skills](https://agentskills.io) format.

<p align="center">
  <img src="assets/microservices-example.png" width="900" alt="Microservices Architecture — generated from a single natural-language prompt">
</p>

## ✨ Highlights

- **6 diagram type presets** — ERD, UML Class, Sequence, Architecture, ML/Deep Learning, Flowchart
- **Visualize a codebase** — extract and auto-lay-out the structure of a Python / JS-TS / Go / Rust project (import graphs) or a Python class hierarchy — Graphviz placement, transitive reduction, nested module containers
- **Search 10,000+ official shapes** — resolve the exact AWS / Azure / GCP / Cisco / Kubernetes / UML / BPMN icon style instead of guessing (no more blank-box `shape=mxgraph.*` typos)
- **Self-check + auto-fix** — reads its own PNG output and auto-fixes overlaps, clipped labels, stacked edges, and more (up to 2 rounds)
- **Iterative feedback loop** — up to 5 rounds of targeted refinement
- **Style presets** — capture your visual style from a `.drawio` file or image, reuse on demand
- **Clean layout** — grid-aligned, spacing scales with diagram size, connectors routed clear of nodes
- **Multi-agent, zero-config** — runs from a single SKILL.md; no MCP server, no background daemon (the optional `npx` installer needs Node, the skill itself does not)

## 🖼️ Examples

> [!TIP]
> **The hero image above was generated from this single prompt:**

```
Create a microservices e-commerce architecture with Mobile/Web/Admin clients,
API Gateway (auth + rate limiting + routing), Auth/User/Order/Product/Payment
services, Kafka message queue, Notification service, and User DB / Order DB /
Product DB / Redis Cache / Stripe API
```

The skill is designed to route edges cleanly across different topologies, avoiding lines that cross through shapes:

<table>
  <tr>
    <td align="center" width="33%">
      <img src="assets/demo-star.png" alt="Star topology" width="100%"><br>
      <b>Star</b> · 7 nodes<br>
      <sub>Central message broker with 6 microservices radiating outward, no edge crossings on this example.</sub>
    </td>
    <td align="center" width="33%">
      <img src="assets/demo-layered.png" alt="Layered flow" width="100%"><br>
      <b>Layered</b> · 10 nodes / 4 tiers<br>
      <sub>E-commerce stack with horizontal and diagonal cross-connections routed via corridors.</sub>
    </td>
    <td align="center" width="33%">
      <img src="assets/demo-ring.png" alt="Ring cycle" width="100%"><br>
      <b>Ring</b> · 8 nodes<br>
      <sub>CI/CD pipeline with a closed loop and 2 spur branches flowing along the perimeter.</sub>
    </td>
  </tr>
</table>

Full walkthrough in [docs/USAGE.md](docs/USAGE.md).

## 🚀 Installation

### 1. Install the draw.io desktop CLI

| Platform | Command |
|----------|---------|
| **macOS** | `brew install --cask drawio` |
| **Windows** | [Download installer](https://github.com/jgraph/drawio-desktop/releases) |
| **Linux** | `.deb`/`.rpm` from [releases](https://github.com/jgraph/drawio-desktop/releases); `sudo apt install xvfb` for headless |

Verify with `drawio --version`. On **WSL2** the CLI is the Windows desktop exe reached via `/mnt/c` — the skill detects this automatically (see [troubleshooting](skills/drawio-skill/references/troubleshooting.md)). Full recipes in [docs/INSTALL_CLI.md](docs/INSTALL_CLI.md).

### 2. Install the skill

```bash
# Any agent (Claude Code, Cursor, Copilot, ...)
npx skills add Agents365-ai/365-skills -g
```

```text
# Claude Code plugin marketplace
> /plugin marketplace add Agents365-ai/365-skills
> /plugin install drawio
```

```bash
# Manual install
git clone https://github.com/Agents365-ai/drawio-skill.git \
  ~/.claude/skills/drawio-skill
```

Also indexed on [SkillsMP](https://skillsmp.com/skills/agents365-ai-drawio-skill-skills-drawio-skill-skill-md) and [ClawHub](https://clawhub.ai/agents365-ai/drawio-pro-skill).

**Updating:** `/plugin update drawio` (Claude Code), `skills update drawio-skill` (SkillsMP), `clawhub update drawio-pro-skill` (OpenClaw), or `git pull` for manual installs — see [docs/INSTALL_SKILL.md#updates](docs/INSTALL_SKILL.md#updates).

## ⚡ Quick Start

After installation, just describe what you want. For example, an ML model:

```
Draw a Transformer encoder-decoder for machine translation: 6-layer encoder
with self-attention, 6-layer decoder with cross-attention, input embeddings
(batch × 512 × 768), positional encoding, and a final output projection.
Annotate tensor shapes between layers and color-code by layer type.
```

The skill plans the layout, generates the `.drawio` XML, exports to your chosen format, self-checks the result, and lets you iterate.

## 🗺️ Visualize a Codebase

Beyond hand-authored diagrams, the skill turns **existing code into structure diagrams** — no manual coordinates. Just ask:

> *"Visualize the module structure of this Python project"* · *"Draw the class hierarchy of `mypackage`"*

<p align="center">
  <img src="assets/code-structure-example.png" width="900" alt="Auto-generated class hierarchy of Python's logging package — modules boxed, inheritance arrows resolved">
</p>

<sub>↑ Python's <code>logging</code> package as a class hierarchy — one command, modules auto-boxed, every inheritance edge resolved.</sub>

Under the hood it runs a bundled extractor → auto-layout → validate pipeline:

```bash
# Import graph — Python / JS-TS / Go / Rust
python3 scripts/pyimports.py   myproject --group -o graph.json
python3 scripts/jsimports.py   ./src     --group -o graph.json
python3 scripts/goimports.py   ./module  --group -o graph.json
python3 scripts/rustimports.py ./crate   --group -o graph.json

# Python class-inheritance hierarchy
python3 scripts/pyclasses.py   mypackage --group -o graph.json

# any extractor → auto-layout → editable .drawio
python3 scripts/autolayout.py  graph.json -o diagram.drawio
```

| Piece | What it does |
|---|---|
| **5 extractors** | import graphs for **Python · JS/TS · Go · Rust**, plus **Python class inheritance** |
| **Auto-layout** | Graphviz places nodes and routes orthogonal edges *around* them — removes the manual-coordinate ceiling for large graphs |
| **Transitive reduction** | drops edges implied by a longer path, turning a dense hairball into a traceable graph (asyncio: 149 → 46 edges) |
| **Nested containers** | `--group` boxes modules by sub-package, nested for deep package trees |
| **Deterministic validator** | `validate.py` lints the `.drawio` (dangling edges, duplicate ids, overlaps) before the visual self-check |

Layout needs Graphviz (`brew install graphviz` / `apt install graphviz`) — optional; everything else works without it. Full format + flag reference in [references/autolayout.md](skills/drawio-skill/references/autolayout.md).

## 🧩 Supported Diagram Types

| Category | Examples | Notable features |
|---|---|---|
| Architecture | microservices, cloud (AWS/GCP/Azure), network topology, deployment | Tier-based swimlanes, hub-center strategy |
| ML / Deep Learning | Transformer, CNN, LSTM, GRU | Tensor shape annotations, layer-type color coding |
| Flowcharts | business processes, workflows, decision trees, state machines | Semantic shapes (parallelogram I/O, diamond decisions) |
| UML | class diagrams, sequence diagrams | Inheritance / composition / aggregation arrows; lifelines + activation boxes |
| Data | ER diagrams, data flow diagrams (DFD) | Table containers, PK/FK notation |
| Other | org charts, mind maps, wireframes | — |

## 🔍 Shape Search

Need a real AWS / Azure / GCP / Cisco / Kubernetes / UML / BPMN icon? The skill searches **10,000+ official draw.io shapes** for the exact style string — so vendor icons render correctly instead of falling back to a blank box from a guessed `shape=mxgraph.*` name.

> *"Add an AWS Lambda wired to an S3 bucket"* · *"Use the real Kubernetes pod icon"*

```bash
python3 scripts/shapesearch.py "aws lambda" --limit 5
# → Lambda (77x93)
#   outlineConnect=0;...;shape=mxgraph.aws3.lambda;fillColor=#F58534;...
```

Covers AWS / Azure / GCP / Cisco / Kubernetes / UML / BPMN / ER / electrical / P&ID and the general shape sets. Hand-writable style cheatsheet + search usage in [references/shapes.md](skills/drawio-skill/references/shapes.md).

## 🎨 Style Presets

Capture a visual style once, reuse it everywhere. Three presets are built in — `default`, `corporate`, `handdrawn` — and you can teach the skill your own style from a `.drawio` file or a flat image:

```
Draw a microservices architecture using my "corporate" style
```

```
Learn my style from ~/diagrams/brand.drawio as "mybrand"
```

The skill extracts colors, shapes, fonts, and edge style, renders a preview, and only saves the preset after you approve. Full preset-management commands in [docs/STYLE_PRESETS.md](docs/STYLE_PRESETS.md).

## 🔄 How it works

<p align="center">
  <img src="assets/workflow.png" width="700" alt="Internal workflow">
</p>

Behind the scenes: **check dependencies → plan layout → generate `.drawio` XML → export draft PNG → self-check + auto-fix** (up to 2 rounds) → **show to user → 5-round feedback loop** until approved → **final export**.

## 🆚 Comparison

### vs Native Agent (no skill)

| Feature | Native agent | drawio-skill |
|---|---|---|
| Self-check after export | ❌ | ✅ reads PNG, auto-fixes 6 issue types |
| Iterative review loop | ❌ manual re-prompt | ✅ targeted edits, 5-round safety valve |
| Diagram type presets | ❌ | ✅ 6 presets (ERD, UML, Seq, Arch, ML, Flow) |
| Visualize a codebase | ❌ | ✅ import graphs (Py/JS/Go/Rust) + class diagrams |
| Auto-layout for large graphs | ❌ hand-places, overlaps | ✅ Graphviz placement, ortho routing, nested containers |
| Structural validation | ❌ | ✅ deterministic `.drawio` linter |
| Official shape search | ❌ guesses, blank boxes | ✅ exact style for 10k+ AWS/Azure/GCP/UML shapes |
| Grid-aligned layout | ❌ | ✅ 10px snap, routing corridors |
| Color palette | random / inconsistent | ✅ 7-color semantic system |
| Style presets | ❌ | ✅ learn from `.drawio` file or image |

### vs Other draw.io Skills & Tools

| Feature | drawio-skill | [jgraph/drawio-mcp](https://github.com/jgraph/drawio-mcp) (official)<br>![stars](https://img.shields.io/github/stars/jgraph/drawio-mcp?style=flat-square&logo=github) | [bahayonghang/drawio-skills](https://github.com/bahayonghang/drawio-skills)<br>![stars](https://img.shields.io/github/stars/bahayonghang/drawio-skills?style=flat-square&logo=github) | [GBSOSS/ai-drawio](https://github.com/GBSOSS/ai-drawio)<br>![stars](https://img.shields.io/github/stars/GBSOSS/ai-drawio?style=flat-square&logo=github) |
|---|---|---|---|---|
| **Approach** | Pure SKILL.md | SKILL.md / MCP / Project | YAML DSL + CLI (MCP optional) | Claude Code plugin |
| **Dependencies** | draw.io desktop only | draw.io desktop | draw.io desktop (MCP optional) | draw.io plugin + browser |
| **Multi-agent** | ✅ 6 platforms | ❌ Claude apps only | ✅ Claude / Gemini / Codex | ❌ Claude Code only |
| **Self-check + auto-fix** | ✅ 2-round (reads PNG) | ❌ | ✅ validation + strict mode | ❌ screenshot only |
| **Iterative review** | ✅ 5-round loop | ❌ generate once | ✅ 3 workflows | ❌ |
| **Diagram presets** | ✅ 6 types | ❌ | ✅ paper-mode classifier | ❌ |
| **ML/DL diagrams** | ✅ tensor shapes, layer colors | ❌ | ❌ | ❌ |
| **Color system** | ✅ 7-color semantic | ❌ | ✅ 6 themes | ❌ |
| **Official shape search** | ✅ 10k+ shapes (local) | ✅ 10k+ shapes (MCP) | ❌ | ❌ |
| **Browser fallback** | ✅ diagrams.net URL (viewer + editable) | ❌ inline preview only | ✅ via optional MCP | ✅ diagrams.net viewer (primary) |
| **Zero-config** | ✅ copy `skills/drawio-skill/` | ✅ | ✅ desktop-only mode | ❌ needs plugin install |

Full comparison + key-advantages summary in [docs/COMPARISON.md](docs/COMPARISON.md) (with audit timestamp).

## 🔗 Related Skills

Part of the [Agents365-ai diagram-skill family](https://github.com/Agents365-ai) — pick the right tool for the job:

| Skill | Style | Best for |
|---|---|---|
| [excalidraw-skill](https://github.com/Agents365-ai/excalidraw-skill) | Hand-drawn / sketchy | Whiteboard mockups, informal diagrams |
| [mermaid-skill](https://github.com/Agents365-ai/mermaid-skill) | Text-based, auto-layout | README-embeddable, version-control friendly |
| [plantuml-skill](https://github.com/Agents365-ai/plantuml-skill) | UML-focused | Class / sequence diagrams in CI pipelines |
| [tldraw-skill](https://github.com/Agents365-ai/tldraw-skill) | Whiteboard collaboration | Casual sketches, FigJam-style boards |

## 💬 Community

- **Discord:** https://discord.gg/79JF5Atuk
- **WeChat:** scan the QR code below

<p align="center">
  <img src="https://raw.githubusercontent.com/Agents365-ai/images_payment/main/qrcode/agents365ai_wechat_1.png" width="200" alt="WeChat Community Group">
</p>

## ❤️ Support

If this skill helps you, consider supporting the author:

<table>
  <tr>
    <td align="center">
      <img src="https://raw.githubusercontent.com/Agents365-ai/images_payment/main/qrcode/wechat-pay.png" width="180" alt="WeChat Pay">
      <br>
      <b>WeChat Pay</b>
    </td>
    <td align="center">
      <img src="https://raw.githubusercontent.com/Agents365-ai/images_payment/main/qrcode/alipay.png" width="180" alt="Alipay">
      <br>
      <b>Alipay</b>
    </td>
    <td align="center">
      <img src="https://raw.githubusercontent.com/Agents365-ai/images_payment/main/qrcode/buymeacoffee.png" width="180" alt="Buy Me a Coffee">
      <br>
      <b>Buy Me a Coffee</b>
    </td>
    <td align="center">
      <img src="https://raw.githubusercontent.com/Agents365-ai/images_payment/main/awarding/award.gif" width="180" alt="Give a Reward">
      <br>
      <b>Give a Reward</b>
    </td>
  </tr>
</table>

## 👤 Author

**Agents365-ai**

- GitHub: https://github.com/Agents365-ai
- Bilibili: https://space.bilibili.com/441831884

## 📄 License

[MIT](LICENSE)
