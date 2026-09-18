#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""SessionStart hook for /start: on every startup/clear, tells Claude whether
this worktree is already scoped to a ticket (inherit path) or needs a fresh
ticket lookup (from-scratch path). Self-contained (no import from skills/done)
so /start can be installed without /done.

Never raises: any failure here should silently skip the nudge, not break the
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
    return out.stdout.strip() or None if out.returncode == 0 else None


def is_worktree(cwd):
    common = git(cwd, "rev-parse", "--git-common-dir")
    local = git(cwd, "rev-parse", "--git-dir")
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


def sibling_sessions(cwd, exclude_id):
    sd = os.path.join(cwd, SESSIONS_SUBDIR)
    out = []
    for name in sorted(os.listdir(sd)) if os.path.isdir(sd) else []:
        if not name.endswith(".json"):
            continue
        sid = name[:-5]
        if sid == exclude_id:
            continue
        rec = load_json(os.path.join(sd, name))
        if rec:
            out.append(rec)
    return out


def get_most_recent_session(cwd, exclude_id):
    """Find the session_id of the most recently started session, excluding the given ID."""
    sessions = sibling_sessions(cwd, exclude_id)
    if not sessions:
        return None
    # Sort by started_at timestamp descending (most recent first)
    sessions.sort(key=lambda x: x.get("started_at", ""), reverse=True)
    return sessions[0].get("session_id")


def write_stub(cwd, session_id):
    path = os.path.join(cwd, SESSIONS_SUBDIR, re.sub(r"[^A-Za-z0-9._-]", "_", session_id) + ".json")
    if os.path.exists(path):
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump({"session_id": session_id, "goal": None, "started_at": now(),
                    "status": "starting", "done_at": None}, fh, indent=2)


INHERIT_PROMPT = """/start: this worktree is already scoped.
Ticket: {ticket} ({branch}, base {base})
{siblings}
Invoke the /start skill's inherit path: confirm the goal for THIS session
(same as the ticket's original goal, or a narrower continuation — ask if
unclear), write .claude/sessions/{sid}.json with that goal and
status "in_progress", then enter Plan Mode and ask how to approach it.
Do not ask for a ticket or create a new worktree."""

FRESH_PROMPT = """/start: no ticket scoped to this session yet.
Invoke the /start skill's from-scratch path: ask the user for a ticket or
work item, fetch its details, determine base branch and branch name, create
a worktree, then scope the goal and enter Plan Mode before any code changes."""

RESUME_PROMPT = """/start: this is a resumed session.
Ticket: {ticket} ({branch}, base {base})
Resumed from: {original_session_id}
{siblings}
This is a continuation of prior work in the same worktree. Log this as a resumed session:
python3 skills/done/scripts/session_log.py --root . start --resumed-from {original_session_id} --goal "<goal>"
Then confirm the goal for THIS session (same as the ticket's original goal,
or a narrower continuation — ask if unclear), enter Plan Mode, and ask how to
approach it. Do not create a new worktree."""



def build_context(cwd, session_id):
    if not is_worktree(cwd):
        return FRESH_PROMPT
    wt = load_json(os.path.join(cwd, WORKTREE_FILE))
    if not wt:
        return FRESH_PROMPT
    write_stub(cwd, session_id)
    sibs = [s for s in sibling_sessions(cwd, session_id) if s.get("status") == "in_progress"]
    sib_text = ""
    if sibs:
        lines = ["Other sessions currently on this worktree:"]
        for s in sibs:
            lines.append("  - %s: %s" % (s.get("session_id"), s.get("goal") or "(no goal yet)"))
        sib_text = "\n".join(lines)
    return INHERIT_PROMPT.format(ticket=wt.get("ticket"), branch=wt.get("branch"),
                                  base=wt.get("base_branch"), siblings=sib_text, sid=session_id)


def build_resume_context(cwd, session_id):
    """Build context for a resumed session."""
    # Find the most recent session (excluding the current one)
    original_session_id = get_most_recent_session(cwd, session_id)
    
    # If no previous session found, treat as fresh
    if not original_session_id:
        return FRESH_PROMPT
    
    # Check if worktree is set up
    if not is_worktree(cwd):
        return FRESH_PROMPT
    
    # Load worktree context
    wt = load_json(os.path.join(cwd, WORKTREE_FILE))
    if not wt:
        return FRESH_PROMPT
    
    # Write stub for this session
    write_stub(cwd, session_id)
    
    # Get sibling sessions (excluding this one and the original)
    sibs = [s for s in sibling_sessions(cwd, session_id) 
            if s.get("status") == "in_progress" and s.get("session_id") != original_session_id]
    sib_text = ""
    if sibs:
        lines = ["Other sessions currently on this worktree:"]
        for s in sibs:
            lines.append("  - %s: %s" % (s.get("session_id"), s.get("goal") or "(no goal yet)"))
        sib_text = "\n".join(lines)
    
    return RESUME_PROMPT.format(
        ticket=wt.get("ticket"), 
        branch=wt.get("branch"),
        base=wt.get("base_branch"), 
        original_session_id=original_session_id,
        siblings=sib_text
    )


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
    session_id = payload["session_id"]
    reason = payload.get("source") or payload.get("startup_reason")
    try:
        if reason == "resume":
            context = build_resume_context(cwd, session_id)
        else:
            context = build_context(cwd, session_id)
    except Exception:
        return
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "SessionStart", "additionalContext": context}}))


if __name__ == "__main__":
    main()
