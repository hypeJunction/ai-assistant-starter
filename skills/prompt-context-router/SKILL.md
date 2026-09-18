---
name: prompt-context-router
description: Runtime enforcement hook that classifies each incoming prompt by task class and topic-pivot, then advises the assistant to treat clear asides as standalone (and delegate cheap ones to a subagent), to consider entering Plan Mode for architecture/extreme-scope prompts — denying the first extreme-scope prompt per session outright, with an opt-in extension to pivot+architecture — flags when a short prompt is riding on a disproportionately large accumulated context, warns when a turn is likely to miss the prompt cache due to elapsed time, flags when a pivot lands on a large accumulated context, and (with a companion PostToolUse hook) denies a pivot away from a plan that was just implemented until EnterPlanMode is called again. Auto-loaded for every user prompt.
category: enforcement
user-invocable: false
---

# Prompt Context Router

Runtime `UserPromptSubmit` hook for Claude Code. Classifies the incoming
prompt on two independent axes — task class and topic-pivot — and, when
useful, injects `additionalContext`, or (only for the first extreme-scope
prompt in a session) denies the prompt outright to force a Plan Mode check.

## Why this exists

A long session accumulates context: prior exploration, file reads, plan
discussion. When the user pivots to an unrelated aside or a quick question,
Claude Code still carries the full accumulated transcript into that turn —
a hook cannot truncate history already in the context window. What it *can*
do is classify the prompt and nudge the assistant's own behavior: answer a
clear aside standalone instead of re-deriving it from the whole prior
thread, and — for cheap, self-contained asides — suggest delegating it to a
subagent so its tool calls happen off the main thread instead of adding to
it.

## Classification

