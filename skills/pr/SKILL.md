---
name: pr
description: Create a well-documented GitHub pull request with quality checks, proper description, and test plan. Use when pushing a branch, creating a merge request, or preparing code for review.
category: process
model: sonnet
effort: medium
triggers:
  - create PR
  - pull request
  - ready for review
  - open PR
  - fix PR description
  - update PR description
---

# Create Pull Request

> **Purpose:** Create a well-documented PR with proper description and test plan
> **Usage:** `/pr`

## Constraints

- All tests must pass before creating PR
- Never force push without explicit request
- Always verify changes are committed before pushing
- Requires `gh` (GitHub CLI) for PR creation
- Flag mixed-concern PRs (feature + refactor) as candidates for splitting
- Never call `gh pr create` or `gh pr edit` outside this workflow — any request to open, create, update, or fix the description of a pull request goes through this skill (starting at whichever step already applies, e.g. Step 6 if the PR already exists), not a standalone `gh` invocation. This applies even when opening several PRs back-to-back as part of a larger task.

> **Note:** Command examples use `npm` as default. Adapt to the project's package manager per `ai-assistant-protocol` — Project Commands.

## Workflow

### Step 0: Check for Uncommitted Changes

```bash
git status --porcelain
```

If uncommitted changes are detected, present options and **wait for user response**:

```markdown
Uncommitted changes detected:
  [list of modified/untracked files]

Options:
  (a) Commit these changes first
  (b) Stash them for now
  (c) Abort — resolve manually

Which would you like to do?
```

**Do not proceed with uncommitted changes.** Handle them based on the user's choice before continuing.

### Step 1: Verify GitHub CLI Authentication

```bash
gh auth status
```

If not authenticated, instruct the user:

```markdown
GitHub CLI is not authenticated. Run `gh auth login` to authenticate, then re-run `/pr`.
```

**Do not proceed without authentication** — PR creation and existing PR detection both require it.

### Step 2: Verify Changes

```bash
MAIN=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")

git status
git diff $MAIN...HEAD --stat
git log $MAIN..HEAD --oneline
```

**If no commits ahead of base branch and no uncommitted changes:** Report "Nothing to push — branch is up to date with base" and exit.

### Step 3: Validate (with Re-Validation Loop)

Run full validation before creating PR. If issues are found, fix them and re-validate. Maximum 3 iterations. All checks must pass before proceeding.

**Delegate to a subagent** — Run this via the `Agent` tool (an independent subagent), never directly in the main agent's shell. Give the subagent the exact command(s) and require full raw output back; read that output yourself before reporting results. See `ai-assistant-protocol` § Validation Execution.

```bash
npm run typecheck
npm run lint
npm run test
```

**Iteration loop:**

1. Run all validation checks
2. If issues are found (type errors, lint warnings/errors, test failures):
   - Fix the issues
   - Re-run all validation checks
3. Repeat until all checks pass or 3 iterations reached
4. If still failing after 3 iterations, report remaining issues and ask user how to proceed

Report format:

```markdown
### Validation (iteration N)

| Check | Status | Details |
|-------|--------|---------|
| Typecheck | PASSED / FAILED | [N errors] |
| Lint | PASSED / FAILED | [N errors, M warnings] |
| Tests | PASSED / FAILED | [N passed, M failed] |
```

**Do not proceed until all checks pass.**

### Step 4: Security Scan

Run concrete security scan commands against the changed files (see also `../commit/references/pre-commit-verification.md` and `../validate/references/security-scan-patterns.md` for detailed pattern guidance):

