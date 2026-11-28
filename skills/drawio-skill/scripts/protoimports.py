#!/usr/bin/env python3
"""Turn Protocol Buffers (.proto) schemas into a diagram as autolayout graph JSON.

Parses .proto files (file or directory) into nodes for services (with RPC methods),
messages (with fields), and enums (with values), connected by edges for service
request/response types and referenced message field types.

Feeds autolayout.py:
  python3 protoimports.py ./proto --group -o graph.json
  python3 autolayout.py graph.json -o services.drawio

Supports proto2 and proto3 syntax using a stdlib-only parser (no protoc required).
Tolerates imports, options, and reserved declarations by skipping them.

Usage: python3 protoimports.py <file.proto-or-dir> [-o graph.json]
       [--direction TB|LR] [--group]
"""
import argparse
import glob
import json
import os
import re
import sys

SERVICE_STYLE = (
    "rounded=1;whiteSpace=wrap;html=1;align=left;verticalAlign=top;"
    "spacingLeft=8;spacingTop=6;fillColor=#dae8fc;strokeColor=#6c8ebf;"
)
MESSAGE_STYLE = (
    "rounded=1;whiteSpace=wrap;html=1;align=left;verticalAlign=top;"
    "spacingLeft=8;spacingTop=6;fillColor=#e1d5e7;strokeColor=#9673a6;"
)
ENUM_STYLE = (
    "rounded=1;whiteSpace=wrap;html=1;align=left;verticalAlign=top;"
    "spacingLeft=8;spacingTop=6;fillColor=#fff2cc;strokeColor=#d6b656;"
)

SERVICE_EDGE = (
    "edgeStyle=orthogonalEdgeStyle;html=1;rounded=0;fontSize=10;"
    "endArrow=open;strokeColor=#6c8ebf;"
)
REF_EDGE = (
    "edgeStyle=orthogonalEdgeStyle;html=1;rounded=0;fontSize=10;"
    "dashed=1;endArrow=open;strokeColor=#9673a6;"
)

SCALAR_TYPES = {
    "double", "float", "int32", "int64", "uint32", "uint64",
    "sint32", "sint64", "fixed32", "fixed64", "sfixed32", "sfixed64",
    "bool", "string", "bytes",
}

TOKEN_RE = re.compile(
    r"""
    (?P<STRING>"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')
  | (?P<COMMENT>//[^\n]*|/\*[\s\S]*?\*/)
  | (?P<NUM>-?[0-9]+(?:\.[0-9]+)?)
  | (?P<IDENT>[A-Za-z_][A-Za-z0-9_.]*)
  | (?P<SYM>[{}();=<>:,\[\]])
  | (?P<WS>\s+)
""",
    re.VERBOSE,
)


class Token:
    __slots__ = ("kind", "value", "line")

    def __init__(self, kind, value, line):
        self.kind = kind
        self.value = value
        self.line = line


def tokenize(text):
    tokens = []
    line = 1
    pos = 0
    # Comments are matched by the tokenizer rather than stripped up front, so a
    # `//` or `/*` inside a string literal (a URL, say) stays part of the string.
    for m in TOKEN_RE.finditer(text):
        kind = m.lastgroup
        val = m.group()
        line += text[pos:m.start()].count("\n")
        pos = m.start()
        if kind not in ("WS", "COMMENT"):
            tokens.append(Token(kind, val, line))
        line += val.count("\n")
        pos = m.end()
    return tokens


