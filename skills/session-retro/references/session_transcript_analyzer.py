#!/usr/bin/env python3
"""
Session transcript analyzer for the `/session-retro` skill.

Parses a single Claude Code session transcript (JSONL, the format written to
~/.claude/projects/<project-slug>/<sessionId>.jsonl) and surfaces candidate
friction points: duplicate tool calls, re-reads of a just-edited file, and
user turns that look like a correction of the assistant's prior action.

Stdlib-only (json, collections) — no dependency install required.

Usage:
    python3 session_transcript_analyzer.py <path-to-session.jsonl>
    python3 session_transcript_analyzer.py <path-to-session.jsonl> --out report.json
"""

import argparse
import collections
import json
import sys

CORRECTION_MARKERS = [
    "no,", "no —", "no -", "don't", "do not ", "stop", "that's wrong",
    "that's not", "thats not", "undo", "revert that", "not what i asked",
    "wrong file", "wrong approach", "why did you", "you shouldn't have",
    "you should not have", "that wasn't", "that isn't", "not right",
    "actually,", "instead of", "i said", "i asked for",
]

RE_READ_TOOLS_WRITE = {"Edit", "Write"}
RE_READ_TOOLS_READ = {"Read"}

# Synthetic/meta content that appears as a "user"-role event but is not the user
# talking: task notifications, hook feedback, local-command output, and the
# system-reminder wrapper around them. Measured on a real 740-message transcript,
# these accounted for 8 of 9 correction-marker matches (e.g. every
# <task-notification> block contains "stop" somewhere in a tool result) — filtering
# them out is required for _find_corrections to mean anything.
SYNTHETIC_USER_MARKERS = (
    "<task-notification>",
    "<local-command-stdout>",
    "<local-command-stderr>",
    "<local-command-caveat>",
    "<system-reminder>",
    "<user-prompt-submit-hook>",
    "<command-name>",
)


def load_events(path):
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _parse_ts(ts):
    try:
        from datetime import datetime

        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ")
    except (ValueError, TypeError):
        return None


def _seconds_between(ts_a, ts_b):
    a, b = _parse_ts(ts_a), _parse_ts(ts_b)
    if a is None or b is None:
        return None
    return (b - a).total_seconds()


