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

## Key Checkpoints

| # | Checkpoint | What to verify |
|---|-----------|----------------|
| 1 | Agent runs the actual queries, doesn't guess | `references/langfuse_queries.py` is invoked (or an equivalent live query) — the agent does not fabricate session IDs or numbers |
| 2 | Agent root-causes before proposing a fix | The `drill` step runs for each shortlisted offender before Step 3; the agent does not jump from "high duplicate count" straight to a proposed rule |
| 3 | Findings distinguish loop vs. retry vs. re-read patterns | The report classifies each offender using the Step 1c table, not a single generic "wasteful" label |
| 4 | Every proposed correction cites evidence | Each diff in "Proposed Corrections" names a session ID and a number (repeat count or cost) |
| 5 | Approval gate before writing | CLAUDE.md/skill files are not modified until the user explicitly approves each proposed diff |
| 6 | Healthy metrics are called out, not flagged | If cache-read % is high (as in this scenario), the agent states it's healthy and out of scope rather than including it as a finding |
| 7 | Baseline recorded for follow-up | After applying an approved diff, the agent records the specific numbers so a later `/cost-audit` run can check whether the pattern's rate dropped |

## Anti-patterns

| Anti-pattern | Why it fails |
|-------------|-------------|
| Agent proposes "reduce token usage" as a CLAUDE.md line with no session evidence | Not actionable, not falsifiable, defeats the purpose of using trace data at all |
| Agent treats every duplicate-call group as the same pattern | A stuck poll and a retry-after-error need different fixes; conflating them produces a fix that doesn't address the actual cause |
| Agent edits CLAUDE.md before presenting the report | Removes the user's ability to reject a bad diff or point out missing context |
| Agent flags the 99%+ cache-read rate as a problem | Confuses healthy caching behavior with waste; wastes the user's attention on something that isn't broken |
| Agent skips the drill-down and proposes a fix straight from the duplicate-count table | Produces generic, unfalsifiable advice instead of a targeted rule |
| Agent doesn't record a baseline | Makes it impossible for a future audit to say whether the fix worked, turning this into a one-off report instead of a self-correcting loop |
