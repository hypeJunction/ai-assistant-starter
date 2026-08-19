// Offline tests for the pure metric helpers in
// skills/cost-audit/references/langfuse_queries.py.
//
// The queries themselves need a live Langfuse, but every judgement the audit makes lives
// in pure functions over observation dicts, so those are testable with synthetic data and
// no network. Driven through `python3 -c` to keep the repo's node --test runner as the
// single entry point.

const { test } = require('node:test');
const assert = require('node:assert');
const { execFileSync } = require('node:child_process');
const path = require('node:path');

const MODULE_DIR = path.join(__dirname, '..', '..', 'skills', 'cost-audit', 'references');

function runPython(body) {
  const script = [
    'import json, sys',
    `sys.path.insert(0, ${JSON.stringify(MODULE_DIR)})`,
    'import langfuse_queries as lq',
    body,
  ].join('\n');
  const out = execFileSync('python3', ['-c', script], { encoding: 'utf8' });
  return JSON.parse(out);
}

function obs(overrides) {
  return Object.assign(
    {
      id: 'o1',
      traceId: 't1',
      sessionId: 's1',
      type: 'GENERATION',
      name: 'LLM Call',
      level: 'DEFAULT',
      totalCost: 0,
      usageDetails: {},
    },
    overrides,
  );
}

test('_usage_of reads all four billed token classes, not just `input`', () => {
  const usage = runPython(`
o = ${JSON.stringify(
    obs({
      usageDetails: {
        input: 100,
        output: 50,
        cache_read_input_tokens: 900000,
        cache_creation_input_tokens: 20000,
      },
    }),
  )}
print(json.dumps({"usage": lq._usage_of(o), "context": lq._context_tokens(lq._usage_of(o))}))
`);
  assert.strictEqual(usage.usage.cache_creation_input_tokens, 20000);
  assert.strictEqual(usage.usage.cache_read_input_tokens, 900000);
  // Context transmitted = fresh + read + write. Summing `input` alone would report 100.
  assert.strictEqual(usage.context, 920100);
});

test('cost shares are rate-invariant and put context re-transmission ahead of output', () => {
  // Proportions taken from a real 30-day window: 13,838 fresh / 568,759,006 read /
  // 8,240,467 write / 1,700,729 output.
  const res = runPython(`
totals = {"input": 13838, "cache_read_input_tokens": 568759006,
          "cache_creation_input_tokens": 8240467, "output": 1700729}
print(json.dumps({"five_min": lq._cost_shares_bie(totals),
                  "one_hour": lq._cost_shares_bie(totals, cache_write_multiplier=2.0)}))
`);
  // Context re-transmission dominates under either cache-write TTL.
  assert.ok(res.five_min.context_retransmission_pct > 85, 'context share should exceed 85%');
  assert.ok(res.one_hour.context_retransmission_pct > 85);
  // Output is an order of magnitude smaller, so "be more concise" is a bounded lever.
  assert.ok(res.five_min.output_pct < 15, 'output share should be under 15%');
  // Typed prompt text is a rounding error — this is why prompt-golfing does not pay.
  assert.ok(res.five_min.fresh_input_pct < 0.1);
});

test('token_economics uses a cache-inclusive denominator instead of pinning at ~100%', () => {
  const res = runPython(`
import collections
totals = collections.Counter({"input": 13838, "cache_read_input_tokens": 568759006,
                              "cache_creation_input_tokens": 8240467, "output": 1700729})
print(json.dumps(lq._token_economics(totals)))
`);
  // The old formula was cache_read / (fresh + cache_read) = 99.9976%, which cannot fall
  // below a >95% "healthy" gate on any window where caching works at all.
  const legacy = (568759006 / (568759006 + 13838)) * 100;
  assert.ok(legacy > 99.99, 'sanity: legacy formula really does pin near 100%');
  // The corrected share counts cache writes as input too, so it can actually move.
  assert.ok(res.cache_read_pct_of_input < legacy);
  assert.ok(Math.abs(res.cache_read_pct_of_input - 98.57) < 0.05);
  assert.strictEqual(res.cache_write_tokens, 8240467);
  assert.ok(res.cache_churn_ratio > 0, 'churn ratio must be reported');
});

test('depth outlier is flagged and ranked by recoverable cost, not by size', () => {
  const res = runPython(`
traces = [
  # Same tool/turn ratio, same call count. Only depth differs.
  {"traceId": "deep",  "cost": 98.0, "tool_call_count": 418, "input_tokens": 100,
   "output_tokens": 50000, "context_depth_per_call": 128000, "generation_count": 1536},
  {"traceId": "shallow", "cost": 2.2, "tool_call_count": 78, "input_tokens": 100,
   "output_tokens": 9000, "context_depth_per_call": 17000, "generation_count": 300},
  {"traceId": "shallow2", "cost": 2.1, "tool_call_count": 66, "input_tokens": 100,
   "output_tokens": 8000, "context_depth_per_call": 17000, "generation_count": 248},
]
print(json.dumps(lq._flag_outlier_traces(traces, factor=3.0)))
`);
  assert.ok(res.length >= 1);
  const deep = res[0];
  assert.strictEqual(deep.traceId, 'deep');
  // Depth must be among the reasons it tripped — the whole point of the added metric.
  assert.ok(deep.outlier_reasons.some((r) => r.metric === 'context_depth_per_call'));
  // The counterfactual quantifies the recoverable part rather than just naming a ratio.
  assert.ok(deep.recoverable_cost > 80, `expected >$80 recoverable, got ${deep.recoverable_cost}`);
  assert.ok(deep.cost_at_median_depth < 15);
  assert.ok(Math.abs(deep.depth_ratio - 128000 / 17000) < 0.05);
});

