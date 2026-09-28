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
    user_turns = []  # list of dicts: ts, text, prompt_est_tokens
    usage_totals = collections.Counter()
    per_message_cache_read = []  # one entry per main-loop assistant message, for the growth check below
    per_message_context = []  # list of dicts: ts, context_tokens — one entry per main-loop assistant message, for _prompt_context_correlation below
    tool_result_sizes = []  # list of dicts: tool_use_id, size, ts — matched to a tool name below
    message_count = 0
    all_ts = []
    # One assistant message spans MULTIPLE transcript lines — one per content block — and
    # every line repeats the same `usage` object. Summing per line therefore counts the
    # same tokens once per block: the factor is workload-dependent (measured between 1x
    # and 14x on real sessions) so there is no fixed correction, and the resulting figures
    # are plausible but wrong — large enough to imply more output tokens than the window
    # physically contains. Deduplicate on `message.id`, which is stable across the lines
    # of one message.
    counted_message_ids = set()
    usage_lines_seen = 0
    usage_lines_counted = 0

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

            usage = message.get("usage") or {}
            message_id = message.get("id")
            if usage:
                usage_lines_seen += 1
            # Fall back to the event uuid when `id` is absent so a message without one is
            # still counted exactly once rather than dropped.
            dedupe_key = message_id or ("uuid:" + str(event.get("uuid")))
            if dedupe_key not in counted_message_ids:
                counted_message_ids.add(dedupe_key)
                message_count += 1
                if usage:
                    usage_lines_counted += 1
                input_tokens = usage.get("input_tokens", 0) or 0
                usage_totals["input_tokens"] += input_tokens
                usage_totals["output_tokens"] += usage.get("output_tokens", 0) or 0
                cache_read = usage.get("cache_read_input_tokens", 0) or 0
                usage_totals["cache_read_input_tokens"] += cache_read
                cache_creation = usage.get("cache_creation_input_tokens", 0) or 0
                usage_totals["cache_creation_input_tokens"] += cache_creation
                if cache_read:
                    per_message_cache_read.append(cache_read)
                if usage:
                    per_message_context.append({"ts": ts, "context_tokens": input_tokens + cache_read + cache_creation})
            tool_calls.extend(calls_for_this_event)

        elif etype == "user" and not is_sidechain:
            text = _extract_user_text(message.get("content"))
            if text and not _is_synthetic_user_text(text):
                # chars/4 matches the estimation convention used elsewhere in this
                # codebase's static-footprint tooling (no tokenizer dependency available).
                user_turns.append({"ts": ts, "text": text, "prompt_est_tokens": len(text) // 4})
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
    prompt_context_outliers = _prompt_context_correlation(user_turns, per_message_context)

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
        # How much a naive per-line sum would have overcounted. Report it so the dedupe is
        # visible rather than silent, and so a transcript-format change that breaks
        # `message.id` shows up as this dropping to 1.0.
        "usage_overcount_factor_avoided": (
            round(usage_lines_seen / usage_lines_counted, 2) if usage_lines_counted else None
        ),
        # Mean tokens transmitted per model call. This — not the totals — is what separates
        # an expensive session from a wasteful one: sessions doing identical work at the
        # same tool-calls-per-message ratio routinely differ many-fold here, and the whole
        # difference is context re-transmission.
        "context_depth_per_call": (
            round(
                (
                    usage_totals["input_tokens"]
                    + usage_totals["cache_read_input_tokens"]
                    + usage_totals["cache_creation_input_tokens"]
                )
                / message_count
            )
            if message_count
            else 0
        ),
        "tool_calls_per_message": round(len(tool_calls) / message_count, 3) if message_count else 0,
        # Prefix churn: cache writes per cache read. Rising churn means the cached prefix
        # keeps being invalidated instead of reused.
        "cache_churn_ratio": (
            round(usage_totals["cache_creation_input_tokens"] / usage_totals["cache_read_input_tokens"], 5)
            if usage_totals["cache_read_input_tokens"]
            else None
        ),
        "tool_histogram": dict(tool_histogram.most_common()),
        "skills_invoked": sorted({(c["input"] or {}).get("skill") for c in skill_calls if c.get("input")}),
        "duplicate_calls": duplicate_calls,
        "reedit_reads": reedit_reads,
        "correction_points": corrections,
        "context_multiplication_signal": context_multiplication_signal,
        "largest_tool_results": largest_tool_results,
        "prompt_context_outliers": prompt_context_outliers,
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

# Defaults for _prompt_context_correlation, matched to the cost-audit skill's
# Langfuse-side equivalent so a session flagged there and drilled into here uses the
# same bar: a short prompt (<=300 est. tokens, ~1200 chars) answered by a call whose
# total context (fresh input + cache read + cache creation) is both large in absolute
# terms (>=20000 tokens) and disproportionate relative to the prompt (>=5x) means the
# turn is paying for context the user's own message didn't ask for.
PROMPT_CONTEXT_MISMATCH_FACTOR = 5.0
PROMPT_CONTEXT_MISMATCH_MIN_CONTEXT_TOKENS = 20000
PROMPT_CONTEXT_MISMATCH_MIN_PROMPT_TOKENS = 300


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


def _prompt_context_correlation(
    user_turns,
    per_message_context,
    factor=PROMPT_CONTEXT_MISMATCH_FACTOR,
    min_context_tokens=PROMPT_CONTEXT_MISMATCH_MIN_CONTEXT_TOKENS,
    min_prompt_tokens=PROMPT_CONTEXT_MISMATCH_MIN_PROMPT_TOKENS,
):
    """Flag user turns whose own prompt was small but whose answering assistant
    call(s) carried disproportionate context. `turn_context_tokens` sums
    `per_message_context` entries timestamped between this turn and the next (or end
    of transcript) — the same fresh-input + cache-read + cache-creation quantity
    `context_depth_per_call` uses, just scoped to one turn instead of averaged across
    the whole session. This is the transcript-side counterpart to `/cost-audit`'s
    per-trace context-vs-prompt check; a turn flagged here is direct evidence for the
    "Oversized skill footprint" / "Inline exploration that should be delegated"
    structural findings, pinned to the exact prompt that triggered the cost.
    """
    findings = []
    for idx, turn in enumerate(user_turns):
        turn_ts = turn["ts"]
        next_ts = user_turns[idx + 1]["ts"] if idx + 1 < len(user_turns) else None
        turn_context_tokens = sum(
            m["context_tokens"]
            for m in per_message_context
            if m["ts"] and turn_ts and m["ts"] >= turn_ts and (next_ts is None or m["ts"] < next_ts)
        )
        prompt_est_tokens = turn["prompt_est_tokens"]
        ratio = turn_context_tokens / max(prompt_est_tokens, 1)
        if (
            prompt_est_tokens <= min_prompt_tokens
            and turn_context_tokens >= min_context_tokens
            and ratio >= factor
        ):
            findings.append(
                {
                    "turn_index": idx,
                    "ts": turn_ts,
                    "prompt_chars": len(turn["text"]),
                    "prompt_est_tokens": prompt_est_tokens,
                    "turn_context_tokens": turn_context_tokens,
                    "ratio": round(ratio, 2),
                    "prompt_excerpt": turn["text"][:80],
                }
            )
    return findings


# How far back a Skill invocation looks for the user turn that prompted it. Reuses
# the same threshold `analyze()` already uses to decide whether two events belong to
# the same active stretch of work, rather than inventing a second window.
SKILL_TRIGGER_LOOKBACK_SECONDS = ACTIVE_GAP_THRESHOLD_SECONDS

# First path segment of a skill invocation's `skill` field is a plugin scope prefix
# (e.g. "ai-assistant-starter:review" vs. bare "review") — same skill, different
# install path. Trigger classification should treat them as one skill.
def _base_skill_name(name):
    return name.split(":")[-1] if name else name


def _extract_slash_command(text):
    """A user typing `/name` is rendered in the transcript as a `<command-name>`
    wrapper (e.g. `<command-name>/pr</command-name>`), not as literal `/pr` text —
    `_is_synthetic_user_text` correctly treats that wrapper as non-prose for the
    corrections check, but for trigger classification it IS the signal: it's the
    one case that unambiguously proves `explicit_slash`. Returns the bare command
    name (no leading slash, no plugin-scope prefix) or None if `text` isn't one.
    """
    import re

    m = re.search(r"<command-name>/?([a-zA-Z0-9_.\-]+)</command-name>", text)
    if not m:
        return None
    return _base_skill_name(m.group(1))


# A Skill invocation's own rendered body comes back on the very next transcript
# line as a "user"-role event with a plain `type: "text"` content block (not a
# `tool_result` wrapper, and not one of SYNTHETIC_USER_MARKERS's tagged forms) —
# confirmed by inspecting a real transcript line, where the "user" text was
# verbatim "Base directory for this skill: .../commit\n\n# Commit\n\n...". Every
# skill body starts with this exact line, so it's a reliable, cheap filter.
# Left un-generalized into `_is_synthetic_user_text` itself since that function's
# existing callers (corrections, in `analyze()`) are out of scope for this change.
SKILL_BODY_MARKER = "Base directory for this skill:"


def _gather_trigger_audit_turns(path):
    """Like `analyze()`'s user_turns, but kept separate: trigger classification
    needs `<command-name>` turns (proof of an explicit slash invocation) that
    `_is_synthetic_user_text` deliberately filters out for the corrections check.
    Other synthetic markers (task notifications, hook/local-command output, and a
    just-invoked skill's own body) are still dropped — none of those are something
    a user typed.
    """
    turns = []
    for event in load_events(path):
        if event.get("type") != "user" or event.get("isSidechain"):
            continue
        ts = event.get("timestamp")
        message = event.get("message") or {}
        raw_text = _extract_user_text(message.get("content"))
        if not raw_text or raw_text.startswith(SKILL_BODY_MARKER):
            continue
        command = _extract_slash_command(raw_text)
        if command:
            turns.append({"ts": ts, "text": "/" + command, "prompt_est_tokens": 1})
        elif not _is_synthetic_user_text(raw_text):
            turns.append({"ts": ts, "text": raw_text, "prompt_est_tokens": len(raw_text) // 4})
    return turns


def _classify_skill_invocations(user_turns, tool_calls, skill_triggers, session_id=None):
    """Classify each `Skill` tool_use event by how the invocation was likely
    prompted: did the user type a slash command for this exact skill
    (`explicit_slash`), does their preceding text contain one of the skill's own
    `triggers:` phrases without a leading slash (`prose_triggered`), does their text
    start with a slash naming a *different* skill than the one actually invoked
    (`ambiguous`, e.g. the model reinterpreted `/plan` as `/adr`), or is there no
    usable preceding user turn within the active-gap window at all
    (`inconclusive`)? One record per Skill invocation, in transcript order.
    """
    findings = []
    for call in tool_calls:
        if call.get("name") != "Skill":
            continue
        skill = (call.get("input") or {}).get("skill")
        if not skill:
            continue
        base = _base_skill_name(skill)
        call_ts = call.get("ts")

        preceding = None
        if call_ts:
            for turn in reversed(user_turns):
                if turn["ts"] and turn["ts"] <= call_ts:
                    gap = _seconds_between(turn["ts"], call_ts)
                    if gap is not None and 0 <= gap <= SKILL_TRIGGER_LOOKBACK_SECONDS:
                        preceding = turn
                    break

        record = {
            "skill": base,
            "session_id": session_id,
            "ts": call_ts,
            "mechanism": "inconclusive",
            "matched_phrase": None,
            "user_text_excerpt": None,
        }

        if preceding is None:
            findings.append(record)
            continue

        text = preceding["text"]
        record["user_text_excerpt"] = text[:120]
        stripped = text.lstrip()

        if stripped.startswith("/"):
            # e.g. "/review foo" or "/plugin:review foo" -> "review"
            slash_token = stripped[1:].split()[0] if len(stripped) > 1 else ""
            slash_name = _base_skill_name(slash_token)
            if slash_name == base:
                record["mechanism"] = "explicit_slash"
            else:
                record["mechanism"] = "ambiguous"
        else:
            text_lower = text.lower()
            matched = next(
                (phrase for phrase in skill_triggers.get(base, []) if phrase.lower() in text_lower),
                None,
            )
            if matched:
                record["mechanism"] = "prose_triggered"
                record["matched_phrase"] = matched
            # else stays "inconclusive": a preceding turn exists but neither a
            # matching slash command nor a known trigger phrase explains the call.

        findings.append(record)

    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("transcript", help="Path to the session's .jsonl transcript file")
    parser.add_argument("--out", help="Write JSON report to this path instead of stdout")
    parser.add_argument(
        "--trigger-audit",
        metavar="TRIGGERS_JSON",
        help="Optional: path to a JSON file mapping skill name -> list of trigger phrases. "
        "When given, also classifies each Skill invocation in this transcript as "
        "explicit_slash/prose_triggered/ambiguous/inconclusive and adds a "
        "'skill_invocation_classification' key to the report. Standalone session-retro "
        "usage is unaffected when this flag is omitted.",
    )
    args = parser.parse_args()

    try:
        report = analyze(args.transcript)
    except FileNotFoundError:
        sys.exit(f"error: transcript not found: {args.transcript}")

    if args.trigger_audit:
        with open(args.trigger_audit) as f:
            skill_triggers = json.load(f)
        # Re-walk the transcript for tool_calls (analyze() only returns derived
        # aggregates, not the raw list) — cheap re-parse of a single file. user_turns
        # comes from the dedicated gatherer, not analyze()'s filtered list, because
        # that filter drops the `<command-name>` turns this classification needs.
        tool_calls = []
        for event in load_events(args.transcript):
            ts = event.get("timestamp")
            message = event.get("message") or {}
            if event.get("type") == "assistant" and not event.get("isSidechain"):
                for item in (message.get("content") or []):
                    if item.get("type") == "tool_use":
                        tool_calls.append({"name": item.get("name"), "input": item.get("input"), "ts": ts, "id": item.get("id")})
        user_turns = _gather_trigger_audit_turns(args.transcript)
        report["skill_invocation_classification"] = _classify_skill_invocations(
            user_turns, tool_calls, skill_triggers, session_id=args.transcript
        )

    output = json.dumps(report, indent=2)
    if args.out:
        with open(args.out, "w") as f:
            f.write(output)
        print(f"wrote {args.out}")
    else:
        print(output)


if __name__ == "__main__":
    main()