```bash
MAIN=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")
CHANGED_FILES=$(git diff $MAIN...HEAD --name-only)

# Secrets detection
grep -rn --include="*.ts" --include="*.tsx" --include="*.js" --include="*.json" \
  -E "(api[_-]?key|secret|password|token|credential|private[_-]?key)\s*[:=]" $CHANGED_FILES

# Insecure pattern detection
grep -rn --include="*.ts" --include="*.tsx" --include="*.js" \
  -E "(eval\(|new Function\(|innerHTML\s*=|dangerouslySetInnerHTML|document\.write\()" $CHANGED_FILES

# Raw SQL interpolation (injection risk)
grep -rn --include="*.ts" --include="*.tsx" --include="*.js" \
  -E "(\\\$queryRaw\`|\\\$executeRaw\`|\.query\(.*\\\$\{|SELECT.*\\\$\{|INSERT.*\\\$\{|UPDATE.*\\\$\{|DELETE.*\\\$\{)" $CHANGED_FILES

# Command injection patterns
grep -rn --include="*.ts" --include="*.tsx" --include="*.js" \
  -E "(child_process|exec\(|execSync\(|spawn\(|execFile\()" $CHANGED_FILES

# Disabled security controls
grep -rn --include="*.ts" --include="*.tsx" --include="*.js" \
  -E "(rejectUnauthorized:\s*false|NODE_TLS_REJECT_UNAUTHORIZED|--no-verify)" $CHANGED_FILES
```

**Interpreting results:**
- Secrets in non-test files: **BLOCKER** — do not proceed
- `eval`/`innerHTML`/`dangerouslySetInnerHTML`: Requires justification — flag for review
- Raw SQL with interpolation: **BLOCKER** unless using tagged template literals
- `child_process`/`exec`: Flag for review — verify no user input reaches the command
- Disabled TLS/verification: **BLOCKER** unless in test configuration only

Exclude test files and example/documentation files from blocking — flag as informational only.

### Step 5: Check for Mixed Concerns

Review the diff for mixed-concern changes. If commits include both feature work and refactoring, or both bug fixes and cleanup, suggest splitting into separate PRs for faster review.

### Step 6: Check for Existing PR

Before creating a new PR, check if one already exists for this branch:

```bash
gh pr view --json number,url,title,state 2>/dev/null
```

**If a PR exists:**

```markdown
Existing PR detected: #[number] ([state])
Title: [title]
URL: [url]

Options:
  (a) Update existing PR #[number]
  (b) Close #[number] and create a new PR
  (c) Abort

Recommend: Update existing PR.
```

**Wait for user response.** If updating, use `gh pr edit` instead of `gh pr create`.

### Step 7: Determine Ticket Number

Ask the user which ticket number this PR should reference:

```markdown
Which ticket number should this PR reference (e.g. T-1234)? Say "none" if there isn't one.
```

**Wait for user response.** Use their answer as `[TICKET]` in the title and description below. If they say there's no ticket, drop the `[TICKET]` suffix from both the title and the body — do not invent one.

### Step 8: Confirm Before Pushing

Present the full PR plan and **wait for explicit user approval** before pushing or creating/updating the PR:

```markdown
**Branch:** [branch name]
**Target:** [base branch]
**Commits:** [N commits]
**Action:** [Create new PR / Update existing PR #N]

**Proposed title:** [component]: [description] [TICKET]

[Full PR body preview]

Confirm push and [create/update] PR? (yes / edit / cancel)
```

**GATE: Do NOT push or create/update the PR until user responds with explicit approval.**

### Step 9: Push and Create/Update PR

```bash
git push -u origin HEAD
```

**PR Description Guidelines:**

Write for a reviewer who has no idea what problem is being solved or what the solution is — spell out context, don't assume shared background.

