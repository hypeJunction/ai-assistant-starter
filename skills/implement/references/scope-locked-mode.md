# Scope-Locked Mode

**Discipline:** Get an explicit, approved file-scope contract before any implementation. Self-check every commit's diff against that contract before pushing. Violations block the commit (report instead of committing and explaining later).

## Iron Laws

1. **NO IMPLEMENTATION BEFORE THE CONTRACT IS APPROVED** — Write the contract, show it, wait for explicit approval. Do not touch production code first.
2. **EVERY COMMIT IS CHECKED AGAINST THE CONTRACT** — Before committing, diff the changed files against `ALLOWED_FILES` and the `FORBIDDEN` list. A violation means stop and report, not commit-and-explain.
3. **A GUESSED CONVENTION IS AN OPEN QUESTION, NOT A DECISION** — If no precedent exists in the codebase for how to do something, it goes in `OPEN_QUESTIONS` for the user to resolve, not into the contract as an assumption.

## Workflow: Baseline → Contract → Failing Tests → Implement → Self-Check → Report

### Phase 1: Baseline

**Goal:** Record the current state of typecheck, lint, and tests so you can distinguish pre-existing failures from new ones.

Run: Invoke `/validate` with typecheck, lint, and test suite flags. Save the exact list of currently-failing checks/tests.

```markdown
## Baseline

**Pre-existing failures:** [list, or "none"]

Any failure in this list is pre-existing and must never be attributed to this change.
```

### Phase 2: Contract

**Goal:** Write an explicit scope boundary and get user approval before touching code.

Write the contract as a plain markdown block with these fields:

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

### Phase 3: Failing Tests

**Goal:** Write tests that encode the desired behavior, scoped to `ALLOWED_FILES`.

Write tests that should fail for the right reason. See `references/tdd-mode.md` for RED-verification table. No production code yet.

### Phase 4: Implement

**Goal:** Implement the minimum needed to pass the tests, touching only files in `ALLOWED_FILES`.

Loop: run tests → read failures → fix → repeat.

If you find yourself wanting to touch a file outside `ALLOWED_FILES` or add anything in `FORBIDDEN`, stop and report it — don't do it and explain afterward.

### Phase 5: Self-Check (before every commit)

**Goal:** Verify the diff is inside scope before committing.

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

### Phase 6: Report

```markdown
## Scope-Locked Mode Complete

**Diff by file:**
[file: one-line summary]

**Tests vs. baseline:** [new passes, no new failures]

**Wanted but forbidden:** [anything you noticed but the contract didn't allow — for the user to decide separately]
```
