---
name: cost-audit
description: Audit Langfuse trace data for token-cost waste patterns — duplicate tool calls, runaway/retry loops, whale sessions — and propose evidence-backed CLAUDE.md or skill corrections. Use periodically, after a cost spike, or when Claude Code usage feels unexpectedly expensive.
category: process
triggers:
  - audit token cost
  - why is claude code expensive
  - reduce claude cost
  - find wasted tokens
  - langfuse cost audit
  - check for retry loops
---

# Cost Audit

> **Purpose:** Turn Langfuse trace data into evidence-backed corrections to CLAUDE.md/skills, then verify the correction actually reduced the waste
> **Usage:** `/cost-audit`

## Constraints

- **Evidence before edits** — never propose a correction that isn't backed by a specific trace ID, repeat count, outlier ratio, or cost figure pulled from Langfuse. Generic advice ("be more efficient") is not acceptable output.
- **Classify before you rank, rank before you fix** — a high duplicate-call rate is a symptom, not a diagnosis. Pull the actual observation inputs for the top offending trace/tool pair, label the pattern, and confirm it's actually driving cost or a runaway loop before proposing a fix — never jump straight from a count to a policy line.
- **Gate before writing** — present findings and proposed diffs; do not edit CLAUDE.md or any skill file until the user approves.
- **Close the loop** — every audit that results in an approved edit gets a follow-up re-run logged, so the next audit can report whether the targeted pattern's rate actually dropped.
- **A high cache-read share is the cost structure, not a clean bill of health** — context re-transmission (cache read + cache write) is typically ~85-90% of spend, so "cache-read % is high" describes where the money goes, not that it is well spent. Read `cost_shares` in `token_economics.json` and act on the largest share. Never treat a high cache-read percentage, or a high input:output ratio, as a reason to stop looking.
- **Distinguish big from wasteful** — cost, token counts and tool-call counts are totals: they scale with how long a trace ran, so a long legitimate trace trips them and a short pathological one does not. `context_depth_per_call` (mean tokens transmitted per model call) is the normalised metric that separates the two. Two traces at the same `tool_calls_per_call` doing the same kind of work can differ many-fold on depth, and that entire difference is re-transmission. Rank by `recoverable_cost` — what the trace would have cost at the window's median depth.
- **Don't touch what isn't broken** — duplication, loops and errors are frequently NOT the driver. Reference benchmark, measured 2026-08-19 over a 30-day Langfuse window (32 sessions, 30,678 observations, $288.92, single seat running mixed audit/coding/research work): duplicate tool calls **0.55%** of all tool calls (35 excess calls of 6,342, max repeat 4), error rate **1.06%** of cost-bearing observations (192 errors; 0.63% if wrapper spans are left in the denominator) — while **71%** of context tokens (409M of 578M) and **71%** of spend ($204 of $289) were context depth above the window median of 17k tokens/call. Treat these as the current baseline to compare a fresh window against, re-measure rather than assume them, and when the duplication/loop/error checks come back negative move on to depth instead of concluding "no waste found".

## Prerequisites

- A Langfuse instance (self-hosted or cloud) receiving Claude Code traces — via the `langfuse-observability` Claude Code plugin/hook, or an equivalent OTel/SDK integration.
- `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL` available in the environment (or a `.env` file the user points you to).
  - **If they're not set**, and this project uses the `langfuse-observability` Claude Code plugin, the credentials already exist on the machine — they're just not exported:
    - `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_BASE_URL` are in `~/.claude/settings.json` under `pluginConfigs["langfuse-observability@langfuse-observability"]`.
    - `LANGFUSE_SECRET_KEY` isn't stored directly — it's base64-encoded inside `env.OTEL_EXPORTER_OTLP_HEADERS` in that same plugin config (an `Authorization: Basic <base64(pk:sk)>` header). Decode that value to recover `pk:sk`, and take the `sk` half.
    - Export all three before running the queries below; don't hardcode them into a file.
- Python 3.8+ on the machine running the audit — `references/langfuse_queries.py` is stdlib-only (`urllib`, `json`), no dependency install required.

If no Langfuse instance is reachable, stop and tell the user what's missing.

