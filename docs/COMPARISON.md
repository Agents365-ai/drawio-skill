# Comparison

[中文](COMPARISON_CN.md)

## vs No Skill (native agent)

| Feature | Native agent | This skill |
|---------|-------------|------------|
| Generate draw.io XML | Yes — LLMs know the format | Yes |
| Self-check after export | No | Yes — reads PNG and auto-fixes 6 issue types |
| Iterative review loop | No — must manually re-prompt | Yes — targeted edits, 5-round safety valve |
| Proactive triggers | No — only when explicitly asked | Yes — auto-suggests when 3+ components |
| Layout guidelines | None — varies by run | Complexity-scaled spacing, routing corridors, hub placement |
| Grid alignment | No | Yes — all coordinates snap to 10px multiples |
| Diagram type presets | No | Yes — 6 presets (ERD, UML, Sequence, Architecture, ML/DL, Flowchart) |
| Visualize a codebase | No | Yes — import graphs (Py/JS/Go/Rust) + class diagrams |
| Auto-layout for large graphs | No — hand-places, overlaps | Yes — Graphviz placement, ortho routing, nested containers |
| Structural validation | No | Yes — deterministic `.drawio` linter |
| Official shape search | No — guesses, blank boxes | Yes — exact style for 10k+ AWS/Azure/GCP/UML shapes |
| AI/LLM brand logos | No — none | Yes — 321 logos (OpenAI/Claude/Gemini/…) via aiicons.py |
| Animated connectors | No | Yes — `flowAnimation=1` for data-flow visualization |
| ML model diagrams | No | Yes — tensor shape annotations, layer-type color coding |
| Color palette | Random/inconsistent | 7-color semantic system (blue=services, green=DB, purple=auth...) |
| Edge routing rules | Basic | Pin entry/exit points, distribute connections, waypoint corridors |
| Container/group patterns | None | Swimlane, group, custom container with parent-child nesting |
| Embed diagram in export | No | Yes — `--embed-diagram` keeps exported PNG/SVG/PDF editable |
| Browser fallback | No | Yes — generates diagrams.net URL when CLI unavailable |
| Auto-launch desktop app | No | Yes — opens `.drawio` file after export for fine-tuning |

## vs Other draw.io Skills & Tools

| Feature | This skill | [jgraph/drawio-mcp](https://github.com/jgraph/drawio-mcp) (official) ![stars](https://img.shields.io/github/stars/jgraph/drawio-mcp?style=flat-square&logo=github) | [bahayonghang/drawio-skills](https://github.com/bahayonghang/drawio-skills) ![stars](https://img.shields.io/github/stars/bahayonghang/drawio-skills?style=flat-square&logo=github) | [GBSOSS/ai-drawio](https://github.com/GBSOSS/ai-drawio) ![stars](https://img.shields.io/github/stars/GBSOSS/ai-drawio?style=flat-square&logo=github) |
|---------|-----------|---------------|-------------------|--------------|
| **Approach** | Pure SKILL.md | MCP servers / Claude Code plugin / Project | YAML DSL + CLI (MCP optional) | Claude Code plugin |
| **Dependencies** | draw.io desktop only | draw.io desktop | draw.io desktop (MCP optional) | draw.io plugin + browser |
| **Multi-agent** | ✅ 6 platforms | ⚠️ MCP hosts (Claude, Cursor, VS Code) | ✅ Claude / Gemini / Codex | ❌ Claude Code only |
| **Self-check** | ✅ 2-round vision-based (reads PNG) | ❌ | ✅ validation + strict mode | ❌ screenshot only |
| **Iterative review** | ✅ 5-round loop | ❌ generate once | ✅ 3 workflows (create/edit/replicate) | ❌ |
| **Layout guidance** | ✅ complexity-scaled + grid snap | ✅ basic spacing | ✅ design-system | ❌ |
| **Diagram presets** | ✅ 6 types (ERD, UML, Seq, Arch, ML, Flow) | ❌ | ✅ paper-mode classifier (architecture/roadmap/workflow) | ❌ |
| **Animated edges** | ✅ `flowAnimation=1` | ❌ | ❌ | ❌ |
| **ML/DL diagrams** | ✅ tensor shapes, layer colors | ❌ | ❌ | ❌ |
| **Color system** | ✅ 7-color semantic | ❌ | ✅ 6 themes | ❌ |
| **Official shape search** | ✅ 10k+ shapes (local) | ✅ 10k+ shapes (MCP) | ❌ | ❌ |
| **AI/LLM brand logos** | ✅ 321 (lobe-icons) | ❌ | ❌ | ❌ |
| **Container/group** | ✅ swimlane + group | ✅ detailed | ❌ | ❌ |
| **Embed diagram** | ✅ `--embed-diagram` | ✅ | ❌ | ❌ |
| **Edge routing** | ✅ corridors + waypoints | ✅ arrowhead rules + libavoid auto-routing | ❌ | ❌ |
| **Browser fallback** | ✅ diagrams.net URL | ✅ diagrams.net URL (plugin) + inline preview | ✅ via optional MCP | ✅ diagrams.net viewer (primary) |
| **Auto-launch** | ✅ opens desktop app | ❌ | ❌ | ✅ opens Chrome |
| **Cloud icons** | AWS basic | ❌ | ✅ AWS/GCP/Azure/K8s | ✅ AWS basic |
| **Zero-config** | ✅ copy skills/drawio-skill/ | ✅ | ✅ desktop-only mode | ❌ needs plugin install |

_Last audited against competitor READMEs on 2026-07-10. Please open an issue or PR if anything is out of date — competitors evolve and table accuracy depends on community help._

## Key advantages

1. **Self-check + iterative loop** — the only pure-SKILL.md solution that reads its own output and auto-fixes before showing the user, then supports multi-round refinement
2. **6 diagram type presets** — ERD, UML Class, Sequence, Architecture, ML/Deep Learning, Flowchart — each with preset shapes, styles, and layout conventions
3. **ML/DL model diagrams** — tensor shape annotations, layer-type color coding, encoder/decoder swimlanes — built for academic papers
4. **Multi-agent, zero-config** — works across 6 platforms with just the `skills/drawio-skill/` directory + draw.io desktop. No MCP server, no Python, no Node.js, no browser
5. **Production-grade layout** — grid-aligned coordinates, complexity-scaled spacing, routing corridors, hub-center strategy, animated connectors
6. **Browser fallback** — generates diagrams.net URLs when the desktop CLI is unavailable, plus auto-launch for desktop editing
