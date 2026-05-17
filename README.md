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

**English** · [中文](README_CN.md) · [📖 Online Docs](https://agents365-ai.github.io/drawio-skill/)

A skill that turns natural-language descriptions into `.drawio` XML and exports them to PNG / SVG / PDF / JPG via the native draw.io desktop CLI. Works with **Claude Code, Cursor, Copilot, OpenClaw, Codex, Hermes**, and any agent compatible with the [Agent Skills](https://agentskills.io) format.

<p align="center">
  <img src="assets/workflow.png" width="900" alt="Workflow">
</p>

## ✨ Highlights

- **6 diagram type presets** — ERD, UML Class, Sequence, Architecture, ML/Deep Learning, Flowchart
- **Self-check + auto-fix** — reads its own PNG output and auto-fixes 6 issue types (up to 2 rounds)
- **Iterative feedback loop** — 5-round targeted refinement until you're satisfied
- **Style presets** — capture your visual style from a `.drawio` file or image, reuse on demand
- **Grid-aligned layout** — complexity-scaled spacing, routing corridors, hub-center strategy
- **Multi-agent, zero-config** — pure SKILL.md; no MCP server, no Python, no Node.js

## 🖼️ Examples

> [!TIP]
> **Try this prompt** to generate the diagram below:

```
Create a microservices e-commerce architecture with Mobile/Web/Admin clients,
API Gateway, Auth/User/Order/Product/Payment services, Kafka message queue,
Notification service, and User DB / Order DB / Product DB / Redis Cache / Stripe API
```

<p align="center">
  <img src="assets/microservices-example.png" width="800" alt="Microservices Architecture">
</p>

The skill also routes edges cleanly across different topologies — no lines crossing through shapes:

<table>
  <tr>
    <td align="center" width="33%">
      <img src="assets/demo-star.png" alt="Star topology" width="100%"><br>
      <b>Star</b> · 7 nodes<br>
      <sub>Central message broker with 6 microservices radiating outward, zero edge crossings.</sub>
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

Verify with `drawio --version`. Full recipes in [docs/INSTALL_CLI.md](docs/INSTALL_CLI.md).

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

After installation, just describe what you want:

```
Create a microservices e-commerce architecture with API Gateway,
Auth/User/Order/Product/Payment services, Kafka message queue,
Notification service, and a separate database per service
```

The skill plans the layout, generates the `.drawio` XML, exports to your chosen format, self-checks the result, and lets you iterate.

## 🧩 Supported Diagram Types

| Category | Examples | Notable features |
|---|---|---|
| Architecture | microservices, cloud (AWS/GCP/Azure), network topology, deployment | Tier-based swimlanes, hub-center strategy |
| ML / Deep Learning | Transformer, CNN, LSTM, GRU | Tensor shape annotations, layer-type color coding |
| Flowcharts | business processes, workflows, decision trees, state machines | Semantic shapes (parallelogram I/O, diamond decisions) |
| UML | class diagrams, sequence diagrams | Inheritance / composition / aggregation arrows; lifelines + activation boxes |
| Data | ER diagrams, data flow diagrams (DFD) | Table containers, PK/FK notation |
| Other | org charts, mind maps, wireframes | — |

## 🎨 Style Presets

Capture a visual style once, reuse it everywhere. Three presets are built in — `default`, `corporate`, `handdrawn` — and you can teach the skill your own style from a `.drawio` file or a flat image:

```
Draw a microservices architecture using my "corporate" style
```

```
Learn my style from ~/diagrams/brand.drawio as "mybrand"
```

The skill extracts colors, shapes, fonts, and edge style, renders a preview, and only saves the preset after you approve. Full preset-management commands in [docs/STYLE_PRESETS.md](docs/STYLE_PRESETS.md).

## 🆚 Comparison

### vs Native Agent (no skill)

| Feature | Native agent | drawio-skill |
|---|---|---|
| Self-check after export | ❌ | ✅ reads PNG, auto-fixes 6 issue types |
| Iterative review loop | ❌ manual re-prompt | ✅ targeted edits, 5-round safety valve |
| Diagram type presets | ❌ | ✅ 6 presets (ERD, UML, Seq, Arch, ML, Flow) |
| Grid-aligned layout | ❌ | ✅ 10px snap, routing corridors |
| Color palette | random / inconsistent | ✅ 7-color semantic system |
| Style presets | ❌ | ✅ learn from `.drawio` file or image |

### vs Other draw.io Skills & Tools

| Feature | drawio-skill | [jgraph/drawio-mcp](https://github.com/jgraph/drawio-mcp) (official)<br>![](https://img.shields.io/github/stars/jgraph/drawio-mcp?style=flat-square&logo=github) | [bahayonghang/drawio-skills](https://github.com/bahayonghang/drawio-skills)<br>![](https://img.shields.io/github/stars/bahayonghang/drawio-skills?style=flat-square&logo=github) | [GBSOSS/ai-drawio](https://github.com/GBSOSS/ai-drawio)<br>![](https://img.shields.io/github/stars/GBSOSS/ai-drawio?style=flat-square&logo=github) |
|---|---|---|---|---|
| **Approach** | Pure SKILL.md | SKILL.md / MCP / Project | YAML DSL + MCP | Plugin + browser |
| **Dependencies** | draw.io desktop only | draw.io desktop | MCP server (`npx`) | Browser + local server |
| **Multi-agent** | ✅ 6 platforms | ❌ Claude Code only | ❌ Claude Code only | ❌ |
| **Self-check + auto-fix** | ✅ 2-round | ❌ | ❌ | ❌ screenshot only |
| **Iterative review** | ✅ 5-round loop | ❌ generate once | ✅ 3 workflows | ❌ |
| **Diagram presets** | ✅ 6 types | ❌ | ❌ | ❌ |
| **ML/DL diagrams** | ✅ tensor shapes, layer colors | ❌ | ❌ | ❌ |
| **Color system** | ✅ 7-color semantic | ❌ | ✅ 5 themes | ❌ |
| **Browser fallback** | ✅ diagrams.net URL | ❌ | ❌ | ❌ |
| **Zero-config** | ✅ copy `skills/drawio-skill/` | ✅ | ❌ needs `npx` | ❌ needs plugin install |

Full 18-row comparison + key-advantages summary in [docs/COMPARISON.md](docs/COMPARISON.md).

## 📚 Documentation

| Doc | What's inside |
|---|---|
| [docs/INSTALL_CLI.md](docs/INSTALL_CLI.md) | draw.io desktop CLI install recipes for macOS / Windows / Linux |
| [docs/INSTALL_SKILL.md](docs/INSTALL_SKILL.md) | Plugin marketplace, manual clone, update commands |
| [docs/USAGE.md](docs/USAGE.md) | Natural-language prompts, microservices walkthrough, topology demos |
| [docs/STYLE_PRESETS.md](docs/STYLE_PRESETS.md) | Built-in presets, "learn my style from a file" workflow, manage commands |
| [docs/COMPARISON.md](docs/COMPARISON.md) | Side-by-side tables vs. native agents and other draw.io skills/tools |
| [skills/drawio-skill/SKILL.md](skills/drawio-skill/SKILL.md) | Workflow guide loaded by the agent |

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
