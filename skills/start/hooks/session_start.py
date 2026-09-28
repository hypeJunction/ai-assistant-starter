#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""SessionStart hook for /start.

Tells Claude one thing: whether this worktree is already scoped to a ticket,
and if so which one. That is the single fact /start cannot cheaply derive
without a round trip, and knowing it up front lets `plan` auto-skip the
worktree phase instead of asking.

It deliberately does not ask for a goal. The session-context plugin's own
SessionStart hook owns that question, and two intake prompts in one turn is
the ergonomic failure this exists to avoid.

Never raises: any failure silently skips the nudge rather than breaking the
session.
"""
import datetime
import json
import os
import re
import subprocess
import sys

SESSIONS_SUBDIR = os.path.join(".claude", "sessions")
WORKTREE_FILE = os.path.join(".claude", "worktree.json")


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def git(cwd, *args):
    try:
        out = subprocess.run(["git", "-C", cwd] + list(args), capture_output=True,
                             text=True, timeout=3)
    except Exception:
        return None
    return (out.stdout.strip() or "") if out.returncode == 0 else None


def is_worktree(cwd):
    common, local = git(cwd, "rev-parse", "--git-common-dir"), git(cwd, "rev-parse", "--git-dir")
    if not common or not local:
        return False
    return os.path.abspath(os.path.join(cwd, common)) != os.path.abspath(os.path.join(cwd, local))


def load_json(path):
    try:
        with open(path) as fh:
            data = json.load(fh)
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def open_siblings(cwd, exclude_id):
    directory = os.path.join(cwd, SESSIONS_SUBDIR)
    out = []
    for name in sorted(os.listdir(directory)) if os.path.isdir(directory) else []:
        if not name.endswith(".json") or name[:-5] == exclude_id:
            continue
        rec = load_json(os.path.join(directory, name))
        if rec and rec.get("status") == "open":
            out.append(rec)
    return out


def write_stub(cwd, session_id):
    path = os.path.join(cwd, SESSIONS_SUBDIR,
                        re.sub(r"[^A-Za-z0-9._-]", "_", session_id) + ".json")
    if os.path.exists(path):
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump({"session_id": session_id, "started_at": now(), "status": "open",
                   "closed_at": None, "flow": None, "phases": []}, fh, indent=2)


SCOPED = """/start: this worktree is already scoped to {ticket} ({branch}, base {base}).
{siblings}
If the user runs /start, its `plan` call will auto-skip the worktree phase —
do not create another worktree or ask for a ticket. Otherwise ignore this."""

FRESH = """/start: no ticket is scoped to this worktree yet.
If the user runs /start, take the full flow: ticket, worktree, goal, handoff.
Otherwise ignore this."""


def build_context(cwd, session_id):
    if not is_worktree(cwd):
        return FRESH
    wt = load_json(os.path.join(cwd, WORKTREE_FILE))
    if not wt:
        return FRESH
    write_stub(cwd, session_id)
    sibs = open_siblings(cwd, session_id)
    text = ""
    if sibs:
        text = "Also open on this worktree: " + ", ".join(
            "%s (%s)" % (s.get("session_id"), s.get("flow") or "no flow") for s in sibs)
    return SCOPED.format(ticket=wt.get("ticket"), branch=wt.get("branch"),
                         base=wt.get("base_branch"), siblings=text)


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return
    if not isinstance(payload, dict) or not payload.get("session_id"):
        return
    if payload.get("hook_event_name") != "SessionStart":
        return
    if (payload.get("source") or payload.get("startup_reason")) not in ("startup", "clear", "resume"):
        return
    cwd = payload.get("cwd") or os.getcwd()
    try:
        context = build_context(cwd, payload["session_id"])
    except Exception:
        return
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "SessionStart", "additionalContext": context}}))


if __name__ == "__main__":
    main()
