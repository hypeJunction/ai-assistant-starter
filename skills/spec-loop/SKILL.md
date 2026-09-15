---
name: spec-loop
description: Scope-locked implementation loop that gets a written file-scope contract approved before any code changes, then self-checks every commit's diff against that contract. Use for autonomous or long-running implementation work where unrequested changes (extra selectors, extra commits, extra refactors) would be expensive to catch after the fact.
category: process
model: sonnet
effort: medium
triggers:
  - work within scope
  - don't change anything else
  - lock the scope
  - contract-first
  - spec-first
  - autonomous implementation
---

# Spec Loop

> **Purpose:** Enforce an explicit, approved scope boundary before implementation, then verify every commit stays inside it
> **Phases:** Baseline → Contract → Failing Tests → Implement → Self-Check → Report
> **Usage:** `/spec-loop <task description>`

## Iron Laws

1. **NO IMPLEMENTATION BEFORE THE CONTRACT IS APPROVED** — Write the contract, show it, wait for explicit approval. Do not touch production code first.
2. **EVERY COMMIT IS CHECKED AGAINST THE CONTRACT** — Before committing, diff the changed files against `ALLOWED_FILES` and the `FORBIDDEN` list. A violation means stop and report, not commit-and-explain.
3. **A GUESSED CONVENTION IS AN OPEN QUESTION, NOT A DECISION** — If no precedent exists in the codebase for how to do something, it goes in `OPEN_QUESTIONS` for the user to resolve, not into the contract as an assumption.

## When to Use

- Long or autonomous implementation runs where you won't be reviewing every step
- Tasks with a history of scope creep (unrequested selectors, extra commits, unrelated refactors)
- Work where "do exactly this, nothing else" matters more than speed

## When NOT to Use

- Small, fully-supervised edits where you're reviewing every diff live → `/implement`
- Test-first feature work without a scope-creep problem → `/tdd`
- Pure refactors with no new behavior → `/refactor`

> **Note:** Command examples use `npm` as default. Adapt to the project's package manager per `ai-assistant-protocol` — Project Commands.

## Gate Enforcement

See `ai-assistant-protocol` for valid approval terms and invalid responses.

---

## Phase 1: Baseline

Run typecheck, lint, and the full (or scoped) test suite. Save the exact list of currently-failing checks/tests.

**Delegate to a subagent** — Run this via the `Agent` tool (an independent subagent), never directly in the main agent's shell. Give the subagent the exact command(s) and require full raw output back; read that output yourself before reporting results. See `ai-assistant-protocol` § Validation Execution.

```markdown
## Baseline

**Pre-existing failures:** [list, or "none"]

Any failure in this list is pre-existing and must never be attributed to this change.
```

---

## Phase 2: Contract

Write the contract as a plain markdown block (not a file, unless the user asks) with these fields:

```markdown
## Scope Contract

**Goal:** [restate the task in one sentence, in your own words]

**ALLOWED_FILES:**
- [explicit path]
- [explicit path]
(globs only if the user approves them explicitly)

**FORBIDDEN:**
- No new exported symbols, selectors, atoms, or helpers unless listed above
- No data-source changes
- No renames outside ALLOWED_FILES
- No commits or pushes until this contract is approved
- [any task-specific forbidden action]

**OPEN_QUESTIONS:**
- [anything you had to guess about because no codebase precedent exists]
```

Before writing FORBIDDEN/OPEN_QUESTIONS, check the codebase for an existing precedent (matching selector patterns, naming, file layout). Follow the precedent if one exists. If none exists, that's an open question — don't decide it yourself.

**GATE: Do not write any implementation code until the user approves this contract.**

---

## Phase 3: Failing Tests

Write tests that encode the desired behavior, scoped to `ALLOWED_FILES` and the test files needed to cover them. Run them and confirm they fail for the right reason (see `tdd` skill's RED-verification table if unsure what counts as a valid failure). No production code yet.

---

## Phase 4: Implement

Implement the minimum needed to pass the tests, touching only files in `ALLOWED_FILES`. Loop: run tests → read failures → fix → repeat.

If you find yourself wanting to touch a file outside `ALLOWED_FILES` or add anything in `FORBIDDEN`, stop and report it — don't do it and explain afterward.

---

## Phase 5: Self-Check (before every commit)

```bash
git diff --name-only
git diff
```

Compare the changed files against `ALLOWED_FILES` and check the diff content against `FORBIDDEN`. If anything is outside scope:

```markdown
## Contract Violation

**File/change:** [what's out of scope]
**Why it happened:** [reason]

Options: (a) revert this part and continue, (b) amend the contract and re-approve, (c) abort.
```

**GATE: Do not commit until the diff is confirmed inside scope, or the contract is amended and re-approved.**

---

## Phase 6: Report

```markdown
## Spec Loop Complete

**Diff by file:**
[file: one-line summary]

**Tests vs. baseline:** [new passes, no new failures]

**Wanted but forbidden:** [anything you noticed but the contract didn't allow — for the user to decide separately]
```

## Acceptance Tests

| ID | Type | Prompt / Condition | Expected |
|----|------|--------------------|----------|
| SL-T1 | Positive | "Implement this but don't touch anything outside the selector file" | Skill triggers |
| SL-T2 | Positive | "I want a spec-first, scope-locked loop for this change" | Skill triggers |
| SL-T3 | Negative | "Add tests for this existing function" | Does NOT trigger (→ /test-coverage) |
| SL-T4 | Negative | "Refactor this with no behavior change" | Does NOT trigger (→ /refactor) |
| SL-T5 | Boundary | Contract drafted but not yet approved | Does NOT proceed to Phase 3 |
| SL-T6 | Boundary | Diff during Phase 5 touches a file outside ALLOWED_FILES | Stops and reports violation instead of committing |
