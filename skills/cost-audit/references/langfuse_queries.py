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
    python3 langfuse_queries.py token_economics     # supersedes cache_read_pct
    python3 langfuse_queries.py payload_profile     # tool-result sizes, image vs text
    python3 langfuse_queries.py underuse_profile    # cheaper paths NOT taken
    python3 langfuse_queries.py reconcile           # recorded cost vs tokens x rates
    python3 langfuse_queries.py drill --trace <id> --tool <name> --limit 5
    python3 langfuse_queries.py session_sequences --growth-factor 2.0
    python3 langfuse_queries.py classify
    python3 langfuse_queries.py all --out-dir ./cost_audit_out

Reading the output: start with `summary.json`. Cost concentrates in context
re-transmission (cache read + cache write), which is typically ~85-90% of spend, so
`context_depth_per_call` and `recoverable_cost` in `trace_outliers.json` are the fields
that decide where to act. Totals (cost, token counts, tool-call counts) measure how BIG a
trace was; depth measures how WASTEFUL it was, and the two routinely disagree.
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

# Langfuse `usageDetails` keys for the four billed token classes. They are billed at
# very different rates, so an audit that sums them together cannot tell an expensive
# trace that *generated* a lot from one that merely *re-read* a lot.
USAGE_FRESH_INPUT = "input"
USAGE_OUTPUT = "output"
USAGE_CACHE_READ = "cache_read_input_tokens"
USAGE_CACHE_WRITE = "cache_creation_input_tokens"

# Every Anthropic rate is a fixed multiple of that model's base input rate:
#   fresh input 1x | 5-min cache write 1.25x | 1-hour cache write 2x
#   cache read 0.1x | output 5x
# Expressing cost in "base-input-equivalents" (BIE) therefore gives token-class cost
# SHARES that are identical for every model and survive any price change — which
# matters because `model` is null on a lot of instrumentation. Absolute dollars still
# need RATES below; shares do not.
BIE_MULTIPLIER = {
    USAGE_FRESH_INPUT: 1.0,
    USAGE_CACHE_WRITE: 1.25,  # assumes the 5-minute TTL; use 2.0 for the 1-hour TTL
    USAGE_CACHE_READ: 0.1,
    USAGE_OUTPUT: 5.0,
}

# Published USD per million tokens (base input, output). Used only by `reconcile`, to
# assert that Langfuse's recorded `totalCost` actually matches the token counts.
# NOTE: Opus 4.8 / Opus 5 are $5/$25 — NOT the older $15/$75. Assuming the old rates
# inflates an estimate 3x. There is also no long-context premium: the 1M window is
# served at standard rates.
RATES = {
    "claude-opus-5": (5.0, 25.0),
    "claude-opus-4-8": (5.0, 25.0),
    "claude-sonnet-5": (3.0, 15.0),
    "claude-sonnet-4-5": (3.0, 15.0),
    "claude-haiku-4-5": (1.0, 5.0),
}

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg", ".pdf")

# A tool result at or above this size dominates the context it lands in and is re-sent on
# every later call in the session. 100KB is roughly 25k tokens of text.
OVERSIZED_PAYLOAD_BYTES = 100_000

# Bash invocations that are really searches/dumps. These return UNBOUNDED output
# straight into context, where it is then re-sent on every later call in the session.
# Grep/Glob return bounded results for the same questions, so a high ratio here with
# zero Grep/Glob use is a context-depth driver, not a style preference.
BASH_SEARCH_PATTERNS = ("grep", "rg ", "find ", "cat ", "ls -", "head -", "tail -", "awk ", "sed -n")

# Tools that keep a large payload OUT of the parent context by design.
DELEGATION_TOOLS = {"Agent", "Task", "Workflow"}
BOUNDED_SEARCH_TOOLS = {"Grep", "Glob"}


def _usage_of(obs):
    """Return the four billed token classes for one observation, defaulting to 0.

    `usageDetails.input` is the FRESH (uncached) input only — cache reads and cache
    writes are reported in their own keys. Summing `input` alone therefore misses
    >98% of the input tokens actually transmitted.
    """
    details = obs.get("usageDetails") or {}
    return {
        key: details.get(key, 0) or 0
        for key in (USAGE_FRESH_INPUT, USAGE_OUTPUT, USAGE_CACHE_READ, USAGE_CACHE_WRITE)
    }