def parse_proto(text, file_path=""):
    tokens = tokenize(text)
    idx = 0
    n = len(tokens)

    package = ""
    enums = []
    messages = []
    services = []

    def peek(offset=0):
        pos = idx + offset
        return tokens[pos] if pos < n else None

    def advance():
        nonlocal idx
        tok = tokens[idx]
        idx += 1
        return tok

    def match(val):
        t = peek()
        if t and t.value == val:
            advance()
            return True
        return False

    def skip_until_semi():
        depth = 0
        bracket_depth = 0
        nonlocal idx
        while idx < n:
            t = advance()
            if t.value == "{":
                depth += 1
            elif t.value == "}":
                depth -= 1
                if depth <= 0 and bracket_depth == 0:
                    break
            elif t.value == "[":
                bracket_depth += 1
            elif t.value == "]":
                bracket_depth -= 1
            elif t.value == ";" and depth == 0 and bracket_depth == 0:
                break

    def parse_enum(scope=""):
        enum_tok = advance()
        name = enum_tok.value
        full_name = f"{scope}.{name}" if scope else name
        line = enum_tok.line
        values = []
        if not match("{"):
            return
        while idx < n:
            t = peek()
            if not t or t.value == "}":
                advance()
                break
            if t.value in ("option", "reserved"):
                skip_until_semi()
                continue
            val_name = advance().value
            if match("="):
                val_num = advance().value
                values.append((val_name, val_num))
                skip_until_semi()
            else:
                skip_until_semi()
        enums.append({
            "name": name,
            "full_name": full_name,
            "values": values,
            "line": line,
            "file": file_path,
            "package": package,
        })

    def parse_service():
        srv_tok = advance()
        name = srv_tok.value
        line = srv_tok.line
        rpcs = []
        if not match("{"):
            return
        while idx < n:
            t = peek()
            if not t or t.value == "}":
                advance()
                break
            if t.value == "rpc":
                advance()
                rpc_tok = advance()
                rpc_name = rpc_tok.value
                rpc_line = rpc_tok.line
                req_stream = False
                resp_stream = False

                match("(")
                if match("stream"):
                    req_stream = True
                req_type = advance().value
                match(")")

                match("returns")

                match("(")
                if match("stream"):
                    resp_stream = True
                resp_type = advance().value
                match(")")

                t2 = peek()
                if t2 and t2.value == "{":
                    skip_until_semi()
                elif t2 and t2.value == ";":
                    advance()
                rpcs.append({
                    "name": rpc_name,
                    "req_type": req_type,
                    "req_stream": req_stream,
                    "resp_type": resp_type,
                    "resp_stream": resp_stream,
                    "line": rpc_line,
                })
            else:
                skip_until_semi()
        services.append({
            "name": name,
            "full_name": name,
            "rpcs": rpcs,
            "line": line,
            "file": file_path,
            "package": package,
        })

    def parse_message(scope=""):
        msg_tok = advance()
        name = msg_tok.value
        full_name = f"{scope}.{name}" if scope else name
        line = msg_tok.line
        fields = []
        if not match("{"):
            return
        while idx < n:
            t = peek()
            if not t or t.value == "}":
                advance()
                break
            if t.value == "message":
                advance()
                parse_message(scope=full_name)
            elif t.value == "enum":
                advance()
                parse_enum(scope=full_name)
            elif t.value == "oneof":
                advance()
                oneof_name = advance().value
                if match("{"):
                    while idx < n:
                        o_tok = peek()
                        if not o_tok or o_tok.value == "}":
                            advance()
                            break
                        f_type = advance().value
                        f_name = advance().value
                        f_line = o_tok.line
                        fields.append({
                            "name": f_name,
                            "type": f_type,
                            "modifier": "oneof",
                            "oneof": oneof_name,
                            "line": f_line,
                        })
                        skip_until_semi()
            elif t.value in ("option", "reserved", "extensions"):
                skip_until_semi()
            elif t.value == "map":
                advance()
                match("<")
                k_type = advance().value
                match(",")
                v_type = advance().value
                match(">")
                f_tok = advance()
                f_name = f_tok.value
                fields.append({
                    "name": f_name,
                    "type": f"map<{k_type}, {v_type}>",
                    "val_type": v_type,
                    "modifier": "map",
                    "line": f_tok.line,
                })
                skip_until_semi()
            else:
                modifier = ""
                if t.value in ("repeated", "optional", "required"):
                    modifier = advance().value
                f_type_tok = advance()
                f_type = f_type_tok.value
                f_name_tok = advance()
                f_name = f_name_tok.value
                fields.append({
                    "name": f_name,
                    "type": f_type,
                    "modifier": modifier,
                    "line": f_type_tok.line,
                })
                skip_until_semi()
        messages.append({
            "name": name,
            "full_name": full_name,
            "fields": fields,
            "line": line,
            "file": file_path,
            "package": package,
        })

    while idx < n:
        tok = peek()
        if not tok:
            break
        if tok.value == "package":
            advance()
            package = advance().value
            match(";")
        elif tok.value in ("syntax", "import", "option"):
            skip_until_semi()
        elif tok.value == "enum":
            advance()
            parse_enum()
        elif tok.value == "message":
            advance()
            parse_message()
        elif tok.value == "service":
            advance()
            parse_service()
        else:
            advance()

    return {
        "package": package,
        "enums": enums,
        "messages": messages,
        "services": services,
    }


