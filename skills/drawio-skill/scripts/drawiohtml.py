#!/usr/bin/env python3
"""Publish a .drawio as a single interactive HTML viewer.

Exports every page to SVG via the draw.io CLI and inlines them into ONE
self-contained .html with pan (drag), zoom (wheel / buttons), page tabs,
node search, and working links — external links open normally and internal
page links ("data:page/id,…", e.g. a C4 model's drill-down) switch tabs
inside the viewer. Share the file with anyone: no draw.io, no server,
no external requests.

  python3 drawiohtml.py architecture.drawio -o architecture.html
  python3 drawiohtml.py c4.drawio                # -> c4.html, drill-down works

Search matches node text (draw.io wraps every cell in <g data-cell-id>);
matches glow, Enter cycles through them and centres each. Internal page
links survive export by being rewritten to "#page-<id>" fragments first
(draw.io drops raw data:page/id links from SVG).

Usage: python3 drawiohtml.py <file.drawio> [-o out.html]
"""
import argparse
import html
import json
import os
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

PAGE_LINK = "data:page/id,"


def pages_of(path):
    """[(id, name)] of the <diagram> pages, in order."""
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as exc:
        sys.exit(f"error: cannot parse {path}: {exc}")
    return [(d.get("id") or f"p{i}", d.get("name") or f"Page {i + 1}")
            for i, d in enumerate(root.findall("diagram"))]


def rewrite_page_links(tree):
    """data:page/id,X links -> #page-X (fragments survive SVG export). Returns count."""
    n = 0
    for el in tree.getroot().iter():
        link = el.get("link")
        if link and link.startswith(PAGE_LINK):
            el.set("link", "#page-" + link[len(PAGE_LINK):])
            n += 1
    return n


def export_svg(drawio_file, index, out_svg):
    """Export one page (1-based index) to SVG via the draw.io CLI."""
    r = subprocess.run(["drawio", "-x", "-f", "svg", "--page-index", str(index),
                        "-o", out_svg, drawio_file], capture_output=True)
    return r.returncode == 0 and os.path.exists(out_svg)


def strip_prolog(svg):
    """Drop any XML declaration / doctype so the SVG can be inlined in HTML."""
    return re.sub(r"^\s*(<\?xml[^>]*\?>\s*|<!DOCTYPE[^>]*>\s*)*", "", svg)


def build_html(title, page_meta, svgs):
    """One self-contained viewer page. page_meta = [(id, name)] aligned with svgs."""
    sections = "\n".join(
        f'<div class="page" data-pgid="{html.escape(pid, quote=True)}">{svg}</div>'
        for (pid, _), svg in zip(page_meta, svgs))
    tabs = json.dumps([{"id": pid, "name": name} for pid, name in page_meta]) \
        .replace("</", "<\\/")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><style>
