#!/usr/bin/env bash
# Runs a command, suppressing its output unless it exits non-zero.
# Usage: quiet-run.sh <label> -- <command> [args...]
set -uo pipefail

if [[ "$2" != "--" ]]; then
  echo "Usage: quiet-run.sh <label> -- <command> [args...]" >&2
  exit 64
fi

label="$1"
shift 2

output="$("$@" 2>&1)"
status=$?

if [[ $status -eq 0 ]]; then
  echo "PASS: ${label}"
else
  echo "FAIL: ${label} (exit ${status})"
  echo "${output}"
fi

exit $status
