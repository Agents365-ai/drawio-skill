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
| Animated connectors | No | Yes — `flowAnimation=1` for data-flow visualization |
| ML model diagrams | No | Yes — tensor shape annotations, layer-type color coding |
| Color palette | Random/inconsistent | 7-color semantic system (blue=services, green=DB, purple=auth...) |
| Edge routing rules | Basic | Pin entry/exit points, distribute connections, waypoint corridors |
| Container/group patterns | None | Swimlane, group, custom container with parent-child nesting |
| Embed diagram in export | No | Yes — `--embed-diagram` keeps exported PNG/SVG/PDF editable |
| Browser fallback | No | Yes — generates diagrams.net URL when CLI unavailable |
| Auto-launch desktop app | No | Yes — opens `.drawio` file after export for fine-tuning |

## vs Other draw.io Skills & Tools

| Feature | This skill | [jgraph/drawio-mcp](https://github.com/jgraph/drawio-mcp) (official, 1.3k⭐) | [bahayonghang/drawio-skills](https://github.com/bahayonghang/drawio-skills) (60⭐) | [GBSOSS/ai-drawio](https://github.com/GBSOSS/ai-drawio) (63⭐) |
|---------|-----------|---------------|-------------------|--------------|
| **Approach** | Pure SKILL.md | SKILL.md / MCP / Project | YAML DSL + MCP | Plugin + browser |
| **Dependencies** | draw.io desktop only | draw.io desktop | MCP server (`npx`) | Browser + local server |
| **Multi-agent** | ✅ 6 platforms | ❌ Claude Code only | ❌ Claude Code only | ❌ |
| **Self-check** | ✅ 2-round auto-fix | ❌ | ❌ | ❌ screenshot |
| **Iterative review** | ✅ 5-round loop | ❌ generate once | ✅ 3 workflows | ❌ |
| **Layout guidance** | ✅ complexity-scaled + grid snap | ✅ basic spacing | ❌ relies on MCP | ❌ |
| **Diagram presets** | ✅ 6 types (ERD, UML, Seq, Arch, ML, Flow) | ❌ | ❌ | ❌ |
| **Animated edges** | ✅ `flowAnimation=1` | ❌ | ❌ | ❌ |
| **ML/DL diagrams** | ✅ tensor shapes, layer colors | ❌ | ❌ | ❌ |
| **Color system** | ✅ 7-color semantic | ❌ | ✅ 5 themes | ❌ |
| **Container/group** | ✅ swimlane + group | ✅ detailed | ❌ | ❌ |
| **Embed diagram** | ✅ `--embed-diagram` | ✅ | ❌ | ❌ |
| **Edge routing** | ✅ corridors + waypoints | ✅ arrowhead rules | ❌ | ❌ |
| **Browser fallback** | ✅ diagrams.net URL | ❌ | ❌ | ❌ |
| **Auto-launch** | ✅ opens desktop app | ❌ | ❌ | ❌ |
| **Cloud icons** | AWS basic | ❌ | ✅ AWS/GCP/Azure/K8s | ❌ |
| **Zero-config** | ✅ copy skills/drawio-skill/ | ✅ | ❌ needs `npx` | ❌ needs plugin install |

## Key advantages

1. **Self-check + iterative loop** — the only pure-SKILL.md solution that reads its own output and auto-fixes before showing the user, then supports multi-round refinement
2. **6 diagram type presets** — ERD, UML Class, Sequence, Architecture, ML/Deep Learning, Flowchart — each with preset shapes, styles, and layout conventions
3. **ML/DL model diagrams** — tensor shape annotations, layer-type color coding, encoder/decoder swimlanes — built for academic papers
4. **Multi-agent, zero-config** — works across 6 platforms with just the `skills/drawio-skill/` directory + draw.io desktop. No MCP server, no Python, no Node.js, no browser
5. **Production-grade layout** — grid-aligned coordinates, complexity-scaled spacing, routing corridors, hub-center strategy, animated connectors
6. **Browser fallback** — generates diagrams.net URLs when the desktop CLI is unavailable, plus auto-launch for desktop editing
