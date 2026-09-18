#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""session_log: per-worktree, per-session state for /start, /done, and /trash.

Two files per worktree:
  .claude/worktree.json            - ticket/branch/base, written once by /start
  .claude/sessions/<session_id>.json - one per Claude Code session, never
                                        shared across concurrent sessions

Stdlib only. Langfuse posting reuses the credential-resolution and payload
shapes from the session-context plugin's session_context.py (resolve_creds,
_lf_post, _lf_score) so it lands in the same Langfuse project/session
without requiring separate credentials. Cost reporting reads the session's
own local JSONL transcript instead — no network call, no export lag, and it
works even when Langfuse isn't configured.
"""
import argparse
import base64
import collections
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.request

SOURCE = "start-done"
HTTP_TIMEOUT = 3
REQUIRED = ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_BASE_URL")
OFFICIAL = "langfuse-observability"

# Published USD per million tokens (base input, output). Mirrors
# skills/cost-audit/references/langfuse_queries.py's RATES table — keep the two
# in sync if pricing changes. Non-Anthropic/third-party-routed models are
# intentionally absent; a session using one reports token counts but no cost.
RATES = {
    "claude-opus-5": (5.0, 25.0),
    "claude-opus-4-8": (5.0, 25.0),
    "claude-sonnet-5": (2.0, 10.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-sonnet-4-5": (3.0, 15.0),
    "claude-sonnet-4-5-20250929": (3.0, 15.0),
    "claude-haiku-4-5": (1.0, 5.0),
    "claude-haiku-4-5-20251001": (1.0, 5.0),
    "claude-fable-5-1": (10.0, 50.0),
    "claude-fable-5": (10.0, 50.0),
    "claude-mythos-5-1": (10.0, 50.0),
}


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def git_validated_sha(root):
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                             capture_output=True, text=True, timeout=5)
        if head.returncode != 0:
            return None
        head_sha = head.stdout.strip()
        diff = subprocess.run(["git", "diff", "HEAD"], cwd=root,
                             capture_output=True, timeout=5)
        if diff.returncode != 0:
            return None
        diff_sha = hashlib.sha256(diff.stdout).hexdigest()[:12]
        return head_sha + "-" + diff_sha
    except Exception:
        return None


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


def new_session(session_id, goal=None, backfilled=False):
    return {"session_id": session_id, "goal": goal, "started_at": now(),
            "status": "in_progress", "done_at": None, "posted": False,
            "backfilled": backfilled}


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


# session_outcome is a 1-10 NUMERIC score, distinct from the legacy session_done
# BOOLEAN — a single flag can't distinguish "shipped cleanly" from "abandoned but
# still technically closed", so a completed session scores 9 and a trashed one
# scores 1. session_done stays alongside it (1 / 0) for continuity with any
# existing dashboards built on the boolean.
OUTCOME_SCORE_DONE = 9
OUTCOME_SCORE_TRASH = 1


def post_outcome(root, rec, done_value, outcome_value, comment=None):
    """Best-effort; never raises, never blocks /done or /trash on failure."""
    cfg = resolve_creds()
    if not cfg:
        return False, "no Langfuse credentials configured"
    try:
        wt = load_worktree(root) or {}
        if wt.get("ticket"):
            _lf_score(cfg, rec["session_id"], "ticket", wt["ticket"], "CATEGORICAL")
        _lf_score(cfg, rec["session_id"], "session_done", done_value, "BOOLEAN", comment)
        _lf_score(cfg, rec["session_id"], "session_outcome", outcome_value, "NUMERIC", comment)
        return True, None
    except Exception as exc:
        return False, str(exc)


def transcript_path(root, session_id):
    """Locate this session's local JSONL transcript, written by Claude Code itself.

    Claude Code writes it to ~/.claude/projects/<slug>/<session_id>.jsonl, where
    <slug> is the absolute cwd path with every path separator replaced by "-"
    (the convention the session-retro skill documents and relies on). This
    assumes `root` is the cwd Claude Code was launched from — true for the
    /start-scoped worktree flow this script is built for.
    """
    base = os.path.expanduser(os.environ.get("CLAUDE_CONFIG_DIR") or "~/.claude")
    slug = os.path.abspath(root).replace(os.sep, "-")
    return os.path.join(base, "projects", slug, session_id + ".jsonl")


def session_cost_local(root, session_id):
    """Best-effort cost + token usage for one session, read from its local transcript.

    Returns None if no transcript file exists yet (e.g. a session ID that was
    never actually run through Claude Code in this project). Deduplicates on
    message.id the same way session-retro's transcript analyzer does — one
    assistant message spans multiple JSONL lines (one per content block), and
    every line repeats the same usage object, so summing per line overcounts.
    Sidechain (subagent) events are excluded — this reports main-loop cost, the
    same scope /done and /trash already track everywhere else.
    """
    path = transcript_path(root, session_id)
    if not os.path.isfile(path):
        return None

    totals = collections.Counter()
    cost = 0.0
    counted_ids = set()
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("type") != "assistant" or event.get("isSidechain"):
                continue
            message = event.get("message") or {}
            usage = message.get("usage") or {}
            if not usage:
                continue
            message_id = message.get("id") or ("uuid:" + str(event.get("uuid")))
            if message_id in counted_ids:
                continue
            counted_ids.add(message_id)

            input_tokens = usage.get("input_tokens", 0) or 0
            output_tokens = usage.get("output_tokens", 0) or 0
            cache_read = usage.get("cache_read_input_tokens", 0) or 0
            creation = usage.get("cache_creation") or {}
            write_5m = creation.get("ephemeral_5m_input_tokens", 0) or 0
            write_1h = creation.get("ephemeral_1h_input_tokens", 0) or 0
            cache_write = usage.get("cache_creation_input_tokens", 0) or (write_5m + write_1h)

            totals["input_tokens"] += input_tokens
            totals["output_tokens"] += output_tokens
            totals["cache_read_tokens"] += cache_read
            totals["cache_write_tokens"] += cache_write

            rate = RATES.get(message.get("model"))
            if rate:
                base_in, out_rate = rate
                # Cache write is billed at 1.25x base input for the 5-minute TTL or 2x
                # for the 1-hour TTL — price each split separately rather than assuming
                # one TTL for the whole session.
                cost += (
                    input_tokens / 1e6 * base_in
                    + write_5m / 1e6 * base_in * 1.25
                    + write_1h / 1e6 * base_in * 2.0
                    + cache_read / 1e6 * base_in * 0.1
                    + output_tokens / 1e6 * out_rate
                )

    return {
        "session_id": session_id,
        "total_cost_usd": round(cost, 4),
        "message_count": len(counted_ids),
        "input_tokens": totals["input_tokens"],
        "output_tokens": totals["output_tokens"],
        "cache_read_tokens": totals["cache_read_tokens"],
        "cache_write_tokens": totals["cache_write_tokens"],
    }


def print_cost_report(root, session_id):
    """Print a one-line cost report from the local transcript; never raises.

    If SESSION_COST_RETRO_THRESHOLD_USD is set and the session's cost exceeds
    it, also prints an advisory line — this script has no way to invoke a
    skill or prompt the user itself, so it's up to the caller (the /done or
    /trash skill) to notice that line and offer /session-retro.
    """
    try:
        r = session_cost_local(root, session_id)
    except Exception as exc:
        print("session_log: cost report unavailable — %s" % exc)
        return
    if r is None:
        print("session_log: cost report unavailable — no local transcript found for %s" % session_id)
        return
    print(
        "session_log: cost report (local transcript) — $%.4f across %d assistant messages "
        "(input=%d, output=%d, cache_read=%d, cache_write=%d)"
        % (r["total_cost_usd"], r["message_count"], r["input_tokens"],
           r["output_tokens"], r["cache_read_tokens"], r["cache_write_tokens"])
    )

    threshold = os.environ.get("SESSION_COST_RETRO_THRESHOLD_USD")
    if threshold:
        try:
            threshold_value = float(threshold)
        except ValueError:
            threshold_value = None
        if threshold_value is not None and r["total_cost_usd"] > threshold_value:
            print(
                "session_log: session cost $%.4f exceeds threshold $%.2f — consider running /session-retro"
                % (r["total_cost_usd"], threshold_value)
            )


# --- CLI ---

def cmd_worktree_init(args):
    save_worktree(args.root, args.ticket, args.summary, args.base, args.branch)
    print("session_log: worktree.json written (%s on %s, base %s)"
          % (args.ticket, args.branch, args.base))


def cmd_start(args):
    rec = load_session(args.root, args.session) or new_session(args.session)
    if args.goal:
        rec["goal"] = args.goal
    if args.resumed_from:
        rec["resumed_from"] = args.resumed_from
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
    backfilled = rec is None
    if backfilled:
        rec = new_session(args.session, backfilled=True)
    rec["status"] = "done"
    rec["done_at"] = now()
    if args.summary:
        rec["summary"] = args.summary
    ok, err = post_outcome(args.root, rec, 1, OUTCOME_SCORE_DONE, comment=rec.get("summary"))
    rec["posted"] = ok
    save_session(args.root, rec)
    if backfilled:
        print("session_log: no prior session record for %s — backfilled one retroactively"
              % args.session)
    if ok:
        print("session_log: session %s marked done, outcome posted to Langfuse (session_outcome=%s)"
              % (args.session, OUTCOME_SCORE_DONE))
    else:
        print("session_log: session %s marked done (kept local: %s)" % (args.session, err))
    print_cost_report(args.root, args.session)


def cmd_trash(args):
    rec = load_session(args.root, args.session)
    backfilled = rec is None
    if backfilled:
        rec = new_session(args.session, backfilled=True)
    rec["status"] = "trashed"
    rec["done_at"] = now()
    rec["reason"] = args.reason
    ok, err = post_outcome(args.root, rec, 0, OUTCOME_SCORE_TRASH, comment=args.reason)
    rec["posted"] = ok
    save_session(args.root, rec)
    if backfilled:
        print("session_log: no prior session record for %s — backfilled one retroactively"
              % args.session)
    if ok:
        print("session_log: session %s marked trashed, outcome posted to Langfuse (session_outcome=%s): %s"
              % (args.session, OUTCOME_SCORE_TRASH, args.reason))
    else:
        print("session_log: session %s marked trashed (kept local: %s): %s" % (args.session, err, args.reason))
    print_cost_report(args.root, args.session)


def cmd_siblings(args):
    sibs = sibling_sessions(args.root, args.session)
    print(json.dumps(sibs, indent=2))


def cmd_status(args):
    out = {"worktree": load_worktree(args.root),
           "session": load_session(args.root, args.session)}
    print(json.dumps(out, indent=2))


def cmd_validated(args):
    rec = load_session(args.root, args.session) or new_session(args.session)
    sha = git_validated_sha(args.root)
    if sha:
        rec["last_validated_sha"] = sha
    rec["last_validated_at"] = now()
    rec["last_validated_mode"] = args.mode
    save_session(args.root, rec)
    print("session_log: validation recorded for %s (mode: %s)" % (args.session, args.mode))


def main(argv):
    parser = argparse.ArgumentParser(prog="session_log.py")
    parser.add_argument("--root", default=os.getcwd(), help="worktree root (default: cwd)")
    subs = parser.add_subparsers(dest="cmd", required=True)

    wi = subs.add_parser("worktree-init")
    wi.add_argument("--ticket", required=True)
    wi.add_argument("--summary")
    wi.add_argument("--base", required=True)
    wi.add_argument("--branch", required=True)

    for name in ("start", "goal", "done", "trash", "siblings", "status"):
        sub = subs.add_parser(name)
        sub.add_argument("--session", required=True)
        if name == "start":
            sub.add_argument("--goal")
            sub.add_argument("--resumed-from")
        if name == "goal":
            sub.add_argument("text")
        if name == "done":
            sub.add_argument("--summary")
        if name == "trash":
            sub.add_argument("--reason", required=True)

    validated = subs.add_parser("validated")
    validated.add_argument("--session", required=True)
    validated.add_argument("--mode", required=True, choices=["quick", "full", "fix", "ci"])

    args = parser.parse_args(argv)
    args.root = os.path.abspath(args.root)
    {"worktree-init": cmd_worktree_init, "start": cmd_start, "goal": cmd_goal,
     "done": cmd_done, "trash": cmd_trash, "siblings": cmd_siblings,
     "status": cmd_status, "validated": cmd_validated}[args.cmd](args)


if __name__ == "__main__":
    main(sys.argv[1:])
