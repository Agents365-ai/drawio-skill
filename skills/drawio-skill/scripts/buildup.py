#!/usr/bin/env python3
"""Animate a static .drawio building itself, node by node -> HTML player.

Reveals a diagram's cells incrementally in dependency order — topological over
its edges, so a source always appears before the targets it points to, with
ties (and any leftover cycle members) falling back to document order — and
assembles a self-contained HTML player (base64-embedded PNG frames, play /
pause / step / scrub) of the diagram constructing itself, like a build
time-lapse.

  python3 buildup.py architecture.drawio
  # -> architecture.drawio's directory / buildup.html
  python3 buildup.py architecture.drawio -o build.html --gif build.gif

Each frame is a temp copy of the diagram with not-yet-revealed cells removed
from <root> (not opacity — draw.io ignores that on headless export). An edge
is only shown once BOTH its endpoints are revealed. Container/group cells are
always shown (only leaf vertices and the edges between them build up one step
at a time). The page size is pinned to the FULL diagram's bounding box on
every frame so nothing jumps around as cells appear. Needs the draw.io CLI;
`--gif` additionally needs Pillow (skipped with a warning if absent — the
HTML is written regardless).

Usage: python3 buildup.py <file.drawio> [-o out.html] [--gif out.gif]
       [--fps N] [--hold N] [--keep-frames]
"""
import argparse
import base64
import copy
import io
import json
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:  # loaded by file path (tests): keep the sibling import working
    sys.path.insert(0, HERE)
from drawio_cli import resolve_drawio


def parse_page(path):
    """First page of a .drawio -> (tree, cells).

    cells: list of dicts {id, el, vertex, edge, parent, source, target, style,
    relative, x, y, w, h} in document order. `el` is the TOP-LEVEL <root>
    child (mxCell / UserObject / object) so it can be removed directly;
    vertex/edge/geometry attributes are read off the inner mxCell for wrapped
    cells (UserObject/object), same unwrapping as drawiodiff.parse().
    """
    try:
        tree = ET.parse(path)
    except (ET.ParseError, OSError) as exc:
        sys.exit(f"error: cannot parse {path}: {exc}")
    pages = tree.getroot().findall("diagram")
    if not pages:
        sys.exit(f"error: no <diagram> pages in {path}")
    if len(pages) > 1:
        sys.stderr.write(f"warning: {path} has {len(pages)} pages, animating the first only\n")
    model = pages[0].find("mxGraphModel")
    root = model.find("root") if model is not None else None
    if root is None:
        sys.exit(f"error: {path}: page is compressed, cannot buildup")

    cells = []
    for el in root:
        inner = el if el.tag == "mxCell" else el.find("mxCell")
        if inner is None:
            continue
        g = inner.find("mxGeometry")
        relative = g is not None and g.get("relative") == "1"
        if g is not None and not relative and g.get("x") is not None and g.get("width") is not None:
            x, y = float(g.get("x")), float(g.get("y", 0))
            w, h = float(g.get("width")), float(g.get("height", 0))
        else:
            x = y = w = h = None
        cells.append({
            "id": el.get("id"), "el": el,
            "vertex": inner.get("vertex") == "1", "edge": inner.get("edge") == "1",
            "parent": inner.get("parent"), "source": inner.get("source"),
            "target": inner.get("target"), "style": inner.get("style") or "",
            "relative": relative, "x": x, "y": y, "w": w, "h": h,
        })
    return tree, cells


def classify(cells):
    """cells -> (leaf_vertex_ids in doc order, container_ids, edges[(id,source,target)]).

    Mirrors drawiodiff.parse(): a vertex that is some other cell's `parent` is
    a container/group (always shown, never an individual reveal step); an
    edge-label sub-cell (relative geometry or an `edgeLabel` style) is neither
    a node nor revealed on its own — it rides along once its parent edge is.
    """
    parents = {c["parent"] for c in cells if c["parent"]}
    leaves, containers, edges = [], set(), []
    for c in cells:
        if c["edge"]:
            if c["source"] and c["target"]:
                edges.append((c["id"], c["source"], c["target"]))
        elif c["vertex"]:
            if c["relative"] or "edgeLabel" in c["style"]:
                continue
            if c["id"] in parents:
                containers.add(c["id"])
            else:
                leaves.append(c["id"])
    return leaves, containers, edges


def bounding_box(cells, margin=40):
    """(width, height) of the full diagram from every absolute cell geometry,
    with a margin — used to pin pageWidth/pageHeight so frames don't jump."""
    xs = [c["x"] + c["w"] for c in cells if c["x"] is not None]
    ys = [c["y"] + c["h"] for c in cells if c["y"] is not None]
    if not xs or not ys:
        return 850, 1100
    return int(max(xs)) + margin, int(max(ys)) + margin


