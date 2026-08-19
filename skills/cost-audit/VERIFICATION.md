# Cost Audit — Verification Scenario

## Scenario

A developer notices their Claude Code spend jumped and asks: "Let's search Langfuse for problematic usage patterns driving high token usage, and recommend how to optimize." Their self-hosted Langfuse instance has been receiving traces via the `langfuse-observability` plugin for a few weeks.

**Invocation:** `/cost-audit`

## Expected Outcome

1. The agent runs `references/langfuse_queries.py all` and finds:
   - Cost concentrated in 3 sessions (69% of total spend)
   - One trace with 340 exact-duplicate calls to `Tool: Read` on the same `file_path`, spaced ~4 seconds apart, no errors nearby (`duplicate_tool_calls.json` already excludes the generic `claude_code.tool`/`claude_code.tool.execution` wrapper spans, so this count is real per-tool repeats, not instrumentation noise)
   - Two other whale sessions with duplicate Playwright `Tool: browser_navigate`/`Tool: browser_close`/`Tool: browser_console_messages` calls
2. The agent drills into the 340-duplicate trace with `--drill --tool Read`, sees timestamps ~4 seconds apart with the same `file_path` input and no adjacent errors, and classifies it as a **stuck poll / runaway loop** — not a retry-after-error.
3. The agent drills into the browser-automation sessions, sees repeated `navigate`→`console_messages`→`close` without an intervening code change, and classifies it as a **browser-automation retry** pattern.
4. The agent proposes two specific corrections, each citing the session ID and numbers:
   - A rule about polling loops needing a growing backoff or an explicit exit condition, backed by the exact session ID and repeat count
   - A reinforcement of the existing "stop after 2-3 failed browser actions and ask" guidance, since the trace shows it wasn't followed
5. The agent presents the full report and asks for approval **before** touching CLAUDE.md.
6. Only after approval does it edit CLAUDE.md, and it records the baseline (which session, which numbers) so a future audit can check whether the duplicate rate for that pattern actually dropped.

## Scenario 2 — clean pathology, expensive anyway

The harder case, and the one the first scenario cannot catch. Same invocation, different window (the 2026-08-19 reference window: 32 sessions, 30,678 observations, $288.92).

**What the queries return:**

- `duplicate_tool_calls` — 35 excess calls out of 6,342 tool calls (**0.55%**), maximum repeat count 4. No loops.
- `error_pct` — 192 errors, **1.06%** of cost-bearing observations. Healthy.
- `token_economics` — `cache_read_pct_of_input` 98.57%, `cost_shares.context_retransmission_pct` ~89%, `output_pct` ~11%.
- `exporter_health` — both exporters active, wrapper spans **41.2%** of observations, so every count-based rate needs the cost-bearing denominator.
- `trace_outliers` — the top trace runs at **128k** `context_depth_per_call` against a window median of **17k** (7.6x) with `tool_calls_per_call` of **0.27** against a median of **0.26**.
- `underuse_profile` — Bash is 63% of named tool calls, **zero** Grep/Glob, delegation at **0.04%** of tool calls.

**Expected outcome:** the agent reports duplication, loops and errors as negative, then reports **$204 of $288.92 (71%)** as recoverable depth. It classifies the top traces as **no context ceiling** — citing that `tool_calls_per_call` is flat across the window while depth varies 19x, so the same shape of work was done while carrying more context per call — plus **unbounded search payload** from `underuse_profile`. Proposed corrections target a context ceiling, routing search to Grep/Glob, and delegating wide reads. It does **not** conclude "no significant waste patterns found", and it does **not** attribute the cost to output tokens.

**Fails if:** the agent stops at the duplication/error checks, calls the 98.57% cache-read share healthy and moves on, ranks by ratio-to-median instead of `recoverable_cost`, or reports the error rate as 0.63% against the wrapper-inflated denominator.

## Key Checkpoints

| # | Checkpoint | What to verify |
|---|-----------|----------------|
| 1 | Agent runs the actual queries, doesn't guess | `references/langfuse_queries.py` is invoked (or an equivalent live query) — the agent does not fabricate session IDs or numbers |
| 2 | Agent root-causes before proposing a fix | The `drill` step runs for each shortlisted offender before Step 3; the agent does not jump from "high duplicate count" straight to a proposed rule |
| 3 | Findings distinguish loop vs. retry vs. re-read patterns | The report classifies each offender using the Step 1c table, not a single generic "wasteful" label |
| 4 | Every proposed correction cites evidence | Each diff in "Proposed Corrections" names a session ID and a number (repeat count or cost) |
| 5 | Approval gate before writing | CLAUDE.md/skill files are not modified until the user explicitly approves each proposed diff |
| 6 | Cache-read % is described, not used as a verdict | The agent reports the cache-read share as the cost *structure* and moves on to `cost_shares` and `context_depth_per_call`. It must neither treat a high cache-read % as evidence the window is healthy, nor flag it as a problem in itself |
| 7 | Depth is checked even when duplication is clean | `summary.total_recoverable_cost` is read and reported. "No significant waste patterns found" is only acceptable when all four stop conditions hold, including negligible recoverable depth |
| 8 | Dollar figures are reconciled | `reconcile.json` is checked before any cost is quoted; a `(null model)` row or a >5% delta is surfaced rather than ignored |
| 9 | Baseline recorded for follow-up | After applying an approved diff, the agent records the specific numbers so a later `/cost-audit` run can check whether the pattern's rate dropped |

## Anti-patterns

| Anti-pattern | Why it fails |
|-------------|-------------|
| Agent proposes "reduce token usage" as a CLAUDE.md line with no session evidence | Not actionable, not falsifiable, defeats the purpose of using trace data at all |
| Agent treats every duplicate-call group as the same pattern | A stuck poll and a retry-after-error need different fixes; conflating them produces a fix that doesn't address the actual cause |
| Agent edits CLAUDE.md before presenting the report | Removes the user's ability to reject a bad diff or point out missing context |
| Agent flags the 99%+ cache-read rate as a problem in itself | Caching is working as intended; the finding is never "you have cache reads", it is how deep the context being re-read is |
| Agent cites a high cache-read % as evidence the window is healthy and stops | Inverts the metric. Cache read + cache write is typically ~85-90% of spend, so a high cache-read share locates the cost, it does not clear it. The old `cache_read_pct` pinned at ~99.99% on every window regardless of quality, which is why it was replaced by `token_economics` |
| Agent concludes "no significant waste patterns found" because duplication, loops and errors are all clean | These three are frequently clean while most of the window's tokens are context depth. On the 2026-08-19 reference window duplicates were 0.55% of tool calls and errors ~1%, yet 71% of spend was recoverable depth |
| Agent explains an expensive trace as "reasoning-heavy work" from its output-token count | Output is ~10-11% of cost. Attributing spend to output while ignoring the ~89% in context re-transmission misreads the cost structure — check `cost_shares` before making this claim |
| Agent ranks offenders by ratio-to-median instead of `recoverable_cost` | A median-multiple rule on a heavy-tailed distribution flags the tail by construction; it identifies the biggest traces, not the ones with money on the table |
| Agent skips the drill-down and proposes a fix straight from the duplicate-count table | Produces generic, unfalsifiable advice instead of a targeted rule |
| Agent doesn't record a baseline | Makes it impossible for a future audit to say whether the fix worked, turning this into a one-off report instead of a self-correcting loop |
