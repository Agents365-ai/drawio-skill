#!/usr/bin/env python3
"""Find Databricks product icons (Unity Catalog, Lakeflow, DLT, ...) as draw.io styles.

draw.io's bundled shape libraries have no Databricks shape set, so a lakehouse
architecture renders as generic boxes. This resolves a Databricks product name
to a draw.io `image` style that references the matching SVG from the community
databricks-architecture-icons project
(https://github.com/oieduardorabelo/databricks-architecture-icons), which
packages official Databricks artwork on a 48x48 canvas.

  python3 dbxicons.py "unity catalog"
  python3 dbxicons.py "DLT" --json
  python3 dbxicons.py "vector search" --variant outline --size 48

Renamed products resolve through aliases: "DLT" and "Delta Live Tables" find
`spark-declarative-pipelines`, "Workflows" finds `lakeflow-jobs`. Match order:
exact slug, exact alias, then ranked substring search over slug, name, and
aliases.

The icon is referenced by URL (data/databricks-icons.json carries names and
category facts only, not the assets), so draw.io fetches it from the project's
GitHub Pages site when the diagram is rendered or opened. That means **network
is required at render time**; an offline export draws a blank box. Use --embed
to fetch the SVG once (from the pinned commit, immutable) and inline it as a
self-contained data URI instead (portable, no network at render time).

Variants: `color` (default), `tile`, `outline`. There is no mono variant on
purpose: the upstream mono SVGs use `currentColor`, which draw.io image shapes
render as black.

The icons are official Databricks artwork served by the community project. They
are trademarks of Databricks, Inc., referenced here for identification only —
the same basis on which draw.io ships AWS/Azure icons. No artwork is bundled.

Usage: python3 dbxicons.py <query> [--limit N] [--variant color|tile|outline]
                                   [--size PX] [--embed] [--json] [--list]
       python3 dbxicons.py --refresh-manifest [--ref REF]   (maintainer-facing)
"""
import argparse
import base64
import json
import os
import re
import sys
import urllib.parse
import urllib.request

MANIFEST = os.path.join(os.path.dirname(__file__), "..", "data", "databricks-icons.json")
STYLE = ("shape=image;html=1;imageAspect=0;aspect=fixed;"
         "verticalLabelPosition=bottom;verticalAlign=top;image=")
_VARIANT_DIRS = {"color": "svg", "tile": "svg-tile", "outline": "svg-outline"}

_REPO = "oieduardorabelo/databricks-architecture-icons"
_SOURCE = f"https://github.com/{_REPO}"
_HOSTED = "https://oieduardorabelo.github.io/databricks-architecture-icons"
_RAW = f"https://raw.githubusercontent.com/{_REPO}/"
_API_COMMIT = f"https://api.github.com/repos/{_REPO}/commits/"
_ALLOWED_HOSTS = {"raw.githubusercontent.com", "api.github.com",
                  "oieduardorabelo.github.io"}

# Curated aliases beyond the upstream catalog's former names ("aka"), for the
# names people still use after Databricks renamed the product. Source of truth
# for --refresh-manifest; edit here, then regenerate the manifest.
EXTRA_ALIASES = {
    "spark-declarative-pipelines": ["DLT", "Delta Live Tables",
                                    "Lakeflow Declarative Pipelines"],
    "lakeflow-jobs": ["Databricks Workflows", "Workflows", "Jobs"],
    "ai-search": ["Vector Search", "Mosaic AI Vector Search"],
    "genie-agents": ["Genie spaces", "AI/BI Genie"],
    "data-quality-monitoring": ["Lakehouse Monitoring"],
    "model-serving": ["Mosaic AI Model Serving"],
    "unity-catalog": ["UC"],
    "databricks-sql": ["DBSQL"],
    "compute-clusters": ["Clusters", "All-purpose compute", "Job compute"],
    "lakehouse-storage": ["Managed tables", "Delta tables"],
    "asset-bundles": ["DAB", "DABs"],
    "git-folders": ["Repos"],
    "mlflow": ["Managed MLflow"],
    "lakebase": ["OLTP", "Postgres"],
    "delta-sharing": ["Data sharing"],
}


