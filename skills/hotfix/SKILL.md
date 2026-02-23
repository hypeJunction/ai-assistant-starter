---
name: hotfix
description: Emergency bug fix with abbreviated validation for production issues. Use when production is broken, a critical security vulnerability is discovered, data corruption is occurring, or a user-blocking bug has no workaround.
category: process
triggers:
  - production broken
  - emergency fix
  - critical bug
  - urgent fix
---

# Hotfix

> **Purpose:** Emergency bug fix with abbreviated validation for production issues
> **Phases:** Prepare -> Triage -> Fix -> Verify -> Deploy
> **Usage:** `/hotfix [scope flags] <issue description>`

## Iron Laws

1. **ONE FIX, ONE ISSUE** — A hotfix touches exactly one bug. No cleanup, no refactoring, no "while I'm here" improvements. Scope creep in a hotfix is how you turn one production issue into two.
2. **REGRESSION TEST IS MANDATORY** — Every hotfix must include a test that reproduces the bug and verifies the fix. A hotfix without a test will break again.
3. **VERIFY ON THE HOTFIX BRANCH** — Run tests on the hotfix branch, not main. The fix must work in isolation.

## Constraints

- **Minimal fix only** -- one issue, one fix
- **No refactoring** during hotfix
- **No adding features** or code cleanup
- **Never skip type check**
- **Never deploy with failing tests** without explicit user approval
- **Regression test required** for every hotfix
- **Requires `gh` CLI** for PR creation in the Deploy phase

> **Note:** Command examples use `npm` as default. Adapt to the project's package manager per `ai-assistant-protocol` — Project Commands.

## When to Use

- Production is broken, critical security vulnerability, data corruption, or user-blocking bug with no workaround

**Do NOT use for:** Non-urgent bugs (use `/debug`), feature requests, performance improvements, or code cleanup.

## Scope Flags

| Flag | Description |
|------|-------------|
| `--files=<paths>` | Known affected files |
| `--ticket=<id>` | Issue/ticket reference |
| `--severity=<level>` | `critical` / `high` (default: critical) |

**Examples:**
```bash
/hotfix --ticket=PROD-123 users cannot login
/hotfix --files=src/auth/ --severity=critical session tokens expiring
/hotfix payment processing failing for credit cards
```

## Workflow

All markdown output templates for each step are in `references/hotfix-templates.md`.

### Phase 0: Prepare

**Goal:** Save current work and set up a clean hotfix branch from main

#### Step 0.1: Verify gh Auth

If the hotfix will need a PR (most cases), verify authentication early so issues don't block the fix after it's ready:

```bash
gh auth status
```

**If not authenticated:** Warn the developer immediately. They can authenticate in parallel while triage begins, but PR creation will be blocked until resolved.

#### Step 0.2: Save Current Work

Record the current branch and stash any uncommitted changes (staged, unstaged, and untracked):

```bash
ORIGINAL_BRANCH=$(git branch --show-current)
git stash push -m "pre-hotfix: ${ORIGINAL_BRANCH}" --include-untracked
```

**If stash fails:** Check `git status`. If the working tree is already clean, proceed without stashing. Record that no stash was created so the restore step knows not to pop.

#### Step 0.3: Create Hotfix Branch from Main

Always branch from the latest main -- never from a feature branch:

```bash
MAIN=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")
git checkout $MAIN && git pull
git checkout -b hotfix/<descriptive-name>
```

Use a descriptive branch name based on the issue (e.g., `hotfix/fix-login-null-check`, `hotfix/fix-payment-timeout`).

---

### Phase 1: Triage

**Goal:** Quickly identify root cause -- skip extensive exploration

#### Step 1.1: Gather Symptoms (Fast)

Present the triage template (see `references/hotfix-templates.md` -- Triage: Symptoms Gathering).

#### Step 1.2: Quick Investigation

```bash
git log --oneline -10
git log --oneline -5 -- [affected-files]
grep -r "TODO\|FIXME\|HACK" [affected-files]
```

#### Step 1.3: Identify Root Cause

Keep investigation brief -- this is an emergency. Present root cause identification (see `references/hotfix-templates.md` -- Triage: Root Cause Identification).

**GATE: Confirm root cause before fixing. Do NOT proceed without explicit user confirmation.**

---

### Phase 2: Fix

**Goal:** Minimal change to fix the issue -- no refactoring

#### Step 2.1: Plan Minimal Fix

Present the fix plan (see `references/hotfix-templates.md` -- Fix Plan).

**GATE: User must approve fix approach before implementing.**

#### Step 2.2: Implement Fix

Present implementation status (see `references/hotfix-templates.md` -- Fix: Implementation Status). Apply the minimal fix.

#### Step 2.3: Add Regression Test