def _extract_user_text(content):
    """A real typed prompt can be a bare string or a list of content blocks
    (measured: str 23, list:text 2, list:tool_result 387 in one real transcript —
    list:text entries are genuine prompts and were previously dropped entirely
    because only the str case was handled)."""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = [
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        return "\n".join(p for p in parts if p).strip()
    return ""


def _is_synthetic_user_text(text):
    return any(marker in text for marker in SYNTHETIC_USER_MARKERS)


# A gap larger than this between consecutive events is treated as the user having
# stepped away (or resumed the session later) rather than active work — resumed
# sessions can span days, and last-timestamp-minus-first-timestamp over the whole
# transcript reports that full calendar span as "Duration" (measured: 167,968s /
# 46.7h for one resumed session), which misrepresents time actually spent working.
ACTIVE_GAP_THRESHOLD_SECONDS = 1800


def analyze(path):
    tool_calls = []  # list of dicts: name, input, ts, uuid — main loop only
    subagent_tool_calls = []  # same shape, for isSidechain events
    user_turns = []  # list of dicts: ts, text
    usage_totals = collections.Counter()
    per_message_cache_read = []  # one entry per main-loop assistant message, for the growth check below
    tool_result_sizes = []  # list of dicts: tool_use_id, size, ts — matched to a tool name below
    message_count = 0
    all_ts = []

    for event in load_events(path):
        ts = event.get("timestamp")
        if ts:
            all_ts.append(ts)

        is_sidechain = bool(event.get("isSidechain"))
        etype = event.get("type")
        message = event.get("message") or {}

        if etype == "assistant":
            calls_for_this_event = [
                {"name": item.get("name"), "input": item.get("input"), "ts": ts, "id": item.get("id")}
                for item in (message.get("content") or [])
                if item.get("type") == "tool_use"
            ]
            if is_sidechain:
                # Subagent turns: keep them out of the main loop's duplicate/re-read
                # detection so a subagent's own tool calls aren't misattributed as
                # main-loop duplication.
                subagent_tool_calls.extend(calls_for_this_event)
                continue

            message_count += 1
            usage = message.get("usage") or {}
            usage_totals["input_tokens"] += usage.get("input_tokens", 0) or 0
            usage_totals["output_tokens"] += usage.get("output_tokens", 0) or 0
            cache_read = usage.get("cache_read_input_tokens", 0) or 0
            usage_totals["cache_read_input_tokens"] += cache_read
            usage_totals["cache_creation_input_tokens"] += usage.get("cache_creation_input_tokens", 0) or 0
            if cache_read:
                per_message_cache_read.append(cache_read)
            tool_calls.extend(calls_for_this_event)

        elif etype == "user" and not is_sidechain:
            text = _extract_user_text(message.get("content"))
            if text and not _is_synthetic_user_text(text):
                user_turns.append({"ts": ts, "text": text})
            content = message.get("content")
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        size = _tool_result_size(block.get("content"))
                        if size:
                            tool_result_sizes.append({"tool_use_id": block.get("tool_use_id"), "size": size, "ts": ts})

    duplicate_calls = _find_duplicates(tool_calls)
    reedit_reads = _find_reedit_reads(tool_calls)
    corrections = _find_corrections(user_turns, tool_calls)
    skill_calls = [c for c in tool_calls if c["name"] == "Skill"]
    tool_histogram = collections.Counter(c["name"] for c in tool_calls)
    largest_tool_results = _largest_tool_results(tool_result_sizes, tool_calls)
    avg_cache_read_per_message = (
        round(sum(per_message_cache_read) / len(per_message_cache_read), 1) if per_message_cache_read else 0
    )
    # A flat, large per-message cache-read alongside a high message_count is the
    # transcript-side view of cost-audit's "Context-multiplication" pattern (see
    # references/langfuse_queries.py in the cost-audit skill): every main-loop turn
    # re-pays cache-read on the same large accumulated context. This local view adds
    # what Langfuse can't see — which specific tool_result (e.g. a skill's own
    # SKILL.md/references body) is contributing to that baseline size.
    context_multiplication_signal = {
        "message_count": message_count,
        "avg_cache_read_per_message": avg_cache_read_per_message,
    }

    wall_clock_seconds = None
    active_duration_seconds = None
    if len(all_ts) >= 2:
        ordered = sorted(t for t in all_ts if _parse_ts(t) is not None)
        if len(ordered) >= 2:
            wall_clock_seconds = _seconds_between(ordered[0], ordered[-1])
            active_duration_seconds = 0.0
            for prev, curr in zip(ordered, ordered[1:]):
                gap = _seconds_between(prev, curr) or 0.0
                if gap <= ACTIVE_GAP_THRESHOLD_SECONDS:
                    active_duration_seconds += gap

    return {
        "message_count": message_count,
        "tool_call_count": len(tool_calls),
        "subagent_tool_call_count": len(subagent_tool_calls),
        "user_turn_count": len(user_turns),
        "wall_clock_seconds": wall_clock_seconds,
        "active_duration_seconds": active_duration_seconds,
        "usage_totals": dict(usage_totals),
        "tool_histogram": dict(tool_histogram.most_common()),
        "skills_invoked": sorted({(c["input"] or {}).get("skill") for c in skill_calls if c.get("input")}),
        "duplicate_calls": duplicate_calls,
        "reedit_reads": reedit_reads,
        "correction_points": corrections,
        "context_multiplication_signal": context_multiplication_signal,
        "largest_tool_results": largest_tool_results,
    }


def _tool_result_size(content):
    """A tool_result's content is a plain string on the vast majority of calls
    (verbatim command/file output), occasionally a list of content blocks (e.g.
    image results) — measured on real transcripts, string is the common case, so
    that's what actually needs measuring here."""
    if isinstance(content, str):
        return len(content)
    if isinstance(content, list):
        return sum(len(b.get("text", "")) for b in content if isinstance(b, dict) and b.get("type") == "text")
    return 0


# How many of the biggest tool_results to surface — enough to spot a skill's own
# SKILL.md/references body (loaded once, near the start of a Skill invocation) or a
# verbose command dump, without listing every large-ish read in a long session.
LARGEST_TOOL_RESULTS_LIMIT = 8


def _largest_tool_results(tool_result_sizes, tool_calls):
    """Rank tool_results by size and label each with the tool call it answers, so a
    large one can be read as e.g. "Read of SKILL.md, 12.4KB" instead of a bare number.
    This is the concrete evidence for a Structural/Agentification finding: a skill
    that loads a large reference doc up front shows up here as one big entry near the
    session's start, then gets re-paid on every later turn per
    `context_multiplication_signal`.
    """
    calls_by_id = {c["id"]: c for c in tool_calls if c.get("id")}
    ranked = sorted(tool_result_sizes, key=lambda r: -r["size"])[:LARGEST_TOOL_RESULTS_LIMIT]
    out = []
    for r in ranked:
        call = calls_by_id.get(r["tool_use_id"])
        out.append(
            {
                "tool": call["name"] if call else None,
                "input_summary": _summarize_input(call["name"], json.dumps(call["input"])) if call else None,
                "size_chars": r["size"],
                "ts": r["ts"],
            }
        )
    return out


def _find_duplicates(tool_calls):
    groups = collections.defaultdict(list)
    for call in tool_calls:
        key = (call["name"], json.dumps(call["input"], sort_keys=True))
        groups[key].append(call["ts"])

    return sorted(
        (
            {"tool": name, "input_summary": _summarize_input(name, input_json), "repeat_count": len(ts_list), "timestamps": ts_list}
            for (name, input_json), ts_list in groups.items()
            if len(ts_list) > 1
        ),
        key=lambda r: -r["repeat_count"],
    )


def _summarize_input(name, input_json):
    try:
        parsed = json.loads(input_json) if input_json else {}
    except json.JSONDecodeError:
        return input_json[:120] if input_json else None
    if isinstance(parsed, dict):
        if "file_path" in parsed:
            return parsed["file_path"]
        if "command" in parsed:
            return str(parsed["command"])[:120]
    return json.dumps(parsed)[:120]


# Bounds for _find_reedit_reads: a re-read only counts as friction when it happens
# right after the edit, not whenever the same path is later touched again. Measured
# on a real session: an unbounded last_write dict produced 27 findings, including a
# read 3 days later in a different worktree — clearly not the same-turn re-verify
# pattern this check is meant to catch.
REEDIT_MAX_CALLS_BETWEEN = 20
REEDIT_MAX_SECONDS_BETWEEN = 300


def _find_reedit_reads(tool_calls):
    """Flag a Read that immediately follows an Edit/Write to the same file_path,
    within a small call-count/time window, with no intervening Read/Edit/Write on
    that path in between.
    """
    last_write = {}  # file_path -> (ts, call_index)
    findings = []
    for idx, call in enumerate(tool_calls):
        input_ = call.get("input") or {}
        file_path = input_.get("file_path")
        if not file_path:
            continue
        if call["name"] in RE_READ_TOOLS_WRITE:
            last_write[file_path] = (call["ts"], idx)
        elif call["name"] in RE_READ_TOOLS_READ:
            pending = last_write.pop(file_path, None)
            if pending is None:
                continue
            write_ts, write_idx = pending
            if idx - write_idx > REEDIT_MAX_CALLS_BETWEEN:
                continue
            elapsed = _seconds_between(write_ts, call["ts"])
            if elapsed is not None and elapsed > REEDIT_MAX_SECONDS_BETWEEN:
                continue
            findings.append({"file": file_path, "edited_at": write_ts, "reread_at": call["ts"]})

    return findings


def _find_corrections(user_turns, tool_calls):
    findings = []
    for turn in user_turns:
        text_lower = turn["text"].lower()
        if any(marker in text_lower for marker in CORRECTION_MARKERS):
            preceding = [c["name"] for c in tool_calls if c["ts"] and turn["ts"] and c["ts"] < turn["ts"]][-5:]
            findings.append(
                {
                    "ts": turn["ts"],
                    "user_text": turn["text"][:300],
                    "preceding_tool_calls": preceding,
                }
            )
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("transcript", help="Path to the session's .jsonl transcript file")
    parser.add_argument("--out", help="Write JSON report to this path instead of stdout")
    args = parser.parse_args()

    try:
        report = analyze(args.transcript)
    except FileNotFoundError:
        sys.exit(f"error: transcript not found: {args.transcript}")

    output = json.dumps(report, indent=2)
    if args.out:
        with open(args.out, "w") as f:
            f.write(output)
        print(f"wrote {args.out}")
    else:
        print(output)


if __name__ == "__main__":
    main()
