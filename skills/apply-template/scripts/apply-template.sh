#!/usr/bin/env bash
# apply-template.sh — merge marker-delimited sections from the apply-template
# CLAUDE.md template into a target project's CLAUDE.md, idempotently.
#
# Security properties (verify by reading this file — it is the whole script):
#   - No network access. No `eval`, no `curl`/`wget`, no sourcing of external files.
#   - Only two paths are ever touched: TEMPLATE (read-only) and TARGET (read/write).
#     Both are required arguments — the script never guesses or globs a path.
#   - Dry-run by default: prints a unified diff and writes nothing unless --apply
#     is passed explicitly.
#   - Merge logic is marker-based (matches `<!-- ai-assistant-starter:begin:X -->`
#     / `:end:X -->` pairs), never a blind regex substitution over arbitrary lines —
#     each section is replaced wholesale between its own markers, or appended if
#     the target has no such block yet. Content outside recognized marker blocks
#     is never modified.
#   - Fails closed: any error exits non-zero before any write.
#
# Usage:
#   apply-template.sh <template-file> <target-CLAUDE.md> [--apply]
set -euo pipefail

TEMPLATE="${1:?usage: apply-template.sh <template-file> <target-CLAUDE.md> [--apply]}"
TARGET="${2:?usage: apply-template.sh <template-file> <target-CLAUDE.md> [--apply]}"
APPLY="${3:-}"

[ -f "$TEMPLATE" ] || { echo "Template not found: $TEMPLATE" >&2; exit 1; }
touch -- "$TARGET" 2>/dev/null || true
[ -e "$TARGET" ] || : > "$TARGET"

WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

MERGED="$WORKDIR/merged.md"
cp -- "$TARGET" "$MERGED"

# Extract each begin/end marker name present in the template, in order.
SECTIONS="$(grep -o 'ai-assistant-starter:begin:[a-zA-Z0-9_-]*' "$TEMPLATE" | sed 's/.*begin://' || true)"

for section in $SECTIONS; do
  BEGIN="<!-- ai-assistant-starter:begin:${section} -->"
  END="<!-- ai-assistant-starter:end:${section} -->"

  # Pull this section's block (inclusive of markers) out of the template.
  awk -v b="$BEGIN" -v e="$END" '
    $0 == b {p=1}
    p {print}
    $0 == e {p=0}
  ' "$TEMPLATE" > "$WORKDIR/block.$section"

  if grep -qF "$BEGIN" "$MERGED"; then
    # Replace the existing block between markers in-place.
    awk -v b="$BEGIN" -v e="$END" -v blockfile="$WORKDIR/block.$section" '
      $0 == b {
        while ((getline line < blockfile) > 0) print line
        p=1
        next
      }
      $0 == e { p=0; next }
      !p { print }
    ' "$MERGED" > "$WORKDIR/merged.next"
  else
    # No existing block — append with a blank line separator.
    cp -- "$MERGED" "$WORKDIR/merged.next"
    { echo ""; cat "$WORKDIR/block.$section"; } >> "$WORKDIR/merged.next"
  fi
  mv -- "$WORKDIR/merged.next" "$MERGED"
done

if [ "$APPLY" != "--apply" ]; then
  echo "--- dry run: diff of $TARGET (no changes written; pass --apply to write) ---"
  diff -u -- "$TARGET" "$MERGED" || true
  exit 0
fi

cp -- "$MERGED" "$TARGET"
echo "Applied $(echo "$SECTIONS" | wc -w | tr -d ' ') section(s) to $TARGET"
