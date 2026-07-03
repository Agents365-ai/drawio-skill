#!/usr/bin/env python3
"""Animate how a codebase's architecture grew, across its git history.

Walks the git history of a directory, re-runs one of the bundled importers at
each sampled commit (the tree is pulled with ``git archive`` — the working copy
is never touched), lays each out and exports a PNG frame, then assembles a
single self-contained HTML player (frames embedded as base64, play / step
controls, no external files or CDNs). Open it in any browser to watch the
modules and edges appear over time.

  python3 timelapse.py skills/drawio-skill/scripts --importer pyimports
  # -> architecture-evolution.html

The importer is any of the bundled graph extractors (pyimports, jsimports,
goimports, rustimports, pyclasses, tfimports, k8simports, composeimports,
sqlerd); it is run against the archived directory with the same positional
"path" argument they all take, so point the path at the project/package/infra
root the importer expects. Extra importer flags pass through via
``--importer-args`` (e.g. ``--importer-args "--group"``).

Commits that touched the directory are sampled evenly (always keeping the first
and last) down to ``--max-frames``; a commit where the importer finds nothing
(the path did not exist yet) is skipped. Needs git, the importer's requirements,
Graphviz (autolayout) and the draw.io CLI — the same tools the importers use.

Usage: python3 timelapse.py <dir> [--importer NAME] [--importer-args STR]
       [--max-frames N] [-o out.html] [--direction TB|LR] [--keep-frames]
"""
import argparse
import base64
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
IMPORTERS = {"pyimports", "jsimports", "goimports", "rustimports", "pyclasses",
             "tfimports", "k8simports", "composeimports", "sqlerd"}


def git(root, *args):
    """Run a git command in `root`; return (returncode, stdout_bytes)."""
    p = subprocess.run(["git", "-C", root, *args], capture_output=True)
    return p.returncode, p.stdout


def sample_indices(total, n):
    """Evenly-spaced indices across range(total), always incl. first and last.

    For total <= n every index is kept; otherwise n indices are picked so the
    first (0) and last (total-1) are always present and the rest are spread
    uniformly between them.
    """
    if total <= 0:
        return []
    if total <= n or n <= 1:
        return list(range(total))
    return sorted({round(i * (total - 1) / (n - 1)) for i in range(n)})


def history(root, subpath):
    """Chronological [(hash, iso_date, subject), ...] of commits touching subpath."""
    code, out = git(root, "log", "--format=%H%x09%aI%x09%s", "--", subpath or ".")
    if code != 0:
        return []
    rows = []
    for line in out.decode("utf-8", "replace").splitlines():
        parts = line.split("\t", 2)
        if len(parts) == 3:
            rows.append(tuple(parts))
    return list(reversed(rows))                        # oldest first


def extract_tree(root, commit, subpath, dest):
    """Extract subpath of `commit` into dest via git archive. False if absent."""
    code, tar_bytes = git(root, "archive", commit, subpath or ".")
    if code != 0 or not tar_bytes:
        return False
    with tarfile.open(fileobj=io.BytesIO(tar_bytes)) as tf:
        tf.extractall(dest)                            # git-authored tar; trusted
    return True


def build_frame(importer, importer_args, work_path, direction, tmp):
    """Importer -> autolayout -> PNG for one commit. Returns (png_bytes, n, e) or None."""
    graph_json = os.path.join(tmp, "graph.json")
    imp = subprocess.run(
        [sys.executable, os.path.join(HERE, importer + ".py"), work_path,
         "-o", graph_json, *importer_args],
        capture_output=True)
    if imp.returncode != 0 or not os.path.exists(graph_json):
        return None
    graph = json.loads(open(graph_json, encoding="utf-8").read())
    if not graph.get("nodes"):
        return None
    graph["direction"] = direction
    open(graph_json, "w", encoding="utf-8").write(json.dumps(graph))
    drawio = os.path.join(tmp, "frame.drawio")
    lay = subprocess.run(
        [sys.executable, os.path.join(HERE, "autolayout.py"), graph_json, "-o", drawio],
        capture_output=True)
    if lay.returncode != 0 or not os.path.exists(drawio):
        return None
    png = os.path.join(tmp, "frame.png")
    exp = subprocess.run(["drawio", "-x", "-f", "png", "--width", "1600",
                          "-o", png, drawio], capture_output=True)
    if exp.returncode != 0 or not os.path.exists(png):
        return None
    return open(png, "rb").read(), len(graph["nodes"]), len(graph["edges"])


