#!/usr/bin/env python3
"""
Static context-footprint measurement for the `/cost-audit` skill.

Measures the fixed, every-turn context baseline — CLAUDE.md files (with
`@file` imports resolved) plus the frontmatter description of every
installed skill (the always-loaded skill index) — separately from the
full body of each skill (only loaded when that skill actually activates).

This is the "what SHOULD the baseline be" half of context-window analysis.
The "what IS the observed baseline" half already comes from Langfuse via
`langfuse_queries.py`'s `avg_cache_read_per_generation` (per trace) and
`/session-retro`'s `avg_cache_read_per_message` (per session) — this script
does not talk to Langfuse or read any transcript; it only reads local files.

Does NOT and CANNOT measure: Claude Code's own base system prompt, tool
schemas, or any other harness-internal overhead — those aren't in any file
this script can read. Never report a total that implies full coverage of
"everything Claude sees every turn" — always frame the total as "the
project/skill-controllable portion of the fixed baseline."

Token counts are an estimate (chars / 4), not an exact tokenization — stdlib
only, no tokenizer dependency. Good enough for relative comparison and
drift-over-time tracking, not for reconciling against a billed token count.

Usage:
    python3 static_footprint.py --project-dir . --out cost_audit_out/static_footprint.json
    python3 static_footprint.py --project-dir . --skills-dir skills   # this repo's own layout
"""

import argparse
import json
import os
import re
import sys

CHARS_PER_TOKEN_ESTIMATE = 4.0

IMPORT_RE = re.compile(r"^@([^\s@].*\.md)\s*$", re.MULTILINE)
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def est_tokens(text):
    return round(len(text) / CHARS_PER_TOKEN_ESTIMATE)


