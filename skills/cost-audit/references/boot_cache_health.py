#!/usr/bin/env python3
"""
Boot/cross-session cache-health measurement for the `/cost-audit` skill.

Measures whether a session's FIRST model call (the "boot call") is served
from a warm prompt cache (cheap cache-read) or forced to rebuild it (expensive
cache-write), and whether that's correlated with edits landing on the files
that make up the cached system-prompt prefix — global/project CLAUDE.md, its
`@`-includes, and every installed skill's SKILL.md — between one session's
boot and the next.

This is the cross-session complement to `static_footprint.py` (which measures
the SIZE of that fixed baseline, not whether it's actually served from cache)
and to `langfuse_queries.py`'s `automation_drift.cache_write_jump` (which
detects a cache-TTL lapse WITHIN one long-running session's cycles, not
between sessions). Reads only local transcripts — no Langfuse credentials
needed, same precedent as `static_footprint.py`.

The causal claim this script tests — that editing CLAUDE.md/SKILL.md between
sessions forces the next session's boot call to miss the prompt cache — is
NOT confirmed by Anthropic documentation. It is inferred from general
prompt-caching mechanics (exact-prefix match). Treat this script's bucketed
hit/miss comparison as the evidence for or against that claim on this user's
own data, not as a foregone conclusion.

Usage:
    python3 boot_cache_health.py --days 30
    python3 boot_cache_health.py --days 30 --json
    python3 boot_cache_health.py --days 30 --recent-edit-window-hours 6
"""
import argparse
import json
import os
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"
GLOBAL_CLAUDE_MD = Path.home() / ".claude" / "CLAUDE.md"
GLOBAL_SKILLS_DIR = Path.home() / ".claude" / "skills"

INCLUDE_RE = re.compile(r"^@(\S+)", re.MULTILINE)

