#!/usr/bin/env bash
# copy-readmes.sh — copy selected companion README files into a target
# project's docs/ directory.
#
# Security properties (verify by reading this file — it is the whole script):
#   - No network access, no `eval`. Only `mkdir -p` and `cp` are invoked.
#   - Source files must already exist under SRC_DIR (this skill's assets/readmes/);
#     the script refuses any filename not present there — it cannot be pointed
#     at an arbitrary source path via its arguments.
#   - Writes are confined to <target-docs-dir>/<filename>; it never deletes or
#     overwrites files outside that directory, and skips (does not clobber) a
#     destination file that already exists unless --force is passed.
#
# Usage:
#   copy-readmes.sh <src-readmes-dir> <target-docs-dir> [--force] <file1.md> [file2.md ...]
set -euo pipefail

SRC_DIR="${1:?usage: copy-readmes.sh <src-readmes-dir> <target-docs-dir> [--force] <file...>}"
DEST_DIR="${2:?usage: copy-readmes.sh <src-readmes-dir> <target-docs-dir> [--force] <file...>}"
shift 2

FORCE=0
if [ "${1:-}" = "--force" ]; then
  FORCE=1
  shift
fi

[ "$#" -ge 1 ] || { echo "No files given to copy." >&2; exit 1; }
[ -d "$SRC_DIR" ] || { echo "Source dir not found: $SRC_DIR" >&2; exit 1; }

mkdir -p -- "$DEST_DIR"

for name in "$@"; do
  case "$name" in
    */*|.*) echo "Refusing suspicious filename: $name" >&2; exit 1 ;;
  esac
  SRC="$SRC_DIR/$name"
  [ -f "$SRC" ] || { echo "Not a known companion README: $name" >&2; exit 1; }

  DEST="$DEST_DIR/$name"
  if [ -e "$DEST" ] && [ "$FORCE" -ne 1 ]; then
    echo "Skipping $DEST (already exists; pass --force to overwrite)"
    continue
  fi
  cp -- "$SRC" "$DEST"
  echo "Copied $name -> $DEST"
done
