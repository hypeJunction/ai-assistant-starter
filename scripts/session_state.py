#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""session_state: the state machine behind /start, /done and /trash.

Three concerns, one file:

  * **Worktree identity** — `.claude/worktree.json`, written once per worktree
    by /start: ticket, Jira summary, base branch, branch name.
  * **Per-session phase state** — `.claude/sessions/<session_id>.json`, one per
    Claude Code session so concurrent sessions in a worktree never clobber each
    other. Holds the flow currently running and the status of each of its
    phases.
  * **A read-only bridge to the session-context plugin**, which owns the goal
    and the outcome rating and is the only thing that posts either to Langfuse.

The phase machine is the point. A flow is a fixed, ordered list of phases. The
caller asks `next` for the one phase it may do now, does it, and reports back
with `complete`. `complete` rejects any phase that is not the running head, so
a flow cannot be reordered, skipped past, or silently abandoned halfway.

Every decision the tree can answer is answered here rather than in a skill
body: which gates the diff has earned (`diff_summary`, `auto_skips`), whether
`publish` creates or updates a PR (`publish_plan`), what /trash would destroy
(`inventory`), and what branch /start would cut (`branch_plan`). `next` hands
a phase out together with those parameters, so the same tree always produces
the same run.

Stdlib only. Nothing here reaches the network: goal and outcome posting belong
to the session-context plugin, and the cost report reads this session's own
local JSONL transcript.
"""
import argparse
import collections
import datetime
import glob
import hashlib
import json
import os
import re
import subprocess
import sys

# Ordered phase lists. A flow is complete when every phase has a terminal
# status; `next` hands them out strictly left to right.
FLOWS = {
    "start": ["scope", "worktree", "goal", "handoff"],
    "done": ["review", "validate", "commit", "publish", "record"],
    "trash": ["assess", "confirm", "discard", "record"],
}

PENDING, RUNNING, PASSED, SKIPPED, FAILED = "pending", "running", "passed", "skipped", "failed"
TERMINAL = (PASSED, SKIPPED, FAILED)

# Published USD per million tokens (base input, output). Non-Anthropic and
# third-party-routed models are intentionally absent; a session using one
# reports token counts but no cost.
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


def fail(message, code=2):
    print("session_state: " + message, file=sys.stderr)
    raise SystemExit(code)


# --- paths and files ---

def claude_dir(root):
    return os.path.join(root, ".claude")


def worktree_path(root):
    return os.path.join(claude_dir(root), "worktree.json")


def session_path(root, session_id):
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", str(session_id))
    return os.path.join(claude_dir(root), "sessions", safe + ".json")


def load_json(path):
    try:
        with open(path) as fh:
            data = json.load(fh)
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(data, fh, indent=2)
    os.replace(tmp, path)


def load_worktree(root):
    return load_json(worktree_path(root))


def load_session(root, session_id):
    return load_json(session_path(root, session_id))


def save_session(root, rec):
    save_json(session_path(root, rec["session_id"]), rec)


def new_session(session_id, backfilled=False):
    return {"session_id": session_id, "started_at": now(), "status": "open",
            "closed_at": None, "flow": None, "phases": [], "backfilled": backfilled}


def require_session(root, session_id):
    rec = load_session(root, session_id)
    if rec is None:
        rec = new_session(session_id, backfilled=True)
        save_session(root, rec)
    return rec


def sibling_sessions(root, exclude):
    out = []
    directory = os.path.join(claude_dir(root), "sessions")
    for name in sorted(os.listdir(directory)) if os.path.isdir(directory) else []:
        if not name.endswith(".json") or name[:-5] == exclude:
            continue
        rec = load_json(os.path.join(directory, name))
        if rec:
            out.append(rec)
    return out


# --- git ---

def run(root, argv, timeout=5):
    """Command output on success, None on any failure. Nothing here is worth
    raising over: every caller has a defined answer for "could not tell"."""
    try:
        out = subprocess.run(argv, cwd=root, capture_output=True, text=True, timeout=timeout)
    except Exception:
        return None
    return (out.stdout.strip() or "") if out.returncode == 0 else None


def git(root, *args):
    return run(root, ["git", "-C", root] + list(args))


def porcelain(root):
    """Working-tree status with this script's own bookkeeping filtered out.

    `.claude/sessions/` and `.claude/worktree.json` are written by the very
    commands that then ask whether the tree is dirty, so counting them would
    make every tree look like it has work in it.
    """
    raw = git(root, "status", "--porcelain", "-uall")
    if raw is None:
        return None
    lines = []
    for line in raw.splitlines():
        path = line[3:].strip().strip('"')
        if path.startswith(".claude/sessions/") or path == ".claude/worktree.json":
            continue
        lines.append(line)
    return "\n".join(lines)


def tree_fingerprint(root):
    """HEAD sha plus a digest of the tracked diff and the untracked file list.

    Identifies an exact code state well enough to answer "has anything changed
    since validation passed". Edits to a file that is untracked at both ends
    are the one thing it cannot see: the name is in the digest, the contents
    are not.
    """
    head = git(root, "rev-parse", "HEAD")
    if not head:
        return None
    try:
        diff = subprocess.run(["git", "-C", root, "diff", "HEAD"],
                              capture_output=True, timeout=5)
    except Exception:
        return None
    if diff.returncode != 0:
        return None
    status = porcelain(root) or ""
    digest = hashlib.sha256(diff.stdout + b"\0" + status.encode()).hexdigest()[:12]
    return head + "-" + digest


def is_linked_worktree(root):
    common, local = git(root, "rev-parse", "--git-common-dir"), git(root, "rev-parse", "--git-dir")
    if not common or not local:
        return False
    return os.path.abspath(os.path.join(root, common)) != os.path.abspath(os.path.join(root, local))


def base_branch(root):
    """The branch this work is measured against: /start's record, else origin's default."""
    wt = load_worktree(root) or {}
    recorded = wt.get("base_branch")
    if recorded:
        # /start records whatever `branch-plan` handed it, which is remote-qualified.
        return recorded[len("origin/"):] if recorded.startswith("origin/") else recorded
    head = git(root, "symbolic-ref", "refs/remotes/origin/HEAD") or ""
    return head.rsplit("/", 1)[-1] or "main"


def commits_ahead(root):
    ahead = git(root, "rev-list", "--count", "origin/%s..HEAD" % base_branch(root))
    try:
        return int(ahead)
    except (TypeError, ValueError):
        return 0


def has_work(root):
    """True when there is anything to close out: dirty tree or commits ahead of base."""
    return bool(porcelain(root)) or commits_ahead(root) > 0


# --- diff size, and the checks it makes worth running ---

# Suffixes and directories whose churn cannot break a build or a test. A diff
# confined to them is what `docs` below means.
DOC_SUFFIXES = (".md", ".mdx", ".rst", ".txt", ".adoc")
DOC_DIRS = ("docs/", "doc/", ".github/ISSUE_TEMPLATE/")

# Churn ceilings per size class, and the /code-review effort each one earns.
# A trivial diff earns no review at all: the gate costs more than it can find.
CLASS_LEVELS = {"trivial": None, "small": "low", "moderate": "medium", "large": "high"}


def env_int(name, default):
    try:
        return int(os.environ[name])
    except (KeyError, ValueError):
        return default


def is_doc(path):
    return path.endswith(DOC_SUFFIXES) or path.startswith(DOC_DIRS)


def diff_range(root):
    """The revision every measurement is taken from: the merge-base with the
    base branch when there is one, else HEAD — which narrows the measurement
    to the working tree alone."""
    base = base_branch(root)
    merge_base = git(root, "merge-base", "origin/" + base, "HEAD")
    return base, merge_base or "HEAD"


def untracked_files(root):
    return [line[3:].strip().strip('"') for line in (porcelain(root) or "").splitlines()
            if line.startswith("??")]


def count_lines(path):
    try:
        if os.path.getsize(path) > 1_000_000:
            return 0
        with open(path, "rb") as fh:
            return fh.read().count(b"\n")
    except OSError:
        return 0


def diff_summary(root):
    """Everything /done would ship — commits ahead of base plus the working
    tree — measured as file count, line churn, and a size class.

    The size class is the whole point: it is what lets `auto_skips` decide
    which gates a diff has earned without anyone reading the diff first.
    """
    base, since = diff_range(root)
    numstat = git(root, "diff", "--numstat", since)
    files, added, removed, binary = {}, 0, 0, 0
    for line in (numstat or "").splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        plus, minus, path = parts
        path = path.strip().strip('"')
        if plus == "-" or minus == "-":
            binary += 1
            files[path] = 0
            continue
        added += int(plus)
        removed += int(minus)
        files[path] = int(plus) + int(minus)

    untracked = untracked_files(root)
    for path in untracked:
        lines = count_lines(os.path.join(root, path))
        added += lines
        files[path] = lines

    churn = added + removed
    paths = sorted(files)
    docs = [p for p in paths if is_doc(p)]
    kind = "docs" if paths and len(docs) == len(paths) else ("code" if not docs else "mixed")

    trivial = env_int("DONE_DIFF_TRIVIAL_LINES", 10)
    small = env_int("DONE_DIFF_SMALL_LINES", 80)
    moderate = env_int("DONE_DIFF_MODERATE_LINES", 400)
    if not paths:
        size = "empty"
    elif churn <= trivial and len(paths) <= 2:
        size = "trivial"
    elif churn <= small:
        size = "small"
    elif churn <= moderate:
        size = "moderate"
    else:
        size = "large"

    return {"base": base, "base_ref": "origin/" + base,
            "since": since, "files": paths, "file_count": len(paths),
            "untracked": untracked, "binary": binary, "added": added, "removed": removed,
            "churn": churn, "class": size, "kind": kind,
            "commits_ahead": commits_ahead(root),
            "review_level": CLASS_LEVELS.get(size)}


def without_paths(summary):
    """The summary minus its file lists — what gets stored and reported.

    The counts are the decision inputs; the 300-line path list is not, and
    persisting it makes a `status` read cost more than the check it answers.
    """
    return {k: v for k, v in summary.items() if k not in ("files", "untracked")}


def diff_lines(summary):
    out = ["DIFF_BASE=%s" % summary["base_ref"],
           "DIFF_FILES=%d" % summary["file_count"],
           "DIFF_ADDED=%d" % summary["added"],
           "DIFF_REMOVED=%d" % summary["removed"],
           "DIFF_CHURN=%d" % summary["churn"],
           "DIFF_CLASS=%s" % summary["class"],
           "DIFF_KIND=%s" % summary["kind"],
           "COMMITS_AHEAD=%d" % summary["commits_ahead"],
           "REVIEW_LEVEL=%s" % (summary["review_level"] or "none")]
    return out


# --- derivations the flows would otherwise re-improvise per run ---

def gh_pr(root):
    """The PR for the current branch as a dict, or None when there is none."""
    raw = run(root, ["gh", "pr", "view", "--json", "number,url,title,state,isDraft"], timeout=20)
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) and data.get("number") else None


def publish_plan(root):
    """Whether `publish` creates a PR, updates one, or has no branch to push."""
    branch = git(root, "rev-parse", "--abbrev-ref", "HEAD")
    wt = load_worktree(root) or {}
    upstream = git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
    unpushed = git(root, "rev-list", "--count", "@{upstream}..HEAD") if upstream else None
    pr = gh_pr(root)
    lines = ["BRANCH=%s" % (branch or ""),
             "BASE=%s" % base_branch(root),
             "TICKET=%s" % (wt.get("ticket") or ""),
             "UPSTREAM=%s" % (upstream or "none"),
             "NEEDS_PUSH=%d" % (0 if upstream and unpushed == "0" else 1),
             "PR_ACTION=%s" % ("update" if pr else "create")]
    if pr:
        lines += ["PR_NUMBER=%s" % pr["number"], "PR_STATE=%s" % pr.get("state", ""),
                  "PR_DRAFT=%d" % (1 if pr.get("isDraft") else 0),
                  "PR_URL=%s" % pr.get("url", "")]
    return lines


def inventory(root, session_id):
    """Everything /trash would destroy, counted rather than described."""
    status = porcelain(root) or ""
    dirty = [line for line in status.splitlines() if line]
    wt = load_worktree(root) or {}
    view = sessionctx_view(session_id)
    stashes = (git(root, "stash", "list") or "").splitlines()
    pr = gh_pr(root)
    lines = ["BRANCH=%s" % (git(root, "rev-parse", "--abbrev-ref", "HEAD") or ""),
             "BASE=%s" % base_branch(root),
             "WORKTREE=%s" % root,
             "LINKED_WORKTREE=%d" % (1 if is_linked_worktree(root) else 0),
             "TICKET=%s" % (wt.get("ticket") or view.get("ticket") or ""),
             "GOAL=%s" % (view.get("goal") or ""),
             "DIRTY_FILES=%d" % len(dirty),
             "UNPUSHED_COMMITS=%d" % commits_ahead(root),
             "STASHES=%d" % len(stashes),
             "PR=%s" % (("#%s %s" % (pr["number"], pr.get("url", ""))) if pr else "none")]
    lines += ["FILE %s" % line for line in dirty]
    log = git(root, "log", "--oneline", "origin/%s..HEAD" % base_branch(root))
    lines += ["COMMIT %s" % line for line in (log or "").splitlines() if line]
    return lines


def version_key(name):
    return [int(n) for n in re.findall(r"\d+", name)] or [-1]


def release_branches(root):
    """`origin/rel/*`-style release branches, newest version first."""
    raw = git(root, "for-each-ref", "--format=%(refname:short)",
              "refs/remotes/origin/rel", "refs/remotes/origin/release")
    names = [n for n in (raw or "").splitlines() if n and not n.endswith("/HEAD")]
    return sorted(names, key=version_key, reverse=True)


def observed_prefixes(root):
    """Branch-name prefixes this repo actually uses, most frequent first."""
    raw = git(root, "for-each-ref", "--sort=-committerdate", "--count=60",
              "--format=%(refname:short)", "refs/remotes/origin")
    counts = collections.Counter()
    for name in (raw or "").splitlines():
        short = name.split("/", 1)[1] if name.startswith("origin/") else name
        if "/" in short:
            counts[short.split("/", 1)[0]] += 1
    return [prefix for prefix, _ in counts.most_common()]


# Issue type to branch prefix, before the repo's own habits are consulted.
TYPE_PREFIXES = {"bug": "fix", "defect": "fix", "hotfix": "fix",
                 "story": "ft", "task": "ft", "improvement": "ft", "epic": "ft"}


def slugify(text, words=5):
    parts = re.findall(r"[A-Za-z0-9]+", (text or "").lower())
    return "-".join(parts[:words])


def branch_plan(root, ticket, issue_type, summary):
    """The base branch, branch name and worktree path /start would choose.

    Prefix comes from the issue type when the repo already uses that prefix,
    and from the repo's most common prefix otherwise — so a branch created
    here looks like the branches around it.
    """
    releases = release_branches(root)
    candidates = releases[:2] or ["origin/" + base_branch(root)]
    wanted = TYPE_PREFIXES.get((issue_type or "").strip().lower(), "feature")
    # Only prefixes from the same vocabulary count as convention. A repo whose
    # branches are mostly `docs/` has not thereby voted on what a bug branch
    # should be called.
    known = set(TYPE_PREFIXES.values()) | {"feature"}
    used = [p for p in observed_prefixes(root) if p in known]
    prefix = wanted if (wanted in used or not used) else used[0]
    slug = slugify(summary)
    branch = "%s/%s%s" % (prefix, (ticket or "").upper(), "-" + slug if slug else "")
    repo = os.path.basename(git(root, "rev-parse", "--show-toplevel") or root)
    lines = ["BASE=%s" % (candidates[0] if len(candidates) == 1 else ""),
             "BASE_CANDIDATES=%s" % ",".join(candidates),
             "BASE_AMBIGUOUS=%d" % (1 if len(candidates) > 1 else 0),
             "PREFIX=%s" % prefix,
             "PREFIX_SOURCE=%s" % ("issue-type" if prefix == wanted else "repo-convention"),
             "BRANCH=%s" % branch,
             "WORKTREE_PATH=%s" % os.path.join(
                 os.path.dirname(os.path.abspath(root)),
                 "%s__%s" % (repo, (ticket or "work").lower()))]
    return lines


def phase_params(root, rec, name):
    """The inputs a phase runs with, derived once by the machine."""
    flow = rec.get("flow")
    if flow == "done" and name == "review":
        summary = rec.get("diff") or diff_summary(root)
        return diff_lines(summary) + ["REVIEW_TARGET=%s" % summary["base_ref"]]
    if flow == "done" and name in ("commit", "validate"):
        summary = rec.get("diff") or diff_summary(root)
        return diff_lines(summary)
    if flow == "done" and name == "publish":
        return publish_plan(root)
    if flow == "trash" and name in ("assess", "confirm", "discard"):
        return inventory(root, rec.get("session_id"))
    return []


# --- session-context bridge (read-only) ---

def sessionctx_dirs():
    """Every plausible session-context state directory, best first.

    Mirrors the plugin's own resolution order, plus the plugin-data location
    its hooks pass explicitly via --state-dir.
    """
    candidates = []
    env = os.environ.get("SESSION_CONTEXT_STATE_DIR")
    if env:
        candidates.append(env)
    config = os.path.expanduser(os.environ.get("CLAUDE_CONFIG_DIR") or "~/.claude")
    candidates.append(os.path.join(config, "state", "session-context"))
    candidates.extend(sorted(glob.glob(os.path.join(config, "plugins", "data", "session-context*"))))
    return [d for d in candidates if os.path.isdir(d)]


def sessionctx_record(session_id):
    for directory in sessionctx_dirs():
        rec = load_json(os.path.join(directory, str(session_id) + ".json"))
        if rec:
            return rec
    return None


def sessionctx_view(session_id):
    """The goal, ticket and outcome the session-context plugin holds, if installed."""
    rec = sessionctx_record(session_id)
    if not rec:
        return {"present": False, "goal": None, "ticket": None,
                "outcome": None, "skipped": None}
    goals = rec.get("goals") or []
    latest = goals[-1].get("text") if goals and isinstance(goals[-1], dict) else None
    return {"present": True, "goal": latest, "ticket": rec.get("ticket"),
            "outcome": rec.get("outcome"), "skipped": rec.get("skipped")}


# --- cost, from the local transcript ---

def transcript_path(root, session_id):
    """Locate this session's JSONL transcript, written by Claude Code itself.

    The path is keyed by the cwd Claude Code was *launched* with, which is not
    necessarily `root` — a session started in the main checkout and now working
    inside a /start-created worktree still writes under the launch-cwd slug. Try
    the root-derived slug, then scan every project directory.
    """
    base = os.path.expanduser(os.environ.get("CLAUDE_CONFIG_DIR") or "~/.claude")
    projects = os.path.join(base, "projects")
    candidate = os.path.join(projects, os.path.abspath(root).replace(os.sep, "-"),
                             session_id + ".jsonl")
    if os.path.isfile(candidate):
        return candidate
    try:
        entries = os.listdir(projects)
    except OSError:
        return candidate
    for entry in entries:
        found = os.path.join(projects, entry, session_id + ".jsonl")
        if os.path.isfile(found):
            return found
    return candidate


def session_cost(root, session_id):
    """Main-loop cost and token usage for one session, or None without a transcript.

    Deduplicates on message.id: one assistant message spans several JSONL lines,
    one per content block, and every line repeats the same usage object.
    """
    path = transcript_path(root, session_id)
    if not os.path.isfile(path):
        return None

    totals = collections.Counter()
    cost = 0.0
    seen = set()
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
            key = message.get("id") or ("uuid:" + str(event.get("uuid")))
            if key in seen:
                continue
            seen.add(key)

            inp = usage.get("input_tokens", 0) or 0
            out = usage.get("output_tokens", 0) or 0
            read = usage.get("cache_read_input_tokens", 0) or 0
            creation = usage.get("cache_creation") or {}
            write_5m = creation.get("ephemeral_5m_input_tokens", 0) or 0
            write_1h = creation.get("ephemeral_1h_input_tokens", 0) or 0
            write = usage.get("cache_creation_input_tokens", 0) or (write_5m + write_1h)

            totals["input"] += inp
            totals["output"] += out
            totals["cache_read"] += read
            totals["cache_write"] += write

            rate = RATES.get(message.get("model"))
            if rate:
                base_in, out_rate = rate
                # Cache writes bill at 1.25x base input on the 5-minute TTL and
                # 2x on the 1-hour TTL, so each split is priced separately.
                # Older transcripts report only the flat total with no TTL
                # breakdown; that remainder is billed at the 5-minute rate.
                flat = max(0, write - write_5m - write_1h)
                cost += (inp / 1e6 * base_in
                         + (write_5m + flat) / 1e6 * base_in * 1.25
                         + write_1h / 1e6 * base_in * 2.0
                         + read / 1e6 * base_in * 0.1
                         + out / 1e6 * out_rate)

    return {"cost_usd": round(cost, 4), "messages": len(seen),
            "input": totals["input"], "output": totals["output"],
            "cache_read": totals["cache_read"], "cache_write": totals["cache_write"]}


def cost_line(root, session_id):
    try:
        report = session_cost(root, session_id)
    except Exception:
        return "COST=unavailable"
    if report is None:
        return "COST=unavailable"
    line = ("COST=$%.4f MESSAGES=%d TOKENS_IN=%d TOKENS_OUT=%d CACHE_READ=%d CACHE_WRITE=%d"
            % (report["cost_usd"], report["messages"], report["input"],
               report["output"], report["cache_read"], report["cache_write"]))
    # A session that cost more than the configured threshold is the one worth
    # mining; the skill offers /retro when this appears, never runs it itself.
    try:
        threshold = float(os.environ["SESSION_COST_RETRO_THRESHOLD_USD"])
    except (KeyError, ValueError):
        return line
    if report["cost_usd"] > threshold:
        line += "\nRETRO_SUGGESTED=1 THRESHOLD=$%.2f" % threshold
    return line


# --- the phase machine ---

def phase_entry(name, status=PENDING, detail=None):
    entry = {"name": name, "status": status}
    if detail:
        entry["detail"] = detail
    return entry


def find_phase(rec, name):
    for entry in rec.get("phases") or []:
        if entry.get("name") == name:
            return entry
    return None


def head_phase(rec):
    """The leftmost phase not yet in a terminal status, or None when the flow is done."""
    for entry in rec.get("phases") or []:
        if entry.get("status") not in TERMINAL:
            return entry
    return None


def auto_skips(root, rec, flow):
    """Skips the machine can decide on its own, so a flow never asks what it can check.

    Keeping these here rather than in the skill body is what makes a run
    reproducible: the same tree and the same record always produce the same
    queue, whoever is driving it.
    """
    decided = {}
    if flow == "done":
        fingerprint = tree_fingerprint(root)
        if fingerprint and rec.get("last_validated_sha") == fingerprint:
            decided["validate"] = "already validated at this exact tree state"
        if not load_worktree(root):
            decided["publish"] = "no .claude/worktree.json — branch was never scoped by /start"

        # Gates are earned by the diff, not run by default. A diff too small to
        # hide a bug does not repay a review pass, and one that cannot reach the
        # build does not repay a test run.
        summary = diff_summary(root)
        if not env_int("DONE_REVIEW_ALWAYS", 0):
            if summary["class"] == "trivial":
                decided["review"] = ("diff is %d lines across %d files — below the review threshold"
                                     % (summary["churn"], summary["file_count"]))
            elif summary["kind"] == "docs":
                decided["review"] = "documentation-only diff — %d lines, no executable code" % summary["churn"]
        if summary["kind"] == "docs" and not env_int("DONE_VALIDATE_ALWAYS", 0):
            decided.setdefault("validate", "documentation-only diff — nothing for tests, lint or build to reach")

        if not has_work(root):
            for name in ("review", "validate", "commit", "publish"):
                decided.setdefault(name, "nothing to close out — clean tree, no commits ahead of base")
    if flow == "trash":
        if not has_work(root):
            decided["discard"] = "nothing to discard — clean tree, no commits ahead of base"
    if flow == "start":
        if load_worktree(root):
            decided["worktree"] = "worktree already scoped — inheriting .claude/worktree.json"
    return decided


def render_queue(rec):
    lines = ["FLOW=%s" % rec.get("flow"), "STATUS=%s" % rec.get("status")]
    for entry in rec.get("phases") or []:
        line = "PHASE %s %s" % (entry["name"], entry["status"])
        if entry.get("detail"):
            line += " :: " + entry["detail"]
        lines.append(line)
    head = head_phase(rec)
    lines.append("NEXT=%s" % (head["name"] if head else "none"))
    return "\n".join(lines)


# --- commands ---

def cmd_worktree_init(args):
    save_json(worktree_path(args.root), {
        "ticket": args.ticket, "jira_summary": args.summary,
        "base_branch": args.base, "branch": args.branch, "created_at": now()})
    print("WORKTREE=%s BRANCH=%s BASE=%s" % (args.ticket, args.branch, args.base))


def cmd_plan(args):
    for name in (args.skip or []) + (args.force or []):
        if name not in FLOWS[args.flow]:
            fail("phase %r is not part of flow %r" % (name, args.flow))

    rec = require_session(args.root, args.session)
    if rec.get("flow") and head_phase(rec) and not args.restart:
        fail("flow %r is still running on session %s — finish it, or re-plan with --restart"
             % (rec["flow"], args.session), code=3)

    decided = {} if args.no_auto else auto_skips(args.root, rec, args.flow)
    for name in args.force or []:
        decided.pop(name, None)
    for name in args.skip or []:
        decided[name] = "skipped by flag"

    rec["flow"] = args.flow
    rec["phases"] = [
        phase_entry(name, SKIPPED if name in decided else PENDING, decided.get(name))
        for name in FLOWS[args.flow]
    ]
    rec["status"] = "open"
    rec["planned_at"] = now()
    if args.flow == "done":
        rec["diff"] = without_paths(diff_summary(args.root))
    save_session(args.root, rec)
    print(render_queue(rec))
    if rec.get("diff"):
        print("\n".join(diff_lines(rec["diff"])))


def cmd_next(args):
    rec = load_session(args.root, args.session)
    if rec is None or not rec.get("flow"):
        fail("no flow planned for session %s — run `plan --flow <start|done|trash>` first" % args.session)
    if rec.get("status") == "blocked":
        blocker = next((e["name"] for e in rec["phases"] if e.get("status") == FAILED), "?")
        fail("flow %r is blocked at %r — fix it and re-plan with --restart, or `abort`"
             % (rec["flow"], blocker), code=3)
    head = head_phase(rec)
    if head is None:
        print("FLOW=%s\nSTATUS=%s\nNEXT=none\nCOMPLETE=1" % (rec["flow"], rec.get("status")))
        return
    if head["status"] != RUNNING:
        head["status"] = RUNNING
        head["started_at"] = now()
        save_session(args.root, rec)
    print("FLOW=%s\nSTATUS=%s\nNEXT=%s" % (rec["flow"], rec.get("status"), head["name"]))
    # A phase is handed out with the parameters it needs, so the caller never
    # derives them itself and two runs of the same phase get the same inputs.
    for line in phase_params(args.root, rec, head["name"]):
        print(line)


def cmd_complete(args):
    rec = load_session(args.root, args.session)
    if rec is None or not rec.get("flow"):
        fail("no flow planned for session %s" % args.session)
    if rec.get("status") == "blocked":
        fail("flow %r is blocked — re-plan with --restart, or `abort`" % rec["flow"], code=3)
    head = head_phase(rec)
    if head is None:
        fail("flow %r is already complete" % rec["flow"], code=3)
    if head["name"] != args.phase:
        fail("out of order: phase %r is next, not %r" % (head["name"], args.phase), code=3)

    head["status"] = args.status
    head["finished_at"] = now()
    if args.detail:
        head["detail"] = args.detail
    if args.phase == "validate" and args.status == PASSED:
        fingerprint = tree_fingerprint(args.root)
        if fingerprint:
            rec["last_validated_sha"] = fingerprint
            rec["last_validated_at"] = now()

    if args.status == FAILED and not args.keep_going:
        rec["status"] = "blocked"
        save_session(args.root, rec)
        print(render_queue(rec))
        print("BLOCKED=%s" % args.phase)
        return

    if args.phase == "record":
        rec["status"] = "trashed" if rec["flow"] == "trash" else "done"
        rec["closed_at"] = now()
        if args.detail:
            rec["summary"] = args.detail

    save_session(args.root, rec)
    print(render_queue(rec))
    if rec.get("status") in ("done", "trashed"):
        print(cost_line(args.root, args.session))


def cmd_abort(args):
    rec = load_session(args.root, args.session)
    if rec is None or not rec.get("flow"):
        fail("no flow planned for session %s — nothing to abort" % args.session)
    for entry in rec.get("phases") or []:
        if entry.get("status") not in TERMINAL:
            entry["status"] = SKIPPED
            entry["detail"] = "aborted: " + args.reason
    rec["status"] = "aborted"
    rec["closed_at"] = now()
    save_session(args.root, rec)
    print(render_queue(rec))


def cmd_status(args):
    rec = load_session(args.root, args.session)
    payload = {
        "root": args.root,
        "linked_worktree": is_linked_worktree(args.root),
        "branch": git(args.root, "rev-parse", "--abbrev-ref", "HEAD"),
        "dirty": bool(porcelain(args.root)),
        "has_work": has_work(args.root),
        "worktree": load_worktree(args.root),
        "diff": without_paths(diff_summary(args.root)),
        "session": rec,
        "session_context": sessionctx_view(args.session),
        "siblings": [
            {"session_id": s.get("session_id"), "status": s.get("status"), "flow": s.get("flow")}
            for s in sibling_sessions(args.root, args.session) if s.get("status") == "open"
        ],
    }
    print(json.dumps(payload, indent=2))


def cmd_goal(args):
    """Print the goal session-context holds for this session, for /start to inherit."""
    view = sessionctx_view(args.session)
    if not view["present"]:
        print("SESSION_CONTEXT=absent\nGOAL=")
        return
    print("SESSION_CONTEXT=present\nGOAL=%s\nTICKET=%s" % (view["goal"] or "", view["ticket"] or ""))


def cmd_siblings(args):
    print(json.dumps(sibling_sessions(args.root, args.session), indent=2))


def cmd_cost(args):
    print(cost_line(args.root, args.session))


def cmd_diff(args):
    summary = diff_summary(args.root)
    if args.json:
        print(json.dumps(summary, indent=2))
        return
    print("\n".join(diff_lines(summary)))
    for path in summary["files"]:
        print("FILE %s" % path)


def cmd_publish_plan(args):
    print("\n".join(publish_plan(args.root)))


def cmd_inventory(args):
    print("\n".join(inventory(args.root, args.session)))


def cmd_branch_plan(args):
    print("\n".join(branch_plan(args.root, args.ticket, args.type, args.summary)))


def build_parser():
    parser = argparse.ArgumentParser(prog="session_state.py")
    parser.add_argument("--root", default=os.getcwd(), help="worktree root (default: cwd)")
    subs = parser.add_subparsers(dest="cmd", required=True)

    init = subs.add_parser("worktree-init", help="record this worktree's ticket and branch")
    init.add_argument("--ticket", required=True)
    init.add_argument("--summary")
    init.add_argument("--base", required=True)
    init.add_argument("--branch", required=True)

    plan = subs.add_parser("plan", help="lay out the phase queue for a flow")
    plan.add_argument("--session", required=True)
    plan.add_argument("--flow", required=True, choices=sorted(FLOWS))
    plan.add_argument("--skip", action="append", metavar="PHASE")
    plan.add_argument("--force", action="append", metavar="PHASE",
                      help="run this phase even if the tree state would auto-skip it")
    plan.add_argument("--no-auto", action="store_true",
                      help="do not auto-skip phases the tree state makes unnecessary")
    plan.add_argument("--restart", action="store_true", help="replace a flow still in progress")

    nxt = subs.add_parser("next", help="claim the one phase that may run now")
    nxt.add_argument("--session", required=True)

    done = subs.add_parser("complete", help="report the outcome of the running phase")
    done.add_argument("--session", required=True)
    done.add_argument("--phase", required=True)
    done.add_argument("--status", required=True, choices=[PASSED, SKIPPED, FAILED])
    done.add_argument("--detail")
    done.add_argument("--keep-going", action="store_true",
                      help="continue the flow after a failed phase instead of blocking")

    abort = subs.add_parser("abort", help="end the running flow without completing it")
    abort.add_argument("--session", required=True)
    abort.add_argument("--reason", required=True)

    diff = subs.add_parser("diff", help="size, kind and earned review level of the pending work")
    diff.add_argument("--json", action="store_true")

    subs.add_parser("publish-plan", help="whether `publish` creates or updates a PR, and from what")

    branch = subs.add_parser("branch-plan", help="the base branch, branch name and worktree path /start would choose")
    branch.add_argument("--ticket", required=True)
    branch.add_argument("--type", help="Jira issue type, e.g. Bug or Story")
    branch.add_argument("--summary", help="ticket summary, slugified into the branch name")

    for name, helptext in (("status", "full JSON view of worktree, session and session-context"),
                           ("goal", "the goal session-context holds for this session"),
                           ("siblings", "other sessions open in this worktree"),
                           ("cost", "this session's local cost report"),
                           ("inventory", "everything /trash would destroy, counted")):
        sub = subs.add_parser(name, help=helptext)
        sub.add_argument("--session", required=True)
    return parser


def main(argv):
    args = build_parser().parse_args(argv)
    args.root = os.path.abspath(args.root)
    {"worktree-init": cmd_worktree_init, "plan": cmd_plan, "next": cmd_next,
     "complete": cmd_complete, "abort": cmd_abort, "status": cmd_status,
     "goal": cmd_goal, "siblings": cmd_siblings, "cost": cmd_cost,
     "diff": cmd_diff, "publish-plan": cmd_publish_plan, "inventory": cmd_inventory,
     "branch-plan": cmd_branch_plan}[args.cmd](args)


if __name__ == "__main__":
    main(sys.argv[1:])
