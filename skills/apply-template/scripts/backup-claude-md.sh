#!/usr/bin/env bash
# backup-claude-md.sh — copy an existing CLAUDE.md aside before apply-template touches it.
#
# Security properties (verify by reading this file — it is the whole script):
#   - No network access, no subprocess other than `cp` and `date`.
#   - No `eval`, no sourcing of external files, no variable command construction.
#   - Only ever reads/writes inside the single target path given as $1.
#   - Fails closed: any error (missing arg, cp failure) exits non-zero and writes nothing.
#
# Usage: backup-claude-md.sh <path-to-target-CLAUDE.md>
set -euo pipefail

TARGET="${1:?usage: backup-claude-md.sh <path-to-target-CLAUDE.md>}"

if [ ! -f "$TARGET" ]; then
  echo "No existing file at $TARGET — nothing to back up." >&2
  exit 0
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="${TARGET}.bak.${STAMP}"

cp -- "$TARGET" "$BACKUP"
echo "Backed up $TARGET -> $BACKUP"