def _context_tokens(usage):
    """Tokens transmitted TO the model on a call: fresh input + cache read + cache write.

    This — not `input` — is the quantity that grows as a session accumulates context and
    is re-sent on every subsequent call.
    """
    return usage[USAGE_FRESH_INPUT] + usage[USAGE_CACHE_READ] + usage[USAGE_CACHE_WRITE]


def _cost_shares_bie(totals, cache_write_multiplier=None):
    """Rate-invariant cost share per token class, in base-input-equivalents.

    Answers the question that decides where optimisation effort goes: is this window
    expensive because of context re-transmission, or because of generated output?
    """
    multipliers = dict(BIE_MULTIPLIER)
    if cache_write_multiplier is not None:
        multipliers[USAGE_CACHE_WRITE] = cache_write_multiplier
    weighted = {key: totals.get(key, 0) * mult for key, mult in multipliers.items()}
    total = sum(weighted.values())
    if not total:
        return {"note": "no usage data in window", "shares_pct": {}}
    shares = {key: round(value / total * 100, 3) for key, value in weighted.items()}
    return {
        "cache_write_multiplier": multipliers[USAGE_CACHE_WRITE],
        "shares_pct": shares,
        "context_retransmission_pct": round(shares[USAGE_CACHE_READ] + shares[USAGE_CACHE_WRITE], 2),
        "output_pct": shares[USAGE_OUTPUT],
        "fresh_input_pct": shares[USAGE_FRESH_INPUT],
    }


def _classify_payload(name, input_json, output):
    """Label a tool result image / text / other.

    Images cannot be grepped or paginated — `Read` is the only way to view one — so an
    image-dominated payload problem needs fewer/smaller screenshots, whereas a
    text-dominated one needs `limit`/`offset` or a bounded search. Getting this
    backwards produces the wrong recommendation, so classify before concluding.
    """
    blob = json.dumps(input_json) if input_json is not None else ""
    lowered = blob.lower()
    if any(ext in lowered for ext in IMAGE_EXTENSIONS):
        return "image"
    text = output if isinstance(output, str) else json.dumps(output) if output is not None else ""
    if "data:image" in text[:2000] or '"type": "image"' in text[:2000] or '"type":"image"' in text[:2000]:
        return "image"
    return "text" if text else "other"


def _payload_bytes(value):
    if value is None:
        return 0
    return len(value if isinstance(value, str) else json.dumps(value))


def _normalize_input(name, input_json):
    """Drop arguments that do not change WHAT was fetched, so near-duplicates group.

    Exact-match dedup misses the common real cases: the same file re-read at a
    different offset, or the same search re-run with a tweaked limit. Those are the
    same retrieval and should be counted as repeats.
    """
    if not isinstance(input_json, dict):
        return json.dumps(input_json, sort_keys=True)
    ignored = {"offset", "limit", "head_limit", "timeout", "description", "run_in_background"}
    reduced = {k: v for k, v in input_json.items() if k not in ignored}
    return json.dumps(reduced, sort_keys=True)


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


# `cost`, `tool_call_count`, `input_tokens` and `output_tokens` are all TOTALS, so they
# scale with how long a trace ran: a long legitimate trace trips them and a short
# pathological one does not. They measure size, not waste.
#
# `context_depth_per_call` is the normalised metric that separates the two — mean tokens
# transmitted per model call. Two traces doing identical work at identical tool/turn
# ratios can differ 19x on this one, and that difference is pure re-transmission.
OUTLIER_METRICS = (
    "cost",
    "tool_call_count",
    "input_tokens",
    "output_tokens",
    "context_depth_per_call",
)