- `## Summary` is one short paragraph (2-4 sentences) of plain prose describing the overall direction and motivation — not a changelog, not a list of edits.
- `## What changed` bullets describe user-visible or behavioral outcomes — never file names, function/variable names, or line-level detail (that's what the diff is for). Cap it at ~5 bullets; group related changes under one higher-level bullet rather than enumerating every commit.
- Include `## Test Plan` only when verification is non-obvious or hard to reproduce (special data setup, a race condition, a multi-step manual flow). Omit it entirely when existing tests or standard manual QA obviously cover the change.
- Include `## Security` only when the change actually touches something security-relevant (auth, secrets, input handling, permissions, new dependencies). Omit it entirely otherwise — don't pad every PR with an always-N/A checklist.
- Title format is `[component]: [description] [TICKET]` — a component/scope name (the area of the codebase affected), not a conventional-commit type. Omit the ` [TICKET]` suffix entirely if there's no ticket (Step 7).
- Add the ticket as a standalone `[TICKET]` line at the very end of the body, after every other section. Omit it entirely if there's no ticket.

**If creating a new PR:**

```bash
gh pr create --title "[component]: Brief description [TICKET]" --body "$(cat <<'EOF'
## Summary

[One paragraph: what this PR does and why, in plain language, for a reviewer with no prior context.]

## What changed

- [Main change 1, described by behavior/outcome]
- [Main change 2]

## Test Plan

[Include only if verification isn't obvious — omit this section otherwise]

## Security

[Include only if the change touches something security-sensitive — omit this section otherwise]

## Screenshots (if applicable)

[Add screenshots for UI changes]

[TICKET]
EOF
)"
```

**If updating an existing PR:**

```bash
gh pr edit [number] --title "[component]: Brief description [TICKET]" --body "$(cat <<'EOF'
[same body template as above]
EOF
)"
```

**When updating because new commits landed:** rewrite the description fresh rather than appending to it.

- Re-derive the `## Summary` paragraph so it still describes the PR's *current* overall direction — edit it in place, don't bolt on a second paragraph for the new commits.
- Add a bullet to `## What changed` only for genuinely new user-facing behavior. If a new commit just fixes or tweaks something already covered by an existing bullet, leave that bullet as-is instead of adding another one.
- Never let the description grow into a changelog or edit history across updates — it should always read as if written fresh for the branch's current state.

### Step 10: Report

```markdown
**PR:** #[number] — [title]
**URL:** [url]
**Status:** [Created / Updated]
**Branch:** [branch] → [base]
**Commits:** [N]

**Next:** Wait for CI checks, request reviewers, or continue working.
```

## Acceptance Tests

| ID | Type | Prompt / Condition | Expected |
|----|------|--------------------|----------|
| PR-T1 | Positive | "Create a pull request" | Skill triggers |
| PR-T2 | Positive | "Ready for review" | Skill triggers |
| PR-T3 | Positive | "Open a PR for this branch" | Skill triggers |
| PR-T4 | Negative | "Commit my changes" | Does NOT trigger (-> /commit) |
| PR-T5 | Negative | "Review the code" | Does NOT trigger (-> /review) |
| PR-T6 | Negative | "Fix the CI failures on my PR" | Does NOT trigger (-> /iterate-pr) |
| PR-T7 | Boundary | "Commit and create a PR" | Triggers (PR is the final intent) |
| PR-T8 | Early-exit | No commits ahead of base branch | Reports "Nothing to push" and exits |
| PR-T9 | Positive | "Fix the description on PR #123" | Skill triggers, jumps to Step 6 (existing PR) then Step 9 with `gh pr edit`, not a standalone `gh` call |

## PR Title Conventions

Format: `component: brief description [TICKET]` — the component is the area of the codebase the change affects, not a conventional-commit type. Drop the `[TICKET]` suffix if there's no ticket.

```
auth: add user authentication [T-1204]
login: resolve issue with special characters [T-1198]
validation: extract shared validation logic [T-1310]
docs: update API documentation [T-1322]
deps: update dependencies
```

## Example PR Body

```markdown
## Summary

Users currently have no way to authenticate — every API endpoint is open. This adds token-based login so requests can be tied to a user and existing routes can be locked down behind auth.

## What changed

- Users can register and log in, receiving a token to use for future requests
- Passwords are stored securely rather than in plain text
- Existing API routes now require a valid token

## Security

- [ ] Passwords hashed before storage, never logged or returned in responses
- [ ] Auth checks added to all previously-open routes
- [ ] N/A — input validation (handled by existing framework middleware)

## Breaking Changes

None — new endpoints only; existing routes now require a token, which is called out above.

[T-1204]
```

Title for this example: `auth: add token-based login [T-1204]`.

Note what's absent: no `## Test Plan` (login/registration is standard flow, covered by the new test suite included in the PR), no file names or variable names anywhere in the body.