:root{{color-scheme:light dark}}
*{{box-sizing:border-box}}
body{{margin:0;font:14px/1.5 system-ui,-apple-system,Segoe UI,sans-serif;
background:#f6f7f9;color:#1a1a1a;height:100vh;display:flex;flex-direction:column}}
@media(prefers-color-scheme:dark){{body{{background:#15171a;color:#e8e8e8}}}}
header{{padding:10px 16px 8px;display:flex;gap:12px;align-items:center;flex-wrap:wrap}}
h1{{margin:0;font-size:15px;font-weight:600}}
nav{{display:flex;gap:6px;flex-wrap:wrap}}
button,input{{font:inherit;color:inherit}}
nav button,.ctl button{{padding:4px 10px;border:1px solid #0002;border-radius:8px;
background:#fff;cursor:pointer}}
@media(prefers-color-scheme:dark){{nav button,.ctl button{{background:#262b31;border-color:#fff2}}}}
nav button.on{{border-color:#0d99ff;color:#0d99ff;font-weight:600}}
.ctl{{display:flex;gap:8px;align-items:center;margin-left:auto}}
.ctl input{{padding:4px 10px;border:1px solid #0002;border-radius:8px;background:#fff;width:180px}}
@media(prefers-color-scheme:dark){{.ctl input{{background:#262b31;border-color:#fff2}}}}
#hits{{font-size:12px;color:#889;min-width:56px}}
#stage{{flex:1;overflow:hidden;position:relative;background:#fff;
border-top:1px solid #0001;cursor:grab;touch-action:none}}
@media(prefers-color-scheme:dark){{#stage{{background:#1e2226;border-color:#fff2}}}}
#stage.drag{{cursor:grabbing}}
.page{{position:absolute;transform-origin:0 0;display:none}}
.page.on{{display:block}}
.page svg{{display:block}}
.hit{{filter:drop-shadow(0 0 3px #ff9800) drop-shadow(0 0 6px #ff980088)}}
.hit.cursel{{filter:drop-shadow(0 0 4px #f44336) drop-shadow(0 0 9px #f44336aa)}}
</style></head><body>
<header><h1>{html.escape(title)}</h1><nav id="tabs"></nav>
<div class="ctl">
 <input id="q" type="search" placeholder="Search nodes… Enter = next">
 <span id="hits"></span>
 <button id="zout" title="zoom out">−</button><button id="zin" title="zoom in">+</button>
 <button id="fit">Fit</button>
</div></header>
<main id="stage">
{sections}
</main>
<script>
const META={tabs};
const stage=document.getElementById('stage');
const pages=[...document.querySelectorAll('.page')];
const view=pages.map(()=>({{x:0,y:0,s:1}}));
let cur=0,hits=[],hi=-1;
const tabs=document.getElementById('tabs');
if(META.length>1)META.forEach((m,i)=>{{
  const b=document.createElement('button');b.textContent=m.name;
  b.onclick=()=>show(i);tabs.appendChild(b);}});
function apply(){{const v=view[cur];
  pages[cur].style.transform=`translate(${{v.x}}px,${{v.y}}px) scale(${{v.s}})`;}}
function svgSize(i){{const s=pages[i].querySelector('svg');
  return[parseFloat(s.getAttribute('width'))||800,
         parseFloat(s.getAttribute('height'))||600];}}
function fit(){{const[w,h]=svgSize(cur),r=stage.getBoundingClientRect(),
  s=Math.min((r.width-40)/w,(r.height-40)/h,4);
  view[cur]={{s,x:(r.width-w*s)/2,y:(r.height-h*s)/2}};apply();}}
function show(i){{cur=i;
  pages.forEach((p,j)=>p.classList.toggle('on',j===i));
  [...tabs.children].forEach((b,j)=>b.classList.toggle('on',j===i));
  if(!pages[i].dataset.seen){{pages[i].dataset.seen=1;fit();}}else apply();
  search();}}
stage.addEventListener('wheel',e=>{{e.preventDefault();const v=view[cur],
  r=stage.getBoundingClientRect(),mx=e.clientX-r.left,my=e.clientY-r.top,
  k=Math.exp(-e.deltaY*0.0015),s=Math.min(Math.max(v.s*k,0.05),8);
  v.x=mx-(mx-v.x)*s/v.s;v.y=my-(my-v.y)*s/v.s;v.s=s;apply();}},{{passive:false}});
let drag=null;
stage.addEventListener('pointerdown',e=>{{if(e.target.closest('a'))return;
  drag={{x:e.clientX,y:e.clientY}};stage.classList.add('drag');
  stage.setPointerCapture(e.pointerId);}});
stage.addEventListener('pointermove',e=>{{if(!drag)return;const v=view[cur];
  v.x+=e.clientX-drag.x;v.y+=e.clientY-drag.y;
  drag={{x:e.clientX,y:e.clientY}};apply();}});
stage.addEventListener('pointerup',()=>{{drag=null;stage.classList.remove('drag');}});
function zoom(k){{const v=view[cur],r=stage.getBoundingClientRect(),
  mx=r.width/2,my=r.height/2,s=Math.min(Math.max(v.s*k,0.05),8);
  v.x=mx-(mx-v.x)*s/v.s;v.y=my-(my-v.y)*s/v.s;v.s=s;apply();}}
document.getElementById('zin').onclick=()=>zoom(1.25);
document.getElementById('zout').onclick=()=>zoom(0.8);
document.getElementById('fit').onclick=fit;
// Internal page links: any anchor whose target ends in #page-<id> switches tabs.
document.addEventListener('click',e=>{{const a=e.target.closest('a');
  if(!a)return;const href=a.getAttribute('xlink:href')||a.getAttribute('href')||'';
  const m=href.match(/#page-(.+)$/);if(!m)return;e.preventDefault();
  const i=META.findIndex(p=>p.id===decodeURIComponent(m[1]));if(i>=0)show(i);}},true);
const q=document.getElementById('q'),hitEl=document.getElementById('hits');
function search(){{
  hits.forEach(g=>g.classList.remove('hit','cursel'));hits=[];hi=-1;
  const t=q.value.trim().toLowerCase();
  if(t){{
    const all=[...pages[cur].querySelectorAll('g[data-cell-id]')]
      .filter(g=>!['0','1'].includes(g.dataset.cellId))
      .filter(g=>g.textContent.toLowerCase().includes(t));
    hits=all.filter(g=>!all.some(o=>o!==g&&g.contains(o)));   // innermost only
    hits.forEach(g=>g.classList.add('hit'));
  }}
  hitEl.textContent=t?hits.length+' hit'+(hits.length===1?'':'s'):'';}}
function centre(g){{const v=view[cur],r=stage.getBoundingClientRect(),
  b=g.getBoundingClientRect();
  v.x+=r.left+r.width/2-(b.left+b.width/2);
  v.y+=r.top+r.height/2-(b.top+b.height/2);apply();}}
q.addEventListener('input',search);
q.addEventListener('keydown',e=>{{
  if(e.key==='Escape'){{q.value='';search();q.blur();}}
  if(e.key!=='Enter'||!hits.length)return;
  if(hi>=0)hits[hi].classList.remove('cursel');
  hi=(hi+1)%hits.length;hits[hi].classList.add('cursel');centre(hits[hi]);}});
show(0);
</script></body></html>
"""


def main():
    ap = argparse.ArgumentParser(description="Export a .drawio to a self-contained interactive HTML viewer.")
    ap.add_argument("file")
    ap.add_argument("-o", "--output", help="output .html (default: alongside input)")
    args = ap.parse_args()

    if not os.path.isfile(args.file):
        sys.exit(f"error: {args.file} not found")
    meta = pages_of(args.file)
    if not meta:
        sys.exit(f"error: no <diagram> pages in {args.file}")

    tree = ET.parse(args.file)
    relinked = rewrite_page_links(tree)

    svgs, kept = [], []
    with tempfile.TemporaryDirectory() as tmp:
        src = args.file
        if relinked:                          # export the rewritten copy instead
            src = os.path.join(tmp, "relinked.drawio")
            tree.write(src, encoding="utf-8", xml_declaration=False)
        for i, (pid, name) in enumerate(meta, 1):   # draw.io --page-index is 1-based
            out = os.path.join(tmp, f"p{i}.svg")
            if not export_svg(src, i, out):
                sys.stderr.write(f"warning: page {i} ({name}) export failed — skipped\n")
                continue
            with open(out, encoding="utf-8") as f:
                svgs.append(strip_prolog(f.read()))
            kept.append((pid, name))

    if not svgs:
        sys.exit("error: no pages exported (is the draw.io CLI installed?)")
    title = os.path.splitext(os.path.basename(args.file))[0]
    out = args.output or os.path.splitext(args.file)[0] + ".html"
    with open(out, "w", encoding="utf-8") as f:
        f.write(build_html(title, kept, svgs))
    sys.stderr.write(f"wrote {out} ({len(svgs)} page{'s' if len(svgs) != 1 else ''}"
                     + (f", {relinked} drill-down link{'s' if relinked != 1 else ''}" if relinked else "")
                     + ")\n")


if __name__ == "__main__":
    main()
