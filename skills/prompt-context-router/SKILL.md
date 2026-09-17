---
name: prompt-context-router
description: Runtime enforcement hook that classifies each incoming prompt by task class and topic-pivot, then advises the assistant to treat clear asides as standalone (and delegate cheap ones to a subagent), and to consider entering Plan Mode for architecture/extreme-scope prompts — denying the first extreme-scope prompt per session outright. Auto-loaded for every user prompt.
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
| any of the above | yes (`"plan"`) | Silent — already there |
| `mechanical` / `implementation` / `debugging` | (n/a) | No plan-mode guidance — only the pivot axis applies |

This hook only ever adds `additionalContext` or, for that one exception,
denies the prompt — pure advisory otherwise, matching
`context-circuit-breaker`'s warn-only precedent. When both axes fire (e.g. a
pivot *and* an architecture-classified prompt), both notes are concatenated
into one `additionalContext` string — neither is dropped.

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
`.claude/settings.json`):

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "*",
        "hooks": [{ "type": "command", "command": "node .claude/skills/prompt-context-router/references/hook.js" }]
      }
    ]
  }
}
```

Install via `/apply-template`'s opt-in hook-install step, or add this
snippet by hand.

## Configuration

| Env var | Default | Meaning |
|---|---|---|
| `PROMPT_CONTEXT_ROUTER_EXTREME_MODE` | `enforce` | `enforce` denies the first `extreme`-classified prompt per session (then downgrades to advisory); `warn-only` never denies, always advisory-only |

## What This Does Not Do

- **Doesn't reduce tokens sent to the model.** It cannot remove prior turns
  from the context window — only `additionalContext` can be added, nothing
  can be subtracted.
- **Not a model router.** It doesn't touch `/model` or `/effort` — for
  automatic model-tier routing on prompt submission, see the
  `claude-model-router-hook` option in `docs/cost-optimization.md`.
- **Mostly stateless.** The pivot/task-class classification itself is
  stateless, per-prompt only. The one exception is the `extreme` deny gate,
  which tracks a single "already nudged this session" flag in a tmpdir file
  keyed by `session_id` — enough to avoid re-denying every continuation
  prompt of an already-approved extreme-scope task, nothing more (no rolling
  "current topic" fingerprint).
- **Can't set `permission_mode` itself.** It's a read-only input field to
  hooks — this hook can only deny a prompt or add `additionalContext`
  suggesting the assistant call `EnterPlanMode`; it can never flip the mode
  directly.

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
