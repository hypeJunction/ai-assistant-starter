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
- **Don't touch what isn't broken** — if cache-read percentage is already high (>95%) and input:output ratio is high only because of that caching, say so explicitly and leave it alone. This audit targets waste (duplication, loops, errors), not the inherent shape of agentic token usage.

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

This writes `trace_outliers.json`, `duplicate_tool_calls.json`, `tool_usage.json`, `error_pct.json`, `cache_read_pct.json`, and `session_sequences.json`:

1. `trace_outliers` — every **trace** (not session) that exceeds 2x the window's median on at least one of: cost, tool-call count, input tokens, output tokens. Each entry lists which metric(s) tripped and by what ratio. This is trace-first rather than session-first on purpose: a session aggregates many turns, so ranking by session cost buries a single runaway trace inside an otherwise-cheap session, and misses a trace that's a tool-call/token outlier without yet being a cost outlier.
2. `duplicate_tool_calls` — groups of `[traceId, tool, input]` where the exact same call happened more than once within one trace (a trace is the natural boundary for one turn/loop, tighter than grouping by the whole session)
3. `tool_usage` — histogram of every dispatched tool (`Bash`, `Edit`, `Skill`, `Agent`, `Workflow`, MCP tools, ...) by invocation count, share of total calls, trace count, and average duration. This is the entry point for tool/skill-churn questions ("what's actually being invoked, and how often") as distinct from `duplicate_tool_calls`, which only catches exact repeats. It carries no cost/token column on purpose: this histogram is read off Claude Code's own native `claude_code.tool` OTel span, which never attaches `totalCost` — that number only exists on the separate cost-bearing spans (`LLM Call`, `Tool: X`) emitted by the langfuse-observability plugin's hook. If both exporters are pointed at the same Langfuse project (compare `OTEL_EXPORTER_OTLP_ENDPOINT` in `settings.json` against the plugin's own endpoint config), every tool call is being traced twice — that duplication is itself worth surfacing as a finding, separately from any cost analysis. For cost impact, use `trace_outliers`/`duplicate_tool_calls`, which are built from the cost-bearing spans.
4. `error_pct` — error rate across observations
5. `cache_read_pct` — baseline caching health (context only; io_ratio can be derived from the same file's input/output token sums if needed)
6. `session_sequences` — every **session** with 2+ traces, traces ordered chronologically, flagged for patterns invisible to any single-trace view: the same `(tool, input)` signature repeated across separate traces in the session (`cross_trace_duplicates`), a jump in input tokens from one trace to the next without proportional new tool work (`context_growth`), and a trace with an error immediately followed by a retry on a pricier model tier (`escalation_after_failure`). A session only appears here if at least one of these three fired — this is explicitly the "does a prompt's cost trace back to something an earlier trace in the same session already established" check the trace-only view can't do.

**Skill-name limitation**: the OTel exporter records `Skill` as one generic tool name — it does not expose *which* skill was invoked (that argument lives only in the assistant's tool-call input, which this exporter drops). If `tool_usage` shows `Skill` at meaningful volume, cross-reference with local session transcripts (`~/.claude/projects/<project-slug>/*.jsonl`, one file per session) to break it down by name: grep each transcript for `"name":"Skill"` tool_use blocks and read the `input.skill` value. Do this only when `Skill` invocation count is itself high enough to be worth decomposing — otherwise note the limitation and move on.

**If `trace_outliers` is empty and no trace has a duplicate-call rate above 10% of its observations, and `session_sequences` is empty:** report "No significant waste patterns found" and stop — do not manufacture findings to justify the audit.

**1b. Shortlist candidates** (max 5 single-trace + max 3 session-level) from that output, prioritized by:

1. Traces flagged on 2+ metrics in `trace_outliers` (e.g. both tool-call count and output tokens) — these are the least ambiguous offenders
2. Traces where duplicate-call count / trace observation count > 15%
3. Remaining traces in `trace_outliers`, ranked by highest ratio-to-median on any single metric, with excess absolute cost as the tiebreak
4. From `tool_usage`, any tool whose `pct_of_calls` is disproportionate to what it should cost per call (e.g. `Bash`/`Edit`/`Read` dominating overall volume is normal agentic shape and not itself a finding, but a heavy `Agent`/`Workflow`/`Skill` dispatch *rate* relative to session count points at process-level churn — skills or subagents re-triggering — rather than a single stuck trace). Cross-reference the trace IDs in `trace_count` against `trace_outliers` before shortlisting; a high invocation count alone isn't evidence of cost impact for this metric (see the cost-attribution caveat above)

From `session_sequences`, shortlist a session (separately from the single-trace list above, capped at 3) when:

5. `cross_trace_duplicates` has a signature spanning 3+ traces, or its `trace_count` is a large share of the session's `trace_count` — a later trace paid to redo what an earlier trace in the same session had already done
6. `context_growth` shows an input-token ratio ≥3x with a tool-call ratio near 1 (i.e. cost grew from accumulated/repeated context, not from new work) — especially when it recurs across several trace-pairs in the session
7. `escalation_after_failure` appears at all — a failed trace immediately followed by a pricier-model retry in the same session is worth root-causing even at low volume, since it implies a fixable root cause was never addressed

`error_pct.json` is a window-wide aggregate only (total observations, error count, breakdown by level) — it has no per-trace or per-timestamp detail, so "traces with an error cluster" is not a criterion this data can support. Don't shortlist on it; if a shortlisted trace's `drill` output happens to show ERROR-level observations clustered in time, that's part of Step 1c's classification (Retry-after-error), not a Step 1b filter.

Drop everything below these — this step is about the worst offenders, not a full inventory. Note the sessionId alongside each shortlisted trace for context in the report, but keep classification and root-causing scoped to the trace.

**1c. Drill into each shortlisted trace** and assign it a pattern label:

```bash
python3 references/langfuse_queries.py drill --trace <traceId> --tool <toolName> --limit 5
```

This returns the input, an output preview, and the timestamp of each matching call. If every row shows `input: null`, that's almost always the generic `claude_code.tool`/`claude_code.tool.execution` wrapper span, not a real signal — those spans never populate `input`, `drill` excludes them by default, but they can still surface if `--tool` targets one directly. Re-run against the actual per-tool span name (observation names are prefixed, e.g. `Tool: Read` not `Read`) or read the session's local transcript for the real arguments before concluding anything about the pattern; null input on its own does not indicate a heartbeat/poll loop.

For a shortlisted **session** (from `session_sequences`), drill separately into each trace named in the relevant `cross_trace_duplicates`/`context_growth`/`escalation_after_failure` entry (same `drill --trace <id> --tool <toolName>` command, one call per trace) to confirm the two traces are doing what the aggregate implies — e.g. that a `cross_trace_duplicate` really is the same file/search re-fetched, not two coincidentally-identical short strings. When the aggregate alone doesn't make the causal story clear (most often for `escalation_after_failure`, since that needs to know *what* the error was and *why* the retry didn't just fix it), read the local transcript for that `sessionId` (`~/.claude/projects/<project-slug>/<sessionId>.jsonl`) around the two traces' timestamps — this is also the only way to confirm an "ignored correction" pattern, since Langfuse's OTel export doesn't reliably carry the user's verbatim wording.

| Pattern | Signature |
|---|---|
| Stuck poll / runaway loop | Same tool + same input repeated dozens to thousands of times with no error in between |
| Re-verification read | Same `Read` on a file immediately after an `Edit`/`Write` to that same file |
| Retry-after-error | Duplicate calls clustered around ERROR-level observations |
| Browser-automation retry | Duplicate `navigate`/`console_messages`/`close` calls without an intervening state change |
| Redundant context re-fetch | Same lookup (file, search, API call) repeated across a session with no code change in between |
| Skill/subagent over-dispatch | A skill or `Agent`/`Workflow` call fires repeatedly within a session (or across near-identical prompts) where one dispatch would cover the work — each re-fires the skill's full instruction body into context |
| Cross-trace redundant fetch | `session_sequences.cross_trace_duplicates`: a later trace in the session re-ran the same tool+input an earlier trace in that session already ran — the earlier trace's result could have been reused instead of re-fetched |
| Context bloat across turns | `session_sequences.context_growth`: input tokens jump sharply from one trace to the next in a session with no matching growth in tool-call count — cost is coming from re-sent/accumulated context (e.g. unpruned prior tool output), not new work |
| Escalation after failure | `session_sequences.escalation_after_failure`: a trace errors, and the very next trace in the session retries on a pricier model tier instead of the root cause getting fixed — the escalation pays for the same mistake twice |
| Ignored correction | A user correction in trace N (visible only in the local transcript, not Langfuse) is not reflected in trace N+M's behavior in the same session — the same wrong approach gets paid for twice. Only confirmable via transcript read, never from Langfuse aggregates alone |

Extend this list if a finding doesn't fit — don't force-fit a label.

### Step 2: Identify What Drives Cost or Loops

Not every classified pattern matters equally. For each labeled trace from Step 1c, connect the label to actual impact:

- **Metric impact**: which metric(s) does this trace's `outlier_reasons` list (cost, tool-call count, input tokens, output tokens), and does the pattern plausibly explain the excess (not just correlate)?
- **Loop severity**: is the repeat count large enough to indicate a runaway condition (hundreds to thousands) versus a handful of understandable retries?
- **Recurrence**: does the same pattern show up in more than one trace (or across traces in the same session), indicating a systemic behavior rather than a one-off?

Rank the labeled traces by this combined impact and keep only the ones worth fixing — a pattern with a low repeat count and a low outlier ratio on every metric doesn't need a policy change. State explicitly which healthy metrics (e.g., a high cache-read %) are NOT drivers and are being left alone.

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
- **Total cost in window**: $[X]
- **Baseline health**: cache-read [X]%, error rate [X]%, io_ratio [X]:1 (context only — not itself a finding)

## Offenders

### [trace-id] (session [session-id]) — outlier on [metric(s)]: [value] vs median [value] ([X]x)
- **Pattern**: [classification from the Step 1c table]
- **Evidence**: [tool name] called [N] times with identical input [describe input briefly]
- **Root cause**: [what was actually happening]

[repeat per offender, max 5]

## Cross-Trace Findings (session-level)

### session [session-id] — [pattern from the Step 1c table] across traces [trace-id-1] → [trace-id-2]
- **Evidence**: [signature/ratio/model-tier detail from `session_sequences.json`, e.g. "same `Read` on `path/to/file` repeated in 3 traces" or "input_tokens 4.1x from trace A to trace B with tool_call_ratio 1.0" or "trace A errored, trace B retried on opus"]
- **Root cause**: [what was actually happening — confirmed via `drill` and/or the local transcript]

[repeat per session-level finding, max 3; omit this section entirely if `session_sequences.json` produced no candidates worth root-causing]

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
- Always run `session_sequences` alongside the single-trace queries (part of the `all` invocation) — a trace-only audit misses waste that only shows up when comparing traces within the same session, and this step exists specifically to catch it
- A cross-trace finding (`cross_trace_duplicates`, `context_growth`, `escalation_after_failure`) gets the same root-cause treatment as a single-trace one — drill into the specific traces involved (or read the local transcript) before proposing a fix, never propose straight from the aggregate ratio
- Present the full report and get per-diff approval before writing any file
- Record a baseline so a future audit can verify the fix worked
- Explicitly state when caching/io_ratio numbers are healthy and out of scope, rather than flagging them as problems

### Recommended
- Run after a noticeable cost spike, not just on a fixed schedule
- Keep the offender list short (≤5 single-trace, ≤3 session-level) — depth over breadth
- When a past `/cost-audit` correction exists, check whether the targeted pattern's rate actually dropped before looking for new offenders
- When a cross-trace finding looks like an ignored user correction, confirm it by reading the local transcript rather than proposing a fix off the Langfuse aggregate alone — that pattern is the one Langfuse's own data is least equipped to confirm on its own

## Acceptance Tests

| ID | Type | Prompt / Condition | Expected |
|----|------|--------------------|----------|
| CA-T1 | Positive | "Why is Claude Code so expensive this week?" | Skill triggers |
| CA-T2 | Positive | "Audit our Langfuse traces for wasted tokens" | Skill triggers |
| CA-T3 | Positive | "Check for retry loops in Claude's tool calls" | Skill triggers |
| CA-T4 | Negative | "How much did we spend on Claude Code last month?" | Does NOT trigger (-> plain usage lookup, no Langfuse root-causing needed) |
| CA-T5 | Negative | "Optimize this SQL query" | Does NOT trigger (-> /performance-guidelines or /debug) |
| CA-T6 | Boundary | "Set up Langfuse tracing for Claude Code" | Does NOT trigger — that's instrumentation setup, not an audit of existing data. Route to plugin installation instead. |
| CA-T7 | Positive | "Is a prompt paying for context an earlier prompt in the same session already set up, in a way that could've been avoided?" | Skill triggers; agent runs `session_sequences` and reports cross-trace findings, not just single-trace outliers |
