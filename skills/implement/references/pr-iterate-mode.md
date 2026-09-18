# PR Iterate Mode

**Discipline:** Drive a PR to merge-ready state by fixing CI failures and addressing review feedback in priority order. Max 3 push-and-verify cycles; escalate after that.

## Workflow: Preflight → Fetch → Categorize → Fix → Validate → Push → Verify → Loop (max 3)

### Phase 0: Preflight

**Goal:** Verify GitHub CLI is authenticated.

```bash
gh auth status
```

If not authenticated, instruct user to run `gh auth login` and abort.

### Phase 1: Fetch PR Status

**Goal:** Gather all CI, review, and merge status information.

Fetch:
- PR details (number, title, state, review decision, status checks)
- CI check results
- Review comments by file
- Merge conflict status

Present status summary.

**Early exit:** If all CI checks pass and no review comments are pending, report "PR is already clean — all checks pass, no pending feedback" and exit.

### Phase 2: Categorize Findings

**Goal:** Group findings by priority so you fix them in the right order.

Group all findings into categories:

**Merge Conflicts (P0 — resolve first):**
- List conflicting files
- Conflicts block all other work and must be resolved before CI fixes or review feedback

**CI Failures:**
- Build errors (typecheck, compilation)
- Lint errors
- Test failures
- Other check failures

**Review Comments:**
- Categorize each by P0-P3 severity (see table below)
- Group by file for efficient fixing

Present the categorized findings:

```markdown
## Findings Summary

**Conflicts:** X files — must resolve before push
**CI:** X failures (Y build, Z lint, W test)
**Reviews:** X comments (Y P0-P1, Z P2, W P3)

Proceed with fixes?
```

**GATE: User must confirm before fixing.**

### Phase 3: Address Findings

**Goal:** Fix all issues in priority order.

**Resolution order:** Merge conflicts first, then CI failures, then review comments.

#### Merge Conflicts (resolve first)

1. Fetch and rebase/merge the latest base branch: `git fetch origin && git merge origin/[base-branch]`
2. Resolve conflicts in each file
3. For lock files (`package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`), accept the base branch version and regenerate (`npm install`, `yarn install`, `pnpm install`)
4. Run full validation after conflict resolution
5. If conflicts are complex (non-trivial code conflicts in multiple files), present them to user for guidance

#### CI Failures

For each CI failure:
1. Read the failure log to understand the exact error
2. Identify the root cause (not just the symptom)
3. Fix the issue locally
4. Run the same check locally to confirm the fix
5. Only after local confirmation, proceed to the next issue

#### Review Comments

**Clarify before implementing:** If ANY review comment is unclear, stop and ask for clarification on ALL unclear items before implementing any fixes.

**YAGNI check:** If a reviewer suggests "implementing properly" or adding features, check actual usage in the codebase first. If the code is unused, push back: "This isn't called anywhere — remove it (YAGNI)?"

**When to push back on feedback:**
- Suggestion breaks existing functionality — reference working tests
- Reviewer lacks full context — provide the missing context
- Violates YAGNI — show grep results proving non-usage
- Technically incorrect for this stack — explain with specifics
- Conflicts with existing architectural decisions — flag to the user

| Severity | Action |
|----------|--------|
| P0-P1 | Auto-fix immediately |
| P2 | Auto-fix + flag to user for verification |
| P3 | Present as numbered menu — user picks which to address |

### Phase 4: Local Validation and Push

**Goal:** Verify all fixes work together before pushing.

1. **Run full local validation:** Invoke `/validate` with typecheck, lint, and test flags. Do not push code that fails locally.

2. **Commit by type:**
   ```bash
   # Conflict resolution (if any)
   git add [affected-files]
   git commit -m "chore: resolve merge conflicts with [base-branch]"

   # Functional fixes (P0-P2, CI failures)
   git add [affected-files]
   git commit -m "fix: address PR feedback — [summary]

   [list of fixes]"

   # Cosmetic fixes (P3, style) — only if any were selected
   git add [affected-files]
   git commit -m "style: address PR style feedback

   [list of changes]"

   # Push
   git push
   ```

### Phase 5: Verify and Reply

See `references/pr-iterate-templates.md` for ready-to-use reply templates (per-comment fix acknowledgment, escalation report, iteration-limit summary).

**Goal:** Watch CI and inform reviewers of fixes.

- Watch CI status until all checks report (pass or fail)
- Reply to resolved review threads with fix reference

Report results:

```markdown
## Iteration Result

**CI:** ✅ All passing / ❌ X still failing
**Reviews:** X resolved, Y remaining

[Details of any remaining failures]
```

### Phase 6: Loop or Exit

**Iteration limit:** Maximum 3 push-and-check cycles. After 3 iterations, escalate to user.

**Exit conditions:**
- All CI checks pass AND all review comments addressed → Done
- Same failure persists after 3 fix attempts → Escalate
- Total iteration count reaches 3 → Escalate and present summary
- User says stop

**Loop condition:** Remaining failures exist AND iteration count < 3 → Return to Phase 1

**Final report:**

```markdown
## Final Report

**Iterations:** X
**Fixes applied:** Y
**Status:** [Ready for re-review / Escalated / User stopped]

**Commits added:**
- `abc1234` fix: [description]
- `def5678` style: [description]
```

## Severity Levels (P0-P3)

Same scale used in `/review` skill:

| Level | Examples |
|-------|----------|
| P0 | Blocking issues: merge conflicts, broken tests, security vulnerabilities |
| P1 | High-priority issues: type errors, lint errors, performance regressions |
| P2 | Medium-priority issues: code clarity, minor refactors, documentation |
| P3 | Low-priority issues: style preferences, naming suggestions, future improvements |
