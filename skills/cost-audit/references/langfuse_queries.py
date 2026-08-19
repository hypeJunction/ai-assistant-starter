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
                 "output_tokens": 0, "models": set()}
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

    traces = [
        {
            "traceId": tid,
            "sessionId": data["sessionId"],
            "cost": data["cost"],
            "observation_count": data["count"],
            "tool_call_count": data["tool_calls"],
            "input_tokens": data["input_tokens"],
            "output_tokens": data["output_tokens"],
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


COMMANDS = {
    "cost_per_session": cmd_cost_per_session,
    "trace_outliers": cmd_trace_outliers,
    "duplicate_tool_calls": cmd_duplicate_tool_calls,
    "tool_usage": cmd_tool_usage,
    "error_pct": cmd_error_pct,
    "cache_read_pct": cmd_cache_read_pct,
    "drill": cmd_drill,
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
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