# The metric whose excess is actually recoverable, as opposed to merely large.
DEPTH_METRIC = "context_depth_per_call"


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

    Ranking is by `recoverable_cost`, not by ratio-to-median. A median-multiple rule on
    a heavy-tailed cost distribution flags the tail by construction and says nothing
    about how much money is actually on the table; `recoverable_cost` answers the
    question the audit exists to answer.
    """
    medians = {}
    for metric in OUTLIER_METRICS:
        values = sorted(t[metric] for t in traces if t[metric] > 0)
        medians[metric] = statistics.median(values) if values else 0

    median_depth = medians.get(DEPTH_METRIC, 0)
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
        # Excess absolute cost over the cost median — kept as a secondary tiebreak.
        t["excess_cost"] = max(0.0, t["cost"] - medians.get("cost", 0))
        # Counterfactual: what this trace would have cost had it run at the window's
        # median context depth, doing the same number of calls. The gap is the part
        # attributable to carrying more context per call, which is the part a context
        # ceiling / delegation / bounded search can actually recover.
        depth = t.get(DEPTH_METRIC) or 0
        if median_depth > 0 and depth > median_depth and t["cost"] > 0:
            t["cost_at_median_depth"] = round(t["cost"] * median_depth / depth, 4)
            t["recoverable_cost"] = round(t["cost"] - t["cost_at_median_depth"], 4)
            t["depth_ratio"] = round(depth / median_depth, 2)
        else:
            t["cost_at_median_depth"] = round(t["cost"], 4)
            t["recoverable_cost"] = 0.0
            t["depth_ratio"] = round(depth / median_depth, 2) if median_depth else None

    outliers = [t for t in traces if t["outlier_reasons"]]
    outliers.sort(key=lambda t: (-t["recoverable_cost"], -t["excess_cost"], -len(t["outlier_reasons"])))
    return outliers


def cmd_combined_metrics(base_url, headers, from_ts, to_ts, factor=3.0, cache_key="cache_read_input_tokens", **_):
    """Single pass computing trace_outliers + error_pct + cache_read_pct together.

    All three need the same unfiltered full-window scan (`basic` is a subset of
    `core,basic,usage,model`), so pulling them separately would triple the paginated
    /observations crawl for the same data. Used by `all`; the standalone
    single-metric commands remain available for one-off queries.
    """
    by_trace = collections.defaultdict(
        lambda: {"sessionId": None, "cost": 0.0, "count": 0, "tool_calls": 0, "generations": 0,
                 "context_tokens": 0, "models": set(),
                 "usage": collections.Counter()}
    )
    by_level = collections.Counter()
    window_usage = collections.Counter()
    span_names = collections.Counter()
    cost_bearing_observations = 0

    for obs in pull_observations(base_url, headers, "core,basic,usage,model", from_ts, to_ts):
        tid = obs.get("traceId") or "(no trace)"
        entry = by_trace[tid]
        entry["sessionId"] = entry["sessionId"] or obs.get("sessionId")
        entry["cost"] += obs.get("totalCost") or 0
        entry["count"] += 1
        name = obs.get("name")
        is_wrapper = name in NO_INPUT_TOOL_SPAN_NAMES
        if obs.get("type") == "TOOL" and not is_wrapper:
            entry["tool_calls"] += 1
        entry["models"].add(obs.get("model"))

        by_level[obs.get("level") or "UNKNOWN"] += 1
        span_names[name or "(unnamed)"] += 1
        if not is_wrapper:
            cost_bearing_observations += 1

        usage = _usage_of(obs)
        context = _context_tokens(usage)
        # A "model call" is any observation that actually transmitted context. Counting
        # GENERATION-typed spans alone misses instrumentations that type them differently;
        # counting all observations would divide by tool spans that transmit nothing and
        # deflate depth toward zero.
        if context > 0 or usage[USAGE_OUTPUT] > 0:
            entry["generations"] += 1
        entry["context_tokens"] += context
        for key, value in usage.items():
            entry["usage"][key] += value
            window_usage[key] += value

    traces = []
    for tid, data in by_trace.items():
        generations = data["generations"]
        traces.append(
            {
                "traceId": tid,
                "sessionId": data["sessionId"],
                "cost": data["cost"],
                "observation_count": data["count"],
                "tool_call_count": data["tool_calls"],
                "generation_count": generations,
                # Retained under the original names so existing report templates keep working.
                "input_tokens": data["usage"][USAGE_FRESH_INPUT],
                "output_tokens": data["usage"][USAGE_OUTPUT],
                "cache_read_tokens": data["usage"][USAGE_CACHE_READ],
                "cache_write_tokens": data["usage"][USAGE_CACHE_WRITE],
                "context_tokens": data["context_tokens"],
                "context_depth_per_call": round(data["context_tokens"] / generations) if generations else 0,
                # Tool calls per model call. Near-constant across sessions doing the same
                # kind of work, so a big depth spread at a flat ratio here is proof the
                # extra cost is context, not extra work.
                "tool_calls_per_call": round(data["tool_calls"] / generations, 3) if generations else 0,
                "models": sorted(m for m in data["models"] if m),
            }
        )
    trace_outliers = _flag_outlier_traces(traces, factor=factor)

    total = sum(by_level.values())
    errors = by_level.get("ERROR", 0)
    error_pct = {
        "total_observations": total,
        "cost_bearing_observations": cost_bearing_observations,
        "error_count": errors,
        "error_pct": (errors / total * 100) if total else 0,
        # The honest rate. Wrapper spans can be ~40% of all observations, and they cannot
        # fail in a way that costs anything, so including them in the denominator
        # understates the real error rate — by 1.7x on a measured window.
        "error_pct_of_cost_bearing": (errors / cost_bearing_observations * 100) if cost_bearing_observations else 0,
        "by_level": dict(by_level),
    }

    return {
        "trace_outliers": trace_outliers,
        "error_pct": error_pct,
        "token_economics": _token_economics(window_usage, cache_key=cache_key),
        "exporter_health": _exporter_health(span_names),
    }


def _token_economics(window_usage, cache_key=USAGE_CACHE_READ):
    """Window-level token accounting and the cost decomposition that drives triage.

    Replaces the old `cache_read_pct`, which divided cache reads by
    (fresh_input + cache_reads). Because `input` is fresh input only — often a few
    thousand tokens against hundreds of millions of cache reads — that ratio pins at
    ~99.99% on any window where caching works at all. It therefore cannot distinguish a
    well-run window from a badly-run one, while reading as a clean bill of health.

    A high cache-read share is not health; it IS the cost structure. What varies between
    a cheap window and an expensive one is `context_depth_per_call` (see
    `trace_outliers`) and `cache_churn_ratio` below.
    """
    fresh = window_usage.get(USAGE_FRESH_INPUT, 0)
    read = window_usage.get(cache_key, 0)
    write = window_usage.get(USAGE_CACHE_WRITE, 0)
    output = window_usage.get(USAGE_OUTPUT, 0)
    total_input = fresh + read + write
    return {
        "fresh_input_tokens": fresh,
        "cache_read_tokens": read,
        "cache_write_tokens": write,
        "output_tokens": output,
        "total_input_tokens": total_input,
        # Correct denominator: all input actually transmitted, cache included.
        "cache_read_pct_of_input": round(read / total_input * 100, 4) if total_input else 0,
        "cache_write_pct_of_input": round(write / total_input * 100, 4) if total_input else 0,
        # Prefix churn: how much was re-written versus re-read. Rising churn means the
        # cached prefix keeps being invalidated — edits landing above the cache breakpoint,
        # or a context that never stabilises.
        "cache_churn_ratio": round(write / read, 5) if read else None,
        "input_output_ratio": round(total_input / output, 1) if output else None,
        "cost_shares": _cost_shares_bie(window_usage),
        "cost_shares_1h_cache": _cost_shares_bie(window_usage, cache_write_multiplier=2.0),
    }


def _exporter_health(span_names):
    """Detect the double-export condition the skill documents but never measured.

    If Claude Code's native OTel exporter and the langfuse-observability plugin are both
    pointed at the same project, every tool call is traced twice and the native spans
    carry no cost. Those wrapper spans then inflate the denominator of every
    count-based metric (error rate, duplicate rate) while contributing no spend.
    """
    wrapper = sum(count for name, count in span_names.items() if name in NO_INPUT_TOOL_SPAN_NAMES)
    named_tools = sum(count for name, count in span_names.items() if str(name).startswith("Tool: "))
    total = sum(span_names.values())
    both_active = wrapper > 0 and named_tools > 0
    return {
        "wrapper_span_count": wrapper,
        "named_tool_span_count": named_tools,
        "total_observations": total,
        "wrapper_pct_of_observations": round(wrapper / total * 100, 2) if total else 0,
        "both_exporters_active": both_active,
        # The plugin emits the cost-bearing spans. If it saw fewer tool calls than the
        # native exporter did, cost/duplicate analysis is blind to the difference.
        "cost_bearing_tool_coverage_pct": (
            round(named_tools / (wrapper / 2) * 100, 1) if wrapper >= 2 else None
        ),
        "warning": (
            "Both exporters are active: every tool call is traced twice. Wrapper spans carry no "
            "cost, so treat `cost_bearing_observations` as the denominator for every rate, and "
            "expect duplicate-rate-per-observation to understate by roughly this factor."
            if both_active
            else None
        ),
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
        # Normalised rather than exact: the same file re-read at a different offset is the
        # same retrieval and should count as a repeat.
        key = (obs.get("traceId"), name, _normalize_input(name, obs.get("input")))
        groups[key].append(
            {
                "id": obs.get("id"),
                "sessionId": obs.get("sessionId"),
                "output_bytes": _payload_bytes(obs.get("output")),
                "kind": _classify_payload(name, obs.get("input"), obs.get("output")),
            }
        )

    result = []
    for (tid, name, _input), ids in groups.items():
        if len(ids) <= 1:
            continue
        # Cost of duplication is token-weighted, not count-weighted: one repeated 500KB
        # read costs far more than fifty repeated `git status` calls. Rank on bytes.
        sizes = sorted((i["output_bytes"] for i in ids), reverse=True)
        wasted = sum(sizes[1:])
        result.append(
            {
                "traceId": tid,
                "sessionId": ids[0]["sessionId"] if ids else None,
                "tool": name,
                "repeat_count": len(ids),
                "payload_kind": ids[0]["kind"],
                "wasted_output_bytes": wasted,
                # Every duplicated payload is admitted to context once per repeat and then
                # re-sent on every later call in the trace, so bytes here understate impact.
                "observation_ids": [i["id"] for i in ids],
            }
        )
    result.sort(key=lambda r: (-r["wasted_output_bytes"], -r["repeat_count"]))
    return result


def cmd_payload_profile(base_url, headers, from_ts, to_ts, **_):
    """Tool-result payload sizes by tool and kind — the missing root-cause measurement.

    Context depth is driven by what gets admitted to context, and the size of each tool
    result is the only direct evidence of that. Splitting image vs text matters because
    the remedies are opposite: images cannot be grepped or paginated (fewer/smaller
    screenshots is the only fix), whereas oversized text yields to a bounded search or
    `limit`/`offset`. Concluding without the split produces the wrong recommendation.
    """
    tool_filter = [{"type": "string", "column": "type", "operator": "=", "value": "TOOL"}]
    by_tool = collections.defaultdict(lambda: {"calls": 0, "bytes": 0, "max_bytes": 0, "kinds": collections.Counter()})
    oversized = []
    for obs in pull_observations(base_url, headers, "core,basic,io", from_ts, to_ts, tool_filter):
        name = obs.get("name")
        if name in NO_INPUT_TOOL_SPAN_NAMES:
            continue
        size = _payload_bytes(obs.get("output"))
        kind = _classify_payload(name, obs.get("input"), obs.get("output"))
        entry = by_tool[name]
        entry["calls"] += 1
        entry["bytes"] += size
        entry["max_bytes"] = max(entry["max_bytes"], size)
        entry["kinds"][kind] += 1
        if size >= OVERSIZED_PAYLOAD_BYTES:
            oversized.append(
                {
                    "traceId": obs.get("traceId"),
                    "sessionId": obs.get("sessionId"),
                    "tool": name,
                    "kind": kind,
                    "output_bytes": size,
                    "input": obs.get("input"),
                }
            )

    oversized.sort(key=lambda r: -r["output_bytes"])
    total_bytes = sum(d["bytes"] for d in by_tool.values()) or 1
    image_bytes = sum(r["output_bytes"] for r in oversized if r["kind"] == "image")
    text_bytes = sum(r["output_bytes"] for r in oversized if r["kind"] == "text")
    return {
        "by_tool": sorted(
            (
                {
                    "tool": name,
                    "calls": d["calls"],
                    "total_output_bytes": d["bytes"],
                    "pct_of_all_output_bytes": round(d["bytes"] / total_bytes * 100, 2),
                    "mean_output_bytes": round(d["bytes"] / d["calls"]) if d["calls"] else 0,
                    "max_output_bytes": d["max_bytes"],
                    "kinds": dict(d["kinds"]),
                }
                for name, d in by_tool.items()
            ),
            key=lambda r: -r["total_output_bytes"],
        ),
        "oversized_payloads": oversized[:25],
        "oversized_threshold_bytes": OVERSIZED_PAYLOAD_BYTES,
        "oversized_image_bytes": image_bytes,
        "oversized_text_bytes": text_bytes,
        "oversized_image_share_pct": (
            round(image_bytes / (image_bytes + text_bytes) * 100, 1) if (image_bytes + text_bytes) else None
        ),
    }


def cmd_underuse_profile(base_url, headers, from_ts, to_ts, **_):
    """Cheaper paths that were available and NOT taken.

    Every other query in this file looks for something happening too much. The two
    largest context-depth drivers are the opposite — something happening too little:
    unbounded Bash search standing in for Grep/Glob, and wide reads kept in the parent
    context instead of delegated to a subagent. Neither is visible in a frequency
    histogram, so they need their own check.
    """
    tool_filter = [{"type": "string", "column": "type", "operator": "=", "value": "TOOL"}]
    counts = collections.Counter()
    bash_search = 0
    bash_total = 0
    search_examples = []
    for obs in pull_observations(base_url, headers, "core,basic,io", from_ts, to_ts, tool_filter):
        name = obs.get("name")
        if name in NO_INPUT_TOOL_SPAN_NAMES:
            continue
        short = name[len("Tool: "):] if str(name).startswith("Tool: ") else name
        counts[short] += 1
        if short == "Bash":
            bash_total += 1
            command = ""
            if isinstance(obs.get("input"), dict):
                command = str(obs["input"].get("command") or "")
            if any(pattern in command for pattern in BASH_SEARCH_PATTERNS):
                bash_search += 1
                if len(search_examples) < 15:
                    search_examples.append(
                        {"traceId": obs.get("traceId"), "command": command[:300],
                         "output_bytes": _payload_bytes(obs.get("output"))}
                    )

    total_calls = sum(counts.values()) or 1
    bounded = sum(counts.get(t, 0) for t in BOUNDED_SEARCH_TOOLS)
    delegation = sum(counts.get(t, 0) for t in DELEGATION_TOOLS)
    findings = []
    if bash_search > 0 and bounded == 0:
        findings.append(
            f"{bash_search} Bash search/dump calls and ZERO Grep/Glob calls. Bash returns unbounded "
            "output straight into context, which is then re-sent on every later call in the session. "
            "Grep/Glob answer the same questions with bounded results."
        )
    if bash_total and bash_search / bash_total > 0.3:
        findings.append(
            f"{bash_search}/{bash_total} ({bash_search / bash_total * 100:.0f}%) of Bash calls are "
            "searches or file dumps — route these to Grep/Glob/Read."
        )
    if delegation / total_calls < 0.01:
        findings.append(
            f"Delegation is {delegation}/{total_calls} ({delegation / total_calls * 100:.2f}%) of tool calls. "
            "A payload of P tokens admitted at call i of n is re-sent (n-i) times; delegating a wide read "
            "to a subagent leaves only its summary in the parent context."
        )
    return {
        "tool_counts": dict(counts.most_common()),
        "bounded_search_calls": bounded,
        "bash_calls": bash_total,
        "bash_search_calls": bash_search,
        "bash_search_pct_of_bash": round(bash_search / bash_total * 100, 1) if bash_total else None,
        "delegation_calls": delegation,
        "delegation_pct_of_tool_calls": round(delegation / total_calls * 100, 3),
        "bash_search_examples": search_examples,
        "findings": findings,
    }


def cmd_reconcile(base_url, headers, from_ts, to_ts, **_):
    """Assert Langfuse's recorded `totalCost` matches tokens x published rates.

    Guards against three failure modes that all silently produce plausible wrong numbers:
    a null `model` (so nothing can be priced), an instrumentation gap where observations
    carry tokens but no cost, and a stale rate table.
    """
    by_model = collections.defaultdict(lambda: {"cost": 0.0, "usage": collections.Counter(), "count": 0,
                                                "zero_cost_with_tokens": 0})
    for obs in pull_observations(base_url, headers, "core,basic,usage,model", from_ts, to_ts):
        usage = _usage_of(obs)
        if not any(usage.values()):
            continue
        entry = by_model[obs.get("model") or "(null model)"]
        entry["count"] += 1
        entry["cost"] += obs.get("totalCost") or 0
        for key, value in usage.items():
            entry["usage"][key] += value
        if not (obs.get("totalCost") or 0):
            entry["zero_cost_with_tokens"] += 1

    rows = []
    for model, data in by_model.items():
        rate = RATES.get(model)
        computed = None
        if rate:
            base_in, out_rate = rate
            usage = data["usage"]
            computed = round(
                usage[USAGE_FRESH_INPUT] / 1e6 * base_in
                + usage[USAGE_CACHE_WRITE] / 1e6 * base_in * 1.25
                + usage[USAGE_CACHE_READ] / 1e6 * base_in * 0.1
                + usage[USAGE_OUTPUT] / 1e6 * out_rate,
                4,
            )
        rows.append(
            {
                "model": model,
                "observations_with_usage": data["count"],
                "observations_with_tokens_but_no_cost": data["zero_cost_with_tokens"],
                "recorded_cost": round(data["cost"], 4),
                "computed_cost": computed,
                "delta_pct": (
                    round((data["cost"] - computed) / computed * 100, 1) if computed else None
                ),
                "usage": dict(data["usage"]),
                "note": None if rate else f"no rate for {model} in RATES — add it or the model is unattributed",
            }
        )
    rows.sort(key=lambda r: -r["recorded_cost"])
    return {
        "by_model": rows,
        "reconciles": all(
            r["delta_pct"] is not None and abs(r["delta_pct"]) <= 5 for r in rows if r["computed_cost"]
        ),
        "guidance": "Investigate any |delta_pct| > 5, any '(null model)' row, and any nonzero "
                    "observations_with_tokens_but_no_cost before quoting a dollar figure.",
    }


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


def cmd_token_economics(base_url, headers, from_ts, to_ts, cache_key=USAGE_CACHE_READ, **_):
    """Window token accounting + rate-invariant cost decomposition.

    Supersedes the old `cache_read_pct` command, which is kept as an alias.
    """
    window_usage = collections.Counter()
    for obs in pull_observations(base_url, headers, "core,basic,usage", from_ts, to_ts):
        for key, value in _usage_of(obs).items():
            window_usage[key] += value
    return _token_economics(window_usage, cache_key=cache_key)


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
                # Sizes BEFORE the preview: payload size is the quantity that drives context
                # depth, and a 300-char preview throws exactly that away. A 500KB screenshot
                # and a 200-byte `git status` look identical once truncated.
                "input_bytes": _payload_bytes(obs.get("input")),
                "output_bytes": _payload_bytes(obs.get("output")),
                "payload_kind": _classify_payload(obs.get("name"), obs.get("input"), obs.get("output")),
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
    "token_economics": cmd_token_economics,
    "cache_read_pct": cmd_token_economics,  # backwards-compatible alias
    "payload_profile": cmd_payload_profile,
    "underuse_profile": cmd_underuse_profile,
    "reconcile": cmd_reconcile,
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
        for name in ("trace_outliers", "error_pct", "token_economics", "exporter_health"):
            out_path = os.path.join(args.out_dir, f"{name}.json")
            with open(out_path, "w") as f:
                json.dump(combined[name], f, indent=2)
            print(f"wrote {out_path}")

        for name, fn in (
            ("duplicate_tool_calls", cmd_duplicate_tool_calls),
            ("tool_usage", cmd_tool_usage),
            ("payload_profile", cmd_payload_profile),
            ("underuse_profile", cmd_underuse_profile),
            ("reconcile", cmd_reconcile),
        ):
            result = fn(base_url, headers, from_ts, to_ts)
            out_path = os.path.join(args.out_dir, f"{name}.json")
            with open(out_path, "w") as f:
                json.dump(result, f, indent=2)
            print(f"wrote {out_path}")

        # Read this first: it is the one file that says where the money went, and it is
        # small enough not to cost meaningful context to load.
        summary = {
            "cost_shares": combined["token_economics"]["cost_shares"],
            "cache_churn_ratio": combined["token_economics"]["cache_churn_ratio"],
            "error_pct_of_cost_bearing": combined["error_pct"]["error_pct_of_cost_bearing"],
            "exporter_warning": combined["exporter_health"]["warning"],
            "top_recoverable": [
                {
                    "traceId": t["traceId"],
                    "sessionId": t["sessionId"],
                    "cost": round(t["cost"], 4),
                    "context_depth_per_call": t["context_depth_per_call"],
                    "depth_ratio": t["depth_ratio"],
                    "tool_calls_per_call": t["tool_calls_per_call"],
                    "recoverable_cost": t["recoverable_cost"],
                }
                for t in combined["trace_outliers"][:10]
            ],
            "total_recoverable_cost": round(sum(t["recoverable_cost"] for t in combined["trace_outliers"]), 4),
        }
        out_path = os.path.join(args.out_dir, "summary.json")
        with open(out_path, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"wrote {out_path}  <- read this one first")

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