**Langfuse is for triage, not the only source of truth.** The OTel exporter drops tool `input` on the majority of TOOL-type spans (the generic `claude_code.tool`/`claude_code.tool.execution` wrapper spans carry no arguments — see `NO_INPUT_TOOL_SPAN_NAMES` in `langfuse_queries.py`), so Langfuse alone can tell you *which* trace/session is expensive but often can't show you *what* it actually did. Local session transcripts (`~/.claude/projects/<project-slug>/<sessionId>.jsonl`) have every tool input verbatim, per-turn token counts, and the user's actual wording — and the join is free: a Langfuse `sessionId` **is** the Claude Code session UUID, and that UUID is also the transcript's filename. Use Langfuse to find and rank the offenders (Step 1), then read the matching transcript directly for root cause on any offender where `drill`'s `input: null` output leaves the actual behavior unclear — don't guess from the aggregate numbers alone. `/session-retro` (see its SKILL.md) does this transcript-level drill-down systematically for a single session; reach for it when a shortlisted trace needs that depth.

## Workflow

Three steps: **classify** every trace worth looking at, **identify** which classified patterns are actually driving cost or loop behavior, then **propose** concrete, evidence-cited fixes. Each step has sub-steps; nothing in Step 3 gets written to disk without the approval gate.

### Step 1: Classify Traces

**1a. Pull metrics** for a time window (default: since the last audit, or last 30 days if this is the first run):

```bash
python3 references/langfuse_queries.py all --out-dir ./cost_audit_out
```

This writes `summary.json` (**read this one first**), `trace_outliers.json`, `duplicate_tool_calls.json`, `tool_usage.json`, `error_pct.json`, `token_economics.json`, `exporter_health.json`, `payload_profile.json`, `underuse_profile.json`, and `reconcile.json`:

0. `summary` — cost shares by token class, the churn ratio, the exporter warning, the top 10 traces by `recoverable_cost`, and the window's total recoverable cost. Small on purpose: it answers "where did the money go" without loading the detail files into context. Open the others only to substantiate what this one points at.
1. `trace_outliers` — every **trace** (not session) that exceeds 3x the window's median (the `--factor` default) on at least one of: cost, tool-call count, input tokens, output tokens, **`context_depth_per_call`**. Each entry lists which metric(s) tripped and by what ratio. This is trace-first rather than session-first on purpose: a session aggregates many turns, so ranking by session cost buries a single runaway trace inside an otherwise-cheap session, and misses a trace that's a tool-call/token outlier without yet being a cost outlier.
   - The first four metrics are **totals** and therefore measure how *big* a trace was. `context_depth_per_call` — mean tokens transmitted per model call — measures how *wasteful* it was, and the two routinely disagree. Also read `tool_calls_per_call`: when that ratio is near-constant across traces but depth varies many-fold, the extra spend is re-transmission, not extra work, and "legitimate heavy work" does not explain it.
   - Ranking is by **`recoverable_cost`** (`cost` − `cost_at_median_depth`), not by ratio-to-median, because a median-multiple rule on a heavy-tailed distribution flags the tail by construction and says nothing about how many dollars are actually on the table.
