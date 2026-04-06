# Codex Review Suggestions for drawio-skill

## Top Risks

- **High**: Over-claims parity with competitors; `assets/` only demonstrates 3 topology demos + workflow, not 6 presets
- **High**: Command naming inconsistent: `draw.io` in SKILL.md vs `drawio` in READMEs
- **High**: OpenClaw package naming inconsistent: `drawio-pro-skill` (install) vs `drawio-skill` (update)

## 1) SKILL.md

| Priority | Suggestion |
|----------|-----------|
| High | Add clarification policy for underspecified requests (ask 1-3 questions) |
| High | Define fallback behavior when CLI, vision, or Python is unavailable |
| Medium | Add edge cases: existing files, filename collisions, multi-page, large diagrams, non-English labels |
| Medium | Add planning template for each preset (nodes, edges, groups, orientation, labels, formats) |
| Low | Soften absolute "always" wording in routing rules |

## 2) README.md / README_CN.md

| Priority | Suggestion |
|----------|-----------|
| High | Add "Known Limitations" section |
| High | Fix EN/CN consistency: CN title still English, OpenClaw slug mismatch |
| Medium | Add quickstart with end-to-end example |
| Medium | Add feature matrix: "implemented" vs "demonstrated" vs "metadata only" |
| Low | Move support/donation blocks below troubleshooting |

## 3) scripts/check-update.sh

| Priority | Suggestion |
|----------|-----------|
| High | Compare against current branch upstream, not `origin HEAD` |
| High | Handle missing `origin`, detached HEAD, shallow clones, dirty trees |
| Medium | Quote `cd` path, print current branch/upstream |
| Low | Add `--json` and `--fetch` modes |

## 4) .github/workflows/publish-clawhub.yml

| Priority | Suggestion |
|----------|-----------|
| High | Pin CLI version instead of `npm install -g clawhub` |
| High | Add concurrency control; gate publish on version change |
| Medium | Replace grep-based version extraction with robust parser |
| Medium | Add validation before publish (schema/lint, link check, dry-run) |
| Low | Set minimal job permissions |

## 5) .claude/settings.local.json

| Priority | Suggestion |
|----------|-----------|
| High | Too permissive (git push, broad python3, clawhub publish) |
| High | Hard-coded absolute paths leak local machine structure |
| Medium | Split authoring/demo permissions from normal use |
| Low | Document why each permission exists |

## 6) docs/index.html / docs/zh.html

| Priority | Suggestion |
|----------|-----------|
| High | Accessibility: tabs use divs, no keyboard support, no focus states, no aria-labels |
| High | Mobile: comparison table has no overflow wrapper |
| Medium | SEO: add canonical URL, og:*, Twitter cards, hreflang, favicon |
| Medium | Demo images use remote URLs instead of local assets |
| Low | Both docs omit Hermes install instructions |

## 7) agents/openai.yaml

| Priority | Suggestion |
|----------|-----------|
| High | Too minimal to justify "Full support" claim |
| Medium | Add examples, capabilities, prerequisites, output formats |
| Low | Align wording with SKILL.md |

## 8) assets/*.drawio

| Priority | Suggestion |
|----------|-----------|
| High | No ERD, UML, sequence, or ML/DL .drawio examples (claimed 6 presets) |
| High | microservices-example.png has no matching source .drawio |
| Medium | Add domain-diverse examples |
| Low | Export sample SVG/PDF artifacts |

## Broken Links / Inconsistencies

- Command naming and ClawHub slug drift are confirmed inconsistencies
- No broken relative links found

## Competitor Gaps

- `bahayonghang/drawio-skills`: real-time browser preview, version history, cloud icons, math typesetting
- `jgraph/drawio-mcp`: Mermaid/CSV entry, inline/browser app modes
