# Semantic workflows

Read this reference for architecture contracts, queries, reviews, failure
simulation, story mode, accessibility, or multi-language delivery.

## Architecture contracts

Rules are JSON or YAML:

```yaml
rules:
  - no-direct-internet-to-database
  - no-cycles
  - no-orphans
  - every-service-has-owner
  - production-has-observability
  - external-dependencies-have-timeouts
  - trust-boundaries-use-protocol
  - accessible-contrast
```

Run them locally or in CI:

```bash
python3 scripts/diagramctl.py test architecture.drawio \
  --rules architecture-policy.yml --strict -o findings.json
```

Errors always fail. Warnings fail only under `--strict`. These rules inspect
declared diagram semantics; they do not claim to prove that the running system
has the same properties.

## Query and review

```bash
python3 scripts/diagramctl.py query architecture.drawio --kind database
python3 scripts/diagramctl.py query architecture.drawio --owner payments-team
python3 scripts/diagramctl.py query architecture.drawio --boundary pci
python3 scripts/diagramctl.py query architecture.drawio --from mobile --to payment-db
python3 scripts/diagramctl.py review architecture.drawio -o review.md
```

Review checks ownership, trust-boundary protocols, external timeouts,
production observability, contrast, dependency cycles, high coupling, and
articulation points that may represent single points of failure. It also flags
long synchronous chains and declared sensitive-data region crossings without a
residency approval. Treat findings as review prompts, not facts: graph topology
alone cannot establish runtime redundancy or security controls.

## What-if failure analysis

```bash
python3 scripts/diagramctl.py whatif architecture.ir.json --fail kafka \
  --drawio kafka-failure.drawio -o impact.json
```

Impact follows outgoing dependencies. An edge with
`properties.isolates_failure=true` stops propagation. The output highlights the
failed node red and impacted nodes amber. This is deterministic reachability,
not a production reliability simulation.

## Story mode

```bash
python3 scripts/diagramctl.py story architecture.ir.json \
  --fail kafka -o walkthrough.html
```

The self-contained HTML includes a guided component sequence, keyboard arrow
navigation, clickable/focusable nodes, SVG title/description, a complete text
alternative, provenance/owner/boundary details, reduced-motion support, and an
optional failure overlay. If nodes define `labels` (for example `zh` and `en`),
the viewer exposes a language selector without creating duplicate diagrams.

The story file makes no external requests. Use `publish --format viewer` for
the existing full-fidelity SVG viewer when the draw.io CLI is available; use
Story mode for a semantic, accessible, dependency-free artifact.