2. `duplicate_tool_calls` — groups of `[traceId, tool, input]` where the exact same call happened more than once within one trace (a trace is the natural boundary for one turn/loop, tighter than grouping by the whole session)
3. `tool_usage` — histogram of every dispatched tool (`Bash`, `Edit`, `Skill`, `Agent`, `Workflow`, MCP tools, ...) by invocation count, share of total calls, trace count, and average duration. This is the entry point for tool/skill-churn questions ("what's actually being invoked, and how often") as distinct from `duplicate_tool_calls`, which only catches exact repeats. It carries no cost/token column on purpose: this histogram is read off Claude Code's own native `claude_code.tool` OTel span, which never attaches `totalCost` — that number only exists on the separate cost-bearing spans (`LLM Call`, `Tool: X`) emitted by the langfuse-observability plugin's hook. If both exporters are pointed at the same Langfuse project (compare `OTEL_EXPORTER_OTLP_ENDPOINT` in `settings.json` against the plugin's own endpoint config), every tool call is being traced twice — that duplication is itself worth surfacing as a finding, separately from any cost analysis. For cost impact, use `trace_outliers`/`duplicate_tool_calls`, which are built from the cost-bearing spans.
4. `error_pct` — error rate across observations. Use **`error_pct_of_cost_bearing`**: wrapper spans can be ~40% of all observations and cannot fail in a way that costs anything, so including them understates the real rate (1.7x on the reference window).
5. `token_economics` — window token accounting split into the four billed classes (fresh input, cache read, cache write, output), plus `cost_shares` in rate-invariant base-input-equivalents, `cache_churn_ratio`, and `input_output_ratio`. **This replaces `cache_read_pct`**, which divided cache reads by (fresh input + cache reads); because `input` is fresh input only, that ratio pins at ~99.99% on any window where caching works at all and cannot distinguish a well-run window from a badly-run one. `cache_read_pct` remains as a command alias.
6. `exporter_health` — whether Claude Code's native OTel exporter and the langfuse-observability plugin are both pointed at the same project. If so every tool call is traced twice, the native wrapper spans carry no cost, and they inflate the denominator of every count-based rate. Read `cost_bearing_tool_coverage_pct` to see how much tool activity the cost-bearing spans actually saw.
7. `payload_profile` — tool-result sizes by tool, with an image/text/other split and the oversized payloads listed. This is the direct evidence for *what* is filling context. The image/text split decides the remedy and getting it backwards produces the wrong recommendation: images cannot be grepped or paginated, so an image-dominated problem needs fewer or smaller screenshots, whereas oversized text yields to a bounded search or `limit`/`offset`.
8. `underuse_profile` — cheaper paths that were available and **not** taken: Bash search/dump calls against Grep/Glob usage, and delegation (`Agent`/`Task`/`Workflow`) share of tool calls. Every other query looks for something happening too much; the two largest depth drivers are something happening too little, which no frequency histogram can show.
9. `reconcile` — recorded `totalCost` against tokens × published rates, per model. Catches a null `model`, observations carrying tokens but no cost, and a stale rate table. Do not quote a dollar figure until this reconciles within 5%. Note the rates in `RATES`: Opus 4.8 / Opus 5 are **$5/$25 per MTok, not $15/$75**, and the 1M window carries no long-context premium.

**Skill-name limitation**: the OTel exporter records `Skill` as one generic tool name — it does not expose *which* skill was invoked (that argument lives only in the assistant's tool-call input, which this exporter drops). If `tool_usage` shows `Skill` at meaningful volume, cross-reference with local session transcripts (`~/.claude/projects/<project-slug>/*.jsonl`, one file per session) to break it down by name: grep each transcript for `"name":"Skill"` tool_use blocks and read the `input.skill` value. Do this only when `Skill` invocation count is itself high enough to be worth decomposing — otherwise note the limitation and move on.

**Stop condition.** Report "No significant waste patterns found" and stop only when **all** of these hold — do not manufacture findings to justify the audit, but do not stop early either:

1. `trace_outliers` is empty, **and**
2. `summary.total_recoverable_cost` is a negligible share of window spend (rule of thumb: under 10%), **and**
3. no trace has a duplicate-call rate above 15% of its **cost-bearing** observations (the same threshold used to shortlist in 1b — see `exporter_health.wrapper_pct_of_observations`, since wrapper spans deflate this rate), **and**
4. `underuse_profile.findings` is empty.

Condition 2 is the one that matters most often: duplication and errors can be genuinely clean while most of the window's tokens are depth. On the 2026-08-19 reference window, conditions 1, 3 and 4 would all have read "clean" on the duplication/error side while 71% of spend was recoverable depth.

**1b. Shortlist candidates** (max 5) from that output, prioritized by:

1. Highest `recoverable_cost` in `trace_outliers` — the dollars actually on the table. Cross-check `depth_ratio` and `tool_calls_per_call`: a high depth ratio at an unremarkable tool ratio is the clearest possible signal, because it means the same shape of work was done while carrying more context per call.
2. Traces flagged on 2+ metrics in `trace_outliers` (e.g. both tool-call count and output tokens) — the least ambiguous offenders on the loop/pathology side
3. Traces where duplicate-call count / trace **cost-bearing** observation count > 15%, ranked by `wasted_output_bytes` rather than `repeat_count` — one repeated 500KB read costs far more than fifty repeated `git status` calls
4. Remaining traces in `trace_outliers`, ranked by highest ratio-to-median on any single metric, with excess absolute cost as the tiebreak
5. From `tool_usage`, any tool whose `pct_of_calls` is disproportionate to what it should cost per call (e.g. `Bash`/`Edit`/`Read` dominating overall volume is normal agentic shape and not itself a finding, but a heavy `Agent`/`Workflow`/`Skill` dispatch *rate* relative to session count points at process-level churn — skills or subagents re-triggering — rather than a single stuck trace). Cross-reference the trace IDs in `trace_count` against `trace_outliers` before shortlisting; a high invocation count alone isn't evidence of cost impact for this metric (see the cost-attribution caveat above)

`error_pct.json` is a window-wide aggregate only (total observations, error count, breakdown by level) — it has no per-trace or per-timestamp detail, so "traces with an error cluster" is not a criterion this data can support. Don't shortlist on it; if a shortlisted trace's `drill` output happens to show ERROR-level observations clustered in time, that's part of Step 1c's classification (Retry-after-error), not a Step 1b filter.

Drop everything below these — this step is about the worst offenders, not a full inventory. Note the sessionId alongside each shortlisted trace for context in the report, but keep classification and root-causing scoped to the trace.

**1c. Drill into each shortlisted trace** and assign it a pattern label:

```bash
python3 references/langfuse_queries.py drill --trace <traceId> --tool <toolName> --limit 5
```

This returns the input, an output preview, and the timestamp of each matching call. If every row shows `input: null`, that's almost always the generic `claude_code.tool`/`claude_code.tool.execution` wrapper span, not a real signal — those spans never populate `input`, `drill` excludes them by default, but they can still surface if `--tool` targets one directly. Re-run against the actual per-tool span name (observation names are prefixed, e.g. `Tool: Read` not `Read`) or read the session's local transcript for the real arguments before concluding anything about the pattern; null input on its own does not indicate a heartbeat/poll loop.

| Pattern | Signature |
|---|---|
| **No context ceiling** | `context_depth_per_call` many-fold above the window median while `tool_calls_per_call` sits in the normal band. Same work, more context carried per call. Usually a long single-context session: cost grows with the square of turn count because every earlier token is re-sent on every later call. Remedy is a ceiling — checkpoint to a handoff file and `/clear` — not a behavioural rule. |
| **Unbounded search payload** | `underuse_profile` shows Bash search/dump calls with zero or near-zero Grep/Glob, and `payload_profile` shows large `Bash` text results. `grep`/`find`/`cat` return unbounded output into context; Grep/Glob answer the same question with bounded results. |
| **Undelegated wide read** | `payload_profile` shows oversized results in the parent trace and `underuse_profile.delegation_pct_of_tool_calls` is ~0. A payload of P tokens admitted at call *i* of *n* is re-sent (n−i) times; a subagent returns a summary instead. |
| **Image payload churn** | `payload_profile.oversized_image_share_pct` is high — screenshots or PDFs entering context via `Read` during verification work. These cannot be grepped or paginated, so the only remedy is fewer/smaller captures or asserting via DOM/console instead. |
| Stuck poll / runaway loop | Same tool + same input repeated dozens to thousands of times with no error in between |
| Re-verification read | Same `Read` on a file immediately after an `Edit`/`Write` to that same file |
| Retry-after-error | Duplicate calls clustered around ERROR-level observations |
| Browser-automation retry | Duplicate `navigate`/`console_messages`/`close` calls without an intervening state change |
| Redundant context re-fetch | Same lookup (file, search, API call) repeated across a session with no code change in between |
| Skill/subagent over-dispatch | A skill or `Agent`/`Workflow` call fires repeatedly within a session (or across near-identical prompts) where one dispatch would cover the work — each re-fires the skill's full instruction body into context |

Extend this list if a finding doesn't fit — don't force-fit a label.

### Step 2: Identify What Drives Cost or Loops

Not every classified pattern matters equally. For each labeled trace from Step 1c, connect the label to actual impact:

- **Metric impact**: which metric(s) does this trace's `outlier_reasons` list (cost, tool-call count, input tokens, output tokens), and does the pattern plausibly explain the excess (not just correlate)?
- **Loop severity**: is the repeat count large enough to indicate a runaway condition (hundreds to thousands) versus a handful of understandable retries?
- **Recurrence**: does the same pattern show up in more than one trace (or across traces in the same session), indicating a systemic behavior rather than a one-off?

Rank the labeled traces by `recoverable_cost` and keep only the ones worth fixing — a pattern with a low repeat count, a low outlier ratio on every metric, and no recoverable depth doesn't need a policy change. State explicitly which checks came back negative (duplication, loops, errors) and are NOT drivers, but never report a negative on those as "no waste found" while recoverable depth is material.

### Step 3: Propose Concrete Improvements

**3a. Draft a fix per confirmed driver.** For each pattern that survived Step 2, draft ONE specific, testable line to add to CLAUDE.md (project-level or global, whichever scope the pattern belongs to) or to strengthen in an existing skill. The fix must:

- Name the exact behavior to stop or change (not "be careful" — "stop after 2 identical tool calls with no new information")
- Cite the evidence during drafting (trace ID, repeat count, which metric(s) it's an outlier on, cost) so it can be shown to the user at the gate
- Prefer strengthening an existing rule over adding a new one, if the pattern is already partially covered (e.g., a "don't re-read after editing" rule exists but isn't being followed — reference it and ask whether it needs to be more prominent/explicit, rather than duplicating it)

**If a pattern doesn't map to a single clean rule** (e.g., it's a one-off bug in a specific automation script, not a recurring behavioral pattern), say so and recommend a code/config fix instead of a CLAUDE.md edit — not every finding should turn into a policy line.

**3b. Present the report and gate.** Present the full report (Output Format below) before writing any changes.

**GATE: user must approve each proposed diff individually before it is applied.** A user can approve some and reject others.

**3c. Apply and schedule follow-up.**

1. Apply only the approved diffs.
2. Record the audit's baseline numbers (which traces/sessions, which duplicate rates, which outlier ratios, which cost) somewhere durable — an ADR-style note, a todo, or a line in the relevant CLAUDE.md's changelog/history if one exists — so the next `/cost-audit` run can report whether the rate for that specific pattern actually dropped.
3. Tell the user when a reasonable follow-up check would be (e.g., "re-run this in ~1-2 weeks of usage" — not a fixed calendar promise, since it depends on usage volume, not time).

## Output Format

```markdown
# Cost Audit Report — [date range]

## Summary
- **Traces analyzed**: [N] (across [M] sessions)
- **Total cost in window**: $[X] — reconciles to tokens x rates within [X]% ([model(s)])
- **Where the money went**: context re-transmission [X]%, output [X]%, fresh input [X]% (from `token_economics.cost_shares`)
- **Recoverable**: $[X] of $[X] ([X]%) is context depth above the window median of [X]k tokens/call
- **Median context depth**: [X]k tokens/call | **tool calls per call**: [X] (band across traces: [X]-[X])
- **Negative checks**: duplicate calls [X]% of tool calls, error rate [X]% of cost-bearing observations, max repeat [N] — [state plainly that these are NOT the driver, if so]
- **Instrumentation**: [exporter_health warning, or "single exporter, clean"]

## Offenders

### [trace-id] (session [session-id]) — $[recoverable_cost] recoverable of $[cost]
- **Depth**: [X]k tokens/call vs median [X]k ([X]x) | **tool calls per call**: [X] (median [X])
- **Also outlier on**: [other metric(s)]: [value] vs median [value] ([X]x)
- **Pattern**: [classification from the Step 1c table]
- **Evidence**: [payload sizes from `payload_profile`, image/text split, duplicate `wasted_output_bytes`, or the tool/input from `drill`]
- **Root cause**: [what was actually happening]
- **Counterfactual**: at median depth this trace costs $[cost_at_median_depth]

[repeat per offender, max 5]

## Proposed Corrections

### 1. [target file: CLAUDE.md / skill name]
> [exact line(s) to add or change]

**Justification**: trace [id] (session [session-id]), [N] duplicate calls, [metric] [X]x median, $[cost] — [one-sentence causal link between the rule and the observed pattern]

[repeat per proposed diff]

## Findings With No Clean Policy Fix
- [pattern] in trace [id] — recommend [code/config fix] instead of a CLAUDE.md rule

## Follow-Up
- Baseline recorded: [where]
- Re-check when: [condition, e.g. "after ~2 weeks of active usage" or "next time a session exceeds $30"]
```

## Rules

### Required
- Every proposed correction cites a specific trace ID (and its session ID) and metric — no unsupported generalizations
- Classify (Step 1) and confirm impact (Step 2) before proposing any fix — never skip straight from "duplicate count is high" to a policy line
- Present the full report and get per-diff approval before writing any file
- Record a baseline so a future audit can verify the fix worked
- Report the negative checks (duplication, loops, errors) plainly when they are clean, without treating a clean result on them as a clean result overall
- Quote no dollar figure until `reconcile` matches within 5%, and name the assumed cache-write TTL whenever citing `cost_shares`

### Recommended
- Run after a noticeable cost spike, not just on a fixed schedule
- Keep the offender list short (≤5) — depth over breadth
- When a past `/cost-audit` correction exists, check whether the targeted pattern's rate actually dropped before looking for new offenders

## Acceptance Tests

| ID | Type | Prompt / Condition | Expected |
|----|------|--------------------|----------|
| CA-T1 | Positive | "Why is Claude Code so expensive this week?" | Skill triggers |
| CA-T2 | Positive | "Audit our Langfuse traces for wasted tokens" | Skill triggers |
| CA-T3 | Positive | "Check for retry loops in Claude's tool calls" | Skill triggers |
| CA-T4 | Negative | "How much did we spend on Claude Code last month?" | Does NOT trigger (-> plain usage lookup, no Langfuse root-causing needed) |
| CA-T5 | Negative | "Optimize this SQL query" | Does NOT trigger (-> /performance-guidelines or /debug) |
| CA-T6 | Boundary | "Set up Langfuse tracing for Claude Code" | Does NOT trigger — that's instrumentation setup, not an audit of existing data. Route to plugin installation instead. |
