#!/usr/bin/env bash
# Check if drawio-skill has updates available on the remote.
# Usage: bash scripts/check-update.sh [skill-dir]
#   skill-dir defaults to the script's parent directory.
# Exit codes: 0 = update available, 1 = up to date, 2 = error

set -euo pipefail

SKILL_DIR="${1:-$(cd "$(dirname "$0")/.." && pwd)}"

if ! git -C "$SKILL_DIR" rev-parse --git-dir &>/dev/null; then
  echo "Not a git repository: $SKILL_DIR" >&2
  exit 2
fi

# Detect current branch and its upstream
BRANCH=$(git -C "$SKILL_DIR" symbolic-ref --short HEAD 2>/dev/null) || {
  echo "Detached HEAD — cannot check for updates. Please checkout a branch." >&2
  exit 2
}

UPSTREAM=$(git -C "$SKILL_DIR" rev-parse --abbrev-ref "${BRANCH}@{upstream}" 2>/dev/null) || {
  echo "Branch '$BRANCH' has no upstream configured. Set with: git branch --set-upstream-to=origin/$BRANCH" >&2
  exit 2
}

REMOTE_NAME="${UPSTREAM%%/*}"

# Fetch latest refs from remote
if ! git -C "$SKILL_DIR" fetch "$REMOTE_NAME" --quiet 2>/dev/null; then
  echo "Cannot reach remote '$REMOTE_NAME' (offline?)" >&2
  exit 2
fi

LOCAL_HASH=$(git -C "$SKILL_DIR" rev-parse HEAD 2>/dev/null)
REMOTE_HASH=$(git -C "$SKILL_DIR" rev-parse "$UPSTREAM" 2>/dev/null)

if [ -z "$REMOTE_HASH" ]; then
  echo "Cannot resolve upstream ref '$UPSTREAM'" >&2
  exit 2
fi

if [ "$REMOTE_HASH" != "$LOCAL_HASH" ]; then
  echo "Update available for drawio-skill (branch: $BRANCH)."
  echo "  Local:  ${LOCAL_HASH:0:8}"
  echo "  Remote: ${REMOTE_HASH:0:8}"
  echo "  Run:    cd \"$SKILL_DIR\" && git pull"
  exit 0
else
  echo "drawio-skill is up to date (branch: $BRANCH)."
  exit 1
fi
