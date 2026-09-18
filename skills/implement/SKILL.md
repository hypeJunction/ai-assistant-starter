---
name: implement
description: Execute an approved plan — code, self-review, test, validate, commit, close. Selectable modes handle debugging, strict TDD, scope-locked autonomous work, and PR-feedback iteration.
category: process
model: sonnet
effort: medium
triggers:
  - build feature
  - add functionality
  - implement
  - create new
  - enhance existing
  - fix bug
  - error
  - test failing
  - test first
  - red green refactor
  - PR feedback
  - CI failing
---

# Implement

> **Purpose:** Execute an approved plan against the codebase
> **Phases:** Determine Mode → Plan Input → Code → Self-Review → Test → Validate → Commit → Close
> **Usage:** `/implement [scope flags] [mode flag] <task description>` or `/implement --todo <todo-file>`

## Iron Laws

1. **NO CODE WITHOUT AN APPROVED PLAN** — this skill executes a plan, it does not create one. If no plan exists, get one first (see Phase 1).
2. **VERIFY AFTER EVERY FILE** — Run typecheck after each file change. Don't batch edits across files without verification. Evidence before assertions.
3. **STAY IN SCOPE** — Never fix, improve, or refactor code outside the approved plan. Create a todo for out-of-scope issues.

## When to Use

- Executing an approved plan (feature work, enhancements, significant changes)
- Debugging, TDD, scope-locked autonomous work, or PR-feedback iteration (via mode flags below) — these are all executions, just with a different discipline for how Phase 1–4 run

## When NOT to Use

- 16+ file changes → `/refactor` (6-15 files: confirm with user, consider `/refactor` if structural)
- Design/planning only, nothing to execute yet → `/plan`
- Quick single-file edit → edit directly
- Emergency fix → `/hotfix`

## Gate Enforcement

See `ai-assistant-protocol` for valid approval terms and invalid responses.

## Scope Flags

| Flag | Description |
|------|-------------|
| `--todo=<file>` | Implement a specific todo from `.ai-project/todos/` |
| `--files=<paths>` | Specific files/directories to work on |
| `--uncommitted` | Build on current uncommitted changes |
| `--branch=<name>` | Branch context (default: current) |
| `--project=<path>` | Project root for monorepos |
| `--debug` | Root-cause-first discipline for bug fixes (see `references/debug-mode.md`) |
| `--tdd` | Strict RED-GREEN-REFACTOR discipline (see `references/tdd-mode.md`) |
| `--scope-locked` | File-scope contract gate for autonomous/long-running work (see `references/scope-locked-mode.md`) |
| `--pr-iterate` | Drive an open PR to merge-ready against CI/review feedback (see `references/pr-iterate-mode.md`) |

> **Note:** Command examples use `npm` as default. Adapt to the project's package manager per `ai-assistant-protocol` — Project Commands.

## Task Tiers (default mode only)

Classify the task early to scale the workflow appropriately. Tiers don't apply to `--debug`/`--tdd`/`--scope-locked`/`--pr-iterate` modes — each has its own fixed discipline.

| Tier | Scope | Workflow |
|------|-------|----------|
| **nano** | 1-2 lines, config tweak | One-line inline plan, quick nod. Edit → validate → commit |
| **small** | 1-2 files, clear approach | One-line inline plan, quick nod. Skip Self-Review |
| **medium** | 3-5 files | Requires an approved plan (via `/plan` or `--todo`). Full workflow |
| **large** | 6+ files | Requires an approved plan. Full workflow + batch execution + suggest feature branch + PR |

**Auto-classification:** Estimate tier from the request. If `--todo` is provided, use the todo's `estimated_effort` field. The user can override at any time ("treat this as nano").

---

## Phase 0: Determine Mode

```bash
git branch --show-current
git status --porcelain
```

Detect the mode from an explicit flag or the phrasing of the request:

| Signal | Mode | Reference |
|---|---|---|
| `--debug`, "fix bug", "error", "test failing" | Debug | `references/debug-mode.md` |
| `--tdd`, "test first", "red green refactor" | TDD | `references/tdd-mode.md` |
| `--scope-locked`, autonomous/long-running work where scope creep is a risk | Scope-locked | `references/scope-locked-mode.md` |
| `--pr-iterate`, "PR feedback", "CI failing" on an already-open PR | PR-iterate | `references/pr-iterate-mode.md` |
| None of the above | Default | Continue to Phase 1 below |

