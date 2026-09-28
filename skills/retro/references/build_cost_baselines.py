#!/usr/bin/env python3
"""
Build compact cost baselines for the `cost-guardrail` hook from Langfuse trace data.

Reuses `langfuse_queries.py`'s auth/pagination/rate machinery — this script only adds
the per-model/per-tool cost aggregation and writes a small, fixed-shape JSON file that
a Node hook can `JSON.parse` synchronously on every `PreToolUse` call, with no Langfuse
credentials needed at read time.

Environment: same as langfuse_queries.py (LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY,
LANGFUSE_BASE_URL, FROM, TO, LANGFUSE_USER_ID).

Usage:
    python3 build_cost_baselines.py --out .claude/cost-audit/cost_baselines.json
    python3 build_cost_baselines.py --out .claude/cost-audit/cost_baselines.json --user '' --min-sample 10
"""

import argparse
import collections
import json
import os
import statistics
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import langfuse_queries as lq  # noqa: E402

FACTOR_DEFAULT = 3.0


def _stats(costs):
    costs = sorted(c for c in costs if c > 0)
    if not costs:
        return None
    return {
        "count": len(costs),
        "median_cost": round(statistics.median(costs), 6),
        "p95_cost": round(costs[min(len(costs) - 1, int(len(costs) * 0.95))], 6),
        "mean_cost": round(statistics.mean(costs), 6),
    }


def build_baselines(base_url, headers, from_ts, to_ts, min_sample):
    by_model_costs = collections.defaultdict(list)
    by_trace_model_cost = collections.defaultdict(float)
    by_trace_model = {}
    for obs in lq.pull_observations(base_url, headers, "core,basic,usage,model", from_ts, to_ts):
        tid = obs.get("traceId") or "(no trace)"
        model = obs.get("model")
        if model:
            by_trace_model[tid] = model
        by_trace_model_cost[tid] += obs.get("totalCost") or 0

    for tid, cost in by_trace_model_cost.items():
        model = by_trace_model.get(tid)
        if model:
            by_model_costs[model].append(cost)

    by_tool_costs = collections.defaultdict(list)
    for obs in lq.pull_observations(
        base_url, headers, "core,basic,usage",
        from_ts, to_ts,
        [{"type": "string", "column": "type", "operator": "=", "value": "TOOL"}],
    ):
        name = obs.get("name")
        if name in lq.NO_INPUT_TOOL_SPAN_NAMES:
            continue
        by_tool_costs[name].append(obs.get("totalCost") or 0)

    by_model = {}
    for model, costs in by_model_costs.items():
        s = _stats(costs)
        if s and s["count"] >= min_sample:
            by_model[model] = s

    by_tool = {}
    for tool, costs in by_tool_costs.items():
        s = _stats(costs)
        if s and s["count"] >= min_sample:
            by_tool[tool] = s

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "window": {"from": from_ts, "to": to_ts},
        "factor_default": FACTOR_DEFAULT,
        "by_model": by_model,
        "by_tool": by_tool,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default=".claude/cost-audit/cost_baselines.json", help="output path")
    parser.add_argument("--min-sample", type=int, default=5, help="min observation count for a model/tool to be included")
    parser.add_argument(
        "--user", default=os.environ.get("LANGFUSE_USER_ID") or None,
        help="restrict to this Langfuse userId (default: LANGFUSE_USER_ID env var). Pass '' to use the whole shared project.",
    )
    args = parser.parse_args()

    lq.USER_ID_FILTER = args.user or None

    base_url = lq._env("LANGFUSE_BASE_URL", default="https://cloud.langfuse.com")
    public_key = lq._env("LANGFUSE_PUBLIC_KEY", required=True)
    secret_key = lq._env("LANGFUSE_SECRET_KEY", required=True)
    headers = lq._auth_header(public_key, secret_key)

    to_dt = datetime.now(timezone.utc)
    from_dt = to_dt - timedelta(days=30)
    to_ts = lq._env("TO", default=to_dt.isoformat())
    from_ts = lq._env("FROM", default=from_dt.isoformat())

    baselines = build_baselines(base_url, headers, from_ts, to_ts, args.min_sample)

    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(baselines, f, indent=2)
    print(f"wrote {args.out}: {len(baselines['by_model'])} model(s), {len(baselines['by_tool'])} tool(s) tracked")


if __name__ == "__main__":
    main()