def build_html(frames, title):
    """Self-contained HTML player for the frame list."""
    data = [{"img": "data:image/png;base64," + base64.b64encode(png).decode(),
             "hash": h[:9], "date": d[:10], "subj": s, "n": n, "e": e}
            for png, h, d, s, n, e in frames]
    peak = max((f["n"] for f in data), default=1) or 1
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
.cap b{{color:inherit;font-weight:600}}.cap .subj{{color:#1a1a1a}}
@media(prefers-color-scheme:dark){{.cap .subj{{color:#e8e8e8}}}}
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
<div id="stage"><img id="img" alt="architecture frame"></div>
<div class="cap">
  <span><b id="idx"></b></span>
  <span><b id="hash"></b> · <span id="date"></span></span>
  <span class="subj" id="subj"></span>
  <span id="counts"></span>
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
const F={payload},PEAK={peak};
let i=0,timer=null;
const $=id=>document.getElementById(id);
$("scrub").max=F.length-1;
function show(k){{
  i=(k+F.length)%F.length;const f=F[i];
  $("img").src=f.img;$("idx").textContent=`Frame ${{i+1}} / ${{F.length}}`;
  $("hash").textContent=f.hash;$("date").textContent=f.date;$("subj").textContent=f.subj;
  $("counts").textContent=`${{f.n}} nodes · ${{f.e}} edges`;
  $("bar").style.width=(6+94*f.n/PEAK)+"%";$("scrub").value=i;
}}
function stop(){{clearInterval(timer);timer=null;$("play").textContent="▶ Play";}}
$("prev").onclick=()=>{{stop();show(i-1);}};
$("next").onclick=()=>{{stop();show(i+1);}};
$("scrub").oninput=e=>{{stop();show(+e.target.value);}};
$("play").onclick=()=>{{
  if(timer){{stop();return;}}
  $("play").textContent="⏸ Pause";
  timer=setInterval(()=>{{if(i>=F.length-1){{show(0);}}else{{show(i+1);}}}},900);
}};
show(0);
</script></body></html>"""


def main():
    ap = argparse.ArgumentParser(description="Git-history architecture time-lapse -> HTML player.")
    ap.add_argument("path", help="directory to visualize (inside a git repo)")
    ap.add_argument("--importer", default="pyimports",
                    help="bundled importer to run at each commit (default pyimports)")
    ap.add_argument("--importer-args", default="",
                    help="extra args passed to the importer, e.g. \"--group\"")
    ap.add_argument("--max-frames", type=int, default=10, help="sample down to N commits")
    ap.add_argument("--direction", default="TB", choices=["TB", "LR"])
    ap.add_argument("-o", "--output", default="architecture-evolution.html")
    ap.add_argument("--keep-frames", action="store_true",
                    help="also write the PNG frames next to the HTML")
    args = ap.parse_args()

    importer = args.importer[:-3] if args.importer.endswith(".py") else args.importer
    if importer not in IMPORTERS:
        sys.exit(f"error: unknown importer {importer!r} (choose one of: "
                 + ", ".join(sorted(IMPORTERS)) + ")")
    if not os.path.isdir(args.path):
        sys.exit(f"error: {args.path} is not a directory")
    code, top = git(args.path, "rev-parse", "--show-toplevel")
    if code != 0:
        sys.exit(f"error: {args.path} is not inside a git repository")
    root = top.decode().strip()
    subpath = os.path.relpath(os.path.abspath(args.path), root)
    if subpath == ".":
        subpath = ""

    commits = history(root, subpath)
    if not commits:
        sys.exit(f"error: no commits touch {args.path}")
    picked = [commits[i] for i in sample_indices(len(commits), args.max_frames)]
    imp_args = args.importer_args.split()

    frames = []
    for n, (h, date, subj) in enumerate(picked, 1):
        sys.stderr.write(f"[{n}/{len(picked)}] {h[:9]} {subj[:50]}\n")
        with tempfile.TemporaryDirectory() as tmp:
            if not extract_tree(root, h, subpath, tmp):
                continue
            work = os.path.join(tmp, subpath) if subpath else tmp
            frame = build_frame(importer, imp_args, work, args.direction, tmp)
            if frame is None:
                sys.stderr.write("    (importer found nothing — skipped)\n")
                continue
            png, nn, ee = frame
            frames.append((png, h, date, subj, nn, ee))
            if args.keep_frames:
                fp = f"{os.path.splitext(args.output)[0]}-frame{len(frames):02d}.png"
                open(fp, "wb").write(png)

    if not frames:
        sys.exit("error: no frames produced (importer found nothing in any commit)")
    title = f"Architecture evolution — {os.path.basename(os.path.abspath(args.path))}"
    open(args.output, "w", encoding="utf-8").write(build_html(frames, title))
    sys.stderr.write(f"wrote {args.output} ({len(frames)} frames)\n")


if __name__ == "__main__":
    main()