def reveal_order(node_ids, edges):
    """Kahn topological order over node_ids given directed (source, target)
    edges. Ties among ready nodes, and any nodes left over from a cycle, fall
    back to document order (node_ids' input order)."""
    doc = list(dict.fromkeys(node_ids))                    # de-dup, keep doc order
    idx = {nid: i for i, nid in enumerate(doc)}
    adj = {nid: [] for nid in doc}
    indeg = {nid: 0 for nid in doc}
    for s, t in edges:
        if s in idx and t in idx and s != t:
            adj[s].append(t)
            indeg[t] += 1

    import heapq
    ready = list({idx[n] for n in doc if indeg[n] == 0})
    heapq.heapify(ready)
    order, seen = [], set()
    while ready:
        nid = doc[heapq.heappop(ready)]
        seen.add(nid)
        order.append(nid)
        for nxt in adj[nid]:
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                heapq.heappush(ready, idx[nxt])
    for nid in doc:                                        # cycle remnants, document order
        if nid not in seen:
            order.append(nid)
    return order


def reveal_steps(node_order, edges):
    """-> (node_step {id: int}, edge_step {edge_id: int}). An edge's step is
    the LATER of its two endpoints' steps, so it only appears once both are
    revealed (endpoints outside node_order, e.g. a container, count as step 0
    — already shown)."""
    node_step = {nid: i for i, nid in enumerate(node_order)}
    edge_step = {eid: max(node_step.get(s, 0), node_step.get(t, 0)) for eid, s, t in edges}
    return node_step, edge_step


def label_of(el):
    """Visible text of a root child (mxCell or UserObject/object wrapper)."""
    if el.tag == "mxCell":
        return el.get("value") or el.get("id") or ""
    return el.get("label") or el.get("value") or el.get("id") or ""


def build_html(frames, title):
    """Self-contained HTML player. frames: [(png_bytes, label, step, total)]."""
    data = [{"img": "data:image/png;base64," + base64.b64encode(png).decode(),
             "label": label, "step": step, "total": total}
            for png, label, step, total in frames]
    payload = json.dumps(data).replace("</", "<\\/")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>
