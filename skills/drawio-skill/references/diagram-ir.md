# Diagram IR and incremental synchronization

Read this reference when a request involves `diagramctl build`, `sync`,
`reconcile`, `views`, `query`, semantic metadata, or provenance.

## Canonical model

Diagram IR v1 separates meaning from draw.io geometry. Its JSON Schema is
`data/diagram-ir.schema.json`; the discriminator is:

```json
{
  "schema": "drawio-skill/diagram-ir/v1",
  "metadata": {"title": "Checkout"},
  "nodes": [
    {
      "id": "orders",
      "label": "Order Service",
      "kind": "service",
      "properties": {
        "owner": "orders-team",
        "environment": "production",
        "observability": "OpenTelemetry",
        "trust_boundary": "private"
      },
      "provenance": {"path": "services/orders.py", "line": 12},
      "labels": {"zh": "订单服务"}
    }
  ],
  "edges": [
    {
      "id": "api-orders",
      "source": "api",
      "target": "orders",
      "label": "HTTPS",
      "kind": "sync",
      "properties": {"protocol": "HTTPS", "timeout": "2s"}
    }
  ],
  "views": []
}
```

IDs are stable semantic identities. Never use draw.io's reserved IDs `0` or
`1`. Importers should record their source in `provenance`; generated `.drawio`
cells retain that metadata as `data-*` attributes.

## Unified commands

```bash
python3 scripts/diagramctl.py build model.json --from ir -o architecture.drawio
python3 scripts/diagramctl.py build ./infra --from terraform --group \
  --ir-output architecture.ir.json -o architecture.drawio
python3 scripts/diagramctl.py inspect architecture.drawio
python3 scripts/diagramctl.py query architecture.drawio --from internet --to orders-db
```

`build --from auto` recognizes Diagram IR/graph JSON, SQL, OpenAPI, compose,
Kubernetes YAML, and common repository markers. Use an explicit `--from` when
the source is ambiguous.

## Reconcile instead of regenerate

Use `sync` when a diagram already contains manual layout or styling:

```bash
python3 scripts/diagramctl.py sync architecture.drawio ./infra \
  --from terraform -o architecture.next.drawio
```

Matching nodes preserve their geometry and style. Labels/properties/provenance
are refreshed, additions are placed below the existing canvas, and removals are
retained as faded red elements. Pass `--prune` only when the user explicitly
wants removed elements deleted. Write to a new output by default so the user can
review the result before replacing the original.

Generated cells retain their last source label/properties. On the next sync,
those values form a three-way comparison between the old source, current manual
diagram, and new source. If both the user and source changed the same label or
property differently, sync preserves the manual value and reports a structured
`conflicts` entry instead of silently overwriting it.

Source IDs are matched first; legacy diagrams fall back to cell IDs. Importers
therefore must keep IDs stable between runs.

## Multi-view projection

```bash
python3 scripts/diagramctl.py views architecture.ir.json \
  --views executive,system,deployment,dataflow,security \
  -o architecture-views.drawio
```

Views are pages over the same model rather than copied models. Nodes carry the
same `data-model-id`; nodes present in several pages link to the next applicable
view. The executive view selects at most twelve high-importance/high-degree
nodes. Deployment/data/security views use semantic properties and fall back to
the complete model when metadata is insufficient. Each view reports a
`fallback` flag with a `fallback_reason` and a `hint` naming the metadata that
would make it distinctive, so a fallback is never silent:

```bash
python3 scripts/diagramctl.py views model.ir.json -o views.drawio
# views[].fallback / fallback_reason / hint
```

## v3.2 semantic fidelity

- **Source-kind profiles**: building from a code importer (`--from python`,
  `js`, `go`, `rust`, `pyclasses`) assigns real `module` / `library` /
  `command` kinds from the file name instead of a blanket `service` — package
  roots (`__init__.py`, `lib.rs`) are `library`, entrypoints
  (`__main__.py`, `main.rs`, `cli.py`) are `command`, everything else is
  `module`. Ownership / observability contract rules therefore do not fire on
  ordinary source modules.
- **Precise provenance**: importer node provenance records the exact file
  path (resolved against the scanned root), and Python edges carry the line
  of the import statement that pulled them in.
- **Profile reporting**: `diagramctl test` reports a `profile` field —
  `code` for module/library/command graphs, `architecture` otherwise.

## Compatibility

The IR reader supports both uncompressed and compressed draw.io pages. The
reconcile writer intentionally requires an uncompressed page because patching a
compressed payload would make review and conflict handling opaque.
