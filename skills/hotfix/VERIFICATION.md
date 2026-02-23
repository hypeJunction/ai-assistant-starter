# Hotfix Skill Verification

## Scenario

A developer is mid-feature on the `feat/dashboard` branch with uncommitted changes. Production reports a critical bug: the login endpoint returns 500 due to a missing null check in `src/auth/login.ts:47`. They invoke `/hotfix`.

## Expected Outcome

Current work is safely stashed, a hotfix branch is created from main, the null check is added, tests pass, the fix is committed and pushed, and the developer's original work is restored.

## Key Checkpoints

1. **Agent verifies `gh` CLI is authenticated** (for PR creation later)
   - Runs `gh auth status` and confirms authentication before proceeding
   - If not authenticated, warns immediately so the developer can fix it before the hotfix is ready to deploy

2. **Agent stashes current uncommitted work on feat/dashboard**
   - Runs `git stash push -m "pre-hotfix: feat/dashboard" --include-untracked`
   - Confirms stash was created successfully before switching branches

3. **Agent creates hotfix branch from main** (`hotfix/fix-login-null-check`)
   - Checks out main: `git checkout main && git pull`
   - Creates hotfix branch: `git checkout -b hotfix/fix-login-null-check`
   - Does NOT branch from `feat/dashboard`

4. **Agent identifies and fixes the null check issue in login.ts:47**
   - Triages the issue (Phase 1), presents root cause, waits for confirmation
   - Plans a minimal fix (Phase 2), waits for approval
   - Adds the null check -- no refactoring, no cleanup

5. **Agent writes a regression test for the null case**
   - Creates a test that reproduces the exact null condition at line 47
   - Test fails without the fix, passes with it

6. **Agent runs targeted tests** (auth tests + regression test)
   - Runs the new regression test: `npm run test -- src/auth/login.spec.ts`
   - Runs related auth tests: `npm run test -- src/auth/`
   - Does NOT run the full test suite (scoped validation for speed)

7. **Agent runs typecheck and lint**
   - `npm run typecheck` passes
   - `npm run lint -- src/auth/login.ts` passes
   - Security quick-check passes (no secrets or insecure patterns introduced)

8. **Agent commits with clear message referencing the issue**
   - Commit message follows the format:
     ```
     fix(auth): add null check for login request body

     [HOTFIX] PROD-XXX

     Root cause: login.ts:47 did not guard against null request body,
     causing unhandled TypeError when upstream proxy sends empty payload
     ```
   - Waits for explicit user approval before committing

9. **Agent offers to create PR or push directly**
   - Presents PR template with hotfix label and rollback plan
   - Creates PR via `gh pr create` if approved
   - Alternatively pushes directly if user requests it

10. **Agent restores original branch and unstashes work**
    - Checks out original branch: `git checkout feat/dashboard`
    - Restores stashed work: `git stash pop`
    - Confirms the developer is back to their pre-hotfix state

## Anti-patterns

- **Agent should not start fixing without first saving current work** -- uncommitted changes on the feature branch must be stashed before any branch switching occurs. Losing a developer's in-progress work during an emergency makes the situation worse.

- **Agent should not create hotfix branch from feature branch (must be from main)** -- hotfix branches must always be created from the latest main. Branching from a feature branch would include unrelated, unreviewed changes in the hotfix.

- **Agent should not skip the regression test for an emergency fix** -- "it's urgent" is never a reason to skip the regression test. A hotfix without a regression test is a bug that will recur. The Iron Laws are explicit: "Regression test is mandatory."

- **Agent should not leave the developer on the hotfix branch after completion** -- the developer was working on `feat/dashboard` before the interruption. The skill must restore their original branch and unstash their work, returning them to exactly where they were.

- **Agent should not skip gh auth check if PR creation is needed** -- discovering authentication failure after the fix is ready wastes time. Verify `gh auth status` early in Phase 0 so the developer can authenticate while the fix is being prepared, not after.

## Known Gaps (Addressed)

The original skill definition had no Phase 0 for saving current work (stash), creating a hotfix branch from main, or verifying gh auth. It jumped straight into triage/fixing, which assumed the developer was already on a clean hotfix branch. This has been addressed by adding Phase 0: Prepare to the skill workflow.
