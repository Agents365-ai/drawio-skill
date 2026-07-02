#!/usr/bin/env python3
"""Extract an ER diagram from SQL DDL as autolayout graph JSON.

Parses ``CREATE TABLE`` statements (regex + paren matching — no SQL library),
one node per table listing its columns with PK/FK markers, and one
crow's-foot edge per foreign key (many side at the referencing table).
The output feeds autolayout.py:

  python3 sqlerd.py schema.sql -o graph.json
  python3 autolayout.py graph.json -o erd.drawio

Understood per table: column name + type, inline ``PRIMARY KEY`` /
``REFERENCES tab(col)``, table-level ``PRIMARY KEY (...)`` and
``[CONSTRAINT x] FOREIGN KEY (col) REFERENCES tab(col)``. Quoted identifiers
("t", `t`, [t]) and ``schema.table`` prefixes are normalized; edges land only
on tables defined in the scanned files. Dialect-specific clauses beyond that
(partitioning, generated columns, …) are simply ignored — worst case a column
line is skipped, never a wrong edge.

Usage: python3 sqlerd.py <file.sql-or-dir> [-o graph.json]
       [--direction TB|LR] [--group] [--no-types]
"""
import argparse
import glob
import json
import os
import re
import sys

TABLE_STYLE = ("rounded=0;whiteSpace=wrap;html=1;align=left;verticalAlign=top;"
               "spacingLeft=6;spacingTop=4;fillColor=#dae8fc;strokeColor=#6c8ebf;")
# orthogonalEdgeStyle (not entityRelationEdgeStyle) so the edge honours the
# obstacle-avoiding waypoints dot computed; ER arrows give the crow's foot.
ER_EDGE = ("edgeStyle=orthogonalEdgeStyle;html=1;rounded=0;fontSize=11;"
           "labelBackgroundColor=#ffffff;"
           "startArrow=ERmany;startFill=0;endArrow=ERone;endFill=0;")

_COMMENT = re.compile(r"/\*.*?\*/|--[^\n]*", re.S)
_CREATE = re.compile(r"\bCREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([\w.\"`\[\]]+)\s*\(",
                     re.I)
_FK = re.compile(r"FOREIGN\s+KEY\s*\(([^)]+)\)\s*REFERENCES\s+([\w.\"`\[\]]+)\s*(?:\(([^)]+)\))?",
                 re.I)
_PK = re.compile(r"PRIMARY\s+KEY\s*\(([^)]+)\)", re.I)
_INLINE_REF = re.compile(r"\bREFERENCES\s+([\w.\"`\[\]]+)", re.I)
_SKIP = re.compile(r"^\s*(CONSTRAINT|UNIQUE|CHECK|KEY|INDEX|FULLTEXT|SPATIAL|EXCLUDE|LIKE)\b",
                   re.I)


def ident(raw):
    """Normalize an identifier: strip quoting, keep the last dotted part."""
    name = raw.strip().strip('"`[]').split(".")[-1].strip('"`[]')
    return name.lower()


def split_columns(body):
    """Split a CREATE TABLE body on top-level commas."""
    items, depth, cur = [], 0, []
    for ch in body:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            items.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    if "".join(cur).strip():
        items.append("".join(cur).strip())
    return items


def parse_tables(text):
    """{table: {"schema", "columns": [(name, type)], "pks": set, "fks": [(col, table)]}}"""
    text = _COMMENT.sub("", text)
    tables = {}
    for m in _CREATE.finditer(text):
        raw_name = m.group(1)
        depth, i = 1, m.end()
        while i < len(text) and depth:
            if text[i] == "(":
                depth += 1
            elif text[i] == ")":
                depth -= 1
            i += 1
        body = text[m.end():i - 1]
        name = ident(raw_name)
        parts = raw_name.strip().strip('"`[]').split(".")
        schema = ident(parts[-2]) if len(parts) > 1 else ""
        cols, pks, fks = [], set(), []
        for item in split_columns(body):
            fk = _FK.search(item)
            if fk:
                for col in fk.group(1).split(","):
                    fks.append((ident(col), ident(fk.group(2))))
                continue
            pk = _PK.search(item)
            if pk and _SKIP.match(item) is None and item.upper().lstrip().startswith("PRIMARY"):
                pks.update(ident(c) for c in pk.group(1).split(","))
                continue
            if _SKIP.match(item):
                continue
            toks = item.split()
            if len(toks) < 2:
                continue
            col, ctype = ident(toks[0]), toks[1].rstrip(",")
            cols.append((col, ctype))
            if re.search(r"\bPRIMARY\s+KEY\b", item, re.I):
                pks.add(col)
            ref = _INLINE_REF.search(item)
            if ref:
                fks.append((col, ident(ref.group(1))))
        tables[name] = {"schema": schema, "columns": cols, "pks": pks, "fks": fks}
    return tables


def main():
    ap = argparse.ArgumentParser(description="SQL DDL -> ER diagram graph JSON.")
    ap.add_argument("path", help=".sql file or directory containing .sql files")
    ap.add_argument("-o", "--output", help="output JSON path (default: stdout)")
    ap.add_argument("--direction", default="TB", choices=["TB", "LR"])
    ap.add_argument("--group", action="store_true", help="group tables by schema")
    ap.add_argument("--no-types", action="store_true",
                    help="list column names only (hide the SQL types)")
    args = ap.parse_args()

    files = ([args.path] if os.path.isfile(args.path)
             else sorted(glob.glob(os.path.join(args.path, "**", "*.sql"), recursive=True)))
    tables = {}
    for path in files:
        with open(path, encoding="utf-8") as f:
            tables.update(parse_tables(f.read()))
    if not tables:
        sys.exit(f"error: no CREATE TABLE statements found under {args.path}")

    nodes, edges = [], []
    for name, t in tables.items():
        fk_cols = {c for c, _ in t["fks"]}
        lines = [name]
        for col, ctype in t["columns"]:
            mark = "PK " if col in t["pks"] else "FK " if col in fk_cols else ""
            lines.append(f"{mark}{col}" + ("" if args.no_types else f": {ctype}"))
        width = max(160, -(-max(7 * len(l) + 30 for l in lines) // 10) * 10)
        height = -(-(30 + 20 * len(t["columns"])) // 10) * 10
        node = {"id": name, "label": "\n".join(lines), "style": TABLE_STYLE,
                "width": width, "height": height}
        if args.group and t["schema"]:
            node["group"] = t["schema"]
        nodes.append(node)
        for col, ref in t["fks"]:
            if ref in tables and ref != name:
                edges.append({"source": name, "target": ref, "label": col,
                              "style": ER_EDGE})

    graph = {"direction": args.direction, "nodes": nodes, "edges": edges}
    text = json.dumps(graph, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        sys.stderr.write(f"wrote {args.output}\n")
    else:
        sys.stdout.write(text)
    sys.stderr.write(f"{len(nodes)} tables, {len(edges)} foreign keys\n")


if __name__ == "__main__":
    main()
