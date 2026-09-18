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

Validation may already have run for these commits during `/commit`. Ask the user explicitly before re-running it:

```markdown
Validation (typecheck/lint/test) may already have run when these changes were committed. Re-run full validation now before creating/updating the PR? (yes / skip)
```

**Wait for user response.** If skip, note in the Step 10 report that validation was skipped on user request and proceed to Step 4. If yes, continue below.

Run full validation before creating PR. If issues are found, fix them and re-validate. Maximum 3 iterations. All checks must pass before proceeding.

Invoke `/validate --full` to run the complete CI pipeline.

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

### Step 4: Delegate Security Scan + Mixed-Concern Check

Both checks are read-only and don't need the main session's context — dispatch a single subagent (via the `Agent` tool) to run the scan and classify the diff, rather than pulling the full diff into the main agent. (See also `../commit/references/pre-commit-verification.md` and `../validate/references/security-scan-patterns.md` for detailed pattern guidance.)

Give the subagent the commands below and instructions to return only the digest format — not raw diff text (except for grep matches, which must be quoted in full):

```bash
MAIN=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")
CHANGED_FILES=$(git diff $MAIN...HEAD --name-only)

grep -rn --include="*.ts" --include="*.tsx" --include="*.js" --include="*.json" \
  -e "(api[_-]?key|secret|password|token|credential|private[_-]?key)\s*[:=]" \
  -e "(eval\(|new Function\(|innerHTML\s*=|dangerouslySetInnerHTML|document\.write\()" \
  -e "(\\\$queryRaw\`|\\\$executeRaw\`|\.query\(.*\\\$\{|SELECT.*\\\$\{|INSERT.*\\\$\{|UPDATE.*\\\$\{|DELETE.*\\\$\{)" \
  -e "(child_process|exec\(|execSync\(|spawn\(|execFile\()" \
  -e "(rejectUnauthorized:\s*false|NODE_TLS_REJECT_UNAUTHORIZED|--no-verify)" \
  -E $CHANGED_FILES | head -100

git diff $MAIN...HEAD
```

**Interpreting results (the subagent applies these, then reports its conclusion — not just raw matches):**
- Secrets in non-test files: **BLOCKER** — do not proceed
- `eval`/`innerHTML`/`dangerouslySetInnerHTML`: Requires justification — flag for review
- Raw SQL with interpolation: **BLOCKER** unless using tagged template literals
- `child_process`/`exec`: Flag for review — verify no user input reaches the command
- Disabled TLS/verification: **BLOCKER** unless in test configuration only

Exclude test files and example/documentation files from blocking — flag as informational only.

**Required digest format returned by the subagent:**

```markdown
## Security Scan
[Clean, or the specific file/line/pattern for each finding, quoted in full, marked BLOCKER or informational]

## Mixed-Concern Check
[None detected, or:]
- **Feature:** [files related to new behavior]
- **Refactor/other:** [files with structural or unrelated changes]
```

Read the digest before proceeding. If it reports a BLOCKER, stop and resolve it (fix and re-dispatch this step, or escalate to the user) before Step 5. If it flags mixed concerns, suggest splitting into separate PRs for faster review.

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

### Step 7: Determine Ticket Number(s)

Ask the user which ticket number(s) this PR should reference:

```markdown
Which ticket number(s) should this PR reference (e.g. T-1234)? List multiple separated by commas if more than one applies. Say "none" if there isn't one.
```

**Wait for user response.** If the user's request already lists ticket numbers explicitly (e.g. pasted issue links or `[CORE-4639] [CORE-4641]`), treat that as the answer instead of asking again.

Use the resulting set as `[TICKETS]` in the title and description below:

