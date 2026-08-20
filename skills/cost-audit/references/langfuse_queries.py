#!/usr/bin/env python3
"""
Langfuse cost-audit queries for the `/cost-audit` skill.

Stdlib-only (urllib + json) so it runs anywhere Python 3.8+ is available,
with no dependency install step.

Environment:
    LANGFUSE_PUBLIC_KEY   required
    LANGFUSE_SECRET_KEY   required
    LANGFUSE_BASE_URL     default: https://cloud.langfuse.com
    FROM                  ISO8601, default: 30 days before TO
    TO                    ISO8601, default: now

Usage:
    python3 langfuse_queries.py trace_outliers --factor 3.0
    python3 langfuse_queries.py cost_per_session
    python3 langfuse_queries.py duplicate_tool_calls
    python3 langfuse_queries.py tool_usage
    python3 langfuse_queries.py error_pct
    python3 langfuse_queries.py cache_read_pct
    python3 langfuse_queries.py drill --trace <id> --tool <name> --limit 5
    python3 langfuse_queries.py session_sequences --growth-factor 2.0
    python3 langfuse_queries.py classify
    python3 langfuse_queries.py all --out-dir ./cost_audit_out
"""

import argparse
import base64
import collections
import json
import os
import statistics
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

PAGE_LIMIT = 1000

# Some Claude Code OTel instrumentation emits generic TOOL-type spans
# ("claude_code.tool", "claude_code.tool.execution") that never populate
# `input` — every call collapses into one (traceId, name, null) group and
# drowns out the real per-tool spans ("Tool: Bash", "Tool: Read", ...) that
# carry actual arguments. Exclude them from duplicate-call detection so it
# reflects genuine repeated calls instead of one bucket per generic span.
NO_INPUT_TOOL_SPAN_NAMES = {"claude_code.tool", "claude_code.tool.execution"}


def _env(name, default=None, required=False):
    value = os.environ.get(name, default)
    if required and not value:
        sys.exit(f"error: {name} is required (env var not set)")
    return value


