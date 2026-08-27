# Databricks Diagrams

How to draw Databricks architectures with real product icons.

## Resolving icons

draw.io has no Databricks shape set. For **any Databricks product** (Unity
Catalog, Lakeflow Jobs, DLT, Databricks SQL, Mosaic AI, ...), never guess a
`shape=` or image URL — resolve it:

```bash
python3 <this-skill-dir>/scripts/dbxicons.py "unity catalog"        # URL reference
python3 <this-skill-dir>/scripts/dbxicons.py "DLT" --embed          # self-contained
python3 <this-skill-dir>/scripts/dbxicons.py --list                 # all 71 products
```

Renamed products resolve through aliases (DLT → `spark-declarative-pipelines`,
Workflows → `lakeflow-jobs`, Vector Search → `ai-search`). Variants:
`--variant color|tile|outline` (no mono — those SVGs render black in draw.io).
For the bare Databricks company logo, `aiicons.py "databricks"` also works.

**URL vs `--embed`:** the default style references the SVG from the community
project's site, so draw.io needs network access when the diagram is rendered or
opened. `--embed` fetches the SVG once (from a commit pinned in the manifest)
and inlines it as a data URI — the diagram is then self-contained and needs
network only at generation time. Prefer `--embed` for diagrams that must render
offline or live long.

## Brand-styled diagrams

Zone colors (Databricks brand rule):

| Zone | Color | Marks |
| --- | --- | --- |
| Lava | `#FF5F46` | the Databricks platform boundary |
| Oat | `#D9D7CE` | external systems |
| Navy | `#143D4A` | customer-owned infrastructure |

Each resolved product carries its `categoryColor` (8 categories: platform
`#FF3621`, engineering `#2272B4`, storage `#00875C`, analytics `#1B5162`, ai
`#98102A`, governance `#1B3139`, sharing `#BA7B23`, devtools `#618794`). Use it
as an accent — a container stroke or a label color — not as a fill behind the
icon.

Capability node (140x60, icon box with a bold label below):

```
shape=image;html=1;whiteSpace=wrap;imageAspect=1;verticalLabelPosition=bottom;verticalAlign=top;labelPosition=center;align=center;fontSize=11;fontStyle=1;fontColor=#1B3139;image=<resolved>;
```

Replace `<resolved>` with the `image=` value from `dbxicons.py` output.

## Attribution

Icons come from the community project
[databricks-architecture-icons](https://github.com/oieduardorabelo/databricks-architecture-icons),
which serves official Databricks artwork; its `drawio/` folder has the full
brand template system. The icons are trademarks of Databricks, Inc., referenced
for identification only. This skill bundles no artwork — only a name manifest
(`data/databricks-icons.json`).
