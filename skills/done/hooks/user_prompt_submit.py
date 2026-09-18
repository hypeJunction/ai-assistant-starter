#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""UserPromptSubmit hook for /done: on the first prompt after /done marked
this session's state file done, nudge Claude to /compact before continuing.

This is advisory only — Claude Code has no mechanism for a hook to force
compaction, so this injects additionalContext asking Claude to run /compact
itself. It fires once: after nudging, the flag is cleared so later prompts in
the same (now-reopened) session are not interrupted again.
"""
import json
import os
import re
import sys

SESSIONS_SUBDIR = os.path.join(".claude", "sessions")

NUDGE = """/done marked this session complete and posted its outcome. Before
doing anything else with the message below, run /compact to reclaim context,
then continue with the user's request."""


def session_path(cwd, session_id):
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", str(session_id))
    return os.path.join(cwd, SESSIONS_SUBDIR, safe + ".json")


def load_json(path):
    try:
        with open(path) as fh:
            data = json.load(fh)
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return
    if not isinstance(payload, dict) or not payload.get("session_id"):
        return
    cwd = payload.get("cwd") or os.getcwd()
    session_id = payload["session_id"]
    path = session_path(cwd, session_id)
    rec = load_json(path)
    if not rec or rec.get("status") != "done" or rec.get("compact_nudged"):
        return
    rec["compact_nudged"] = True
    try:
        with open(path, "w") as fh:
            json.dump(rec, fh, indent=2)
    except Exception:
        return
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit", "additionalContext": NUDGE}}))


if __name__ == "__main__":
    main()
