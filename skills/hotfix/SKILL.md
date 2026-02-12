---
name: hotfix
description: Emergency bug fix with abbreviated validation for production issues. Use when production is broken, a critical security vulnerability is discovered, data corruption is occurring, or a user-blocking bug has no workaround.
---

# Hotfix

> **Purpose:** Emergency bug fix with abbreviated validation for production issues
> **Phases:** Triage -> Fix -> Verify -> Deploy
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
# Check fix files for insecure patterns
grep -rn -E "(eval\(|innerHTML\s*=|dangerouslySetInnerHTML|\\\$\{.*\}.*WHERE|exec\(|rejectUnauthorized:\s*false)" [affected-files]
grep -rn -E "(api[_-]?key|secret|password|token|credential)\s*[:=]" [affected-files]
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

**STOP HERE. Wait for explicit user confirmation before committing.**

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

## Post-Hotfix Actions

1. **Create follow-up todo** if the fix is a workaround
2. **Schedule post-mortem** for critical issues
3. **Update documentation** if not done in Phase 4

## References

- [Hotfix Templates](references/hotfix-templates.md) — Display templates for verification warnings, docs prompts, commit messages, PR descriptions, and completion summaries
