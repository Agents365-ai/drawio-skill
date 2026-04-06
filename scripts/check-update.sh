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

REMOTE_HASH=$(git -C "$SKILL_DIR" ls-remote origin HEAD 2>/dev/null | cut -f1)
LOCAL_HASH=$(git -C "$SKILL_DIR" rev-parse HEAD 2>/dev/null)

if [ -z "$REMOTE_HASH" ]; then
  echo "Cannot reach remote (offline?)" >&2
  exit 2
fi

if [ "$REMOTE_HASH" != "$LOCAL_HASH" ]; then
  echo "Update available for drawio-skill."
  echo "  Local:  ${LOCAL_HASH:0:8}"
  echo "  Remote: ${REMOTE_HASH:0:8}"
  echo "  Run:    cd $SKILL_DIR && git pull"
  exit 0
else
  echo "drawio-skill is up to date."
  exit 1
fi
