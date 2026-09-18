# Finish Options

Structured exit decision tree for concluding a development session. Present these options after all validation passes, before or after the commit.

## Exit Options

After committing (or deciding not to), present exactly these options:

```markdown
## Session Complete

Work committed as `abc1234`: feat(auth): add JWT validation

**What's next?**

1. **Push & PR** — Push branch and create a pull request
2. **Push only** — Push to remote, create PR later
3. **Keep local** — Leave committed locally, push later
4. **Continue working** — Stay in this session, start next task
```

### Option Details

#### 1. Push & PR

```bash
# Push branch to remote
git push -u origin $(git branch --show-current)

# Create PR (requires gh CLI)
gh pr create --title "[type]: [description]" --body "## Summary\n- [changes]\n\n## Test Plan\n- [how to verify]"
```

**When to suggest:** Medium/large changes, feature branches, team projects.

#### 2. Push Only

```bash
git push -u origin $(git branch --show-current)
```

**When to suggest:** Work in progress, not ready for review yet.

#### 3. Keep Local

No action needed. The commit is saved locally.

**When to suggest:** Experimenting, unsure about the approach, working offline.

#### 4. Continue Working

Return to normal operation. The session isn't ending.

**When to suggest:** User said "commit" but didn't say "finish."

## Post-Merge Verification

If the user chooses to merge (locally or via PR), verify after merge:

```bash
# After merge to main
git checkout main
git pull
npm run test       # Verify tests pass on merged result
npm run typecheck  # Verify types pass on merged result
npm run build      # Verify build passes
```

**Why:** Merge conflicts can introduce subtle breakage that wasn't in either branch independently. Always verify the merged result.

## Discard / Abandon

If the user wants to abandon the work:

```markdown
## Confirm Discard

The following will be permanently lost:
- [N] uncommitted file changes
- [list of modified files]

Type "discard" to confirm, or choose a different option.
```

**Only discard after explicit confirmation.** Never discard uncommitted work without the user typing "discard."

```bash
# If confirmed
git checkout -- .
git clean -fd  # Only if untracked files need removal — confirm first
```

## Worktree Cleanup

If working in a git worktree, clean up after completing the work:

```bash
# Check if in a worktree
git worktree list | grep "$(pwd)"
```

**When to clean up worktrees:**
- After merging locally (Option 1 equivalent) — remove the worktree
- After pushing & creating PR — keep the worktree (may need fixes)
- After discarding work — remove the worktree
- After "keep local" — keep the worktree

```bash
# Remove worktree (from main working directory)
git worktree remove <worktree-path>
```

## Stash for Later

If the user wants to pause and switch tasks:

```bash
# Save current work
git stash push -m "WIP: [description of current work]"

# List stashes later
git stash list

# Resume later
git stash pop
```

**When to suggest:** User needs to switch branches, handle an urgent issue, or pause for the day.

## Session Summary Template

Present this summary at the end of every `/done` session:

```markdown
## Session Summary

### Work Completed
- **Branch:** `feature/auth-jwt`
- **Commits:** 2 (abc1234, def5678)
- **Files changed:** 5 (+120 / -15)

### Quality Checks
| Check | Result |
|-------|--------|
| Type check | Pass |
| Lint | Pass |
| Tests | 12 passed, 0 failed |
| Build | Pass |
| Self-review | No critical issues |

### What Was Done
- Added JWT token validation to auth middleware
- Created `validateToken()` utility with expiry handling
- Added 3 test cases for valid/expired/malformed tokens

### Remaining Work
- [ ] Add refresh token rotation (see todo: `refresh-tokens.md`)
- [ ] Update API documentation

### Todos Closed
- `add-jwt-auth.md` — closed, ADR: `jwt-over-sessions.md`

### Next Session Recommendations
- Start with `/implement --todo refresh-tokens.md`
- Consider running `/security-review --module auth` before PR
```

### Summary Sections

| Section | When to Include |
|---------|----------------|
| Work Completed | Always |
| Quality Checks | Always |
| What Was Done | Always (bullet list of changes) |
| Remaining Work | When there are known follow-up tasks |
| Todos Closed | When todos were resolved (Phase 8) |
| Next Session Recommendations | When there's clear follow-up work |