> **REQUIRED:** Every hotfix must include a regression test to prevent recurrence.

Follow the regression test template (see `references/hotfix-templates.md` -- Fix: Regression Test).

#### Step 2.4: Type Check

```bash
npm run typecheck
```

**If type errors:** They must be resolved before proceeding.

---

### Phase 3: Verify

**Goal:** Scoped validation -- only affected code

#### Step 3.1: Run Scoped Tests

```bash
npm run typecheck
npm run lint -- [affected-files]
npm run test -- [regression-test-file]
npm run test -- [affected-test-pattern]
```

#### Step 3.2: Security Quick-Check

Even under emergency conditions, verify the fix doesn't introduce security issues:

```bash
# Secrets detection in affected files (aligned with commit skill patterns)
grep -rn --include="*.ts" --include="*.tsx" --include="*.js" --include="*.json" \
  -E "(api[_-]?key|secret|password|token|credential|private[_-]?key)\s*[:=]" [affected-files]

# Insecure patterns (aligned with commit skill patterns + SQL injection check)
grep -rn --include="*.ts" --include="*.tsx" --include="*.js" \
  -E "(eval\(|new Function\(|innerHTML\s*=|dangerouslySetInnerHTML|\\\$\{.*\}.*WHERE|\.exec\(|rejectUnauthorized:\s*false)" [affected-files]
```

**If any match:** Verify they are not exploitable before proceeding. Emergency is never an excuse for introducing vulnerabilities.

#### Step 3.3: Verification Report

Present verification report (see `references/hotfix-templates.md` -- Verification Report).

**GATE: All tests (especially the regression test) must pass before deployment.**

**If tests fail:** Present test failure warning (see `references/hotfix-templates.md` -- Verification: Test Failure Warning).

---

### Phase 4: Docs (Optional)

**Goal:** Quick documentation if issue revealed a gap

> **Note:** Keep this lightweight. Hotfixes need to ship fast.

Present docs prompt (see `references/hotfix-templates.md` -- Docs Prompt). If `skip` (most common), proceed immediately to deploy.

---

### Phase 5: Deploy

**Goal:** Fast-track commit and PR

#### Step 5.1: Create Hotfix Commit

Present commit template (see `references/hotfix-templates.md` -- Deploy: Commit).

**GATE: User must approve before committing.**

```bash
git add [affected-files]
git commit -m "fix: [description]

[HOTFIX] [TICKET-ID]

Root cause: [explanation]"
```

#### Step 5.2: Create PR or Push

**If on feature branch:** Present PR template (see `references/hotfix-templates.md` -- Deploy: PR).

**If approved:**

```bash
git push -u origin HEAD
gh pr create --title "[HOTFIX] [description]" --body "..." --label hotfix,priority:critical
```

#### Step 5.3: Deployment Notes

Present completion summary (see `references/hotfix-templates.md` -- Deploy: Completion).

### Phase 6: Restore

**Goal:** Return the developer to their pre-hotfix context

After the hotfix is committed and pushed/PR-created, restore the developer's original working state:

```bash
git checkout [original-branch]
```

If work was stashed in Phase 0:

```bash
git stash pop
```

**If stash pop conflicts:** Warn the developer. The stash is preserved (not dropped) on conflict, so no work is lost. They can resolve manually with `git stash show -p` and `git stash drop` after resolving.

**If no stash was created** (working tree was clean in Phase 0): Skip `git stash pop`.

Present restore confirmation:

```markdown
## Context Restored

**Branch:** `[original-branch]`
**Stash:** [restored / not needed]

You're back where you were before the hotfix.
```

---

## Post-Hotfix Actions

1. **Create follow-up todo** if the fix is a workaround
2. **Schedule post-mortem** for critical issues
3. **Update documentation** if not done in Phase 4

## Acceptance Tests

| ID | Type | Prompt / Condition | Expected |
|----|------|--------------------|----------|
| HOT-T1 | Positive | "Production is down, fix the login" | Skill triggers |
| HOT-T2 | Positive | "Emergency fix for payment processing" | Skill triggers |
| HOT-T3 | Positive | "Critical security vulnerability found" | Skill triggers |
| HOT-T4 | Negative | "There's a minor bug in the dashboard" | Does NOT trigger (-> /debug) |
| HOT-T5 | Negative | "Add a new feature" | Does NOT trigger (-> /implement) |
| HOT-T6 | Negative | "Refactor the auth module" | Does NOT trigger (-> /refactor) |
| HOT-T7 | Boundary | "Fix this bug urgently" | Context-dependent — if production-impacting, trigger; if not urgent, route to /debug |

## References

- [Hotfix Templates](references/hotfix-templates.md) — Display templates for verification warnings, docs prompts, commit messages, PR descriptions, and completion summaries