def esc(text):
    """Escape HTML metacharacters for draw.io's html=1 labels.

    Without it a field type such as `map<string, Item>` is swallowed as an
    unknown HTML tag when draw.io renders the label.
    """
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def compute_dimensions(lines):
    width = max(160, -(-max(7 * len(l) + 30 for l in lines) // 10) * 10)
    height = max(50, -(-(30 + 18 * len(lines)) // 10) * 10)
    return width, height


def build(proto_data_list, group=False, direction="TB"):
    """List of parse_proto dicts -> autolayout graph JSON."""
    nodes = []
    edges = []
    seen_edges = set()

    # Build symbol map: qualified name & short name -> node_id
    # Also index by package
    all_symbols = {}
    package_symbols = {}
    # Package -> package-relative full name (Cart.Item) -> node_id, for
    # scoped lookups. Short names alone collide across parent messages.
    full_symbols = {}

    # Assign IDs
    # If package exists, prefix with package to ensure uniqueness across packages
    for data in proto_data_list:
        pkg = data.get("package", "")
        for s in data["services"]:
            nid = f"{pkg}.{s['name']}" if pkg else s["name"]
            s["id"] = nid
            all_symbols[nid] = nid
            all_symbols[s["name"]] = nid
            package_symbols.setdefault(pkg, {})[s["name"]] = nid

        for m in data["messages"]:
            nid = f"{pkg}.{m['full_name']}" if pkg else m["full_name"]
            m["id"] = nid
            all_symbols[nid] = nid
            all_symbols[m["full_name"]] = nid
            all_symbols[m["name"]] = nid
            package_symbols.setdefault(pkg, {})[m["full_name"]] = nid
            package_symbols.setdefault(pkg, {})[m["name"]] = nid
            full_symbols.setdefault(pkg, {})[m["full_name"]] = nid

        for e in data["enums"]:
            nid = f"{pkg}.{e['full_name']}" if pkg else e["full_name"]
            e["id"] = nid
            all_symbols[nid] = nid
            all_symbols[e["full_name"]] = nid
            all_symbols[e["name"]] = nid
            package_symbols.setdefault(pkg, {})[e["full_name"]] = nid
            package_symbols.setdefault(pkg, {})[e["name"]] = nid
            full_symbols.setdefault(pkg, {})[e["full_name"]] = nid

    def resolve(type_name, current_pkg="", scope=""):
        if type_name in SCALAR_TYPES:
            return None
        # Search the enclosing message scopes innermost first, as protoc does,
        # so a nested `Item` only shadows a top-level `Item` inside its parent.
        full_map = full_symbols.get(current_pkg, {})
        parts = scope.split(".") if scope else []
        for i in range(len(parts), -1, -1):
            candidate = ".".join(parts[:i] + [type_name])
            if candidate in full_map:
                return full_map[candidate]
        # Check current package first
        pkg_map = package_symbols.get(current_pkg, {})
        if type_name in pkg_map:
            return pkg_map[type_name]
        # Then global table
        return all_symbols.get(type_name)

    def add_edge(src, dst, style, label="", line=0, file_path=""):
        key = (src, dst, label)
        if src != dst and key not in seen_edges:
            seen_edges.add(key)
            edge = {
                "source": src,
                "target": dst,
                "style": style,
                "label": label,
            }
            if file_path or line:
                edge["provenance"] = {"path": file_path, "line": line}
            edges.append(edge)

    for data in proto_data_list:
        pkg = data.get("package", "")

        for s in data["services"]:
            lines = [f"«service»\n{s['name']}", "—"]
            if s["rpcs"]:
                for r in s["rpcs"]:
                    req = f"stream {r['req_type']}" if r["req_stream"] else r["req_type"]
                    resp = f"stream {r['resp_type']}" if r["resp_stream"] else r["resp_type"]
                    lines.append(f"{r['name']}({req}): {resp}")
            else:
                lines.append("(no rpcs)")

            w, h = compute_dimensions(lines)
            node = {
                "id": s["id"],
                "label": esc("\n".join(lines)),
                "style": SERVICE_STYLE,
                "width": w,
                "height": h,
                "provenance": {"path": s["file"], "line": s["line"]},
            }
            if group and pkg:
                node["group"] = pkg
            nodes.append(node)

            for r in s["rpcs"]:
                target_req = resolve(r["req_type"], pkg)
                if target_req:
                    add_edge(s["id"], target_req, SERVICE_EDGE, r["name"], r["line"], s["file"])
                target_resp = resolve(r["resp_type"], pkg)
                if target_resp:
                    add_edge(s["id"], target_resp, SERVICE_EDGE, r["name"], r["line"], s["file"])

        for m in data["messages"]:
            lines = [m["full_name"], "—"]
            if m["fields"]:
                for f in m["fields"]:
                    prefix = f"{f['modifier']} " if f["modifier"] in ("repeated", "optional") else ""
                    lines.append(f"{f['name']}: {prefix}{f['type']}")
            else:
                lines.append("(no fields)")

            w, h = compute_dimensions(lines)
            node = {
                "id": m["id"],
                "label": esc("\n".join(lines)),
                "style": MESSAGE_STYLE,
                "width": w,
                "height": h,
                "provenance": {"path": m["file"], "line": m["line"]},
            }
            if group and pkg:
                node["group"] = pkg
            nodes.append(node)

            for f in m["fields"]:
                ref_type = f.get("val_type") or f["type"]
                target = resolve(ref_type, pkg, m["full_name"])
                if target:
                    add_edge(m["id"], target, REF_EDGE, f["name"], f["line"], m["file"])

        for e in data["enums"]:
            lines = [f"«enum»\n{e['full_name']}", "—"]
            if e["values"]:
                for v_name, v_num in e["values"]:
                    lines.append(f"{v_name} = {v_num}")
            else:
                lines.append("(empty)")

            w, h = compute_dimensions(lines)
            node = {
                "id": e["id"],
                "label": esc("\n".join(lines)),
                "style": ENUM_STYLE,
                "width": w,
                "height": h,
                "provenance": {"path": e["file"], "line": e["line"]},
            }
            if group and pkg:
                node["group"] = pkg
            nodes.append(node)

    return {"direction": direction, "nodes": nodes, "edges": edges}


def main():
    ap = argparse.ArgumentParser(description="Protocol Buffers (.proto) -> message/service graph JSON.")
    ap.add_argument("path", help=".proto file or directory containing .proto files")
    ap.add_argument("-o", "--output", help="output JSON path (default: stdout)")
    ap.add_argument("--direction", default="TB", choices=["TB", "LR"])
    ap.add_argument("--group", action="store_true", help="group messages and services by package")
    args = ap.parse_args()

    if os.path.isfile(args.path):
        files = [args.path]
    elif os.path.isdir(args.path):
        files = sorted(glob.glob(os.path.join(args.path, "**", "*.proto"), recursive=True))
    else:
        sys.exit(f"error: {args.path} not found")

    if not files:
        sys.exit(f"error: no .proto files found under {args.path}")

    parsed_list = []
    for fpath in files:
        # pi-lens-ignore: ast-grep:unchecked-throwing-call-python
        with open(fpath, encoding="utf-8", errors="replace") as fh:
            parsed_list.append(parse_proto(fh.read(), file_path=fpath))

    graph = build(parsed_list, group=args.group, direction=args.direction)
    text = json.dumps(graph, indent=2, ensure_ascii=False)
    if args.output:
        # pi-lens-ignore: ast-grep:unchecked-throwing-call-python
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(text)
        sys.stderr.write(f"wrote {args.output}\n")
    else:
        sys.stdout.write(text)

    srv_count = sum(len(p["services"]) for p in parsed_list)
    msg_count = sum(len(p["messages"]) for p in parsed_list)
    enum_count = sum(len(p["enums"]) for p in parsed_list)
    sys.stderr.write(
        f"{srv_count} services, {msg_count} messages, {enum_count} enums, {len(graph['edges'])} edges\n"
    )


if __name__ == "__main__":
    main()