If a mode matched, load its reference file now and follow it — it supplies its own version of Phase 1 (its gate *is* its plan-equivalent) and tells you which of Phases 2–4 it replaces or skips. All modes still finish through this skill's shared Phase 5 (Validate), Phase 6 (Commit), and Phase 7 (Close Todo) unless their reference file says otherwise.

If `--todo` is provided, read the todo file to seed the implementation: extract description, context, affected files, and acceptance criteria — the todo becomes the source of truth for scope and success criteria.

---

## Phase 1: Plan Input (Default Mode)

**No exploration or planning happens here — this skill consumes an already-approved plan.**

- **nano/small tiers:** state the one-line change and get a quick approval nod (yes/no) — no full plan needed.
- **medium/large tiers:**
  - If `--todo=<file>` was given, or a plan was just approved via `/plan`/Plan Mode earlier in this same conversation, use it directly as the source of truth for scope, files, and steps.
  - Otherwise, **call `/plan` now** and wait for its approval gate — do not proceed with a shrunken re-derivation of exploration and design. Once `/plan` produces an approved plan, resume here at Phase 2.

**GATE: Do NOT proceed to Phase 2 until a plan is approved (or the nano/small quick nod is given).**

---

## Phase 2: Code

**Mode:** Full access — implement the approved plan.

### Step 2.1: Create Git Savepoint

For complex implementations, create a savepoint before starting:

```bash
git stash push -m "savepoint: before [feature]" --include-untracked
git stash pop
```

Or commit any existing work so you can revert cleanly if needed.

### Step 2.2: Implement (Verify Per File)

For each file in plan, follow the micro-step pattern (see `references/task-decomposition.md`):
1. Edit the file (one step per file — if a step touches >1 file, split it)
2. **Run typecheck immediately** — don't batch multiple file edits
3. Show fresh evidence of the result before claiming success
4. Report progress

If typecheck fails after a change, fix it before moving to the next file.

When creating a new file: (a) Check if an existing file should be extended instead, (b) Follow the project's file naming conventions, (c) Mirror the structure of similar existing files, (d) Ensure the new file is properly imported/registered where needed (e.g., route registration, barrel exports).

### Batch Execution (Large Tier)

For large-tier tasks (6+ files), execute plan steps in batches with review checkpoints:

1. **Review plan critically** before starting — raise concerns about gaps or unclear instructions
2. **Execute in batches of 3 steps** — complete each step fully (edit, typecheck, verify)
3. **Pause between batches** — report what was implemented, show verification output, say "Ready for feedback"
4. **Apply feedback** if any, then execute the next batch
5. **Stop immediately** on blockers — don't guess through unclear instructions or repeated failures

### Step 2.3: Handle Surprises

| Surprise Type | Response |
|---------------|----------|
| **Scope expansion** | Stop. Present additional scope and ask for approval. |
| **Missing dependency** | Note it, ask if it should be added. |
| **Design conflict** | Present options. Don't force the original plan. |
| **Existing bug found** | Create a todo. Do NOT fix — out of scope. |

See `references/task-decomposition.md` for detailed decision trees for each surprise type and evidence-before-claims requirements.

### Step 2.4: Validate Code

```bash
npm run typecheck
npm run lint
```

---

## Phase 3: Self-Review

**Mode:** Read-only — review your own work before testing.

Compare implementation against the approved plan:

```markdown
## Spec Compliance
| Plan Item | Status | Notes |
|-----------|--------|-------|
| [Step 1] | ✓ / ✗ | [deviations] |
```

Invoke `/review --quick` for the checklist pass (unused imports, `any` types, hardcoded values, inconsistent patterns, and the security checklist — secrets, `eval`/`innerHTML`, raw SQL interpolation, `child_process` with unsanitized input, disabled security controls, missing input validation/authz at boundaries). Fix issues it flags before proceeding.

---

## Phase 4: Test

**Mode:** Testing — ensure new code has appropriate test coverage.

**Delegate each check to its own subagent** — run every distinct command via a separate `Agent` call, never directly in the main agent's shell and never bundled into one call. Send independent checks in a single message with multiple tool uses so they run concurrently. Give each subagent its exact command and require full raw output back; read every subagent's output yourself before reporting results. See `ai-assistant-protocol` § Validation Execution.