def _auth_header(public_key, secret_key):
    token = base64.b64encode(f"{public_key}:{secret_key}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def _get(base_url, path, params, headers):
    url = f"{base_url}{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"error: {e.code} {e.reason} fetching {path}: {e.read().decode()[:500]}")


def pull_observations(base_url, headers, fields, from_ts, to_ts, extra_filter=None):
    """Paginate through /api/public/v2/observations, yielding every observation dict."""
    cursor = None
    while True:
        params = {
            "fields": fields,
            "fromStartTime": from_ts,
            "toStartTime": to_ts,
            "limit": PAGE_LIMIT,
        }
        if cursor:
            params["cursor"] = cursor
        if extra_filter:
            params["filter"] = json.dumps(extra_filter)

        page = _get(base_url, "/api/public/v2/observations", params, headers)
        rows = page.get("data", [])
        for row in rows:
            yield row

        cursor = (page.get("meta") or {}).get("cursor") or None
        if not cursor or not rows:
            break


def cmd_cost_per_session(base_url, headers, from_ts, to_ts, **_):
    by_session = collections.defaultdict(lambda: {"cost": 0.0, "count": 0, "models": set()})
    for obs in pull_observations(base_url, headers, "basic,usage,model", from_ts, to_ts):
        sid = obs.get("sessionId") or "(no session)"
        entry = by_session[sid]
        entry["cost"] += obs.get("totalCost") or 0
        entry["count"] += 1
        entry["models"].add(obs.get("model"))

    result = sorted(
        (
            {
                "sessionId": sid,
                "total_cost": data["cost"],
                "observation_count": data["count"],
                "models": sorted(m for m in data["models"] if m),
            }
            for sid, data in by_session.items()
        ),
        key=lambda r: -r["total_cost"],
    )
    return result


OUTLIER_METRICS = ("cost", "tool_call_count", "input_tokens", "output_tokens")


def _flag_outlier_traces(traces, factor=3.0):
    """Tag each trace with the metrics on which it exceeds factor * median.

    A trace only needs to blow past the median on ONE metric to be worth a look —
    a trace with unremarkable cost but a huge tool_call_count (a stuck loop that
    hasn't run up much spend yet) is exactly the kind of offender a cost-sorted
    session list misses.

    Default factor is 3.0, not 2.0: measured against a real two-day window,
    factor=2.0 flagged 36 of 117 traces (31%) — not an outlier set, just "above
    average." 3.0 is still a starting point, not a tuned constant; adjust per
    instance if it over- or under-flags.
    """
    medians = {}
    for metric in OUTLIER_METRICS:
        values = sorted(t[metric] for t in traces if t[metric] > 0)
        medians[metric] = statistics.median(values) if values else 0

    for t in traces:
        reasons = []
        for metric in OUTLIER_METRICS:
            median = medians[metric]
            value = t[metric]
            if median > 0 and value > factor * median:
                reasons.append(
                    {"metric": metric, "value": value, "median": median, "ratio": round(value / median, 2)}
                )
        t["outlier_reasons"] = reasons
        # Excess absolute cost over the cost median — used as the ranking tiebreak so a
        # trace tripping several cheap metrics doesn't outrank one genuinely expensive trace.
        t["excess_cost"] = max(0.0, t["cost"] - medians.get("cost", 0))

    outliers = [t for t in traces if t["outlier_reasons"]]
    outliers.sort(
        key=lambda t: (-len(t["outlier_reasons"]), -max(r["ratio"] for r in t["outlier_reasons"]), -t["excess_cost"])
    )
    return outliers


def cmd_combined_metrics(base_url, headers, from_ts, to_ts, factor=3.0, cache_key="cache_read_input_tokens", **_):
    """Single pass computing trace_outliers + error_pct + cache_read_pct together.

    All three need the same unfiltered full-window scan (`basic` is a subset of
    `core,basic,usage,model`), so pulling them separately would triple the paginated
    /observations crawl for the same data. Used by `all`; the standalone
    single-metric commands remain available for one-off queries.
    """
    by_trace = collections.defaultdict(
        lambda: {"sessionId": None, "cost": 0.0, "count": 0, "tool_calls": 0, "input_tokens": 0,
                 "output_tokens": 0, "generation_count": 0, "cache_read_tokens": 0, "models": set()}
    )
    by_level = collections.Counter()
    total_input_tokens = 0
    cache_tokens = 0

    for obs in pull_observations(base_url, headers, "core,basic,usage,model", from_ts, to_ts):
        tid = obs.get("traceId") or "(no trace)"
        entry = by_trace[tid]
        entry["sessionId"] = entry["sessionId"] or obs.get("sessionId")
        entry["cost"] += obs.get("totalCost") or 0
        entry["count"] += 1
        if obs.get("type") == "TOOL" and obs.get("name") not in NO_INPUT_TOOL_SPAN_NAMES:
            entry["tool_calls"] += 1
        entry["models"].add(obs.get("model"))

        by_level[obs.get("level") or "UNKNOWN"] += 1

        details = obs.get("usageDetails") or {}
        entry["input_tokens"] += details.get("input", 0) or 0
        entry["output_tokens"] += details.get("output", 0) or 0
        total_input_tokens += details.get("input", 0) or 0
        cache_tokens += details.get(cache_key, 0) or 0
        if obs.get("type") == "GENERATION":
            # Every GENERATION span (one per LLM call, i.e. one agentic turn) re-pays
            # cache_read on the full accumulated context. generation_count is the turn
            # count; cache_read_tokens / generation_count is what that context costs per
            # turn — the multiplication factor a duplicate-call check can't see, because
            # each of these calls has a genuinely distinct tool_use, not a repeat.
            entry["generation_count"] += 1
            entry["cache_read_tokens"] += details.get(cache_key, 0) or 0

    traces = [
        {
            "traceId": tid,
            "sessionId": data["sessionId"],
            "cost": data["cost"],
            "observation_count": data["count"],
            "tool_call_count": data["tool_calls"],
            "input_tokens": data["input_tokens"],
            "output_tokens": data["output_tokens"],
            "generation_count": data["generation_count"],
            "cache_read_tokens": data["cache_read_tokens"],
            "avg_cache_read_per_generation": round(data["cache_read_tokens"] / data["generation_count"], 1)
            if data["generation_count"] else 0,
            "models": sorted(m for m in data["models"] if m),
        }
        for tid, data in by_trace.items()
    ]
    trace_outliers = _flag_outlier_traces(traces, factor=factor)

    total = sum(by_level.values())
    errors = by_level.get("ERROR", 0)
    error_pct = {
        "total_observations": total,
        "error_count": errors,
        "error_pct": (errors / total * 100) if total else 0,
        "by_level": dict(by_level),
    }

    denom = total_input_tokens + cache_tokens
    cache_read_pct = {
        "input_tokens": total_input_tokens,
        "cache_read_tokens": cache_tokens,
        "cache_read_pct": (cache_tokens / denom * 100) if denom else 0,
    }

    return {
        "trace_outliers": trace_outliers,
        "error_pct": error_pct,
        "cache_read_pct": cache_read_pct,
    }


def cmd_duplicate_tool_calls(base_url, headers, from_ts, to_ts, **_):
    """Group by traceId rather than sessionId — a trace is the natural boundary for a
    single loop/turn, so this stays precise even when one session spans many traces.
    """
    groups = collections.defaultdict(list)
    tool_filter = [{"type": "string", "column": "type", "operator": "=", "value": "TOOL"}]
    for obs in pull_observations(base_url, headers, "core,basic,io", from_ts, to_ts, tool_filter):
        name = obs.get("name")
        if name in NO_INPUT_TOOL_SPAN_NAMES:
            continue
        key = (obs.get("traceId"), name, json.dumps(obs.get("input"), sort_keys=True))
        groups[key].append({"id": obs.get("id"), "sessionId": obs.get("sessionId")})

    result = sorted(
        (
            {
                "traceId": tid,
                "sessionId": ids[0]["sessionId"] if ids else None,
                "tool": name,
                "repeat_count": len(ids),
                "observation_ids": [i["id"] for i in ids],
            }
            for (tid, name, _input), ids in groups.items()
            if len(ids) > 1
        ),
        key=lambda r: -r["repeat_count"],
    )
    return result


def cmd_tool_usage(base_url, headers, from_ts, to_ts, **_):
    """Histogram of tool invocations by `attributes.tool_name`, read off the
    `claude_code.tool` SPAN — Claude Code's own native OTel exporter (as
    opposed to the `LLM Call` / `Tool: X` observations emitted separately by
    the langfuse-observability plugin's hook, which is where real cost/token
    numbers live). The two exporters can both be active against the same
    Langfuse project (check `OTEL_EXPORTER_OTLP_ENDPOINT` in settings.json
    vs. the plugin's own config) — if so every tool call is traced twice,
    which is itself worth flagging, and it means `claude_code.tool`
    observations carry NO cost/usage data (`totalCost` is always 0 on this
    span in that case) — there is deliberately no cost/token column here;
    don't compute one from this span, it will silently read zero across the
    board. Use `trace_outliers`/`duplicate_tool_calls` (built from the
    cost-bearing spans) for cost impact; use this command only for raw
    invocation-frequency / churn profiling.

    Note: `Skill` is reported as one bucket — this API does not expose which
    skill name was dispatched. Cross-reference with local session transcripts
    (~/.claude/projects/*/*.jsonl) to break `Skill` down by name if that
    granularity is needed.
    """
    tool_filter = [{"type": "string", "column": "name", "operator": "=", "value": "claude_code.tool"}]
    by_tool = collections.defaultdict(lambda: {"count": 0, "duration_ms": 0, "traces": set()})
    for obs in pull_observations(base_url, headers, "basic,metadata", from_ts, to_ts, tool_filter):
        md = obs.get("metadata") or {}
        name = md.get("attributes.tool_name") or "(unknown)"
        entry = by_tool[name]
        entry["count"] += 1
        entry["duration_ms"] += md.get("attributes.duration_ms") or 0
        if obs.get("traceId"):
            entry["traces"].add(obs["traceId"])

    total_calls = sum(data["count"] for data in by_tool.values()) or 1
    result = sorted(
        (
            {
                "tool": name,
                "invocation_count": data["count"],
                "pct_of_calls": round(data["count"] / total_calls * 100, 1),
                "trace_count": len(data["traces"]),
                "avg_duration_ms": round(data["duration_ms"] / data["count"], 1) if data["count"] else 0,
            }
            for name, data in by_tool.items()
        ),
        key=lambda r: -r["invocation_count"],
    )
    return result


def cmd_error_pct(base_url, headers, from_ts, to_ts, **_):
    by_level = collections.Counter()
    for obs in pull_observations(base_url, headers, "basic", from_ts, to_ts):
        by_level[obs.get("level") or "UNKNOWN"] += 1

    total = sum(by_level.values())
    errors = by_level.get("ERROR", 0)
    return {
        "total_observations": total,
        "error_count": errors,
        "error_pct": (errors / total * 100) if total else 0,
        "by_level": dict(by_level),
    }


def cmd_cache_read_pct(base_url, headers, from_ts, to_ts, cache_key="cache_read_input_tokens", **_):
    input_tokens = 0
    cache_tokens = 0
    for obs in pull_observations(base_url, headers, "core,basic,usage", from_ts, to_ts):
        details = obs.get("usageDetails") or {}
        input_tokens += details.get("input", 0) or 0
        cache_tokens += details.get(cache_key, 0) or 0

    denom = input_tokens + cache_tokens
    return {
        "input_tokens": input_tokens,
        "cache_read_tokens": cache_tokens,
        "cache_read_pct": (cache_tokens / denom * 100) if denom else 0,
    }


def cmd_drill(base_url, headers, from_ts, to_ts, session, tool, limit, trace=None, **_):
    """Pull the actual input/output content for a trace (or session) + tool pair — root-cause step."""
    tool_filter = [{"type": "string", "column": "type", "operator": "=", "value": "TOOL"}]
    if trace:
        tool_filter.append({"type": "string", "column": "traceId", "operator": "=", "value": trace})
    if session:
        tool_filter.append({"type": "string", "column": "sessionId", "operator": "=", "value": session})
    if tool:
        # Per-tool observations are named "Tool: <name>" (e.g. "Tool: Read"), not the bare
        # tool name — auto-prefix so `--tool Read` matches instead of silently returning 0 rows.
        tool_name = tool if tool.startswith("Tool: ") or tool in NO_INPUT_TOOL_SPAN_NAMES else f"Tool: {tool}"
        tool_filter.append({"type": "string", "column": "name", "operator": "=", "value": tool_name})
    matches = []
    for obs in pull_observations(base_url, headers, "core,basic,io", from_ts, to_ts, tool_filter):
        if not tool and obs.get("name") in NO_INPUT_TOOL_SPAN_NAMES:
            continue
        matches.append(
            {
                "id": obs.get("id"),
                "name": obs.get("name"),
                "startTime": obs.get("startTime"),
                "level": obs.get("level"),
                "input": obs.get("input"),
                "output_preview": str(obs.get("output"))[:300],
            }
        )
        if len(matches) >= limit:
            break
    return matches


def cmd_trace_outliers(base_url, headers, from_ts, to_ts, factor=3.0, **_):
    return cmd_combined_metrics(base_url, headers, from_ts, to_ts, factor=factor)["trace_outliers"]


# Rough cost-tier ordering for escalation detection — only used to tell "moved to a
# pricier model after a failure" from "moved to a cheaper one." Not a pricing source.
MODEL_TIER = {"haiku": 0, "sonnet": 1, "opus": 2, "fable": 3}


def _model_tier(model_names):
    tiers = [MODEL_TIER[t] for name in model_names for t in MODEL_TIER if name and t in name.lower()]
    return max(tiers) if tiers else None


def cmd_session_sequences(base_url, headers, from_ts, to_ts, growth_factor=2.0, **_):
    """Group traces by session, ordered chronologically, and flag waste patterns that
    only show up when comparing across traces in the same session — invisible to
    trace_outliers/duplicate_tool_calls, which each treat a trace in isolation.

    Three cross-trace patterns are flagged directly (the agent still root-causes with
    `drill` before proposing a fix — this is Step 1 classification input, not a verdict):

    - cross_trace_duplicate: the same (tool, input) signature appears in 2+ traces
      within one session — a later trace re-did work an earlier trace in the same
      session already did (re-reading a file, re-running the same search).
    - context_growth: input_tokens jumps by more than `growth_factor`x from one trace
      to the next in the same session while tool_call_count does NOT grow proportionally
      — cost growth from accumulating context/history rather than new work.
    - escalation_after_failure: a trace with an ERROR-level observation is immediately
      followed (same session) by a trace using a higher-cost-tier model — a retry that
      escalated model tier instead of fixing the root cause.

    Ignored-correction patterns (a user correction in trace N not followed in trace N+M)
    are NOT computed here — Langfuse's OTel export doesn't reliably carry the user's verbatim
    wording across all span types. Flag a session as a candidate here (e.g. via
    cross_trace_duplicate on a "should have learned this" tool call) and confirm by reading
    the local transcript, same as the existing Skill-name-decomposition step.
    """
    by_trace = collections.defaultdict(
        lambda: {"sessionId": None, "cost": 0.0, "tool_calls": 0, "input_tokens": 0, "output_tokens": 0,
                 "start": None, "models": set(), "error_count": 0, "tool_inputs": set()}
    )
    for obs in pull_observations(base_url, headers, "core,basic,usage,model,io", from_ts, to_ts):
        tid = obs.get("traceId") or "(no trace)"
        entry = by_trace[tid]
        entry["sessionId"] = entry["sessionId"] or obs.get("sessionId")
        entry["cost"] += obs.get("totalCost") or 0
        st = obs.get("startTime")
        if st and (entry["start"] is None or st < entry["start"]):
            entry["start"] = st
        if obs.get("level") == "ERROR":
            entry["error_count"] += 1
        name = obs.get("name")
        if obs.get("type") == "TOOL" and name not in NO_INPUT_TOOL_SPAN_NAMES:
            entry["tool_calls"] += 1
            entry["tool_inputs"].add((name, json.dumps(obs.get("input"), sort_keys=True)))
        entry["models"].add(obs.get("model"))
        details = obs.get("usageDetails") or {}
        entry["input_tokens"] += details.get("input", 0) or 0
        entry["output_tokens"] += details.get("output", 0) or 0

    by_session = collections.defaultdict(list)
    for tid, data in by_trace.items():
        if not data["sessionId"] or not data["start"]:
            continue
        by_session[data["sessionId"]].append({
            "traceId": tid,
            "start": data["start"],
            "cost": data["cost"],
            "tool_call_count": data["tool_calls"],
            "input_tokens": data["input_tokens"],
            "output_tokens": data["output_tokens"],
            "error_count": data["error_count"],
            "models": sorted(m for m in data["models"] if m),
            "tool_inputs": data["tool_inputs"],
        })

    sessions_out = []
    for sid, traces in by_session.items():
        if len(traces) < 2:
            continue  # cross-trace patterns need at least 2 traces to compare
        traces.sort(key=lambda t: t["start"])

        cross_trace_duplicates = []
        seen_sig_traces = collections.defaultdict(set)
        for t in traces:
            for sig in t["tool_inputs"]:
                seen_sig_traces[sig].add(t["traceId"])
        for (tool, inp), trace_ids in seen_sig_traces.items():
            if len(trace_ids) > 1:
                cross_trace_duplicates.append(
                    {"tool": tool, "input": json.loads(inp) if inp != "null" else None,
                     "trace_ids": sorted(trace_ids), "trace_count": len(trace_ids)}
                )
        cross_trace_duplicates.sort(key=lambda d: -d["trace_count"])

        context_growth = []
        escalation_after_failure = []
        for prev, nxt in zip(traces, traces[1:]):
            if prev["input_tokens"] > 0:
                ratio = nxt["input_tokens"] / prev["input_tokens"]
                tool_ratio = (nxt["tool_call_count"] / prev["tool_call_count"]) if prev["tool_call_count"] > 0 else float("inf")
                if ratio > growth_factor and tool_ratio < ratio / 2:
                    context_growth.append({
                        "from_trace": prev["traceId"], "to_trace": nxt["traceId"],
                        "input_tokens_ratio": round(ratio, 2),
                        "tool_call_ratio": round(tool_ratio, 2) if tool_ratio != float("inf") else None,
                    })
            if prev["error_count"] > 0:
                prev_tier, next_tier = _model_tier(prev["models"]), _model_tier(nxt["models"])
                if prev_tier is not None and next_tier is not None and next_tier > prev_tier:
                    escalation_after_failure.append({
                        "from_trace": prev["traceId"], "to_trace": nxt["traceId"],
                        "from_models": prev["models"], "to_models": nxt["models"],
                        "prev_error_count": prev["error_count"],
                    })

        if not (cross_trace_duplicates or context_growth or escalation_after_failure):
            continue

        sessions_out.append({
            "sessionId": sid,
            "trace_count": len(traces),
            "total_cost": round(sum(t["cost"] for t in traces), 6),
            "trace_order": [t["traceId"] for t in traces],
            "cross_trace_duplicates": cross_trace_duplicates,
            "context_growth": context_growth,
            "escalation_after_failure": escalation_after_failure,
        })

    sessions_out.sort(key=lambda s: -s["total_cost"])
    return sessions_out


def _parse_ts(ts):
    if not ts:
        return None
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return None


def _file_path(input_obj):
    if isinstance(input_obj, dict):
        return input_obj.get("file_path") or input_obj.get("path")
    return None


BROWSER_TOOL_MARKERS = ("navigate", "console_messages", "close", "screenshot", "computer")
EDIT_TOOL_MARKERS = ("Edit", "Write", "NotebookEdit")
READ_TOOL_MARKERS = ("Read",)
DISPATCH_TOOL_MARKERS = ("Agent", "Workflow", "Skill")


def _errors_near(timestamps, errors, window_seconds):
    """True if any repeat in the group has an ERROR-level observation in the
    `window_seconds` immediately preceding it — the signature of a retry loop
    rather than a healthy repeated call."""
    for ts in timestamps[1:]:
        for err_ts in errors:
            if 0 <= (ts - err_ts).total_seconds() <= window_seconds:
                return True
    return False


def _classify_group(name, input_json, timestamps, gaps, errors, all_events,
                     stuck_poll_repeat_threshold, stuck_poll_regularity_cv,
                     error_window_seconds, reverify_window_seconds):
    """Assign one pattern label to a (tool, input) repeat group within a trace,
    from timing/error/sequence signatures alone — no LLM judgment involved.

    Order matters: retry-after-error is checked first since an error can occur
    alongside any other signature (a browser retry or a read-after-edit can
    both also be error-driven, and the error is the more specific cause). The
    final `redundant-context-refetch` bucket is an explicit "none of the
    deterministic signatures matched" catch-all — it still needs a human/LLM
    to read `drill` output or the local transcript before it gets a sharper
    label; it is not a confident classification on its own.
    """
    repeat_count = len(timestamps)
    mean_gap = sum(gaps) / len(gaps) if gaps else 0
    cv = (statistics.pstdev(gaps) / mean_gap) if mean_gap and len(gaps) > 1 else None

    if _errors_near(timestamps, errors, error_window_seconds):
        return "retry-after-error", {
            "reason": f"{repeat_count} repeats with an ERROR observation within "
                      f"{error_window_seconds}s before a repeat",
        }

    if any(marker in name for marker in READ_TOOL_MARKERS):
        input_obj = json.loads(input_json) if input_json != "null" else None
        path = _file_path(input_obj)
        if path:
            for e in all_events:
                if any(m in e["name"] for m in EDIT_TOOL_MARKERS) and _file_path(e["input"]) == path:
                    for ts in timestamps:
                        if 0 <= (ts - e["ts"]).total_seconds() <= reverify_window_seconds:
                            return "re-verification-read", {
                                "reason": f"Read on {path} within {reverify_window_seconds}s "
                                          f"after {e['name']} on the same file",
                            }

    if any(marker in name for marker in BROWSER_TOOL_MARKERS):
        return "browser-automation-retry", {
            "reason": f"{repeat_count} repeats of a browser-automation call ({name}) with identical input",
        }

    if any(marker in name for marker in DISPATCH_TOOL_MARKERS):
        return "skill-or-subagent-over-dispatch", {
            "reason": f"{repeat_count} repeats of the same {name} dispatch with identical input",
        }

    if repeat_count >= stuck_poll_repeat_threshold and cv is not None and cv < stuck_poll_regularity_cv:
        return "stuck-poll-or-runaway-loop", {
            "reason": f"{repeat_count} repeats at regular ~{round(mean_gap, 1)}s intervals "
                      f"(coefficient of variation={round(cv, 2)}), no adjacent errors",
        }

    return "redundant-context-refetch", {
        "reason": f"{repeat_count} repeats of the same call within one trace; no error/edit-adjacency/"
                  f"browser-sequence/regular-interval signature matched — confirm with `drill` or the "
                  f"local transcript before assigning a sharper label",
        "needs_manual_confirmation": True,
    }


def cmd_classify(base_url, headers, from_ts, to_ts, stuck_poll_repeat_threshold=10,
                  stuck_poll_regularity_cv=0.5, error_window_seconds=30,
                  reverify_window_seconds=120, **_):
    """Deterministically assign a pattern label to every within-trace duplicate-call
    group, from call timing, ERROR-level adjacency, and tool-name sequences.

    This replaces manual `drill`-and-eyeball classification for the common patterns
    (retry-after-error, re-verification-read, browser-automation-retry,
    skill/subagent-over-dispatch, stuck-poll-or-runaway-loop). It does NOT compute
    the cross-trace patterns (cross_trace_duplicates, context_growth,
    escalation_after_failure) — those already exist as structured fields in
    `session_sequences`, so classifying them again here would be redundant, not
    complementary. It also does NOT compute 'ignored correction' — that pattern is
    only confirmable from the user's verbatim wording in the local transcript,
    which Langfuse's OTel export doesn't reliably carry.

    A finding with `needs_manual_confirmation: true` (the redundant-context-refetch
    catch-all) is the one case where a human/LLM still has to read `drill` output or
    the transcript before the pattern label can be trusted — everything else here is
    a mechanical read of the same fields `duplicate_tool_calls` already surfaces,
    just with the labeling done in code instead of in the agent's head.
    """
    by_trace = collections.defaultdict(lambda: {"sessionId": None, "tool_events": [], "error_events": []})
    for obs in pull_observations(base_url, headers, "core,basic,io", from_ts, to_ts):
        tid = obs.get("traceId") or "(no trace)"
        entry = by_trace[tid]
        entry["sessionId"] = entry["sessionId"] or obs.get("sessionId")
        ts = _parse_ts(obs.get("startTime"))
        if obs.get("level") == "ERROR" and ts:
            entry["error_events"].append(ts)
        if obs.get("type") == "TOOL" and obs.get("name") not in NO_INPUT_TOOL_SPAN_NAMES and ts:
            entry["tool_events"].append({"name": obs.get("name"), "input": obs.get("input"), "ts": ts})

    findings = []
    for tid, data in by_trace.items():
        events = sorted(data["tool_events"], key=lambda e: e["ts"])
        errors = sorted(data["error_events"])

        groups = collections.defaultdict(list)
        for e in events:
            key = (e["name"], json.dumps(e["input"], sort_keys=True))
            groups[key].append(e["ts"])

        for (name, input_json), timestamps in groups.items():
            if len(timestamps) < 2:
                continue
            timestamps = sorted(timestamps)
            gaps = [(b - a).total_seconds() for a, b in zip(timestamps, timestamps[1:])]
            pattern, evidence = _classify_group(
                name, input_json, timestamps, gaps, errors, events,
                stuck_poll_repeat_threshold, stuck_poll_regularity_cv,
                error_window_seconds, reverify_window_seconds,
            )
            findings.append({
                "traceId": tid,
                "sessionId": data["sessionId"],
                "tool": name,
                "input": json.loads(input_json) if input_json != "null" else None,
                "repeat_count": len(timestamps),
                "first_seen": timestamps[0].isoformat(),
                "last_seen": timestamps[-1].isoformat(),
                "pattern": pattern,
                "evidence": evidence,
            })

    findings.sort(key=lambda f: -f["repeat_count"])
    return findings


def _rank_findings(classified, trace_outliers, session_sequences):
    """Merge classified within-trace findings with trace-level outlier data and
    session-level cross-trace flags into one sorted list — this mechanizes the
    Step 1b shortlisting criteria (outlier-metric count, then ratio, then excess
    cost, then repeat count) that used to be applied by eye.
    """
    outlier_by_trace = {t["traceId"]: t for t in trace_outliers}
    session_flagged = {s["sessionId"] for s in session_sequences}

    ranked = []
    for f in classified:
        outlier = outlier_by_trace.get(f["traceId"])
        outlier_reasons = outlier["outlier_reasons"] if outlier else []
        ranked.append({
            **f,
            "is_trace_outlier": bool(outlier_reasons),
            "outlier_reasons": outlier_reasons,
            "outlier_metric_count": len(outlier_reasons),
            "outlier_max_ratio": max((r["ratio"] for r in outlier_reasons), default=0),
            "excess_cost": outlier["excess_cost"] if outlier else 0,
            "session_flagged_cross_trace": f["sessionId"] in session_flagged,
        })

    ranked.sort(key=lambda r: (
        -r["outlier_metric_count"],
        -r["outlier_max_ratio"],
        -r["excess_cost"],
        -r["repeat_count"],
    ))
    return ranked


COMMANDS = {
    "cost_per_session": cmd_cost_per_session,
    "trace_outliers": cmd_trace_outliers,
    "duplicate_tool_calls": cmd_duplicate_tool_calls,
    "tool_usage": cmd_tool_usage,
    "error_pct": cmd_error_pct,
    "cache_read_pct": cmd_cache_read_pct,
    "drill": cmd_drill,
    "session_sequences": cmd_session_sequences,
    "classify": cmd_classify,
}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=list(COMMANDS) + ["all"])
    parser.add_argument("--session", help="sessionId, for `drill` (alternative to --trace)")
    parser.add_argument("--trace", help="traceId, for `drill` (preferred — a trace is one turn/loop)")
    parser.add_argument("--tool", help="tool/observation name filter, used by `drill`")
    parser.add_argument("--limit", type=int, default=5, help="max rows for `drill` (default 5)")
    parser.add_argument(
        "--factor", type=float, default=3.0, help="outlier threshold as a multiple of the median, for `trace_outliers`"
    )
    parser.add_argument(
        "--growth-factor", type=float, default=2.0,
        help="input_tokens jump threshold between consecutive traces in a session, for `session_sequences`"
    )
    parser.add_argument(
        "--stuck-poll-repeat-threshold", type=int, default=10,
        help="min repeat count to consider a group for stuck-poll-or-runaway-loop, for `classify`"
    )
    parser.add_argument(
        "--stuck-poll-regularity-cv", type=float, default=0.5,
        help="max coefficient of variation of inter-call gaps to count as 'regular interval', for `classify`"
    )
    parser.add_argument(
        "--error-window-seconds", type=float, default=30,
        help="seconds before a repeat to look for an ERROR observation, for `classify`"
    )
    parser.add_argument(
        "--reverify-window-seconds", type=float, default=120,
        help="seconds after an Edit/Write to look for a Read on the same file, for `classify`"
    )
    parser.add_argument("--out-dir", default="./cost_audit_out", help="output dir for `all`")
    args = parser.parse_args()

    base_url = _env("LANGFUSE_BASE_URL", default="https://cloud.langfuse.com")
    public_key = _env("LANGFUSE_PUBLIC_KEY", required=True)
    secret_key = _env("LANGFUSE_SECRET_KEY", required=True)
    headers = _auth_header(public_key, secret_key)

    to_dt = datetime.now(timezone.utc)
    from_dt = to_dt - timedelta(days=30)
    to_ts = _env("TO", default=to_dt.isoformat())
    from_ts = _env("FROM", default=from_dt.isoformat())

    if args.command == "drill" and not (args.session or args.trace):
        sys.exit("error: --trace or --session is required for `drill`")

    if args.command == "all":
        os.makedirs(args.out_dir, exist_ok=True)

        combined = cmd_combined_metrics(base_url, headers, from_ts, to_ts, factor=args.factor)
        for name in ("trace_outliers", "error_pct", "cache_read_pct"):
            out_path = os.path.join(args.out_dir, f"{name}.json")
            with open(out_path, "w") as f:
                json.dump(combined[name], f, indent=2)
            print(f"wrote {out_path}")

        result = cmd_duplicate_tool_calls(base_url, headers, from_ts, to_ts)
        out_path = os.path.join(args.out_dir, "duplicate_tool_calls.json")
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"wrote {out_path}")

        result = cmd_tool_usage(base_url, headers, from_ts, to_ts)
        out_path = os.path.join(args.out_dir, "tool_usage.json")
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"wrote {out_path}")

        session_sequences = cmd_session_sequences(base_url, headers, from_ts, to_ts, growth_factor=args.growth_factor)
        out_path = os.path.join(args.out_dir, "session_sequences.json")
        with open(out_path, "w") as f:
            json.dump(session_sequences, f, indent=2)
        print(f"wrote {out_path}")

        classified = cmd_classify(
            base_url, headers, from_ts, to_ts,
            stuck_poll_repeat_threshold=args.stuck_poll_repeat_threshold,
            stuck_poll_regularity_cv=args.stuck_poll_regularity_cv,
            error_window_seconds=args.error_window_seconds,
            reverify_window_seconds=args.reverify_window_seconds,
        )
        out_path = os.path.join(args.out_dir, "classified_findings.json")
        with open(out_path, "w") as f:
            json.dump(classified, f, indent=2)
        print(f"wrote {out_path}")

        ranked = _rank_findings(classified, combined["trace_outliers"], session_sequences)
        out_path = os.path.join(args.out_dir, "ranked_findings.json")
        with open(out_path, "w") as f:
            json.dump(ranked, f, indent=2)
        print(f"wrote {out_path}")
        return

    fn = COMMANDS[args.command]
    result = fn(
        base_url,
        headers,
        from_ts,
        to_ts,
        session=args.session,
        trace=args.trace,
        tool=args.tool,
        limit=args.limit,
        factor=args.factor,
        growth_factor=args.growth_factor,
        stuck_poll_repeat_threshold=args.stuck_poll_repeat_threshold,
        stuck_poll_regularity_cv=args.stuck_poll_regularity_cv,
        error_window_seconds=args.error_window_seconds,
        reverify_window_seconds=args.reverify_window_seconds,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
