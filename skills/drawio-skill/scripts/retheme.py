#!/usr/bin/env python3
"""retheme.py — rebrand an existing .drawio in one command via its theme sidecar.

Given <name>.drawio + sidecar <name>.theme.json (written by poster.py / theme.py),
compute old->new hex pairs and swap them everywhere theme color can live:
  - style attributes (fillColor=, strokeColor=, fontColor=, gradientColor=, ...)
  - HTML label spans (color:#hex inside value="...") — spans override cell fontColor
  - embedded SVG data-URIs (url-encoded payloads carry the hex as %23AABBCC)

Modes (exactly one):
  retheme.py file.drawio --to "#7A0619" [--override k=hex ...]   re-derive ramp from new brand
  retheme.py file.drawio --to-theme other.theme.json             map onto another theme file
  retheme.py file.drawio --swap "#OLD=#NEW" [--swap ...]         explicit pairs (no sidecar needed)

Options:
  --sidecar PATH   sidecar location (default: <file minus .drawio>.theme.json)
  --dry-run        print the swap table, change nothing
  -o PATH          write result to PATH instead of in-place

The swap is a single pass over the raw XML with exact case-insensitive hex matching
(# and %23 spellings), so it is deterministic, chain-safe, and idempotent. Caveat: the
pass is context-blind by design — a label or link whose PROSE literally cites an old
theme hex is rewritten too (check --dry-run when labels talk about colors).
On apply, the sidecar is rewritten to the new theme so the file can be re-themed again.
"""
import argparse
import importlib.util
import json
import os
import re
import sys

HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def _load_theme_module():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "theme.py")
    spec = importlib.util.spec_from_file_location("theme", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _flatten(theme):
    """theme JSON -> {label: hex} for tokens + palette slots (invalid hexes dropped)."""
    out = {}
    for k, v in (theme.get("tokens") or {}).items():
        out["tokens.%s" % k] = v
    for slot, pair in (theme.get("palette") or {}).items():
        out["%s.fill" % slot] = pair.get("fillColor")
        out["%s.stroke" % slot] = pair.get("strokeColor")
    bad = [k for k, v in out.items() if not (isinstance(v, str) and HEX_RE.match(v))]
    for k in bad:
        print("warning: theme label %s has invalid hex %r — skipped" % (k, out[k]),
              file=sys.stderr)
        del out[k]
    return out


def build_pairs(old_theme, new_theme):
    """Match old/new theme by label -> {old_hex_lower: new_hex} (identity pairs dropped)."""
    old_f, new_f = _flatten(old_theme), _flatten(new_theme)
    pairs = {}
    for label, old_hex in old_f.items():
        new_hex = new_f.get(label)
        if not new_hex or old_hex.lower() == new_hex.lower():
            continue
        prev = pairs.get(old_hex.lower())
        if prev and prev.upper() != new_hex.upper():
            print("warning: %s maps %s -> %s but an earlier label mapped it -> %s; keeping first"
                  % (label, old_hex, new_hex, prev), file=sys.stderr)
            continue
        pairs[old_hex.lower()] = new_hex
    return pairs


def apply_pairs(xml, pairs):
    """Swap every #hex / %23hex occurrence per pairs (case-insensitive, single pass)."""
    if not pairs:
        return xml, 0
    alt = "|".join(re.escape(h.lstrip("#")) for h in pairs)
    # Trailing lookahead: never rewrite the head of a longer hex (#RRGGBBAA alpha).
    rx = re.compile(r"(#|%23)(" + alt + r")(?![0-9A-Fa-f])", re.IGNORECASE)
    n = 0

    def sub(m):
        nonlocal n
        n += 1
        return m.group(1) + pairs["#" + m.group(2).lower()].lstrip("#")

    return rx.sub(sub, xml), n


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("file", help=".drawio file to retheme")
    p.add_argument("--to", metavar="HEX", help="new brand hex; re-derives the ramp")
    p.add_argument("--override", action="append", metavar="KEY=HEX",
                   help="with --to: token/slot overrides (see theme.py derive)")
    p.add_argument("--to-theme", metavar="PATH", help="target theme JSON file")
    p.add_argument("--swap", action="append", metavar="#OLD=#NEW", help="explicit pair (repeatable)")
    p.add_argument("--sidecar", metavar="PATH", help="theme sidecar (default <file>.theme.json)")
    p.add_argument("--dry-run", action="store_true", help="print swap table only")
    p.add_argument("-o", "--out", metavar="PATH", help="write to PATH instead of in-place")
    args = p.parse_args(argv)

    modes = [bool(args.to), bool(args.to_theme), bool(args.swap)]
    if sum(modes) != 1:
        p.error("exactly one of --to / --to-theme / --swap required")

    if not os.path.isfile(args.file):
        sys.exit("error: no such file: %s" % args.file)
    sidecar = args.sidecar or re.sub(r"\.drawio$", "", args.file) + ".theme.json"

    new_theme = None
    if args.swap:
        pairs = {}
        for s in args.swap:
            if "=" not in s:
                sys.exit("--swap expects #OLD=#NEW, got %r" % s)
            old, new = (x.strip() for x in s.split("=", 1))
            if not (HEX_RE.match(old) and HEX_RE.match(new)):
                sys.exit("--swap colors must be #RRGGBB, got %r" % s)
            pairs[old.lower()] = new
        if not os.path.isfile(sidecar):
            print("warning: no sidecar at %s — swaps applied blind, sidecar not updated"
                  % sidecar, file=sys.stderr)
    else:
        if not os.path.isfile(sidecar):
            sys.exit("error: sidecar not found: %s (use --swap for sidecar-less mode)" % sidecar)
        with open(sidecar, encoding="utf-8") as f:
            old_theme = json.load(f)
        if args.to_theme:
            try:
                with open(args.to_theme, encoding="utf-8") as f:
                    new_theme = json.load(f)
            except (OSError, ValueError) as exc:
                sys.exit("error: cannot read --to-theme %s: %s" % (args.to_theme, exc))
        else:
            theme_mod = _load_theme_module()
            overrides = {}
            for ov in args.override or []:
                if "=" not in ov:
                    sys.exit("--override expects key=hex, got %r" % ov)
                k, v = ov.split("=", 1)
                overrides[k.strip()] = v.strip()
            try:
                _, new_theme = theme_mod.build_theme(args.to, overrides)
            except ValueError as e:
                sys.exit("error: %s" % e)
            new_theme["name"] = old_theme.get("name")
        pairs = build_pairs(old_theme, new_theme)

    if not pairs:
        print("nothing to do: themes identical (or no matching labels)")
        return

    if args.dry_run:
        w = max(len(o) for o in pairs)
        for old, new in sorted(pairs.items()):
            print("%-*s -> %s" % (w, old, new))
        return

    with open(args.file, encoding="utf-8") as f:
        xml = f.read()
    xml, n = apply_pairs(xml, pairs)
    out = args.out or args.file
    with open(out, "w", encoding="utf-8") as f:
        f.write(xml)
    if new_theme is not None:
        out_sidecar = (sidecar if args.out is None
                       or os.path.abspath(out) == os.path.abspath(args.file)
                       else re.sub(r"\.drawio$", "", out) + ".theme.json")
        with open(out_sidecar, "w", encoding="utf-8") as f:
            json.dump(new_theme, f, indent=2)
            f.write("\n")
    print("%s: %d occurrence(s) swapped across %d color(s)" % (out, n, len(pairs)))


if __name__ == "__main__":
    main()
