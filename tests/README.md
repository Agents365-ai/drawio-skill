# Tests

Dependency-free regression tests for the bundled scripts (stdlib `unittest`
only — no pip install). They live at the repo root so they are **not** shipped
with the skill package.

```bash
# from the repo root
python3 -m unittest discover -s tests -v
```

## Coverage

| Area | What's locked in |
|---|---|
| `shapesearch.py` | Soundex codes, index loads, known queries resolve, **title-exact ranking** (`dynamodb` → *DynamoDB*), empty on no match |
| `aiicons.py` | variant families, brand/token matching, `-color` preference with mono fallback (OpenAI) |
| `encode_drawio_url.py` | **CJK + `%` round-trip** (the encodeURIComponent-before-deflate fix), viewer vs editor URLs |
| `autolayout.py` | palette sourced from `default.json` (not the fallback), group tinting, explicit-style wins, `--mono` |
| `validate.py` | good `.drawio` passes (exit 0), dangling edge fails (exit 1) |
| importers | `pyimports` intra-project edge, `pyclasses` inheritance edge + no hard-coded colour |

Auto-layout is exercised through `to_drawio()` with synthetic positions, so the
suite needs **no Graphviz or draw.io** to run.
