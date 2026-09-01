# CI gates

Two composite GitHub Actions ship with this repo. Both can be used from your
own repository without copying code:

```yaml
uses: Agents365-ai/drawio-skill/.github/actions/<action>@main
```

(Pin to a tag instead of `main` for reproducible gates, e.g. `@v3.1.0`.)

## drawio-architecture-test — pure Python, seconds to run

Runs the Diagram-as-Test architecture contract rules against Diagram IR files
on every PR. Needs **no draw.io desktop, no Xvfb, no Graphviz** — a stock
runner works, because the rules operate on the IR JSON.

Inputs: `ir-files` (newline-separated paths/globs, required), `rules`
(optional policy YAML/JSON), `strict` (fail on warnings), `summary`,
`post-comment` (sticky PR comment), `github-token`.

Behavior: each failing model increments the gate; the job exits non-zero when
any model has errors (or warnings under `strict`). The report lands in the
job summary, the `drawio-architecture-test` artifact, and a sticky PR comment.

Ready-to-copy workflow: `.github/workflows/drawio-architecture-test.example.yml`
in this repo. Typical adoption:

1. Export the model once and commit the IR:
   `python3 diagramctl.py build ./src --ir-output architecture.ir.json -o architecture.drawio`
2. Reference the action with `ir-files: architecture.ir.json` and, optionally,
   `rules: policy.yml` (see `diagramctl.py test --help` for the rule ids).

## drawio-diff — visual PR diagram diff

Renders base/head/diff PNGs for every `.drawio` changed in a PR and posts a
sticky Markdown report. This one needs the draw.io desktop CLI + Graphviz +
Xvfb (the action installs them unless `skip-tool-install: true`); full
adoption guide in `references/pr-bot.md`.

## Choosing between them

| You want | Action |
| --- | --- |
| Architecture rules enforced in CI (ownership, trust boundaries, cycles, Internet→DB access, timeouts, contrast) | `drawio-architecture-test` |
| Visual diff of rendered diagrams for changed `.drawio` files | `drawio-diff` |

They compose: run the IR gate on every PR cheaply, and the visual diff when
`.drawio` files actually change.