- **Title suffix** stays plain text regardless of ticket count (titles don't render markdown links) — e.g. `[T-1234]` or `[T-1234][T-1240]`. Every ticket must appear; never collapse to one or silently drop any.
- **Body ticket section** is one line per ticket, each rendered as a markdown link when a URL is known — `[TICKET](URL)`. A URL is known when the user pasted it (as issue links, or via a reference like `[CORE-4639]: https://...`) or it's otherwise established for this project (e.g. a tracker base URL already used in this session). If no URL is known for a ticket, list it as plain text (`TICKET`) on its own line rather than inventing a URL.
- **No tickets:** drop the ticket suffix from the title and omit the body's ticket section entirely — do not invent one.

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

- `## Summary` is one short paragraph (2-4 sentences) of plain prose describing the overall direction and motivation — not a changelog, not a list of edits. When the PR spans multiple tickets, the paragraph must synthesize one coherent narrative covering all of them (what they collectively accomplish), not a per-ticket recap or a paragraph per ticket.
- `## What changed` bullets describe user-visible or behavioral outcomes — never file names, function/variable names, or line-level detail (that's what the diff is for). Cap it at ~5 bullets; group related changes under one higher-level bullet rather than enumerating every commit. When multiple tickets are involved, group bullets by outcome, not by ticket — don't label bullets with ticket numbers.
- Include `## Test Plan` only when verification is non-obvious or hard to reproduce (special data setup, a race condition, a multi-step manual flow). Omit it entirely when existing tests or standard manual QA obviously cover the change.
- Include `## Security` only when the change actually touches something security-relevant (auth, secrets, input handling, permissions, new dependencies). Omit it entirely otherwise — don't pad every PR with an always-N/A checklist.
- Title format is `[component]: [description] [TICKETS]` — a component/scope name (the area of the codebase affected), not a conventional-commit type. With multiple tickets, list every ticket back-to-back, e.g. `[T-1234][T-1240]`. Omit the ticket suffix entirely if there's no ticket (Step 7).
- Add the ticket(s) at the very end of the body, after every other section — one ticket per line, each a markdown link (`[TICKET](URL)`) when its URL is known, plain text otherwise. Never combine multiple tickets on one line, and never omit one. Omit the section entirely if there's no ticket.

**If creating a new PR:**

```bash
gh pr create --title "[component]: Brief description [TICKETS]" --body "$(cat <<'EOF'
## Summary

[One paragraph: what this PR does and why, in plain language, for a reviewer with no prior context. If multiple tickets are involved, synthesize one narrative covering all of them.]

## What changed

- [Main change 1, described by behavior/outcome]
- [Main change 2]

## Test Plan

[Include only if verification isn't obvious — omit this section otherwise]

## Security

[Include only if the change touches something security-sensitive — omit this section otherwise]

## Screenshots (if applicable)

[Add screenshots for UI changes]

[TICKETS]
EOF
)"
```

`[TICKETS]` is every referenced ticket, one per line, each a markdown link when its URL is known, e.g.:

```markdown
[T-1234](https://tracker.example.com/browse/T-1234)
[T-1240](https://tracker.example.com/browse/T-1240)
```

**If updating an existing PR:**

```bash
gh pr edit [number] --title "[component]: Brief description [TICKETS]" --body "$(cat <<'EOF'
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
**Validation:** [Passed / Skipped on user request]

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
| PR-T6 | Negative | "Fix the CI failures on my PR" | Does NOT trigger (-> /implement --pr-iterate) |
| PR-T7 | Boundary | "Commit and create a PR" | Triggers (PR is the final intent) |
| PR-T8 | Early-exit | No commits ahead of base branch | Reports "Nothing to push" and exits |
| PR-T9 | Positive | "Fix the description on PR #123" | Skill triggers, jumps to Step 6 (existing PR) then Step 9 with `gh pr edit`, not a standalone `gh` call |
| PR-T10 | Boundary | Request lists two ticket links, e.g. "[CORE-4639] [CORE-4641]" with URLs | Step 7 treats both as given (no re-ask); title suffix is `[CORE-4639][CORE-4641]`; body lists each as its own markdown-link line; Summary synthesizes one narrative, not two |

## PR Title Conventions

Format per the title rule under "Push and Create/Update PR" above. Examples:

```
auth: add user authentication [T-1204]
login: resolve issue with special characters [T-1198]
validation: extract shared validation logic [T-1310]
docs: update API documentation [T-1322]
deps: update dependencies
auth: add login and session refresh [T-1204][T-1207]
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
