#!/usr/bin/env bash
# write-further-reading.sh — merge a "Further Reading" CLAUDE.md section that
# lists only the companion READMEs actually copied into <docs-dir>, never a
# fixed list of all available ones.
#
# This exists because the "further-reading" marker section used to live in
# the main CLAUDE.md.template and always got merged in full, regardless of
# which (if any) companion docs the user chose to install — leaving dead
# `docs/README-*.md` links when a target has no docs/ directory at all.
#
# Usage:
#   write-further-reading.sh <target-CLAUDE.md> <docs-dir-name> [--apply] <readme-file...>
set -euo pipefail

TARGET="${1:?usage: write-further-reading.sh <target-CLAUDE.md> <docs-dir-name> [--apply] <readme-file...>}"
DOCS_DIR="${2:?usage: write-further-reading.sh <target-CLAUDE.md> <docs-dir-name> [--apply] <readme-file...>}"
shift 2

APPLY=""
if [ "${1:-}" = "--apply" ]; then
  APPLY="--apply"
  shift
fi

[ "$#" -ge 1 ] || { echo "No installed README files given — nothing to link, skip this step." >&2; exit 1; }

describe() {
  case "$1" in
    README-cost-optimization.md) echo "pointer to the full cost-optimization reference (command-filtering hooks, model-tier routing setup, settings.json skeleton)" ;;
    README-search-relevance.md) echo "the reasoning behind the Search & Relevance Protocol above" ;;
    README-security-scripts.md) echo "what the apply-template install scripts do and don't do" ;;
    *) echo "companion reference" ;;
  esac
}

WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT
BLOCK="$WORKDIR/further-reading.template"

{
  echo "<!-- ai-assistant-starter:begin:further-reading -->"
  echo "## Further Reading"
  echo ""
  echo "Additional adoption guides installed in \`${DOCS_DIR}/\`:"
  for name in "$@"; do
    case "$name" in
      */*|.*) echo "Refusing suspicious filename: $name" >&2; exit 1 ;;
    esac
    echo "- \`${DOCS_DIR}/${name}\` — $(describe "$name")"
  done
  echo "<!-- ai-assistant-starter:end:further-reading -->"
} > "$BLOCK"

exec skills/apply-template/scripts/apply-template.sh "$BLOCK" "$TARGET" $APPLY