def _read(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


def resolve_claude_md(path, _depth=0, _seen=None):
    """Read a CLAUDE.md and recursively resolve `@relative/file.md` import lines.

    Depth-capped at 5 and dedupes by realpath to guard against import cycles;
    Claude Code's own import resolution has no documented depth limit, so this
    is a safety bound for this script, not a claim about runtime behavior.
    """
    _seen = _seen if _seen is not None else set()
    real = os.path.realpath(path)
    if real in _seen or _depth > 5:
        return []
    _seen.add(real)

    text = _read(path)
    if text is None:
        return []

    entries = [{"path": path, "chars": len(text), "est_tokens": est_tokens(text)}]
    base_dir = os.path.dirname(path)
    for match in IMPORT_RE.finditer(text):
        import_path = os.path.join(base_dir, match.group(1))
        if os.path.isfile(import_path):
            entries.extend(resolve_claude_md(import_path, _depth + 1, _seen))
    return entries


def parse_frontmatter(text):
    """Extract simple top-level `key: value` pairs from a SKILL.md's frontmatter block.

    Deliberately not a full YAML parser (stdlib-only, no PyYAML dependency) —
    only handles the flat scalar fields this project's skills actually use
    (name, description, category, user-invocable). Multi-line list fields
    (e.g. `triggers:`) are skipped; nothing here needs their content.
    """
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    fields = {}
    for line in match.group(1).splitlines():
        if line.startswith((" ", "\t", "-")):
            continue
        kv = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
        if kv:
            fields[kv.group(1)] = kv.group(2).strip()
    return fields


def find_skill_md_files(skills_dirs):
    """Yield one (name, path) per skill *name*, first match wins in `skills_dirs` order.

    A skill installed via `npx skills add` typically exists both in this repo's own
    `skills/` source directory and in the consuming project's `.claude/skills/` (or
    the user's global `~/.claude/skills/`) — same skill, multiple copies on disk.
    Counting every copy would multiply the fixed baseline by however many locations
    happen to carry it, which isn't how the runtime actually loads it (once, from
    wherever it resolves first) — dedupe by name, not by realpath, so each skill is
    counted once regardless of how many install locations it appears in.
    """
    seen_names = set()
    for d in skills_dirs:
        if not d or not os.path.isdir(d):
            continue
        for entry in sorted(os.listdir(d)):
            if entry in seen_names:
                continue
            skill_md = os.path.join(d, entry, "SKILL.md")
            if os.path.isfile(skill_md):
                seen_names.add(entry)
                yield entry, skill_md


def measure_skills(skills_dirs):
    always_loaded = []  # frontmatter description — part of the fixed skill-index baseline
    on_activation = []  # full body — only paid when the skill actually loads
    for name, path in find_skill_md_files(skills_dirs):
        text = _read(path)
        if text is None:
            continue
        fm = parse_frontmatter(text)
        description = fm.get("description", "")
        index_line = f"{fm.get('name', name)}: {description}"
        always_loaded.append({
            "name": fm.get("name", name),
            "path": path,
            "chars": len(index_line),
            "est_tokens": est_tokens(index_line),
            "user_invocable": fm.get("user-invocable", "true") != "false",
        })
        on_activation.append({
            "name": fm.get("name", name),
            "path": path,
            "chars": len(text),
            "est_tokens": est_tokens(text),
        })
    return always_loaded, on_activation


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project-dir", default=".", help="project root to scan for CLAUDE.md and skills/")
    parser.add_argument("--skills-dir", action="append", default=None,
                         help="additional skills directory to scan (repeatable); default scans "
                              "<project-dir>/skills, <project-dir>/.claude/skills, ~/.claude/skills")
    parser.add_argument("--out", default=None, help="write JSON here instead of stdout")
    args = parser.parse_args()

    project_dir = args.project_dir
    claude_md_candidates = [
        os.path.join(project_dir, "CLAUDE.md"),
        os.path.expanduser("~/.claude/CLAUDE.md"),
    ]
    claude_md_entries = []
    seen_realpaths = set()
    for candidate in claude_md_candidates:
        if not os.path.isfile(candidate):
            continue
        for entry in resolve_claude_md(candidate):
            real = os.path.realpath(entry["path"])
            if real not in seen_realpaths:
                seen_realpaths.add(real)
                claude_md_entries.append(entry)

    skills_dirs = args.skills_dir
    if not skills_dirs:
        skills_dirs = [
            os.path.join(project_dir, "skills"),
            os.path.join(project_dir, ".claude", "skills"),
            os.path.expanduser("~/.claude/skills"),
        ]
    always_loaded, on_activation = measure_skills(skills_dirs)

    claude_md_total = sum(e["est_tokens"] for e in claude_md_entries)
    skill_index_total = sum(e["est_tokens"] for e in always_loaded)
    fixed_baseline_total = claude_md_total + skill_index_total

    on_activation_sorted = sorted(on_activation, key=lambda e: -e["est_tokens"])

    result = {
        "claude_md": sorted(claude_md_entries, key=lambda e: -e["est_tokens"]),
        "claude_md_total_est_tokens": claude_md_total,
        "skill_index": sorted(always_loaded, key=lambda e: -e["est_tokens"]),
        "skill_index_total_est_tokens": skill_index_total,
        "skill_count": len(always_loaded),
        "fixed_baseline_total_est_tokens": fixed_baseline_total,
        "fixed_baseline_note": (
            "This total covers only what this script can read from disk: CLAUDE.md files "
            "(with @imports resolved) plus every skill's frontmatter description. It excludes "
            "Claude Code's own base system prompt, tool schemas, and any other harness-internal "
            "overhead, which this script has no access to and does not estimate."
        ),
        "largest_on_activation_skills": on_activation_sorted[:10],
        "on_activation_note": (
            "Full SKILL.md body size, for skills that actually activate this session — NOT part "
            "of the fixed baseline above. Compare against /session-retro's largest_tool_results "
            "and context_multiplication_signal to see whether an activated skill's own body is "
            "what's driving a session's observed avg_cache_read_per_message."
        ),
    }

    output = json.dumps(result, indent=2)
    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w") as f:
            f.write(output)
        print(f"wrote {args.out}")
    else:
        print(output)


if __name__ == "__main__":
    main()