:root{{color-scheme:light dark}}
*{{box-sizing:border-box}}
body{{margin:0;font:14px/1.5 system-ui,-apple-system,Segoe UI,sans-serif;
background:#f6f7f9;color:#1a1a1a}}
@media(prefers-color-scheme:dark){{body{{background:#15171a;color:#e8e8e8}}}}
header{{padding:16px 20px 4px}}h1{{margin:0;font-size:17px;font-weight:600}}
main{{max-width:1100px;margin:0 auto;padding:8px 16px 28px}}
#stage{{background:#fff;border:1px solid #0001;border-radius:10px;
min-height:60vh;display:flex;align-items:center;justify-content:center;padding:12px}}
@media(prefers-color-scheme:dark){{#stage{{background:#1e2226;border-color:#fff2}}}}
#stage img{{max-width:100%;max-height:74vh;object-fit:contain}}
.cap{{display:flex;gap:14px;flex-wrap:wrap;align-items:baseline;
padding:12px 4px 6px;color:#556;font-size:13px}}
@media(prefers-color-scheme:dark){{.cap{{color:#9aa}}}}
.cap .lbl{{color:#1a1a1a;font-weight:600}}
@media(prefers-color-scheme:dark){{.cap .lbl{{color:#e8e8e8}}}}
.bar{{height:6px;border-radius:3px;background:#0d99ff;transition:width .3s}}
.barwrap{{height:6px;background:#0001;border-radius:3px;margin:2px 4px 12px}}
.ctl{{display:flex;gap:10px;align-items:center;padding:4px}}
button{{font:inherit;padding:6px 12px;border:1px solid #0002;border-radius:8px;
background:#fff;cursor:pointer;color:inherit}}
@media(prefers-color-scheme:dark){{button{{background:#262b31;border-color:#fff2}}}}
button:hover{{border-color:#0d99ff}}
input[type=range]{{flex:1;accent-color:#0d99ff}}
</style></head><body>
<header><h1>{title}</h1></header>
<main>
<div id="stage"><img id="img" alt="build-up frame"></div>
<div class="cap">
  <span><b id="idx"></b></span>
  <span>+ <span class="lbl" id="label"></span></span>
</div>
<div class="barwrap"><div class="bar" id="bar"></div></div>
<div class="ctl">
  <button id="prev">‹ Prev</button>
  <button id="play">▶ Play</button>
  <button id="next">Next ›</button>
  <input type="range" id="scrub" min="0" value="0">
</div>
</main>
<script>
const F={payload};
let i=0,timer=null;
const $=id=>document.getElementById(id);
$("scrub").max=F.length-1;
function show(k){{
  i=(k+F.length)%F.length;const f=F[i];
  $("img").src=f.img;$("idx").textContent=`Step ${{f.step}} / ${{f.total}}`;
  $("label").textContent=f.label;
  $("bar").style.width=(6+94*f.step/f.total)+"%";$("scrub").value=i;
}}
function stop(){{clearInterval(timer);timer=null;$("play").textContent="▶ Play";}}
$("prev").onclick=()=>{{stop();show(i-1);}};
$("next").onclick=()=>{{stop();show(i+1);}};
$("scrub").oninput=e=>{{stop();show(+e.target.value);}};
$("play").onclick=()=>{{
  if(timer){{stop();return;}}
  $("play").textContent="⏸ Pause";
  timer=setInterval(()=>{{if(i>=F.length-1){{show(0);}}else{{show(i+1);}}}},700);
}};
show(0);
</script></body></html>"""


def make_gif(pngs, out_path, fps, hold):
    """Assemble PNG frame bytes into an animated GIF via Pillow. Skips with a
    stderr warning (not fatal) if Pillow isn't installed."""
    try:
        from PIL import Image
    except ImportError:
        sys.stderr.write("warning: Pillow not installed, skipping --gif (pip install Pillow)\n")
        return
    frames = [Image.open(io.BytesIO(p)).convert("RGB") for p in pngs]
    duration = [int(1000 / fps)] * (len(frames) - 1) + [int(hold * 1000)]
    frames[0].save(out_path, save_all=True, append_images=frames[1:],
                   duration=duration, loop=0)
    sys.stderr.write(f"wrote {out_path} ({len(frames)} frames)\n")


def main():
    ap = argparse.ArgumentParser(description="Animate a .drawio building itself -> self-contained HTML player.")
    ap.add_argument("file", help="input .drawio (uncompressed)")
    ap.add_argument("-o", "--output", help="output .html (default: buildup.html alongside input)")
    ap.add_argument("--gif", help="also assemble frames into an animated GIF (needs Pillow)")
    ap.add_argument("--fps", type=float, default=2.0, help="GIF frames per second (default 2)")
    ap.add_argument("--hold", type=float, default=1.5, help="seconds to hold the final GIF frame")
    ap.add_argument("--keep-frames", action="store_true", help="also write the PNG frames next to the output")
    args = ap.parse_args()

    if not os.path.isfile(args.file):
        sys.exit(f"error: {args.file} not found")
    drawio = resolve_drawio()
    if not drawio:
        sys.exit("error: draw.io CLI not found on PATH (is the draw.io CLI installed?)")

    tree, cells = parse_page(args.file)
    leaves, containers, edge_list = classify(cells)
    if not leaves:
        sys.exit(f"error: no revealable vertices found in {args.file}")

    order = reveal_order(leaves, [(s, t) for _, s, t in edge_list])
    node_step, edge_step = reveal_steps(order, edge_list)
    width, height = bounding_box(cells)
    labels = {c["id"]: label_of(c["el"]) for c in cells}
    n_total = len(order)

    out = args.output or os.path.join(
        os.path.dirname(os.path.abspath(args.file)) or ".", "buildup.html")

    frames = []
    with tempfile.TemporaryDirectory() as tmp:
        for k in range(n_total):
            revealed_nodes = set(order[:k + 1])
            revealed_edges = {eid for eid, _, _ in edge_list if edge_step[eid] <= k}
            keep = {"0", "1"} | containers | revealed_nodes | revealed_edges
            keep |= {c["id"] for c in cells if c["id"] not in keep and c["parent"] in keep}

            frame_tree = copy.deepcopy(tree)
            model = frame_tree.getroot().find("diagram").find("mxGraphModel")
            model.set("pageWidth", str(width))
            model.set("pageHeight", str(height))
            froot = model.find("root")
            for child in list(froot):
                if child.get("id") not in keep:
                    froot.remove(child)

            src = os.path.join(tmp, f"step{k:03d}.drawio")
            frame_tree.write(src, encoding="utf-8", xml_declaration=False)
            png_path = os.path.join(tmp, f"step{k:03d}.png")
            r = subprocess.run([drawio, "-x", "-f", "png", "--page-index", "1",
                                "--width", "2000", "-o", png_path, src], capture_output=True)
            if r.returncode != 0 or not os.path.exists(png_path):
                sys.stderr.write(f"warning: step {k + 1}/{n_total} export failed — skipped\n")
                continue
            with open(png_path, "rb") as f:
                png = f.read()
            label = labels.get(order[k], order[k])
            frames.append((png, label, k + 1, n_total))
            if args.keep_frames:
                with open(f"{os.path.splitext(out)[0]}-frame{k + 1:03d}.png", "wb") as f:
                    f.write(png)
            sys.stderr.write(f"[{k + 1}/{n_total}] revealed {label!r}\n")

    if not frames:
        sys.exit("error: no frames exported (is the draw.io CLI installed?)")

    title = os.path.splitext(os.path.basename(args.file))[0] + " — build-up"
    with open(out, "w", encoding="utf-8") as f:
        f.write(build_html(frames, title))
    sys.stderr.write(f"wrote {out} ({len(frames)} frames)\n")

    if args.gif:
        make_gif([f[0] for f in frames], args.gif, args.fps, args.hold)


if __name__ == "__main__":
    main()
