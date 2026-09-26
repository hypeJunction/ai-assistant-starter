---
name: pivot
description: Explicitly pause the current thread of work and re-enter Plan Mode for a new direction.
category: process
model: sonnet
effort: low
triggers:
  - let's pivot
  - new direction
  - switch tasks
  - different task now
  - scrap that, let's do
---

# Pivot

> **Purpose:** Force a fresh Plan Mode cycle for a new direction instead of continuing with direct edits.
> **Usage:** `/pivot [new direction]`

## Constraints

- **Never make direct edits for the new direction without going through Plan
  Mode first** — that's this skill's entire reason to exist. If you catch
  yourself about to `Edit`/`Write`/run a mutating `Bash` command for the new
  topic before `EnterPlanMode` has been called, stop and call it first.
- **Pause, don't discard.** This skill never reverts, stashes, or comments on
  work already done for the prior thread — it only shifts what happens next.
  If the user wants the prior work rolled back too, that's a separate,
  explicit ask.
- This is the manual counterpart to `prompt-context-router`'s automatic
  post-plan-pivot check (see Related Skills) — use it whenever that
  automatic detection might miss a pivot, or to force one proactively.

## Workflow

### Step 1: Acknowledge the Pause

One short line — no recap of what was done, just that the thread is
pausing:

```markdown
Pausing the current thread — moving to a new direction.
```

### Step 2: Determine the New Direction

If the user supplied it inline (e.g. `/pivot let's redo the auth flow
instead`), use it as-is. Otherwise ask:

```markdown
What's the new direction?
```

**Wait for user response.**

### Step 3: Enter Plan Mode

Call `EnterPlanMode`, then proceed with the normal Plan Mode phases
(explore → design → review → final plan → `ExitPlanMode`) for the new
direction, exactly as if the user's next message had triggered Plan Mode
directly.

## Related Skills

- `prompt-context-router` — the background enforcement hook that does this
  automatically: once a plan has been approved and implemented in the
  session, a follow-up prompt that looks like a pivot gets denied once with
  instructions to call `EnterPlanMode` again
  (`PROMPT_CONTEXT_ROUTER_POST_PLAN_PIVOT_MODE`, default `enforce`). `/pivot`
  is the explicit, user-invoked version of the same behavior.
- `plan` — the phased workflow this skill hands off to in Step 3.
