# Architecture Studio showcase

These examples exercise the three workflows introduced in drawio-skill 3.0:

1. `codebase/` → `generated/codebase.ir.json` → editable import graph.
2. Baseline model → manually tuned diagram → three-way reconciliation with
   explicit label/property conflicts.
3. Semantic checkout architecture → linked views, policy result, failure
   overlay, impact report, and accessible offline Story HTML.

Regenerate every checked-in artifact from the repository root:

```bash
python3 examples/architecture-studio/generate.py
```

Or keep the repository untouched and write into a temporary directory:

```bash
python3 examples/architecture-studio/generate.py --output-dir /tmp/drawio-showcase
```

Open `generated/reconciled.drawio` to inspect the preserved manual geometry and
`data-conflict` annotations. Open `generated/checkout-story.html` in any modern
browser; it is self-contained and makes no external requests.

Generated timestamps are evidence of the most recent regeneration and are not
intended to be byte-for-byte reproducible. Tests assert semantic and structural
invariants instead.
