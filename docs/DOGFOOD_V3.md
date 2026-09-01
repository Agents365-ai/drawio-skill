# Architecture Studio 3.0 dogfood report

Date: 2026-09-01  
Target: `skills/drawio-skill/scripts/` in this repository

## Workflow exercised

```bash
python3 skills/drawio-skill/scripts/diagramctl.py build \
  skills/drawio-skill/scripts --from python --group \
  --ir-output /tmp/drawio-skill.ir.json -o /tmp/drawio-skill.drawio
python3 skills/drawio-skill/scripts/diagramctl.py inspect /tmp/drawio-skill.ir.json
python3 skills/drawio-skill/scripts/diagramctl.py review /tmp/drawio-skill.ir.json --format json
python3 skills/drawio-skill/scripts/diagramctl.py views /tmp/drawio-skill.ir.json \
  --views executive,system,deployment,dataflow,security -o /tmp/drawio-skill.views.drawio
python3 skills/drawio-skill/scripts/diagramctl.py story /tmp/drawio-skill.ir.json \
  -o /tmp/drawio-skill.story.html
```

## Observed results

- Import: 41 nodes and 1 intra-project edge.
- Structural validation: zero errors, warnings, edge-through-node routes,
  crossings, or overlaps for both the system diagram and five-view diagram.
- Views: Executive selected 12 nodes; the other four views retained all 41.
- Story: generated offline with 41 accessible components.
- Review: 41 owner warnings and no errors.

## What the run taught us

The low edge count is plausible for this toolbox: most scripts are independent
commands and only `diagramctl.py` imports `diagram_ir.py`. The importer therefore
reflected the code, but assigning every module the semantic kind `service`
made the ownership contract noisy. Likewise, deployment/data-flow/security
views correctly fell back to the complete graph, but the result did not add
information because code importers currently emit no runtime, boundary, or data
metadata.

These are modeling/profile gaps, not layout failures. They feed the v3.1
roadmap rather than being hidden by example-specific rules.