**Task class** — the same mechanical/implementation/debugging/architecture/
extreme/abstain taxonomy already used for model-tier routing (see
`CLAUDE.md`'s Task Classification table), reapplied via keyword/structural
heuristics. This is intentionally the same taxonomy, not a second one.

**Pivot** — does the prompt look like a standalone aside rather than a
continuation of the immediately preceding turn? Signals: explicit aside
markers ("quick question", "btw", "unrelated", "separately"), absence of
continuation pronouns ("it", "that", "this") tied to prior context, absence
of file/symbol references, and short prompt length. This is a heuristic,
not a precise classifier — false negatives (missing a real pivot) are fine;
it only needs to catch the clear cases.

## What It Outputs (pivot axis)

| Pivot? | Task class | `additionalContext` |
|---|---|---|
| No | any | none — stays silent |
| Yes | mechanical / implementation | Treat as standalone; consider delegating to the `dispatch` subagent |
| Yes | debugging / architecture / extreme | Flag as a pivot, but recommend verifying whether it still depends on the current plan/branch before treating it as standalone |
| Yes | abstain | Treat as standalone (no delegation suggestion — task shape unclear) |

## Plan Mode Guidance (task-class axis, independent of pivot)

A hook cannot set `permission_mode` itself — it's a read-only input field
(see [code.claude.com/docs/en/hooks](https://code.claude.com/docs/en/hooks)) —
so this is advisory except for one deliberate exception:

| Task class | `permission_mode` already `"plan"`? | Output |
|---|---|---|
| `abstain` | no | `additionalContext` pointing at `context-disambiguation` — ask a clarifying question before pulling in broad context |
| `architecture` | no | `additionalContext` suggesting the assistant call `EnterPlanMode` — matches the `plan` skill's phased workflow |
| `extreme`, first time this session | no | `permissionDecision: "deny"` — forces engagement before proceeding (see "Relationship to other skills" below) |
| `extreme`, any later prompt this session | no | Downgrades to the same `additionalContext` nudge as `architecture` — never denies twice |
| `architecture` **and** pivot | no | Strengthened `additionalContext` wording (a pivot into architecture scope has less contextual justification than an in-thread request). With `PROMPT_CONTEXT_ROUTER_PIVOT_ARCHITECTURE_MODE=enforce` (opt-in, default off), also extends the one-per-session deny pattern to this case, using its own independent session-state key |
| `extreme` **and** pivot | no | Same strengthened wording layered on top of the existing `extreme` deny/downgrade behavior (unchanged mechanics, stronger text) |
| any of the above | yes (`"plan"`) | Silent — already there |
| `mechanical` / `implementation` / `debugging` | (n/a) | No plan-mode guidance — only the pivot axis applies |

This hook only ever adds `additionalContext` or, for those exceptions,
denies the prompt — pure advisory otherwise, matching
`context-circuit-breaker`'s warn-only precedent. When multiple axes fire
(e.g. a pivot *and* an architecture-classified prompt), all applicable notes
are concatenated into one `additionalContext` string — neither is dropped.

## Context Ballast Advisory (fourth, independent axis)

The live counterpart to `/cost-audit`'s `prompt_context_mismatch` and
`/session-retro`'s `prompt_context_outliers` — same signal (a short new
prompt riding on a disproportionately large paid context), checked at submit
time instead of after the fact. Runs independently of task class and pivot;
any of the four axes can fire together, and their `additionalContext`
strings are concatenated, none dropped.

**How it's computed:** the hook estimates this prompt's size (chars/4, no
tokenizer available) and, if that's small (`<=300` est. tokens), tails
`input.transcript_path` (the session's own local `.jsonl`) for the last
main-loop (non-sidechain) assistant message's `usage.cache_read_input_tokens`
+ `usage.cache_creation_input_tokens` + `usage.input_tokens` — the same
fresh-input + cache-read + cache-write total `_context_tokens()` computes on
the Langfuse side. If that total is at least 20,000 tokens **and** at least
5x the prompt's own estimated size, it adds an `additionalContext` note
suggesting the next step run in a subagent, or that a `/clear` checkpoint is
due.

**Why this can only ever advise:** a hook cannot remove tokens already
committed to the context window — it can only shape what the assistant does
with the *next* turn, same limitation as the rest of this hook.

**Why the tail read, not the full transcript:** this hook runs on every
single prompt submit, so parsing a multi-MB session history in full each
time would add real latency to every turn. Reading the last 256KB is enough
to reach the most recent assistant usage line in practice; if the tail slice
happens to start mid-JSON, that one line just fails to parse and is skipped.

**Cross-reference with the pivot axis:** when a prompt is both a pivot and
sitting on `>=20,000` accumulated context tokens (independently configurable
from the ratio-based ballast check above, since a pivot has no "prompt is
short" precondition), the plain pivot message from the table above is left
completely unchanged, and a second, separate note is concatenated after it
suggesting subagent delegation or a `/clear` checkpoint. The two are kept as
distinct sentences rather than merged into one, since they're independently
actionable signals (treat-as-standalone vs. the thread itself being
expensive) and merging them risked drifting the plain pivot wording that
PCR-T2/T3 assert exactly.

## Cache TTL-Miss Warning (fifth, additive axis)

Anthropic's prompt cache expires after a TTL — 5 minutes by default, up to
1 hour on extended-cache sessions. This hook cannot see which TTL was
actually requested on the prior API call (only cache-read/cache-write usage
counters are visible in the transcript, no TTL metadata), so it compares the
wall-clock gap since the last main-loop assistant message's `timestamp`
against an operator-configured assumption
(`PROMPT_CONTEXT_ROUTER_CACHE_TTL_SECONDS`, default 300s). If that gap has
likely exceeded the TTL and the accumulated context is large enough to
matter (`>=20,000` tokens by default), it adds an `additionalContext` note
that this turn is about to pay full/cache-write pricing due to timing, not
prompt content — purely informational, distinct from the ballast and pivot
axes, and never interacts with the deny path.

Operators on a 1-hour extended-cache session should set
`PROMPT_CONTEXT_ROUTER_CACHE_TTL_SECONDS=3600` to match; the default (300s)
assumes the standard short-lived cache.

## Post-Plan Pivot Guard (seventh, independent axis)

Catches the specific failure this hook was originally missing: a plan gets
approved and implemented, then the user makes a follow-up remark that's a
genuine pivot to a new direction — and instead of a fresh Plan Mode cycle,
direct edits continue immediately. This axis is independent of task class
(a pivot away from a just-shipped plan warrants re-planning regardless of
how risky the new direction's keywords look) and is checked *before* the
task-class-based Plan Mode guidance above.

`hook.js` alone can't detect this — `UserPromptSubmit` has no view into tool
calls made between prompts. A companion `PostToolUse` hook,
`post-tool-hook.js` (same directory), watches for `ExitPlanMode` (starts a
fresh cycle) followed by a mutating tool call — `Edit`, `Write`,
`NotebookEdit`, or `Bash` (marks `implementedSincePlan: true`) — and writes
that into the same tmpdir state file `hook.js` already reads for its
`extremeNudged`/`architecturePivotNudged` flags.

When `hook.js` then sees a pivot-shaped prompt with `implementedSincePlan`
set, it applies the identical one-shot-per-cycle deny pattern used for
`extreme` (its own `postPlanPivotNudged` key, reset whenever `ExitPlanMode`
fires again — so a later, unrelated pivot in a new plan cycle gets checked
fresh). Unlike the other opt-in enforce modes in this hook, this one
**defaults to `enforce`**, not `warn-only` — silently continuing with direct
edits after a pivot is exactly the failure mode this check exists to catch.
Set `PROMPT_CONTEXT_ROUTER_POST_PLAN_PIVOT_MODE=warn-only` to soften it to
advisory-only.

The explicit, user-invoked counterpart to this automatic check is `/pivot` —
use it to force the same Plan Mode re-entry when the automatic detection
might miss a pivot, or proactively.

## Relationship to Other Skills

This hook deliberately points at existing skills instead of reimplementing
their guidance:

- **`context-disambiguation`** already owns "ambiguous prompt → ask a
  clarifying question instead of broad exploration." The `abstain` task
  class is exactly that skill's trigger condition, so the `abstain` nudge
  defers to it rather than suggesting Plan Mode directly.
- **`plan`** documents the phased workflow (Explore → Design → Review →
  Final Plan → `ExitPlanMode`) that real Plan Mode is meant to run inside.
  The `architecture`/`extreme` nudges point at calling `EnterPlanMode`
  specifically because that's what actually engages this phased workflow
  with harness enforcement — unlike `/plan`'s prose-only, instruction-driven
  version of the same idea.

## Installation

Add to your Claude Code settings (`~/.claude/settings.json` or project
`.claude/settings.json`). Both hooks share the same tmpdir state file, so
install both — `post-tool-hook.js` alone is silent, and without it
`hook.js`'s post-plan-pivot axis never has `implementedSincePlan` set:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "*",
        "hooks": [{ "type": "command", "command": "node .claude/skills/prompt-context-router/references/hook.js" }]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "ExitPlanMode",
        "hooks": [{ "type": "command", "command": "node .claude/skills/prompt-context-router/references/post-tool-hook.js" }]
      },
      {
        "matcher": "Edit",
        "hooks": [{ "type": "command", "command": "node .claude/skills/prompt-context-router/references/post-tool-hook.js" }]
      },
      {
        "matcher": "Write",
        "hooks": [{ "type": "command", "command": "node .claude/skills/prompt-context-router/references/post-tool-hook.js" }]
      },
      {
        "matcher": "NotebookEdit",
        "hooks": [{ "type": "command", "command": "node .claude/skills/prompt-context-router/references/post-tool-hook.js" }]
      },
      {
        "matcher": "Bash",
        "hooks": [{ "type": "command", "command": "node .claude/skills/prompt-context-router/references/post-tool-hook.js" }]
      }
    ]
  }
}
```

Install via `/apply-template`'s opt-in hook-install step (Step 5.8, installs
both hooks together), or add this snippet by hand.

## Configuration

| Env var | Default | Meaning |
|---|---|---|
| `PROMPT_CONTEXT_ROUTER_EXTREME_MODE` | `enforce` | `enforce` denies the first `extreme`-classified prompt per session (then downgrades to advisory); `warn-only` never denies, always advisory-only |
| `PROMPT_CONTEXT_ROUTER_BALLAST_FACTOR` | `5.0` | Min `context_tokens / prompt_est_tokens` ratio to trigger the context ballast advisory — same default as `/cost-audit`'s `--prompt-context-factor` |
| `PROMPT_CONTEXT_ROUTER_BALLAST_MIN_TOKENS` | `20000` | Min accumulated context tokens (from the last main-loop assistant message) for a prompt to be eligible for the ballast advisory — same default as `/cost-audit`'s `--prompt-context-min-tokens` |
| `PROMPT_CONTEXT_ROUTER_PIVOT_CONTEXT_MIN_TOKENS` | `20000` | Min accumulated context tokens for a pivot to also get the pivot+ballast cross-reference note, independent of the ratio-based ballast check |
| `PROMPT_CONTEXT_ROUTER_CACHE_TTL_SECONDS` | `300` | Assumed cache TTL in seconds; elapsed time since the last main-loop assistant message beyond this triggers the TTL-miss advisory. Set to `3600` for extended-cache (1hr) sessions |
| `PROMPT_CONTEXT_ROUTER_CACHE_TTL_MIN_TOKENS` | `20000` | Min accumulated context tokens for the TTL-miss advisory to be worth surfacing |
| `PROMPT_CONTEXT_ROUTER_PIVOT_ARCHITECTURE_MODE` | `warn-only` | `enforce` extends the one-per-session deny pattern (normally exclusive to `extreme`) to pivot+`architecture` prompts too, using an independent session-state key; `warn-only` never denies for this case, advisory only |
| `PROMPT_CONTEXT_ROUTER_POST_PLAN_PIVOT_MODE` | `enforce` | `enforce` denies a pivot-shaped prompt once per plan cycle when `post-tool-hook.js` has recorded `implementedSincePlan: true` (then downgrades to advisory until the next `ExitPlanMode`); `warn-only` never denies, always advisory-only |

## What This Does Not Do

- **Doesn't reduce tokens sent to the model.** It cannot remove prior turns
  from the context window — only `additionalContext` can be added, nothing
  can be subtracted. The context ballast advisory is no exception: it can
  flag that this turn is about to re-pay a large accumulated context, not
  shrink it.
- **Ballast estimate is approximate.** `prompt_est_tokens` is chars/4, not a
  real tokenizer count, and the transcript's own `usage.input_tokens` field
  is not always populated on every line — the advisory leans on
  `cache_read_input_tokens`/`cache_creation_input_tokens`, which are the
  reliable part of that total, same caveat the audit-side scripts document.
- **Not a model router.** It doesn't touch `/model` or `/effort` — for
  automatic model-tier routing on prompt submission, see the
  `claude-model-router-hook` option in `docs/cost-optimization.md`.
- **Mostly stateless.** The pivot/task-class classification itself is
  stateless, per-prompt only. The exceptions are the `extreme` deny gate and
  the post-plan-pivot gate, each tracking a single "already nudged" flag
  (session-scoped for `extreme`, plan-cycle-scoped — reset on the next
  `ExitPlanMode` — for post-plan-pivot) in a tmpdir file keyed by
  `session_id`. Neither tracks a rolling "current topic" fingerprint or the
  actual content of the approved plan — `implementedSincePlan` only knows
  *that* a mutating tool ran after `ExitPlanMode`, not whether it matched the
  plan's scope.
- **Post-plan-pivot detection needs the companion `PostToolUse` hook
  installed too.** `hook.js` alone never sees tool calls between prompts —
  without `post-tool-hook.js` wired in, `implementedSincePlan` never becomes
  true and this axis never fires (silently, not an error).
- **Can't set `permission_mode` itself.** It's a read-only input field to
  hooks — this hook can only deny a prompt or add `additionalContext`
  suggesting the assistant call `EnterPlanMode`; it can never flip the mode
  directly.
- **TTL-miss detection assumes a configured value, it doesn't observe the
  real one.** Anthropic's transcript usage fields report cache-read/
  cache-write token counts, not which TTL (5min vs 1hr extended) was
  actually requested on a given call — this hook can only compare elapsed
  time to an operator-set assumption (`PROMPT_CONTEXT_ROUTER_CACHE_TTL_SECONDS`),
  which will be wrong if that assumption doesn't match actual usage.

## Acceptance Tests

| ID | Condition | Expected |
|----|-----------|----------|
| PCR-T1 | Prompt continues the current thread (contains "it"/"that" tied to context, or references a file/symbol) | Silent, no `additionalContext` |
| PCR-T2 | Short prompt, mechanical-shaped ("what version is X"), no continuation pronouns | `additionalContext` suggesting standalone treatment + dispatch delegation |
| PCR-T3 | Short prompt, debugging-shaped ("this crashes with a stack trace") with an aside marker | `additionalContext` flagging the pivot but recommending it stay in the main thread |
| PCR-T4 | Empty or whitespace-only prompt | Silent, no output |
| PCR-T5 | `abstain`-classified prompt, `permission_mode` not `"plan"` | `additionalContext` pointing at `context-disambiguation` |
| PCR-T6 | `architecture`-classified prompt, `permission_mode` not `"plan"` | `additionalContext` suggesting `EnterPlanMode` |
| PCR-T7 | First `extreme`-classified prompt in a session, `PROMPT_CONTEXT_ROUTER_EXTREME_MODE=enforce` (default) | `permissionDecision: "deny"`, session flag written to tmpdir |
| PCR-T8 | Second `extreme`-classified prompt in the same session | `additionalContext` only, never denies again |
| PCR-T9 | Any of the above with `permission_mode: "plan"` already set | Silent — no plan-mode guidance at all |
| PCR-T10 | `extreme`-classified prompt, `PROMPT_CONTEXT_ROUTER_EXTREME_MODE=warn-only` | `additionalContext` only, never denies |
| PCR-T11 | Short prompt (`<=300` est. tokens), `transcript_path` tail shows a last main-loop assistant message with `cache_read_input_tokens` + `cache_creation_input_tokens` >= 20,000 and >= 5x the prompt's estimated size | `additionalContext` context-ballast advisory, concatenated with any other axis that also fired |
| PCR-T12 | Short prompt, but the last main-loop assistant message's accumulated context is below 20,000 tokens or below the 5x ratio | No context-ballast `additionalContext` (other axes may still fire independently) |
| PCR-T13 | Prompt itself is long (`>300` est. tokens), regardless of accumulated context | No context-ballast `additionalContext` — only short prompts are eligible |
| PCR-T14 | `transcript_path` missing, unreadable, or the last main-loop assistant message has no `usage` | Silent on this axis (fail-open), no crash |
| PCR-T15 | Last main-loop assistant `timestamp` is older than `PROMPT_CONTEXT_ROUTER_CACHE_TTL_SECONDS` ago, `contextTokens >= PROMPT_CONTEXT_ROUTER_CACHE_TTL_MIN_TOKENS` | `additionalContext` TTL-miss advisory fires |
| PCR-T16 | Same as PCR-T15 but `contextTokens` below the min | No TTL-miss `additionalContext` |
| PCR-T17 | Last main-loop assistant `timestamp` within the TTL window | No TTL-miss `additionalContext` |
| PCR-T18 | `timestamp` field missing/unparseable on the last main-loop assistant message | Silent on this axis (fail-open), no crash |
| PCR-T19 | Pivot-shaped prompt, `contextTokens >= PROMPT_CONTEXT_ROUTER_PIVOT_CONTEXT_MIN_TOKENS` | Today's plain pivot `additionalContext` (PCR-T2/T3 wording, unchanged) plus a second, separate pivot+context note concatenated after it |
| PCR-T20 | Pivot-shaped prompt, `contextTokens` below `PROMPT_CONTEXT_ROUTER_PIVOT_CONTEXT_MIN_TOKENS` | Only today's plain pivot `additionalContext` — no second note |
| PCR-T21 | Pivot-shaped prompt classified `architecture`, `permission_mode` not `"plan"`, `PROMPT_CONTEXT_ROUTER_PIVOT_ARCHITECTURE_MODE=warn-only` (default) | Strengthened `additionalContext` wording, never denies |
| PCR-T22 | Same as PCR-T21 but `PROMPT_CONTEXT_ROUTER_PIVOT_ARCHITECTURE_MODE=enforce`, first occurrence this session | `permissionDecision: "deny"`, independent `architecturePivotNudged` state key written (doesn't affect `extremeNudged`) |
| PCR-T23 | Same as PCR-T22, second occurrence in the same session | Downgrades to the strengthened `additionalContext`, never denies again |
| PCR-T24 | `post-tool-hook.js` receives `tool_name: "ExitPlanMode"`, then `tool_name: "Edit"`, same `session_id`; `hook.js` then receives a pivot-shaped prompt, `permission_mode` not `"plan"`, `PROMPT_CONTEXT_ROUTER_POST_PLAN_PIVOT_MODE=enforce` (default) | `permissionDecision: "deny"`, checked and returned before the task-class-based Plan Mode guidance; `postPlanPivotNudged` written to the shared state file |
| PCR-T25 | Same session state as PCR-T24, a second pivot-shaped prompt | Downgrades to `additionalContext` only, never denies again — until the next `ExitPlanMode` resets the flag |
| PCR-T26 | `post-tool-hook.js` receives `tool_name: "ExitPlanMode"` only (no mutating tool call yet); `hook.js` then receives a pivot-shaped prompt | Silent on this axis — `implementedSincePlan` is still false |
| PCR-T27 | `implementedSincePlan: true` in state, but the incoming prompt is not pivot-shaped | Silent on this axis regardless of state |
| PCR-T28 | Same as PCR-T24 but `permission_mode: "plan"` already set | Silent — no post-plan-pivot guidance while already in Plan Mode |
| PCR-T29 | Same as PCR-T24 but `PROMPT_CONTEXT_ROUTER_POST_PLAN_PIVOT_MODE=warn-only` | `additionalContext` only, never denies |
| PCR-T30 | `post-tool-hook.js` receives an unrelated `tool_name` (e.g. `Read`, `Grep`) | No state change — `implementedSincePlan` untouched |
