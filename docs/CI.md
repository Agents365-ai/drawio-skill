# Rendering diagrams in CI

[中文](CI_CN.md)

Keep diagram **sources** in the repo (graph JSON from the importers, `seq.json`, `c4.json`, or hand-written `.drawio`) and let CI regenerate, lint, and export them — the diagram-as-code loop:

```
source (.tf / manifests / schema.sql / seq.json / graph.json)
   → extractor (tfimports / k8simports / sqlerd / seqlayout / …)
   → autolayout.py → validate.py --strict (gate) → drawio -x (render) → artifact
```

Importer node ids are stable (module paths, `type.name`, `kind/name`), so regenerated `.drawio` files produce reviewable diffs when the underlying code or infra changes.

## Option A — draw.io desktop + xvfb (GitHub Actions)

The desktop CLI works headless under `xvfb`. Complete workflow:

```yaml
name: diagrams
on:
  push:
    paths: ["infra/**", "diagrams/**"]

jobs:
  render:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # The skill's scripts (importers, autolayout, validate)
      - run: git clone --depth 1 https://github.com/Agents365-ai/drawio-skill /tmp/drawio-skill
      - run: sudo apt-get update && sudo apt-get install -y graphviz xvfb

      # draw.io desktop (latest release .deb)
      - name: Install draw.io
        run: |
          URL=$(curl -s https://api.github.com/repos/jgraph/drawio-desktop/releases/latest \
                | grep -o 'https://[^"]*amd64[^"]*\.deb' | head -1)
          curl -sL "$URL" -o /tmp/drawio.deb
          sudo apt-get install -y /tmp/drawio.deb

      - name: Regenerate, lint, render
        run: |
          S=/tmp/drawio-skill/skills/drawio-skill/scripts
          python3 $S/tfimports.py infra -o /tmp/graph.json
          python3 $S/autolayout.py /tmp/graph.json -o diagrams/infra.drawio
          python3 $S/validate.py diagrams/infra.drawio --strict   # gate: fail on any warning
          export HOME=${HOME:-/tmp}
          xvfb-run -a --server-args="-screen 0 1280x1024x24" \
            drawio -x -f png -e -s 2 -o diagrams/infra.drawio.png \
            diagrams/infra.drawio --disable-gpu --no-sandbox
          python3 $S/repair_png.py diagrams/infra.drawio.png       # fix -e IEND truncation

      - uses: actions/upload-artifact@v4
        with: {name: diagrams, path: "diagrams/*.png"}
```

Notes (all from the skill's troubleshooting experience):

- `--no-sandbox` must be the **last** argument — earlier positions make drawio treat it as the input file. Required when running as root (CI containers).
- `export HOME=/tmp` if the runner has no home; add `--disable-gpu` on servers.
- After any `-e` PNG export, run `repair_png.py` — the CLI truncates the IEND chunk (issue #8).
- `--page-index <n>` (1-based) exports one page of a multi-page file (e.g. `c4.py` output).
- If the `.deb` install fails on missing libs: `sudo apt-get install -y libgtk-3-0 libnotify4 libnss3 libgbm1 libasound2t64`.

## Option B — Docker REST renderer (no desktop install)

[`tomkludy/drawio-renderer`](https://hub.docker.com/r/tomkludy/drawio-renderer) exposes headless export as a REST API — useful on runners where installing a `.deb` is not an option:

```yaml
jobs:
  render:
    runs-on: ubuntu-latest
    services:
      drawio:
        image: tomkludy/drawio-renderer:latest
        ports: ["5000:5000"]
    steps:
      - uses: actions/checkout@v4
      - name: Render via REST
        run: |
          curl -s -X POST http://localhost:5000/convert \
            -H 'Content-Type: application/json' \
            -d "$(python3 -c 'import json,sys;print(json.dumps({
                  "source": open("diagrams/infra.drawio").read(),
                  "format": "png", "scale": 2}))')" \
            -o diagrams/infra.png
```

Validation (`validate.py --strict`) needs only Python — it runs the same way in both options.

## Committing rendered images back

Prefer uploading artifacts or publishing to Pages over committing PNGs. If you do commit them (e.g. README images), guard against loops:

```yaml
      - name: Commit refreshed diagrams
        run: |
          git config user.name github-actions
          git config user.email github-actions@github.com
          git add diagrams/*.png
          git diff --cached --quiet || git commit -m "ci: refresh diagrams [skip ci]"
          git push
```
