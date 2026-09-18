---
name: start
description: Scope a new work session to a ticket, worktree, and goal before any code is written. Auto-triggers on session start; also invocable manually.
category: process
model: sonnet
effort: medium
triggers:
  - start session
  - start ticket
  - new work item
  - begin task
  - pick up ticket
---

# Start

> **Purpose:** Turn "I have a ticket" into a scoped worktree, a one-line goal, and a Plan Mode kickoff — never an open-ended session.
> **Usage:** `/start` (also fires automatically via a `SessionStart` hook on every new/cleared session)

## Constraints

- Never leave a session's goal unscoped — if the ticket implies more than one
  concrete outcome, ask the user to narrow it before continuing.
- Never invent a Jira ticket's contents — if the Atlassian MCP fetch fails,
  ask the user to paste the details.
- Never guess a base branch when more than one release branch is a plausible
  target — ask, offering the two most recent as options.
- Never skip Plan Mode — no exploration or code changes start before it.

## Setup (one-time per project)

This skill needs its `SessionStart` hook registered in the project's
`.claude/settings.json` (matcher `startup|resume|clear`, pointing at
`skills/start/hooks/session_start.py`) to auto-trigger. Use the
`update-config` skill to add it if it isn't already there. Without the hook,
`/start` still works when typed manually.

## State

Two files at the worktree root (gitignored):
- `.claude/worktree.json` — ticket, Jira summary, base branch, branch name.
  Written once, shared by every session that works in this worktree.
- `.claude/sessions/<session_id>.json` — one per Claude Code session
  (`session_id` from the `SessionStart` hook payload), so concurrent
  sessions in the same worktree never overwrite each other's goal/status.

## Workflow

### Step 0: Determine path

Compare `git rev-parse --git-common-dir` vs `--git-dir` in the current
directory — if they differ, this is a linked worktree.

- **Worktree + `.claude/worktree.json` exists** → **Inherit path** (Step 1).
- **Otherwise** (root checkout, or a worktree with no state file yet) →
  **From-scratch path** (Step 2).

When triggered by the `SessionStart` hook, the hook has already made this
determination and tells you which path to take, plus a summary of any
sibling sessions already working in this worktree — use that instead of
re-deriving it.

### Step 1: Inherit Path

1. Load `.claude/worktree.json` — ticket, branch, base.
2. Print a one-line summary: ticket, branch, base, and any in-progress
   sibling sessions (from the hook context or
   `python3 skills/done/scripts/session_log.py --root . siblings --session <id>`).
3. Confirm the goal for *this* session. It may be the same as the ticket's
   original goal, or a narrower continuation (e.g. "fix the regression the
   last session's tests found") — ask if it's not obvious from context.
4. Write `.claude/sessions/<session_id>.json`:
   ```bash
   python3 skills/done/scripts/session_log.py --root . start --session <id> --goal "<goal>"
   ```
5. Go to Step 6 (Plan Mode).

### Step 2: From-Scratch Path — Get the Ticket

Ask for the ticket number or work item name via `AskUserQuestion`, unless
already given in the user's request.

### Step 3: Fetch Ticket Details

Use the Atlassian MCP connector:
- `mcp__claude_ai_Atlassian__getJiraIssue` if a ticket key was given.
- `mcp__claude_ai_Atlassian__searchJiraIssuesUsingJql` if only a name/summary
  was given, to find the matching issue first.

Extract summary, description, issue type, and status. If the fetch fails
(no connection, ticket not found), ask the user to paste the details
manually rather than inventing them.

### Step 4: Determine Base Branch

List branches matching a release-prefix pattern (default `rel/`, e.g.
`rel/2.6`, `rel/2.7`), sorted by version, and take the last two:

```bash
git branch -a --list 'rel/*' 'origin/rel/*' | sed 's#remotes/origin/##' | sort -V -u | tail -2
```

- If exactly one clearly matches the ticket's target version, use it
  silently.
- Otherwise present the last two via `AskUserQuestion` plus an "other"
  free-text option — never guess between two plausible release branches.

### Step 5: Determine Branch Name

Infer the prefix from the Jira issue type (Bug/Defect → `fix/`,
Story/Task/Improvement → `ft/`; ask if ambiguous).

Don't hardcode one naming scheme for every consumer repo — sample the
target repo's recent non-backup branch names and check whether most match
`^(\w+)/([\d.]+)\+(.+)$` (e.g. `ft/2.5+rel-filter`,
`fix/2.6+core-4641-offline-component-status`). If they do, reuse that
template: `<ft|fix>/<base-version>+<TICKET>-<slug>`. Otherwise fall back to
`git-conventions`'s `feature/TICKET-123-slug` / `fix/TICKET-456-slug`.

### Step 6: Create the Worktree

```bash
git worktree add ../<repo-basename>__<ticket-lower> -b <branch> <base>
```

Sibling directory, mirroring the `/stack` skill's
`git worktree add ../wt-stack-<n> -b ...` pattern
(`skills/stack/SKILL.md`).

### Step 7: Write State

```bash
cd ../<repo-basename>__<ticket-lower>
python3 <path-to>/skills/done/scripts/session_log.py --root . worktree-init \
  --ticket <TICKET> --summary "<jira summary>" --base <base> --branch <branch>
python3 <path-to>/skills/done/scripts/session_log.py --root . start --session <id> --goal "<goal>"
```

### Step 8: Scope the Goal

Derive a one-line goal from the Jira summary and description. If it reads
broad or covers multiple outcomes, ask the user to narrow it to one concrete
outcome before proceeding. Never start a session with an open-ended goal.

### Step 9: Enter Plan Mode

Call `EnterPlanMode`, then ask the user directly how they'd like to approach
the problem — this seeds the exploration and plan phases that follow,
rather than the agent guessing an approach unprompted.

## Related Skills

- `/done` — closes out the session this skill opens: commit, PR, session
  bookkeeping, compaction nudge.
- `/plan` — the Plan Mode workflow this skill hands off into at Step 9.
- `/stack` — the worktree-per-bucket pattern this skill's worktree naming
  mirrors.
