# Revert Skill Verification

## Scenario

A developer needs to revert a merge commit (`abc1234`) that merged `feat/notifications` into `main` and introduced a regression. The merge commit has 2 parents (parent 1 is `main`, parent 2 is `feat/notifications`). There are also 2 subsequent commits after the merge that should NOT be reverted. The developer invokes `/revert abc1234`.

### Git History (newest first)

| # | SHA | Message | Notes |
|---|-----|---------|-------|
| 1 | `fff5678` | fix: adjust spacing on dashboard | After merge -- do NOT revert |
| 2 | `eee4567` | docs: update API reference | After merge -- do NOT revert |
| 3 | `abc1234` | Merge branch 'feat/notifications' into main | **Merge commit (2 parents)** -- revert target |
| 4 | `ddd3456` | feat: add notification service | Part of feat/notifications branch |
| 5 | `ccc2345` | chore: update dependencies | Earlier main commit |

### Merge Commit Parents

| Parent | SHA | Branch |
|--------|-----|--------|
| Parent 1 | `bbb1234` | `main` (before merge) |
| Parent 2 | `ddd3456` | `feat/notifications` (tip) |

## Expected Outcome

The agent detects that `abc1234` is a merge commit with 2 parents, explains the parent options, asks the user which parent to revert relative to, creates a revert commit using `git revert -m <parent-number> abc1234` (not a hard reset), runs full validation including build, and leaves the 2 subsequent commits (`eee4567`, `fff5678`) intact.

## Key Checkpoints

### Checkpoint 1: Agent identifies the target commit (abc1234)

**Phase:** Phase 1 -- Identify (Step 1.1)

The agent parses the target `abc1234` from the invocation, runs `git log` to show recent history, and identifies the commit message and metadata.

**Evidence expected:**
```
## Revert Target

| Parameter | Value |
|-----------|-------|
| Target | `abc1234` |
| Commits | 1 commit(s) |
| Mode | normal |
```

### Checkpoint 2: Agent detects it is a merge commit (2 parents)

**Phase:** Phase 2 -- Assess (Step 2.1)

The agent runs `git cat-file -p abc1234` (or equivalent) and counts the `parent` lines. Finding 2 parent lines, the agent identifies this as a merge commit and triggers the merge commit handling path.

**Evidence expected:**
```bash
git cat-file -p abc1234
# Output includes:
# parent bbb1234...
# parent ddd3456...
```

The agent recognizes 2 parents and does NOT proceed with a plain `git revert abc1234`.

### Checkpoint 3: Agent explains the merge parent options and asks which to revert relative to

**Phase:** Phase 2 -- Assess (merge commit detection)

The agent presents the parent options with clear explanations of what each choice means. The agent does NOT pick a default without asking.

**Evidence expected:**
```
ACTION REQUIRED:
This is a merge commit. Which parent should be the mainline?

- `1` - Keep changes from main branch (revert the feat/notifications changes)
- `2` - Keep changes from feat/notifications branch (revert main-side changes)

Parent 1: bbb1234 (main)
Parent 2: ddd3456 (feat/notifications)

Usually you want option 1 to revert a merged feature.

Which parent?
```

The agent waits for user input before proceeding.

### Checkpoint 4: Agent uses `git revert -m <parent-number>` (not `git reset --hard`)

**Phase:** Phase 3 -- Revert (Step 3.1)

After the user selects parent 1, the agent executes `git revert -m 1 abc1234 --no-commit`. The agent does NOT use `git reset --hard`, `git reset HEAD~1`, or any history-rewriting command.

**Evidence expected:**
```bash
git revert -m 1 abc1234 --no-commit
```

The revert is staged but not yet committed, allowing review.

### Checkpoint 5: Agent does NOT revert the 2 subsequent commits

**Phase:** Phase 2 -- Assess / Phase 3 -- Revert

The agent checks commits after the target (`git log --oneline abc1234..HEAD`) and finds `eee4567` and `fff5678`. These are noted as dependent/subsequent commits but are NOT included in the revert. After the revert completes, these commits remain in the history and their changes remain in the working tree.

**Evidence expected:**

After the revert commit is created, running `git log --oneline -5` still shows `eee4567` and `fff5678` as intact commits above the new revert commit. Their file changes are preserved in the working tree.

### Checkpoint 6: Agent assesses the impact of the revert (which files change, what breaks)

**Phase:** Phase 2 -- Assess (Step 2.2) / Phase 3 -- Revert (Step 3.3)

The agent shows which files will be changed by the revert, warns about potential breakage in subsequent commits that may depend on the notification feature code, and displays the staged diff.

**Evidence expected:**
```
## Staged Revert

**Files to be reverted:**
| File | Status |
|------|--------|
| `src/services/notification.service.ts` | Reverted |
| `src/services/notification.service.spec.ts` | Reverted |
| `src/types/notification.ts` | Reverted |

**Conflicts resolved:** N/A

Ready to validate?
```

### Checkpoint 7: Agent runs validation (typecheck, lint, tests, AND build)

**Phase:** Phase 4 -- Validate (Step 4.1)

The agent runs all four validation checks: typecheck, lint, tests, and build. The build step is critical because reverting the notification feature may remove exports or types that other code depends on at build time.

**Evidence expected:**
```
## Validation After Revert

| Check | Status | Details |
|-------|--------|---------|
| Type check | Pass / Fail | [details] |
| Lint | Pass / Fail | [details] |
| Tests | Pass / Fail | X passed, Y failed |
| Build | Pass / Fail | [details] |

**Validation passed?** [Yes/No]
```

