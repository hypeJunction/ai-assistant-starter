---
name: revert
description: Safely rollback changes using git revert with impact assessment and validation. Use when a commit needs to be undone, a PR introduced a bug, or changes need to be rolled back without rewriting history.
triggers:
  - undo commit
  - rollback
  - revert changes
  - undo last change
---

# Revert

> **Purpose:** Safely rollback changes using git revert
> **Phases:** Identify -> Assess -> Revert -> Validate -> Commit
> **Usage:** `/revert [target] [scope flags]`

## Constraints

- **Never force push after revert** without explicit approval
- **Never revert without user confirmation**
- **Never leave unresolved conflicts**
- **Never use `git reset --hard`** -- use `git revert` instead
- **Never revert shared history** without team coordination
- Show what will be reverted before applying
- User confirmation of target required
- User approval of plan required
- Validation after revert required
- User confirmation before commit required
- Document reason for revert when provided
- Create follow-up todo if revert is temporary
- Notify team of significant reverts
- Consider PR for reverts on shared branches

> **Note:** Command examples use `npm` as default. Adapt to the project's package manager per `ai-assistant-protocol` — Project Commands.

## Target Options

| Target | Description |
|--------|-------------|
| `HEAD` | Revert last commit (default) |
| `HEAD~N` | Revert last N commits |
| `<sha>` | Revert specific commit |
| `<sha>..<sha>` | Revert range of commits |
| `--pr=<number>` | Revert all commits from a PR |

## Scope Flags

| Flag | Description |
|------|-------------|
| `--dry-run` | Preview revert without applying |
| `--no-commit` | Stage reverts without committing |
| `--reason=<text>` | Document reason for revert |

**Examples:**
```bash
/revert                            # Revert last commit
/revert HEAD~3                     # Revert last 3 commits
/revert abc123                     # Revert specific commit
/revert --pr=456                   # Revert PR #456
/revert abc123 --reason="broke prod"  # Revert with reason
/revert HEAD --dry-run             # Preview revert
```

## Workflow

### Phase 1: Identify

**Goal:** Parse target and show what will be reverted

#### Step 1.1: Parse Target

```bash
# Get current state
git branch --show-current
git log --oneline -10
```

**Parse target from input:**

```markdown
## Revert Target

| Parameter | Value |
|-----------|-------|
| Target | `[HEAD / sha / range]` |
| Commits | N commit(s) |
| Reason | [if provided] |
| Mode | [normal / dry-run / no-commit] |
```

#### Step 1.2: Show Commits to Revert

```bash
# For single commit
git show --stat [sha]

# For range
git log --oneline [range]

# For PR
gh pr view [number] --json commits
```

**Display commits:** See [references/revert-display-templates.md](references/revert-display-templates.md) for full display format.

#### Step 1.3: Show What Will Change

```bash
# Show combined diff of commits being reverted
git diff [sha]^..[sha]
```

**Display changes:** See [references/revert-display-templates.md](references/revert-display-templates.md) for full display format.

#### Step 1.4: Confirm Target

**Display confirmation prompt:** See [references/revert-display-templates.md](references/revert-display-templates.md) for full display format.

**GATE: User must confirm target.**

---

### Phase 2: Assess

**Goal:** Evaluate impact and conflict risk

#### Step 2.1: Check for Dependent Changes

```bash
# Check if any commits after target depend on it
git log --oneline [sha]..HEAD

# Check for merge commits that include target
git log --oneline --merges [sha]..HEAD
```

**If dependent commits found:** See [references/revert-display-templates.md](references/revert-display-templates.md) for warning display format.

Wait for decision.

#### Step 2.2: Assess Conflict Risk

```bash
# Check if files were modified since target
git diff --name-only [sha] HEAD
```

**If conflicts likely:** See [references/revert-display-templates.md](references/revert-display-templates.md) for conflict risk display format.

#### Step 2.3: Present Revert Plan

```markdown
## Revert Plan

**Target:** `[sha]` - "[message]"

**Approach:**
- Revert method: `git revert [sha]`
- Conflict risk: [Low / Medium / High]
- Dependent commits: [None / List]

**Expected outcome:**
- Changes from `[sha]` will be undone
- New commit will be created: "Revert [message]"
- History preserved (original commit visible)

**Approve revert?** (yes / modify / abort)
```