**Test ordering:**
- **New functions/modules** — prefer writing the test first (write failing test, then implement, then verify). This produces tighter, more targeted code.
- **Enhancements to existing code** — write tests after implementation, verifying both new and existing behavior.
- **For strict TDD**, use `--tdd` mode instead (see `references/tdd-mode.md`).

**Steps:**
1. Categorize changed files by verification type (utility → unit tests, component → component tests, types → skip)
2. Write tests with Gherkin test plans as comments
3. Run tests: `npm run test -- [changed-files-pattern]`

**GATE: All tests must pass.**

---

## Phase 5: Validate

Invoke `/validate` (full mode for medium/large tiers, quick for nano/small) rather than running checks inline.

**GATE: All validations must pass. If any fail, fix before proceeding.**

---

## Phase 6: Commit

**Mode:** Git operations with user confirmation required.

### Step 6.1: Completion Evidence

```markdown
## Completion Evidence
| Verification | Result |
|--------------|--------|
| Type check | ✓ Pass |
| Lint | ✓ Pass |
| Tests | ✓ Pass (N tests) |
| Build | ✓ Pass |
| Spec compliance | ✓ All plan items |
```

### Step 6.2: Confirm Commit

Delegate to `/commit` for the actual diff analysis, security scan, and confirmation flow — don't re-implement that here.

**GATE: Do NOT run `git commit` until the user responds with explicit approval (enforced by `/commit`).**

---

## Phase 7: Close Todo

**Mode:** Housekeeping — finalize the work item.

**Skip this phase** if no `--todo` was provided and no todo is associated with the work.

### Step 7.1: Verify Acceptance Criteria

Check the todo's acceptance criteria against what was implemented:

```markdown
## Todo Acceptance
| Criterion | Status |
|-----------|--------|
| [From todo] | ✓ / ✗ |
```

All criteria must be met. If any are unmet, note what remains and keep the todo open.

### Step 7.2: Create ADR (if applicable)

If the implementation involved design decisions (chose between approaches, adopted a pattern, established a convention), invoke `/adr --from-todo <todo-file>` to capture the decision record.

**Skip the ADR** if the work was purely mechanical (no alternatives considered, no architectural choices).

### Step 7.3: Delete the Todo

Remove the completed todo file. The ADR (if created) and git history preserve the full context.

```markdown
## Closed
- **Todo:** `{todo-file}` — deleted
- **ADR:** `{adr-file}` — created (or: no ADR needed)
```

**Do not suggest or invoke `/done` from here.** Closing the todo ends this skill's job; wrapping up the session (commit review, PR, session bookkeeping) only happens when the user explicitly types `/done` themselves, after their own look at the diff.

---

## Quick Reference

| Phase | Mode | Gate |
|-------|------|------|
| 0. Determine Mode | Read-only | — |
| 1. Plan Input | Read-only | **Plan approved** (or quick nod for nano/small) |
| 2. Code | Full access | Typecheck passes per file |
| 3. Self-Review | Read-only | `/review --quick` issues fixed |
| 4. Test | Testing | **All tests pass** |
| 5. Validate | Validation | **`/validate` passes** |
| 6. Commit | Git only | **User confirms (via `/commit`)** |
| 7. Close | Housekeeping | Acceptance criteria met (todo-driven only) |

## Acceptance Tests

| ID | Type | Prompt / Condition | Expected |
|----|------|--------------------|----------|
| IMP-T1 | Positive | "Build a login form" | Skill triggers, default mode |
| IMP-T2 | Positive | "Add dark mode support" | Skill triggers, default mode |
| IMP-T3 | Positive | "Why is login broken?" | Skill triggers, debug mode |
| IMP-T4 | Positive | "Let's do this test-first" | Skill triggers, TDD mode |
| IMP-T5 | Positive | "Fix the PR feedback on #123" | Skill triggers, PR-iterate mode |
| IMP-T6 | Negative | "Review my code before merging" | Does NOT trigger (→ `/review`) |
| IMP-T7 | Negative | "Rename all utils to helpers" | Does NOT trigger (→ `/refactor`) |
| IMP-T8 | Boundary | "Quick one-line change to config" | Does NOT trigger (direct edit) |
| IMP-T9 | Boundary | Medium-tier request, no `--todo`, no prior plan | Hands off to `/plan` before Phase 2 |
