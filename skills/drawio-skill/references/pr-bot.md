# PR Diagram Bot — reviewing `.drawio` changes as pictures

Goal: in CI, for every `.drawio` file a pull request touches, render the base
version, the head version, and a colour-coded diff, then post them as a
sticky PR comment (and the job summary) so reviewers see pictures instead of
raw XML diffs.

Read this when you're setting up (or troubleshooting) automated PR diagram
review for a repo.

## Pieces

- `scripts/prdiff.py` — the script. `changed_drawios()` finds what changed
  (`git diff --name-status`); for each file it exports base/head PNGs via the
  draw.io CLI and, for modified files, chains `drawiodiff.py` ->
  `autolayout.py` -> CLI export into a third diff PNG; `render_markdown()`
  turns all of that into one Markdown report.
- `.github/actions/drawio-diff/action.yml` — a composite action that checks
  out full history, installs draw.io + Graphviz, runs `prdiff.py`, uploads
  the PNGs + report as a build artifact, writes the report to
  `$GITHUB_STEP_SUMMARY`, and posts/updates a sticky PR comment.
- `.github/workflows/drawio-pr-diff.example.yml` — a template workflow that
  wires the action to `pull_request` events. It ships as `.example.yml` and
  gated with `if: false` so it does **nothing** until you copy and adapt it
  in your own repo (see the comment at the top of that file).

## Adopting it in your own repo

Without copying anything, reference this repo's action directly:

```yaml
- uses: Agents365-ai/drawio-skill/.github/actions/drawio-diff@main
```

(Pin to a tag for reproducibility; the action checks out its own skill
scripts via `github.action_repository`.) The pure-Python
`drawio-architecture-test` gate needs no desktop tools at all —
see `references/ci-gate.md`.

Alternatively, vendor the pieces:

1. Copy `.github/actions/drawio-diff/` and `skills/drawio-skill/` (or at
   least `scripts/prdiff.py`, `scripts/drawiodiff.py`, `scripts/autolayout.py`)
   into your repo.
2. Copy `.github/workflows/drawio-pr-diff.example.yml` to
   `.github/workflows/drawio-pr-diff.yml`, drop the `if: false` guard, and
   uncomment the `pull_request: paths: ["**/*.drawio"]` trigger.
3. Give the job `permissions: pull-requests: write` (already set in the
   example) — the sticky comment step needs it; `contents: read` covers the
   checkout.
4. Push a PR that touches a `.drawio` file and watch it run.

## Runner tooling

The draw.io desktop CLI is Electron-based, so headless CI needs the same
setup documented in `docs/CI.md` "Option A" of this repo: Graphviz (`dot`,
for `autolayout.py`) and a virtual display (`xvfb-run`). The composite action
installs both by default (latest `drawio-desktop` `.deb` + `apt-get
graphviz xvfb`); pass `skip-tool-install: true` if your runner/container
already provides `drawio` and `dot` on PATH.

If the draw.io CLI is missing (or fails), `prdiff.py` does **not** hard-fail
the run — the Markdown report still lists every changed file and its status,
just without images, with a note that image export was skipped. `git`
missing (or `--repo` not being a git repository) IS fatal, since without git
there is nothing to diff.

## How the sticky comment works

The action tags its comment body with an HTML marker
(`<!-- drawio-pr-diff-bot -->`) and, before posting, searches the PR's
existing comments (via `gh api .../issues/<n>/comments`) for one starting
with that marker. If found, it `PATCH`es that comment in place; otherwise it
creates a new one with `gh pr comment`. This keeps one running comment per PR
instead of a new comment on every push.

## Running it locally

```
python3 skills/drawio-skill/scripts/prdiff.py --base origin/main --head HEAD \
  --out-dir drawio-pr -o drawio-pr/report.md
```

`--base`/`--head` are any git refs or SHAs (`--head` defaults to `HEAD`);
`--repo` points at a different working tree (default: current directory).
Open `drawio-pr/report.md` to preview exactly what the PR comment will say.