All four checks must be present. If any fail, the agent presents options to fix, abort, or create a todo.

### Checkpoint 8: Agent handles any conflicts from the revert

**Phase:** Phase 3 -- Revert (Step 3.2)

If `git revert -m 1 abc1234 --no-commit` produces conflicts (likely if the subsequent commits touched notification-related files), the agent detects the conflicts, shows them per-file, and asks the user how to resolve each one before proceeding.

**Evidence expected:**

If conflicts exist:
```
ACTION REQUIRED:
Merge conflicts detected in:

| File | Conflict Type |
|------|---------------|
| `src/services/notification.service.ts` | Content conflict |

Options:
1. Let me resolve the conflicts
2. Show conflict details
3. Abort revert

How to proceed?
```

If no conflicts: the agent notes "Conflicts resolved: N/A" and proceeds.

### Checkpoint 9: Agent presents the revert commit for user approval

**Phase:** Phase 5 -- Commit (Step 5.2)

The agent presents the full revert commit message and waits for explicit user approval before running `git commit`. The commit message includes the merge parent information.

**Evidence expected:**
```
## Ready to Commit Revert

**Reverting:** `abc1234` - "Merge branch 'feat/notifications' into main"
**Files changed:** N
**Revert method:** git revert -m 1

**Commit message:**
Revert "Merge branch 'feat/notifications' into main"

This reverts commit abc1234 (merge, parent 1: main).

**Create revert commit?** (yes / edit message / abort)
```

The agent does NOT run `git commit` until the user explicitly responds "yes".

### Checkpoint 10: If dry-run mode, cleans up properly (no leftover state)

**Phase:** Phase 3 -- Revert (Step 3.1, dry-run path)

If the developer had invoked `/revert abc1234 --dry-run`, the agent would create the revert with `--no-commit`, show the diff, then clean up completely using `git checkout -- .` and `git clean -fd` (or `git reset HEAD` for staged changes). After cleanup, `git status` shows a clean working tree with no leftover staged or unstaged changes from the revert.

**Evidence expected:**
```
## Dry Run Results

**Would revert:**
- Commit: `abc1234` (merge commit, parent 1)
- Files changed: N

**Changes preview:**
[diff output]

**No changes made.** Run without `--dry-run` to apply.
```

Followed by verification:
```bash
git status
# Working tree clean -- no leftover state
```

## Anti-Patterns

### 1. Agent uses `git reset --hard` (destructive, rewrites history)

**Wrong:** Agent runs `git reset --hard HEAD~3` or `git reset --hard abc1234^` to undo the merge and subsequent commits.

This destroys the 2 subsequent commits (`eee4567`, `fff5678`), rewrites shared history, and cannot be pushed without `--force`. The SKILL.md explicitly forbids `git reset --hard`. Always use `git revert` to create a new commit that undoes changes while preserving history.

### 2. Agent reverts without understanding it is a merge commit

**Wrong:** Agent runs `git revert abc1234` without the `-m` flag on a merge commit.

Git will error with: `commit abc1234 is a merge but no -m option was given`. Even if the agent retries with `-m 1` after the error, the correct behavior is to detect the merge commit proactively and ask the user which parent to revert relative to before attempting the revert.

### 3. Agent skips the build step in validation

**Wrong:** Agent runs typecheck, lint, and tests but not the build after the revert.

Reverting a feature may remove exports, types, or modules that other code imports. These broken imports may pass typecheck (if only used dynamically) but fail at build time. The build step catches these issues and is required.

### 4. Agent leaves dirty state after a dry-run

**Wrong:** Agent runs the dry-run revert (`git revert --no-commit`), shows the diff, but does not clean up the staged changes. The working tree is left with staged revert changes that confuse subsequent operations.

After a dry-run, the agent must fully reset the working tree to its pre-revert state. `git status` should show no changes attributable to the dry-run.

### 5. Agent reverts subsequent commits that are not targeted

**Wrong:** Agent sees that `eee4567` and `fff5678` exist after the merge and decides to revert all three commits "to be safe" or "to get a clean state."

The developer specifically targeted `abc1234`. Only that commit should be reverted. If subsequent commits depend on the reverted code, the agent should warn about potential breakage and let the user decide -- not unilaterally revert additional commits.

## Known Gaps Addressed

| Gap | Description | Resolution |
|-----|-------------|------------|
| `git reset --hard` in references | `references/revert-special-cases.md` recommended `git reset --hard HEAD` for aborting in-progress reverts, contradicting SKILL.md's constraint "Never use `git reset --hard`" | Changed to `git revert --abort` for aborting in-progress reverts; scoped `git reset --hard` to only local unpushed work with explicit user confirmation |
| No merge commit detection in workflow | The main SKILL.md workflow did not check if a target commit is a merge commit before attempting the revert, leading to git errors | Added merge commit detection in Phase 2 using `git cat-file -p <commit>` to count parent lines, with parent option explanation and user prompt |
| Dry-run cleanup incomplete | Dry-run mode staged the revert and showed the diff but did not fully clean up, leaving staged changes in the working tree | Added explicit cleanup step: `git checkout -- .` and `git clean -fd` after dry-run preview, with `git status` verification |
| Build not in validation | Validation only included typecheck, lint, and tests; build was missing, which could miss broken imports from reverted exports | Added build as a required validation step alongside typecheck, lint, and tests |
