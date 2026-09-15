# Cost Optimization

This project's `CLAUDE.md` includes a **Task Classification** table (model-tier
routing) as an advisory rule. That's option B of three levers described in
full in the canonical reference:

**[ai-assistant-starter/docs/cost-optimization.md](https://github.com/hypefi/ai-assistant-starter/blob/main/docs/cost-optimization.md)**

That doc covers, in order of setup cost:

1. **Command-level filtering** — a `PreToolUse` hook that rewrites noisy Bash
   commands (verbose `git status`, full `git log`, etc.) before they reach
   the model.
2. **Model-tier routing** — the table already in this file's `CLAUDE.md`, plus
   two stronger options: a `dispatch` subagent (one Markdown file, no hooks),
   or a real classifier hook
   ([`claude-model-router-hook`](https://github.com/tzachbon/claude-model-router-hook))
   that scores and auto-routes every prompt/subagent spawn.
3. **Context and process hygiene** — already folded into this `CLAUDE.md`
   under "Context & Process Hygiene."

If you want the filtering hook or the automatic router, they're not
installed by `/apply-template` — it only wires the advisory rules into
`CLAUDE.md`. Follow the canonical doc's "Getting started" section to add
either one; they involve adding hooks/settings.json entries that touch your
actual tool execution path, and shouldn't be installed silently.

## Runtime circuit breaker

`/apply-template` *does* offer one hook directly, as an explicit opt-in step
(Step 5.5): `context-circuit-breaker`, a `PreToolUse` hook that warns —
never blocks — on subagent fan-out (many `Agent`/`Task` spawns in a short
window) and expensive-call loops (the same tool called repeatedly with
near-identical or oversized input). See
`skills/context-circuit-breaker/SKILL.md` for the exact thresholds and what
it does and doesn't do. This is a live, per-session warning layer,
complementary to the after-the-fact analysis that `cost-audit` and
`session-retro` already provide from trace/transcript data.
