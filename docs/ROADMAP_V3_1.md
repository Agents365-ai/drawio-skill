# Roadmap: Architecture Studio 3.1

This backlog is based on the 3.0 release gate, checked showcase, and dogfood run
against this repository. It is intentionally ordered by observed usefulness.

## P0 — semantic fidelity  ✅ shipped in 3.2.0

- ~~Add source profiles so code modules use kinds such as `module`, `library`,
  `adapter`, and `command` instead of defaulting to `service`.~~ ✅ (`module`/`library`/`command`)
- ~~Scope architecture contracts by kind/profile; ownership and production
  observability rules should not fire on ordinary source modules.~~ ✅ (kinds + `profile` field)
- ~~Emit exact file-and-line provenance from language importers rather than only
  the scanned root path.~~ ✅ (per-file path + Python edge line numbers)
- ~~Report when a projected view falls back to the entire model, including which
  metadata would make that view distinctive.~~ ✅ (`fallback`/`fallback_reason`/`hint`)

## P1 — richer analysis

- Add policy parameters and per-rule severity overrides without introducing an
  expression evaluator that executes user content.
- Model dependency direction and failure semantics explicitly: caller/callee,
  upstream/downstream, retry, circuit breaker, queue buffering, and redundancy.
- Add a view-difference summary so CI can detect five nominal views that are
  effectively identical.
- Support deterministic timestamps through `SOURCE_DATE_EPOCH` for reproducible
  checked artifacts.

## P2 — release confidence and presentation

- Add cross-platform visual golden tests for Graphviz and grid fallback layouts.
- Export a small PNG/SVG gallery from the semantic showcase in release CI.
- Track importer precision, policy signal-to-noise, manual-layout preservation,
  view differentiation, and Story accessibility as release metrics.

## Exit criteria

3.1 is ready when a codebase dogfood run produces no architecture-only policy
noise, provenance identifies source lines, fallback views explain themselves,
and the showcase passes on macOS, Linux/Xvfb, and the pure-Python fallback.
