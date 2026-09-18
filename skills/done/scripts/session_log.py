#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""session_log: per-worktree, per-session state for /start and /done.

Two files per worktree:
  .claude/worktree.json            - ticket/branch/base, written once by /start
  .claude/sessions/<session_id>.json - one per Claude Code session, never
                                        shared across concurrent sessions

Stdlib only. Langfuse posting reuses the credential-resolution and payload
shapes from the session-context plugin's session_context.py (resolve_creds,
_lf_post, _lf_score) so it lands in the same Langfuse project/session
without requiring separate credentials.
"""
import argparse
import base64
import datetime
import json
import os
import re
import sys
import urllib.request

SOURCE = "start-done"
HTTP_TIMEOUT = 3
REQUIRED = ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_BASE_URL")
OFFICIAL = "langfuse-observability"


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def claude_dir(root):
    return os.path.join(root, ".claude")


def worktree_path(root):
    return os.path.join(claude_dir(root), "worktree.json")


def sessions_dir(root):
    return os.path.join(claude_dir(root), "sessions")


def session_path(root, session_id):
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", str(session_id))
    return os.path.join(sessions_dir(root), safe + ".json")


def load_json(path):
    try:
        with open(path) as fh:
            data = json.load(fh)
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(data, fh, indent=2)


def load_worktree(root):
    return load_json(worktree_path(root))


def save_worktree(root, ticket, jira_summary, base_branch, branch):
    save_json(worktree_path(root), {
        "ticket": ticket, "jira_summary": jira_summary,
        "base_branch": base_branch, "branch": branch, "created_at": now(),
    })


def load_session(root, session_id):
    return load_json(session_path(root, session_id))


def save_session(root, rec):
    save_json(session_path(root, rec["session_id"]), rec)


def new_session(session_id, goal=None):
    return {"session_id": session_id, "goal": goal, "started_at": now(),
            "status": "in_progress", "done_at": None, "posted": False}


def sibling_sessions(root, exclude):
    out = []
    sd = sessions_dir(root)
    for name in sorted(os.listdir(sd)) if os.path.isdir(sd) else []:
        if not name.endswith(".json"):
            continue
        sid = name[:-5]
        if sid == exclude:
            continue
        rec = load_json(os.path.join(sd, name))
        if rec:
            out.append(rec)
    return out


# --- Langfuse posting (ported from session-context's session_context.py) ---

_official_cache = {}


def official_options():
    cfg = os.path.expanduser(os.environ.get("CLAUDE_CONFIG_DIR") or "~/.claude")
    path = os.path.join(cfg, "settings.json")
    try:
        stamp = os.stat(path).st_mtime_ns
        cached = _official_cache.get(path)
        if cached and cached[0] == stamp:
            return cached[1]
        with open(path) as fh:
            configs = json.load(fh).get("pluginConfigs")
        found = {}
        for pid, entry in (configs.items() if isinstance(configs, dict) else []):
            if str(pid).split("@")[0] == OFFICIAL and isinstance(entry, dict):
                opts = entry.get("options")
                found = opts if isinstance(opts, dict) else {}
                break
        _official_cache[path] = (stamp, found)
        return found
    except Exception:
        return {}


def own(name):
    return os.environ.get("CLAUDE_PLUGIN_OPTION_" + name) or os.environ.get(name)


def _triple(get):
    def text(name):
        value = get(name)
        return value.strip() if isinstance(value, str) else None

    vals = {"pk": text("LANGFUSE_PUBLIC_KEY"), "sk": text("LANGFUSE_SECRET_KEY"),
            "host": text("LANGFUSE_BASE_URL") or text("LANGFUSE_HOST")}
    missing = [name for name, key in zip(REQUIRED, ("pk", "sk", "host")) if not vals[key]]
    return vals, missing


def resolve_creds():
    sources = [own, official_options().get]
    for get in sources:
        vals, missing = _triple(get)
        if not missing:
            return dict(vals, host=vals["host"].rstrip("/"), user=get("LANGFUSE_USER_ID"))
    return None


def _lf_post(cfg, path, payload, extra_headers=None):
    auth = base64.b64encode(("%s:%s" % (cfg["pk"], cfg["sk"])).encode()).decode()
    headers = {"Content-Type": "application/json", "Authorization": "Basic " + auth}
    headers.update(extra_headers or {})
    req = urllib.request.Request(cfg["host"] + path, data=json.dumps(payload).encode(),
                                  headers=headers, method="POST")
    urllib.request.urlopen(req, timeout=HTTP_TIMEOUT).read()


def _lf_score(cfg, session_id, name, value, data_type, comment=None):
    body = {"id": "%s-%s-%s" % (SOURCE, name, session_id), "name": name,
            "sessionId": session_id, "value": value, "dataType": data_type}
    if comment:
        body["comment"] = comment
    _lf_post(cfg, "/api/public/scores", body)


def post_done(root, rec):
    """Best-effort; never raises, never blocks /done on failure."""
    cfg = resolve_creds()
    if not cfg:
        return False, "no Langfuse credentials configured"
    try:
        wt = load_worktree(root) or {}
        if wt.get("ticket"):
            _lf_score(cfg, rec["session_id"], "ticket", wt["ticket"], "CATEGORICAL")
        _lf_score(cfg, rec["session_id"], "session_done", 1, "BOOLEAN", rec.get("summary"))
        return True, None
    except Exception as exc:
        return False, str(exc)


# --- CLI ---

def cmd_worktree_init(args):
    save_worktree(args.root, args.ticket, args.summary, args.base, args.branch)
    print("session_log: worktree.json written (%s on %s, base %s)"
          % (args.ticket, args.branch, args.base))


def cmd_start(args):
    rec = load_session(args.root, args.session) or new_session(args.session)
    if args.goal:
        rec["goal"] = args.goal
    rec["status"] = "in_progress"
    save_session(args.root, rec)
    print("session_log: session %s started (goal: %s)" % (args.session, rec.get("goal")))


def cmd_goal(args):
    rec = load_session(args.root, args.session) or new_session(args.session)
    rec["goal"] = args.text
    save_session(args.root, rec)
    print("session_log: goal recorded for %s" % args.session)


def cmd_done(args):
    rec = load_session(args.root, args.session)
    if rec is None:
        sys.exit("session_log: no session record for %s, run start first" % args.session)
    rec["status"] = "done"
    rec["done_at"] = now()
    if args.summary:
        rec["summary"] = args.summary
    ok, err = post_done(args.root, rec)
    rec["posted"] = ok
    save_session(args.root, rec)
    if ok:
        print("session_log: session %s marked done, outcome posted to Langfuse" % args.session)
    else:
        print("session_log: session %s marked done (kept local: %s)" % (args.session, err))


def cmd_siblings(args):
    sibs = sibling_sessions(args.root, args.session)
    print(json.dumps(sibs, indent=2))


def cmd_status(args):
    out = {"worktree": load_worktree(args.root),
           "session": load_session(args.root, args.session)}
    print(json.dumps(out, indent=2))


def main(argv):
    parser = argparse.ArgumentParser(prog="session_log.py")
    parser.add_argument("--root", default=os.getcwd(), help="worktree root (default: cwd)")
    subs = parser.add_subparsers(dest="cmd", required=True)

    wi = subs.add_parser("worktree-init")
    wi.add_argument("--ticket", required=True)
    wi.add_argument("--summary")
    wi.add_argument("--base", required=True)
    wi.add_argument("--branch", required=True)

    for name in ("start", "goal", "done", "siblings", "status"):
        sub = subs.add_parser(name)
        sub.add_argument("--session", required=True)
        if name == "start":
            sub.add_argument("--goal")
        if name == "goal":
            sub.add_argument("text")
        if name == "done":
            sub.add_argument("--summary")

    args = parser.parse_args(argv)
    args.root = os.path.abspath(args.root)
    {"worktree-init": cmd_worktree_init, "start": cmd_start, "goal": cmd_goal,
     "done": cmd_done, "siblings": cmd_siblings, "status": cmd_status}[args.cmd](args)


if __name__ == "__main__":
    main(sys.argv[1:])
