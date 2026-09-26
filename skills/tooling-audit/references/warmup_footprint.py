#!/usr/bin/env python3
"""Measure the CLAUDE.md / settings.json warmup footprint across recently-active projects.

Walks ~/.claude/projects/*/, resolves each session directory's real cwd from its
transcripts, groups worktrees of the same repo together, and reports the character/
token cost of each project's CLAUDE.md (plus any @-included files) and settings
files. Read-only: makes no changes.
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

STUB_WORD_THRESHOLD = 50
LARGE_WORD_THRESHOLD = 3000
LARGE_SETTINGS_CHAR_THRESHOLD = 5000
LARGE_SETTINGS_ENTRY_THRESHOLD = 100

INCLUDE_RE = re.compile(r"^@(\S+)", re.MULTILINE)


def chars_to_tokens(n_chars):
    return round(n_chars / 4)


def word_count(text):
    return len(text.split())


def find_latest_jsonl(session_dir):
    jsonls = list(session_dir.glob("*.jsonl"))
    if not jsonls:
        return None
    return max(jsonls, key=lambda p: p.stat().st_mtime)


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


def find_git_root(path):
    p = Path(path)
    while p != p.parent:
        git_path = p / ".git"
        if git_path.exists():
            if git_path.is_file():
                # worktree: .git is a file pointing at the common gitdir
                try:
                    text = git_path.read_text()
                    m = re.search(r"gitdir:\s*(.+)", text)
                    if m:
                        gitdir = Path(m.group(1).strip())
                        # .../worktrees/<name> -> common repo is gitdir.parent.parent
                        if "worktrees" in gitdir.parts:
                            idx = gitdir.parts.index("worktrees")
                            common = Path(*gitdir.parts[:idx])
                            return str(common.parent)
                except OSError:
                    pass
            return str(p)
        p = p.parent
    return None


def resolve_includes(claude_md_path, text):
    total_chars = len(text)
    includes = []
    base_dir = claude_md_path.parent
    for match in INCLUDE_RE.finditer(text):
        rel = match.group(1)
        include_path = (base_dir / rel).expanduser()
        if not include_path.is_absolute():
            include_path = (Path.home() / rel).expanduser()
        candidates = [base_dir / rel, Path.home() / rel]
        for candidate in candidates:
            if candidate.is_file():
                inc_text = candidate.read_text(errors="ignore")
                total_chars += len(inc_text)
                includes.append((str(candidate), len(inc_text)))
                break
    return total_chars, includes


def count_permission_entries(settings_json):
    try:
        data = json.loads(settings_json)
    except json.JSONDecodeError:
        return None
    perms = data.get("permissions", {})
    return len(perms.get("allow", [])) + len(perms.get("deny", []))


def measure_settings(dir_path):
    out = {}
    for name in ("settings.json", "settings.local.json"):
        p = dir_path / ".claude" / name
        if p.is_file():
            text = p.read_text(errors="ignore")
            out[name] = {
                "chars": len(text),
                "entries": count_permission_entries(text),
            }
    return out


def discover_active_projects(days):
    cutoff = time.time() - days * 86400
    results = []
    if not CLAUDE_PROJECTS_DIR.is_dir():
        return results
    for session_dir in CLAUDE_PROJECTS_DIR.iterdir():
        if not session_dir.is_dir():
            continue
        jsonls = [p for p in session_dir.glob("*.jsonl") if p.stat().st_mtime >= cutoff]
        if not jsonls:
            continue
        latest = max(jsonls, key=lambda p: p.stat().st_mtime)
        cwd = extract_cwd(latest)
        if not cwd:
            continue
        results.append({"session_dir": str(session_dir), "cwd": cwd, "last_active": latest.stat().st_mtime})
    return results


def build_report(days):
    projects = discover_active_projects(days)

    by_cwd = {}
    for proj in projects:
        by_cwd[proj["cwd"]] = proj

    clusters = defaultdict(list)
    orphans = []
    for cwd, proj in by_cwd.items():
        exists = os.path.isdir(cwd)
        proj["exists"] = exists
        if not exists:
            orphans.append(proj)
            continue
        git_root = find_git_root(cwd)
        key = git_root or cwd
        clusters[key].append(proj)

    global_text = GLOBAL_CLAUDE_MD.read_text(errors="ignore") if GLOBAL_CLAUDE_MD.is_file() else ""
    global_total_chars, global_includes = resolve_includes(GLOBAL_CLAUDE_MD, global_text) if global_text else (0, [])

    report = {
        "days": days,
        "global_claude_md": {
            "path": str(GLOBAL_CLAUDE_MD),
            "chars": len(global_text),
            "tokens": chars_to_tokens(len(global_text)),
            "includes": [{"path": p, "chars": c, "tokens": chars_to_tokens(c)} for p, c in global_includes],
            "total_chars": global_total_chars,
            "total_tokens": chars_to_tokens(global_total_chars),
        },
        "stale_entries": [{"session_dir": p["session_dir"], "cwd": p["cwd"]} for p in orphans],
        "clusters": [],
    }

    for key, members in clusters.items():
        variants = {}
        for m in members:
            claude_md = Path(m["cwd"]) / "CLAUDE.md"
            agents_md = Path(m["cwd"]) / "AGENTS.md"
            text = claude_md.read_text(errors="ignore") if claude_md.is_file() else ""
            settings = measure_settings(Path(m["cwd"]))
            entry = {
                "cwd": m["cwd"],
                "claude_md_chars": len(text),
                "claude_md_tokens": chars_to_tokens(len(text)),
                "has_agents_md": agents_md.is_file(),
                "settings": settings,
            }
            variants.setdefault(text, []).append(entry)

        flags = []
        if len(variants) > 1 and any(v for v in variants if v):
            flags.append("claude_md_drift_within_cluster")

        member_entries = []
        for text, entries in variants.items():
            wc = word_count(text)
            variant_flags = []
            if text and wc < STUB_WORD_THRESHOLD:
                variant_flags.append("stub")
            if wc > LARGE_WORD_THRESHOLD:
                variant_flags.append("oversized")
            for e in entries:
                e["word_count"] = wc
                e["variant_flags"] = variant_flags
                for sname, sinfo in e["settings"].items():
                    sflags = []
                    if sinfo["chars"] > LARGE_SETTINGS_CHAR_THRESHOLD:
                        sflags.append("large_settings_bytes")
                    if sinfo["entries"] is not None and sinfo["entries"] > LARGE_SETTINGS_ENTRY_THRESHOLD:
                        sflags.append("large_permission_list")
                    sinfo["flags"] = sflags
                member_entries.append(e)

        report["clusters"].append({
            "repo_key": key,
            "member_count": len(member_entries),
            "distinct_claude_md_variants": len([v for v in variants if v]),
            "cluster_flags": flags,
            "members": member_entries,
        })

    return report


def render_markdown(report):
    lines = []
    lines.append(f"# Warmup Footprint Report (last {report['days']} days)\n")

    g = report["global_claude_md"]
    lines.append("## Global CLAUDE.md (paid every session, every project)\n")
    lines.append(f"- `{g['path']}`: {g['chars']} chars (~{g['tokens']} tokens)")
    for inc in g["includes"]:
        lines.append(f"  - includes `{inc['path']}`: {inc['chars']} chars (~{inc['tokens']} tokens)")
    lines.append(f"- **Total with includes: {g['total_chars']} chars (~{g['total_tokens']} tokens)**\n")

    lines.append("## Project Clusters\n")
    lines.append("| Repo | Members | Distinct CLAUDE.md variants | CLAUDE.md tokens (per variant) | Flags |")
    lines.append("|---|---|---|---|---|")
    for c in sorted(report["clusters"], key=lambda c: -c["member_count"]):
        variant_tokens = sorted({m["claude_md_tokens"] for m in c["members"]}, reverse=True)
        variant_str = ", ".join(f"~{t}" for t in variant_tokens) if variant_tokens else "none"
        lines.append(
            f"| `{c['repo_key']}` | {c['member_count']} | {c['distinct_claude_md_variants']} | "
            f"{variant_str} | {', '.join(c['cluster_flags']) or '-'} |"
        )

    lines.append("\n## Settings Bloat\n")
    lines.append("| Project | File | Chars | Entries | Flags |")
    lines.append("|---|---|---|---|---|")
    for c in report["clusters"]:
        for m in c["members"]:
            for sname, sinfo in m["settings"].items():
                if sinfo["flags"]:
                    lines.append(
                        f"| `{m['cwd']}` | {sname} | {sinfo['chars']} | "
                        f"{sinfo['entries']} | {', '.join(sinfo['flags'])} |"
                    )

    if report["stale_entries"]:
        lines.append("\n## Stale Project Entries (cwd no longer exists)\n")
        for s in report["stale_entries"]:
            lines.append(f"- `{s['cwd']}` (session dir `{s['session_dir']}`)")

    stub_or_oversized = [
        (m["cwd"], m["variant_flags"])
        for c in report["clusters"]
        for m in c["members"]
        if m["variant_flags"]
    ]
    if stub_or_oversized:
        lines.append("\n## CLAUDE.md Content Flags\n")
        for cwd, flags in stub_or_oversized:
            lines.append(f"- `{cwd}`: {', '.join(flags)}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=30, help="only consider projects active in the last N days")
    parser.add_argument("--json", action="store_true", help="output JSON instead of markdown")
    args = parser.parse_args()

    report = build_report(args.days)
    if args.json:
        json.dump(report, sys.stdout, indent=2)
        print()
    else:
        print(render_markdown(report))


if __name__ == "__main__":
    main()