# Same rate table `langfuse_queries.py` maintains (USD per million tokens):
# (base_input_rate, output_rate), confirmed against
# https://platform.claude.com/docs/en/about-claude/pricing. Cache multipliers
# below are expressed as multiples of base_input_rate, matching
# langfuse_queries.py's BIE_MULTIPLIER (cache_read=0.1, cache_write_5m=1.25)
# plus the 1h-TTL cache-write value (2.0) it applies as a raw literal rather
# than a named constant.
RATES = {
    "claude-opus-5-5": (4.0, 20.0),
    "claude-opus-5": (5.0, 25.0),
    "claude-opus-4-8": (5.0, 25.0),
    "claude-opus-4-7": (5.0, 25.0),
    "claude-opus-4-6": (5.0, 25.0),
    "claude-opus-4-5": (5.0, 25.0),
    "claude-sonnet-5": (2.0, 10.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-sonnet-4-5": (3.0, 15.0),
    "claude-sonnet-4-5-20250929": (3.0, 15.0),
    "claude-haiku-4-5": (1.0, 5.0),
    "claude-haiku-4-5-20251001": (1.0, 5.0),
    "claude-fable-5-1": (10.0, 50.0),
    "claude-fable-5": (10.0, 50.0),
    "claude-mythos-5-1": (10.0, 50.0),
    "claude-mythos-5": (10.0, 50.0),
}
DEFAULT_RATE = (5.0, 25.0)
CACHE_WRITE_5M_MULTIPLIER = 1.25
CACHE_WRITE_1H_MULTIPLIER = 2.0
# Cache-READ (hit) multiplier: 0.1x base input is standard, except Opus 5.5
# (0.05x) and Fable/Mythos 5.1 (0.025x) — same three exceptions
# langfuse_queries.py tracks in CACHE_READ_MULTIPLIER_OVERRIDE.
CACHE_READ_MULTIPLIER_OVERRIDE = {
    "claude-opus-5-5": 0.05,
    "claude-fable-5-1": 0.025,
    "claude-mythos-5-1": 0.025,
}
DEFAULT_CACHE_READ_MULTIPLIER = 0.1

HIT_THRESHOLD = 0.9   # cache_read >= 90% of (cache_read + cache_creation) -> hit
MISS_THRESHOLD = 0.9  # cache_creation >= 90% of (cache_read + cache_creation) -> miss

# Model IDs seen that aren't in RATES — priced at DEFAULT_RATE (Opus-tier) as
# a placeholder, which over/understates cost for whatever the real tier is.
# Surfaced in the report so pricing-table staleness (e.g. a new model
# release) is visible instead of silently skewing every bucket average.
_unpriced_models_seen = set()


def price_usage(model, usage):
    if model not in RATES:
        _unpriced_models_seen.add(model or "<unknown>")
    base_in, out_rate = RATES.get(model, DEFAULT_RATE)
    cache_read_mult = CACHE_READ_MULTIPLIER_OVERRIDE.get(model, DEFAULT_CACHE_READ_MULTIPLIER)
    fresh_in = usage.get("input_tokens", 0) or 0
    cache_read = usage.get("cache_read_input_tokens", 0) or 0
    cache_creation = usage.get("cache_creation_input_tokens", 0) or 0
    output = usage.get("output_tokens", 0) or 0

    creation = usage.get("cache_creation") or {}
    write_1h = creation.get("ephemeral_1h_input_tokens", 0) or 0
    write_5m = creation.get("ephemeral_5m_input_tokens", 0) or 0
    # Older/other payloads only carry the flat field with no 1h/5m split;
    # assume the (cheaper, more common) 5-minute tier when we can't tell.
    if not write_1h and not write_5m and cache_creation:
        write_5m = cache_creation

    cost = (
        fresh_in / 1e6 * base_in
        + cache_read / 1e6 * base_in * cache_read_mult
        + write_5m / 1e6 * base_in * CACHE_WRITE_5M_MULTIPLIER
        + write_1h / 1e6 * base_in * CACHE_WRITE_1H_MULTIPLIER
        + output / 1e6 * out_rate
    )
    return round(cost, 6), cache_read, cache_creation


def classify_boot(cache_read, cache_creation):
    total = cache_read + cache_creation
    if total == 0:
        return "no_cache_signal"
    if cache_read / total >= HIT_THRESHOLD:
        return "cache_hit"
    if cache_creation / total >= MISS_THRESHOLD:
        return "cache_miss"
    return "mixed"


def find_boot_usage(jsonl_path):
    """First assistant message carrying a usage object in this transcript."""
    try:
        with open(jsonl_path, "r", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if obj.get("type") != "assistant":
                    continue
                message = obj.get("message") or {}
                usage = message.get("usage")
                if not isinstance(usage, dict):
                    continue
                ts = obj.get("timestamp")
                return {
                    "model": message.get("model") or "",
                    "usage": usage,
                    "timestamp": ts,
                }
    except OSError:
        return None
    return None


def extract_cwd(jsonl_path):
    try:
        with open(jsonl_path, "r", errors="ignore") as f:
            for _ in range(20):
                line = f.readline()
                if not line:
                    break
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                cwd = obj.get("cwd")
                if cwd:
                    return cwd
    except OSError:
        return None
    return None


def parse_iso_ts(ts):
    if not ts:
        return None
    try:
        # transcript timestamps are ISO8601 with a trailing "Z"
        t = time.strptime(ts.split(".")[0].rstrip("Z"), "%Y-%m-%dT%H:%M:%S")
        return time.mktime(t)
    except (ValueError, AttributeError):
        return None


def resolve_include_mtimes(claude_md_path):
    """mtime of claude_md_path plus every @-include it resolves to."""
    mtimes = []
    if not claude_md_path.is_file():
        return mtimes
    mtimes.append(claude_md_path.stat().st_mtime)
    try:
        text = claude_md_path.read_text(errors="ignore")
    except OSError:
        return mtimes
    base_dir = claude_md_path.parent
    for match in INCLUDE_RE.finditer(text):
        rel = match.group(1)
        for candidate in (base_dir / rel, Path.home() / rel):
            if candidate.is_file():
                mtimes.append(candidate.stat().st_mtime)
                break
    return mtimes


def _git_commit_times(project_dir, pathspec):
    """Every commit timestamp touching pathspec, or [] if not a git repo /
    no history. A full history, not just the latest commit, because a
    session's boot time can fall between two edits — the latest commit as
    of NOW may be long after that session ran."""
    if not (Path(project_dir) / ".git").exists():
        return []
    import subprocess
    try:
        out = subprocess.run(
            ["git", "-C", str(project_dir), "log", "--format=%at", "--", *pathspec],
            capture_output=True, text=True, timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if out.returncode != 0:
        return []
    times = []
    for line in out.stdout.splitlines():
        line = line.strip()
        if line.isdigit():
            times.append(float(line))
    return times


def project_prefix_edit_candidates(project_dir):
    """Every known edit timestamp to this project's cache-prefix files:
    CLAUDE.md and every installed skill's SKILL.md (the always-loaded
    index). Git commit history when the project is a git repo (accurate at
    any point in the past); otherwise the single current mtime, which is
    only valid as a lower bound for sessions that booted after it — the
    caller filters candidates against each session's boot time."""
    candidates = _git_commit_times(project_dir, ["CLAUDE.md"])
    candidates += _git_commit_times(project_dir, ["skills", ".claude/skills"])

    p = Path(project_dir) / "CLAUDE.md"
    if p.is_file() and not candidates:
        candidates.append(p.stat().st_mtime)

    skills_dirs = [
        Path(project_dir) / "skills",
        Path(project_dir) / ".claude" / "skills",
        GLOBAL_SKILLS_DIR,
    ]
    seen = set()
    for skills_dir in skills_dirs:
        if not skills_dir.is_dir():
            continue
        for skill_md in skills_dir.glob("*/SKILL.md"):
            try:
                real = skill_md.resolve()
            except OSError:
                real = skill_md
            if real in seen:
                continue
            seen.add(real)
            try:
                candidates.append(skill_md.stat().st_mtime)
            except OSError:
                continue
    return candidates


def find_git_root(path):
    p = Path(path)
    while p != p.parent:
        if (p / ".git").exists():
            return str(p)
        p = p.parent
    return None


def discover_sessions(days):
    cutoff = time.time() - days * 86400
    sessions = []
    if not CLAUDE_PROJECTS_DIR.is_dir():
        return sessions
    for session_dir in CLAUDE_PROJECTS_DIR.iterdir():
        if not session_dir.is_dir():
            continue
        for jsonl in session_dir.glob("*.jsonl"):
            if jsonl.stat().st_mtime < cutoff:
                continue
            cwd = extract_cwd(jsonl)
            if not cwd or not os.path.isdir(cwd):
                continue
            sessions.append({"jsonl": jsonl, "cwd": cwd})
    return sessions


def build_report(days, recent_edit_window_hours):
    global_mtimes = resolve_include_mtimes(GLOBAL_CLAUDE_MD)
    global_last_edit = max(global_mtimes) if global_mtimes else None

    prefix_candidates_cache = {}  # git_root -> all known prefix-edit timestamps (incl. global)

    sessions = discover_sessions(days)
    per_session = []

    for s in sessions:
        boot = find_boot_usage(s["jsonl"])
        if not boot:
            continue
        cost, cache_read, cache_creation = price_usage(boot["model"], boot["usage"])
        state = classify_boot(cache_read, cache_creation)
        boot_ts = parse_iso_ts(boot["timestamp"]) or s["jsonl"].stat().st_mtime

        git_root = find_git_root(s["cwd"]) or s["cwd"]
        if git_root not in prefix_candidates_cache:
            prefix_candidates_cache[git_root] = list(global_mtimes) + project_prefix_edit_candidates(git_root)
        candidates = prefix_candidates_cache[git_root]

        # Only a timestamp that actually precedes this session's boot tells us
        # anything about the file's state AT boot — a candidate from AFTER
        # boot (e.g. today's edit, for a session from last week) is excluded,
        # not treated as "the file was already stale."
        before_boot = [t for t in candidates if t <= boot_ts]
        last_prefix_edit = max(before_boot) if before_boot else None

        hours_since_edit = None
        if last_prefix_edit is not None:
            hours_since_edit = round((boot_ts - last_prefix_edit) / 3600, 2)

        per_session.append({
            "session": s["jsonl"].stem,
            "cwd": s["cwd"],
            "model": boot["model"],
            "boot_state": state,
            "boot_cost_usd": cost,
            "cache_read_tokens": cache_read,
            "cache_creation_tokens": cache_creation,
            "hours_since_last_prefix_edit": hours_since_edit,
        })

    recent = [s for s in per_session if s["hours_since_last_prefix_edit"] is not None
              and 0 <= s["hours_since_last_prefix_edit"] <= recent_edit_window_hours]
    not_recent = [s for s in per_session if s["hours_since_last_prefix_edit"] is not None
                  and s["hours_since_last_prefix_edit"] > recent_edit_window_hours]
    unknown = [s for s in per_session if s["hours_since_last_prefix_edit"] is None]

    def bucket_summary(bucket):
        n = len(bucket)
        if n == 0:
            return {"sessions": 0, "cache_miss_rate": None, "avg_boot_cost_usd": None}
        misses = sum(1 for s in bucket if s["boot_state"] == "cache_miss")
        avg_cost = round(sum(s["boot_cost_usd"] for s in bucket) / n, 6)
        return {
            "sessions": n,
            "cache_miss_rate": round(misses / n, 4),
            "avg_boot_cost_usd": avg_cost,
        }

    recent_summary = bucket_summary(recent)
    not_recent_summary = bucket_summary(not_recent)
    cost_delta_usd = None
    if recent_summary["avg_boot_cost_usd"] is not None and not_recent_summary["avg_boot_cost_usd"] is not None:
        cost_delta_usd = round(recent_summary["avg_boot_cost_usd"] - not_recent_summary["avg_boot_cost_usd"], 6)

    return {
        "days": days,
        "recent_edit_window_hours": recent_edit_window_hours,
        "global_claude_md_last_edit": global_last_edit,
        "sessions_analyzed": len(per_session),
        "sessions_with_unknown_edit_recency": len(unknown),
        "buckets": {
            "recent_prefix_edit": recent_summary,
            "no_recent_prefix_edit": not_recent_summary,
            "boot_cost_delta_usd": cost_delta_usd,
        },
        "overall": bucket_summary(per_session),
        "unpriced_models": sorted(_unpriced_models_seen),
        "sessions": per_session,
    }


def render_markdown(report):
    lines = []
    lines.append(f"# Boot Cache Health (last {report['days']} days)\n")
    lines.append(
        "> Correlational evidence only — whether editing CLAUDE.md/SKILL.md "
        "between sessions actually forces the next boot call to miss the "
        "prompt cache is inferred from prompt-caching mechanics, not "
        "confirmed by Anthropic documentation. Read the bucket comparison "
        "below as this user's own observed data, not a foregone conclusion.\n"
    )
    lines.append(f"- Sessions analyzed: **{report['sessions_analyzed']}** "
                  f"({report['sessions_with_unknown_edit_recency']} with no resolvable prefix-edit timestamp)")
    o = report["overall"]
    lines.append(f"- Overall cache-miss rate at boot: **{o['cache_miss_rate']}** "
                  f"(avg boot cost ${o['avg_boot_cost_usd']})\n")

    if report["unpriced_models"]:
        lines.append(
            f"- ⚠️ **Pricing table is stale for**: {', '.join(report['unpriced_models'])} "
            f"— priced at the DEFAULT_RATE placeholder (Opus-tier), not that model's actual rate. "
            f"Add these to `RATES` in this file and `langfuse_queries.py` for accurate cost figures.\n"
        )

    b = report["buckets"]
    lines.append(f"## Booted within {report['recent_edit_window_hours']}h of a CLAUDE.md/SKILL.md edit\n")
    r = b["recent_prefix_edit"]
    nr = b["no_recent_prefix_edit"]
    lines.append(f"- Recent-edit sessions: {r['sessions']}, cache-miss rate {r['cache_miss_rate']}, "
                  f"avg boot cost ${r['avg_boot_cost_usd']}")
    lines.append(f"- No-recent-edit sessions: {nr['sessions']}, cache-miss rate {nr['cache_miss_rate']}, "
                  f"avg boot cost ${nr['avg_boot_cost_usd']}")
    lines.append(f"- **Boot cost delta (recent − not-recent): ${b['boot_cost_delta_usd']}**\n")

    lines.append("## Per-Session Detail\n")
    lines.append("| Session | Repo | Boot state | Boot cost | Hours since prefix edit |")
    lines.append("|---|---|---|---|---|")
    for s in sorted(report["sessions"], key=lambda s: -(s["boot_cost_usd"] or 0))[:30]:
        lines.append(f"| `{s['session'][:12]}` | `{s['cwd']}` | {s['boot_state']} | "
                      f"${s['boot_cost_usd']} | {s['hours_since_last_prefix_edit']} |")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--days", type=int, default=30, help="only consider sessions active in the last N days")
    parser.add_argument("--recent-edit-window-hours", type=float, default=6.0,
                         help="a session boots 'near' a prefix edit if within this many hours of it")
    parser.add_argument("--out", default=None, help="write output here instead of stdout")
    parser.add_argument("--json", action="store_true", help="output JSON instead of markdown")
    args = parser.parse_args()

    report = build_report(args.days, args.recent_edit_window_hours)
    output = json.dumps(report, indent=2) if args.json else render_markdown(report)

    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w") as f:
            f.write(output)
        print(f"wrote {args.out}")
    else:
        print(output)


if __name__ == "__main__":
    main()