def squish(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def data_uri(svg_bytes):
    """SVG bytes -> marker-less base64 data URI. draw.io splits style values on
    ';', so a ';base64,' marker would truncate the image= value (issue #80);
    draw.io detects base64 by content."""
    return "data:image/svg+xml," + base64.b64encode(svg_bytes).decode()


def icon_path(product, variant):
    return f"icons/{_VARIANT_DIRS[variant]}/{product['slug']}.svg"


def search(products, query, limit):
    """Rank products against the query (squished + per-token matching) over
    slug, name, and aliases — the same scoring as aiicons.py."""
    q = squish(query)
    tokens = [t for t in re.findall(r"[a-z0-9]+", query.lower()) if t]
    scored = {}
    for i, p in enumerate(products):
        s = 0
        for key in [p["slug"], p["name"]] + p.get("aliases", []):
            b = squish(key)
            if not b:
                continue
            if q and q == b:
                s = max(s, 100)
            elif q and b.startswith(q):
                s = max(s, 60)
            elif q and q in b:
                s = max(s, 40)
            for t in tokens:
                if t == b:
                    s = max(s, 90)
                elif len(t) >= 3 and b.startswith(t):
                    s = max(s, 50)
                elif len(t) >= 3 and t in b:
                    s = max(s, 30)
        if s:
            scored[i] = s
    ranked = sorted(scored, key=lambda i: (-scored[i], products[i]["slug"]))
    return [products[i] for i in ranked[:limit]]


def resolve(products, query, limit):
    """Exact slug, then exact alias/name (case-insensitive), then ranked search."""
    q = squish(query)
    for p in products:
        if squish(p["slug"]) == q:
            return [p]
    for p in products:
        if any(squish(a) == q for a in [p["name"]] + p.get("aliases", [])):
            return [p]
    return search(products, query, limit)


# ---------------------------------------------------------------- refresh ---

def _fetch(url, accept=None):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in _ALLOWED_HOSTS:
        raise ValueError(f"refusing icon URL outside allowlist: {url}")
    headers = {"User-Agent": "drawio-skill-dbxicons"}
    if accept:
        headers["Accept"] = accept
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def parse_aka(aka):
    """Upstream 'aka' prose -> former-name facts.
    'Lakeflow X. Formerly Delta Live Tables (DLT)' -> two names."""
    names = []
    for part in re.split(r"[.;]", aka or ""):
        part = re.sub(r"^\s*formerly\s+", "", part.strip(), flags=re.I)
        for name in re.split(r"\s+/\s+", part):
            name = name.strip()
            if name:
                names.append(name)
    return names


def build_manifest(catalog, sha):
    """Upstream icons/catalog.json -> the facts-only manifest (no descriptions,
    no docs URLs — those stay upstream)."""
    categories = {key: {"label": val["label"], "color": val["color"]}
                  for key, val in catalog["categories"].items()}
    products = []
    for p in catalog["products"]:
        seen = {squish(p["slug"]), squish(p["name"])}
        aliases = []
        for alias in parse_aka(p.get("aka")) + EXTRA_ALIASES.get(p["slug"], []):
            if squish(alias) not in seen:
                seen.add(squish(alias))
                aliases.append(alias)
        products.append({"slug": p["slug"], "name": p["name"], "aliases": aliases,
                         "category": p["category"],
                         "categoryColor": p["categoryColor"]})
    return {"source": _SOURCE, "hostedBase": _HOSTED, "pinnedRef": sha,
            "canvas": catalog.get("canvas", "48x48"),
            "categories": categories, "products": products}


def refresh_manifest(ref):
    sha = ref if re.fullmatch(r"[0-9a-f]{40}", ref or "") else \
        _fetch(_API_COMMIT + (ref or "main"), accept="application/vnd.github.sha").decode()
    catalog = json.loads(_fetch(f"{_RAW}{sha}/icons/catalog.json"))

    slugs = {p["slug"] for p in catalog["products"]}
    for slug in EXTRA_ALIASES:
        if slug not in slugs:
            sys.stderr.write(f"warning: EXTRA_ALIASES key {slug!r} is not in the "
                             f"upstream catalog (renamed upstream?)\n")

    manifest = build_manifest(catalog, sha)

    old = {}
    if os.path.exists(MANIFEST):
        with open(MANIFEST, encoding="utf-8") as f:
            old = {p["slug"]: p for p in json.load(f).get("products", [])}
    new = {p["slug"]: p for p in manifest["products"]}
    for slug in sorted(set(new) - set(old)):
        print(f"added:   {slug}")
    for slug in sorted(set(old) - set(new)):
        print(f"removed: {slug}")
    for slug in sorted(set(old) & set(new)):
        if old[slug]["name"] != new[slug]["name"]:
            print(f"renamed: {slug}: {old[slug]['name']} -> {new[slug]['name']}")

    with open(MANIFEST, "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print(f"wrote {os.path.normpath(MANIFEST)}: {len(new)} products, "
          f"{len(manifest['categories'])} categories, pinned {sha}")


# ------------------------------------------------------------------- main ---

def main():
    ap = argparse.ArgumentParser(
        description="Find Databricks product icons as draw.io styles (community-hosted official artwork).")
    ap.add_argument("query", nargs="?", help='product name, e.g. "unity catalog" or "DLT"')
    ap.add_argument("--limit", type=int, default=8)
    ap.add_argument("--variant", choices=sorted(_VARIANT_DIRS), default="color",
                    help="icon style (no mono: upstream mono SVGs render black in draw.io)")
    ap.add_argument("--size", type=int, default=48, help="cell width/height in px (icons are square)")
    ap.add_argument("--embed", action="store_true",
                    help="inline the SVG as a data URI (fetches it now from the pinned commit; "
                         "portable, no network at render time)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--list", action="store_true", help="list all products and exit")
    ap.add_argument("--refresh-manifest", action="store_true",
                    help="maintainer-facing: regenerate data/databricks-icons.json from the upstream catalog")
    ap.add_argument("--ref", help="git ref for --refresh-manifest (default: remote main HEAD)")
    args = ap.parse_args()

    if args.refresh_manifest:
        refresh_manifest(args.ref)
        return

    if not os.path.exists(MANIFEST):
        sys.exit(f"error: manifest not found at {MANIFEST}")
    with open(MANIFEST, encoding="utf-8") as f:
        manifest = json.load(f)
    hosted = urllib.parse.urlparse(manifest.get("hostedBase", ""))
    if hosted.scheme != "https" or hosted.hostname not in _ALLOWED_HOSTS:
        sys.exit("error: manifest hostedBase is outside the icon host allowlist")
    products = manifest["products"]

    if args.list:
        for p in sorted(products, key=lambda p: p["slug"]):
            print(f"{p['slug']}  {p['name']}")
        return
    if not args.query:
        ap.error("a query is required (or use --list)")

    results = []
    for p in resolve(products, args.query, args.limit):
        path = icon_path(p, args.variant)
        if args.embed:
            url = f"{_RAW}{manifest['pinnedRef']}/{path}"
            try:
                svg = _fetch(url)
            except Exception as exc:                   # noqa: BLE001 - report and skip
                sys.stderr.write(f"warning: could not fetch {url} ({exc})\n")
                continue
            image = data_uri(svg)
        else:
            image = f"{manifest['hostedBase']}/{path}"
        results.append({"product": p["slug"], "name": p["name"],
                        "category": p["category"], "categoryColor": p["categoryColor"],
                        "file": path, "w": args.size, "h": args.size,
                        "style": STYLE + image})

    if not results:
        sys.exit(f"no Databricks product for {args.query!r} — for the bare Databricks "
                 f"logo try aiicons.py 'databricks'; otherwise shapesearch.py {args.query!r}")

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        for r in results:
            shown = r["style"] if len(r["style"]) < 160 else r["style"][:157] + "..."
            print(f"{r['product']}  {r['name']}  ({r['file']}, {r['w']}x{r['h']})\n  {shown}")


if __name__ == "__main__":
    main()