test('a large-but-shallow trace is not ranked as recoverable waste', () => {
  const res = runPython(`
traces = [
  # Genuinely big: 4x the calls and 4x the cost, but at the median depth. Nothing to recover.
  {"traceId": "big_shallow", "cost": 40.0, "tool_call_count": 400, "input_tokens": 100,
   "output_tokens": 40000, "context_depth_per_call": 17000, "generation_count": 1200},
  {"traceId": "a", "cost": 2.2, "tool_call_count": 78, "input_tokens": 100,
   "output_tokens": 9000, "context_depth_per_call": 17000, "generation_count": 300},
  {"traceId": "b", "cost": 2.1, "tool_call_count": 66, "input_tokens": 100,
   "output_tokens": 8000, "context_depth_per_call": 17000, "generation_count": 248},
]
out = lq._flag_outlier_traces(traces, factor=3.0)
print(json.dumps({t["traceId"]: t["recoverable_cost"] for t in out}))
`);
  assert.strictEqual(res.big_shallow, 0, 'depth at median means zero recoverable cost');
});

test('error rate is reported against cost-bearing observations, not wrapper spans', () => {
  // Span counts from a real double-exported 30-day window, summing to its 30,678
  // observations: 12,641 wrapper spans + 2,758 named tool spans + 15,279 generations.
  const res = runPython(`
import collections
names = collections.Counter({"claude_code.tool": 6342, "claude_code.tool.execution": 6299,
                             "Tool: Bash": 1740, "Tool: Read": 332, "Tool: Edit": 479,
                             "Tool: Write": 76, "Tool: Agent": 11, "Tool: Skill": 8,
                             "Tool: other": 112, "LLM Call": 15279})
print(json.dumps(lq._exporter_health(names)))
`);
  assert.strictEqual(res.total_observations, 30678);
  assert.strictEqual(res.wrapper_span_count, 12641);
  assert.strictEqual(res.named_tool_span_count, 2758);
  assert.strictEqual(res.both_exporters_active, true);
  assert.ok(res.warning, 'double export must produce a warning');
  assert.ok(Math.abs(res.wrapper_pct_of_observations - 41.2) < 0.5);
  // The plugin saw far fewer tool calls than the native exporter, so cost/duplicate
  // analysis is blind to the difference.
  assert.ok(res.cost_bearing_tool_coverage_pct < 70);
});

test('single exporter produces no warning', () => {
  const res = runPython(`
import collections
names = collections.Counter({"Tool: Bash": 100, "LLM Call": 400})
print(json.dumps(lq._exporter_health(names)))
`);
  assert.strictEqual(res.both_exporters_active, false);
  assert.strictEqual(res.warning, null);
});

test('near-duplicate reads group despite differing offset/limit', () => {
  const res = runPython(`
a = lq._normalize_input("Tool: Read", {"file_path": "/x/SKILL.md", "offset": 0, "limit": 100})
b = lq._normalize_input("Tool: Read", {"file_path": "/x/SKILL.md", "offset": 400, "limit": 50})
c = lq._normalize_input("Tool: Read", {"file_path": "/x/OTHER.md"})
print(json.dumps({"same": a == b, "different": a == c}))
`);
  assert.strictEqual(res.same, true, 'same file at a different offset is the same retrieval');
  assert.strictEqual(res.different, false);
});

test('payload classifier separates images from text, and sizes are measured', () => {
  const res = runPython(`
img = lq._classify_payload("Tool: Read", {"file_path": "/tmp/shot.png"}, "iVBORw0KGgo")
txt = lq._classify_payload("Tool: Bash", {"command": "grep -r foo ."}, "src/a.ts:1: foo")
print(json.dumps({"img": img, "txt": txt,
                  "bytes": lq._payload_bytes("x" * 1234),
                  "none": lq._payload_bytes(None)}))
`);
  // Images cannot be grepped or paginated, so the remedy differs from oversized text.
  assert.strictEqual(res.img, 'image');
  assert.strictEqual(res.txt, 'text');
  assert.strictEqual(res.bytes, 1234);
  assert.strictEqual(res.none, 0);
});

test('reconcile prices Opus 5 at $5/$25 rather than the retired $15/$75', () => {
  const res = runPython(`print(json.dumps({"opus5": lq.RATES["claude-opus-5"], "sonnet5": lq.RATES["claude-sonnet-5"]}))`);
  assert.deepStrictEqual(res.opus5, [5.0, 25.0]);
  assert.deepStrictEqual(res.sonnet5, [3.0, 15.0]);
});

test('every command in the registry is callable and the legacy alias survives', () => {
  const res = runPython(`
print(json.dumps({"commands": sorted(lq.COMMANDS),
                  "alias_ok": lq.COMMANDS["cache_read_pct"] is lq.COMMANDS["token_economics"],
                  "depth_metric_registered": lq.DEPTH_METRIC in lq.OUTLIER_METRICS}))
`);
  assert.strictEqual(res.alias_ok, true, 'cache_read_pct must keep working');
  assert.strictEqual(res.depth_metric_registered, true);
  for (const name of ['payload_profile', 'underuse_profile', 'reconcile', 'token_economics']) {
    assert.ok(res.commands.includes(name), `${name} should be registered`);
  }
});