**GATE: User must approve plan.**

---

### Phase 3: Revert

**Goal:** Apply the revert and handle any conflicts

#### Step 3.1: Apply Revert

**If dry-run mode:**

```bash
git revert --no-commit [sha]
git diff --staged
git reset HEAD  # Undo the staged revert
```

```markdown
## Dry Run Results

**Would revert:**
- Commit: `[sha]`
- Files changed: N

**Changes preview:**
[diff output]

**No changes made.** Run without `--dry-run` to apply.
```

**Otherwise:**

```bash
# For single commit
git revert [sha] --no-commit

# For multiple commits (reverse order)
git revert [sha1] [sha2] [sha3] --no-commit

# For range
git revert [older]..[newer] --no-commit
```

#### Step 3.2: Handle Conflicts

**If conflicts occur:** See [references/revert-display-templates.md](references/revert-display-templates.md) for conflict resolution display format.

Wait for decision.

**If resolving:**

```bash
# Show conflict markers
git diff --name-only --diff-filter=U
```

**For each conflicted file:** See [references/revert-display-templates.md](references/revert-display-templates.md) for per-file conflict display format.

**After resolution:**

```bash
git add [resolved-files]
```

#### Step 3.3: Review Staged Revert

```markdown
## Staged Revert

**Files to be reverted:**
| File | Status |
|------|--------|
| `src/feature.ts` | Reverted |
| `tests/feature.spec.ts` | Reverted |

**Conflicts resolved:** [Yes/No/N/A]

Ready to validate?
```

---

### Phase 4: Validate

**Goal:** Confirm the codebase is healthy after revert

#### Step 4.1: Run Validation

```bash
# Type check
npm run typecheck

# Lint
npm run lint

# Tests (scoped to affected areas)
npm run test -- [affected-patterns]
```

#### Step 4.2: Validation Report

```markdown
## Validation After Revert

| Check | Status | Details |
|-------|--------|---------|
| Type check | Pass / Fail | [details] |
| Lint | Pass / Fail | [details] |
| Tests | Pass / Fail | X passed, Y failed |

**Validation passed?** [Yes/No]
```

**If failures:**

```markdown
> **WARNING:**
> Validation failed after revert.
>
> **Issues:**
> - [list issues]
>
> **This likely means:**
> - Later code depends on the reverted changes
> - Additional fixes needed after revert
>
> **Options:**
> 1. Fix issues and continue with revert
> 2. Abort revert (reset staged changes)
> 3. Create todo for fixes and proceed
>
> **How to proceed?**
```

Wait for decision.

---

### Phase 5: Commit

**Goal:** Finalize the revert commit

#### Step 5.1: Prepare Commit Message

```markdown
## Revert Commit

**Default message:**
```
Revert "[original commit message]"

This reverts commit [sha].

[Reason if provided]
```

**Customize message?** (yes / use default)
```

#### Step 5.2: Confirm Commit

```markdown
## Ready to Commit Revert

**Reverting:** `[sha]` - "[message]"
**Files changed:** N
**Reason:** [reason if provided]

**Commit message:**
```
Revert "feat: add feature"

This reverts commit abc123.

Reason: Feature caused production issues.
```

**Create revert commit?** (yes / edit message / abort)
```

**GATE: Never commit without explicit "yes".**

```bash
git commit -m "Revert \"[original message]\"

This reverts commit [sha].

[Reason]"
```

#### Step 5.3: Completion

```markdown
## Revert Complete

| Item | Value |
|------|-------|
| Reverted commit | `[sha]` |
| Revert commit | `[new-sha]` |
| Files changed | N |

**Next steps:**
- Push to remote: `git push origin [branch]`
- Create PR if needed
- Deploy if urgent

**Note:** Original commit `[sha]` remains in history.
To undo this revert: `git revert [new-sha]`
```

## Additional References

- [Special Cases & Recovery Options](references/revert-special-cases.md) -- Merge commit reverts, PR reverts, partial reverts, and recovery procedures
- [Display Templates](references/revert-display-templates.md) -- Full markdown display templates for user-facing output in each phase
