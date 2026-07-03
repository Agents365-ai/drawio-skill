# 在 CI 中渲染图表

[English](CI.md)

把图表的**源**放进仓库(importer 产出的 graph JSON、`seq.json`、`c4.json`,或手写的 `.drawio`),由 CI 负责重新生成、校验、导出 —— 完整的 diagram-as-code 闭环:

```
源 (.tf / manifests / schema.sql / seq.json / graph.json)
   → 提取器 (tfimports / k8simports / sqlerd / seqlayout / …)
   → autolayout.py → validate.py --strict（门禁）→ drawio -x（渲染）→ 产物
```

Importer 的节点 id 是稳定的(模块路径、`type.name`、`kind/name`),代码或基础设施变更后重新生成的 `.drawio` diff 可读、可 review。

## 方案 A —— draw.io 桌面版 + xvfb(GitHub Actions)

桌面版 CLI 在 `xvfb` 下可无头运行。完整 workflow:

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

      # 本 skill 的脚本(importer、autolayout、validate)
      - run: git clone --depth 1 https://github.com/Agents365-ai/drawio-skill /tmp/drawio-skill
      - run: sudo apt-get update && sudo apt-get install -y graphviz xvfb

      # draw.io 桌面版(最新 release 的 .deb)
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
          python3 $S/validate.py diagrams/infra.drawio --strict   # 门禁:任何警告即失败
          export HOME=${HOME:-/tmp}
          xvfb-run -a --server-args="-screen 0 1280x1024x24" \
            drawio -x -f png -e -s 2 -o diagrams/infra.drawio.png \
            diagrams/infra.drawio --disable-gpu --no-sandbox
          python3 $S/repair_png.py diagrams/infra.drawio.png       # 修复 -e 的 IEND 截断

      - uses: actions/upload-artifact@v4
        with: {name: diagrams, path: "diagrams/*.png"}
```

注意事项(均来自本 skill 的踩坑记录):

- `--no-sandbox` 必须放在**最后一个**参数 —— 放前面会被当成输入文件名。CI 容器以 root 运行时必需。
- Runner 没有 home 目录时 `export HOME=/tmp`;服务器上加 `--disable-gpu`。
- 任何 `-e` PNG 导出之后都要跑 `repair_png.py` —— CLI 会截断 IEND chunk(issue #8)。
- `--page-index <n>`(1-based)导出多页文件的指定页(如 `c4.py` 的输出)。
- `.deb` 安装报缺库时:`sudo apt-get install -y libgtk-3-0 libnotify4 libnss3 libgbm1 libasound2t64`。

## 方案 B —— Docker REST 渲染器(无需安装桌面版)

[`tomkludy/drawio-renderer`](https://hub.docker.com/r/tomkludy/drawio-renderer) 把无头导出封装成 REST API,适合不方便装 `.deb` 的 runner:

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

校验(`validate.py --strict`)只需要 Python,两种方案下用法完全一致。

## 把渲染结果提交回仓库

优先用 artifact 或发布到 Pages,而不是提交 PNG。确实要提交(比如 README 配图)时,注意防循环:

```yaml
      - name: Commit refreshed diagrams
        run: |
          git config user.name github-actions
          git config user.email github-actions@github.com
          git add diagrams/*.png
          git diff --cached --quiet || git commit -m "ci: refresh diagrams [skip ci]"
          git push
```
