#!/usr/bin/env python3
"""Find AI / LLM brand logos (OpenAI, Claude, Gemini, ...) as draw.io styles.

draw.io's bundled shape libraries have no modern AI/LLM brand logos, so an
"LLM app architecture" renders as generic boxes. This resolves a brand name to a
draw.io `image` style that references the matching SVG from the lobe-icons set
(https://github.com/lobehub/lobe-icons, MIT) on the unpkg CDN.

  python3 aiicons.py "openai"
  python3 aiicons.py "claude" --json
  python3 aiicons.py "langchain" --variant mono --size 48

The icon is referenced by URL (data/lobe-icons.json carries only the name list,
not the assets), so draw.io fetches it from the CDN when the diagram is rendered
or opened. That means **network is required at render time**; an offline export
draws a blank box. Use --embed to fetch the SVG once and inline it as a
self-contained data URI instead (portable, no network at render time).

The logos are trademarks of their respective owners and are referenced here for
identification only — the same basis on which draw.io ships AWS/Azure icons.

Usage: python3 aiicons.py <query> [--limit N] [--variant color|mono|text]
                                  [--size PX] [--embed] [--json] [--list]
"""
import argparse
import base64
import json
import os
import re
import sys
import urllib.request

MANIFEST = os.path.join(os.path.dirname(__file__), "..", "data", "lobe-icons.json")
STYLE = ("shape=image;html=1;imageAspect=0;aspect=fixed;"
         "verticalLabelPosition=bottom;verticalAlign=top;image=")
_VARIANT = re.compile(r"-(?:color|text(?:-[a-z]{2})?|brand(?:-color)?)$")

# Common RAG/LLM data stores that lobe-icons lacks, mapped to simple-icons
# slugs (https://simpleicons.org, CC0). Served from the simple-icons CDN. Each
# slug below is verified to return HTTP 200 at https://cdn.simpleicons.org/<slug>.
_SIMPLEICONS_CDN = "https://cdn.simpleicons.org/"
_SUPPLEMENT = {
    "qdrant": "qdrant",
    "milvus": "milvus",
    "supabase": "supabase",
    "redis": "redis",
    "postgresql": "postgresql",
    "mongodb": "mongodb",
    "elasticsearch": "elasticsearch",
    "neo4j": "neo4j",
    "kafka": "apachekafka",
    "clickhouse": "clickhouse",
    "duckdb": "duckdb",
    "mysql": "mysql",
    "sqlite": "sqlite",
    "cassandra": "apachecassandra",
    "snowflake": "snowflake",
    "databricks": "databricks",
    "mariadb": "mariadb",
    "couchbase": "couchbase",
}


def families(icons):
    """base brand name -> set of its variant filenames (without .svg)."""
    fam = {}
    for name in icons:
        base = _VARIANT.sub("", name)
        fam.setdefault(base, set()).add(name)
    return fam


def squish(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def search(fam, query, limit):
    """Rank brand bases against the query (squished + per-token matching)."""
    q = squish(query)
    tokens = [t for t in re.findall(r"[a-z0-9]+", query.lower()) if t]
    scored = {}
    for base in fam:
        b = squish(base)
        s = 0
        if q and q == b:
            s = 100
        elif q and b.startswith(q):
            s = 60
        elif q and q in b:
            s = 40
        for t in tokens:
            if t == b:
                s = max(s, 90)
            elif len(t) >= 3 and b.startswith(t):
                s = max(s, 50)
            elif len(t) >= 3 and t in b:
                s = max(s, 30)
        if s:
            scored[base] = s
    return sorted(scored, key=lambda base: (-scored[base], base))[:limit]


def search_supplement(query):
    """Fall back to the simple-icons supplement (exact or substring match)."""
    q = squish(query)
    if not q:
        return None
    if q in _SUPPLEMENT:
        return q
    for brand in _SUPPLEMENT:
        if q in brand or brand in q:
            return brand
    return None


def pick_variant(base, variants, prefer):
    order = {"color": ["-color", "-brand-color", "", "-brand", "-text", "-text-cn"],
             "mono":  ["", "-brand", "-color", "-brand-color", "-text", "-text-cn"],
             "text":  ["-text", "-text-cn", "-brand", "-brand-color", "-color", ""]}[prefer]
    for suffix in order:
        cand = base + suffix
        if cand in variants:
            return cand
    return next(iter(sorted(variants)), None)


def main():
    ap = argparse.ArgumentParser(description="Find AI/LLM brand logos as draw.io styles (lobe-icons via CDN).")
    ap.add_argument("query", nargs="?", help='brand name, e.g. "openai" or "claude"')
    ap.add_argument("--limit", type=int, default=8)
    ap.add_argument("--variant", choices=["color", "mono", "text"], default="color")
    ap.add_argument("--size", type=int, default=48, help="cell width/height in px (icons are square)")
    ap.add_argument("--embed", action="store_true",
                    help="inline the SVG as a data URI (fetches it now; portable, no network at render time)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--list", action="store_true", help="list all brand names and exit")
    args = ap.parse_args()

    if not os.path.exists(MANIFEST):
        sys.exit(f"error: manifest not found at {MANIFEST}")
    manifest = json.load(open(MANIFEST, encoding="utf-8"))
    fam = families(manifest["icons"])
    cdn = manifest["cdn"]

    if args.list:
        for base in sorted(fam):
            print(base)
        return
    if not args.query:
        ap.error("a query is required (or use --list)")

    matches = search(fam, args.query, args.limit)

    results = []
    if matches:
        for base in matches:
            file = pick_variant(base, fam[base], args.variant)
            url = f"{cdn}{file}.svg"
            if args.embed:
                try:
                    svg = urllib.request.urlopen(url, timeout=15).read()
                except Exception as exc:                   # noqa: BLE001 - report and skip
                    sys.stderr.write(f"warning: could not fetch {url} ({exc})\n")
                    continue
                # Rewrite the 1em intrinsic size so draw.io scales the inlined SVG.
                svg = svg.replace(b'width="1em"', b'width="24"').replace(b'height="1em"', b'height="24"')
                image = "data:image/svg+xml;base64," + base64.b64encode(svg).decode()
            else:
                image = url
            results.append({"brand": base, "file": file, "w": args.size, "h": args.size,
                            "style": STYLE + image})
    else:
        # lobe has no logo for this brand; fall back to the simple-icons supplement.
        brand = search_supplement(args.query)
        if brand:
            slug = _SUPPLEMENT[brand]
            url = _SIMPLEICONS_CDN + slug
            image = url
            if args.embed:
                try:
                    svg = urllib.request.urlopen(url, timeout=15).read()
                    image = "data:image/svg+xml;base64," + base64.b64encode(svg).decode()
                except Exception as exc:                   # noqa: BLE001 - keep the CDN URL
                    sys.stderr.write(f"warning: could not fetch {url} ({exc}); using CDN URL\n")
            results.append({"brand": brand, "file": f"simpleicons:{slug}",
                            "w": args.size, "h": args.size, "style": STYLE + image})

    if not results:
        sys.exit(f"no logo for {args.query!r} — for a data store try a cylinder "
                 f"(shape=cylinder3) or shapesearch.py '{args.query} database'")

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        for r in results:
            shown = r["style"] if len(r["style"]) < 160 else r["style"][:157] + "..."
            print(f"{r['brand']}  ({r['file']}, {r['w']}x{r['h']})\n  {shown}")


if __name__ == "__main__":
    main()
