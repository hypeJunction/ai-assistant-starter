---
name: start
description: Scope a new work session to a ticket, worktree, and goal via flags — no mid-run prompts for mode/config. Auto-triggers on session start; also invocable manually with `/start [<ticket>] [--worktree|--no-worktree] [--goal=<text>] [--plan|--no-plan]`.
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

Scopes a session to a ticket, worktree, and goal, then optionally hands off
into native plan mode. Unrecognized flags are an error — report and stop.

## Flags

| Flag | Description |
|------|-------------|
| `<ticket>` | optional ticket/issue identifier |
| `--worktree` / `--no-worktree` | create an isolated git worktree (default: `--worktree` if a ticket is given, else `--no-worktree`) |
| `--goal=<text>` | session goal, recorded verbatim, no paraphrase |
| `--plan` / `--no-plan` | enter native plan mode after scoping (default: `--plan`) |

Requires a `SessionStart` hook (`skills/start/hooks/session_start.py`,
matcher `startup|resume|clear`) in `.claude/settings.json` to auto-trigger —
add via `update-config` if missing; without it, `/start` still works typed
manually.

## State

Both written via `python3 skills/done/scripts/session_log.py`:
- `.claude/worktree.json` — ticket, Jira summary, base branch, branch name;
  written once per worktree, shared by every session in it.
- `.claude/sessions/<session_id>.json` — one per Claude Code session
  (`session_id` from the hook payload), so concurrent sessions in the same
  worktree never overwrite each other's goal/status; `/done` reads and
  updates this same file.

## Workflow

1. **Determine path.** Compare `git rev-parse --git-common-dir` vs
   `--git-dir`; if they differ this is a linked worktree. Worktree +
   `.claude/worktree.json` present → step 2. Otherwise → step 3. The
   `SessionStart` hook, when it fires this, already made this determination
   plus a sibling-session summary — use that instead of re-deriving it.

2. **Inherit.** Load `.claude/worktree.json`; print ticket, branch, base,
   and in-progress siblings (hook context, or `session_log.py siblings
   --session <id>`). Goal: `--goal` verbatim if given, else the ticket's
   original goal unless this session is a narrower continuation — infer
   from context, ask only if genuinely ambiguous. Go to step 5.

3. **Get the ticket.** Use `<ticket>` if given, else ask via
   `AskUserQuestion`. Fetch details via Atlassian MCP (`getJiraIssue` for a
   key, `searchJiraIssuesUsingJql` for a name); if the fetch fails, ask the
   user to paste details rather than inventing them.

4. **Resolve base, branch, worktree.** Pre-flight: confirm the repo via
   `git rev-parse --show-toplevel`, then `git fetch origin` first. Base:
   last two `origin/rel/*`-style branches by version — the one clear match
   silently, else ask with an "other" option. Branch prefix from issue type
   (Bug/Defect → `fix/`, Story/Task/Improvement → `ft/`); reuse the repo's
   own recent naming template if evident, else `git-conventions`'s
   `feature/TICKET-123-slug`. If `--worktree` is effective: `git worktree
   add ../<repo-basename>__<ticket-lower> -b <branch> <base>` (mirrors
   `/stack`'s `../wt-stack-<n>`), then `cd` into it, and write
   `.claude/worktree.json`:
   ```bash
   session_log.py --root . worktree-init --ticket <T> --summary "<s>" --base <base> --branch <branch>
   ```

5. **Scope the goal and write the session file.** `--goal` verbatim if
   given, else derive one line from the ticket; if it covers more than one
   concrete outcome, ask the user to narrow it — never start open-ended.
   ```bash
   session_log.py --root . start --session <id> --goal "<goal>"
   ```

6. **Enter plan mode.** If `--plan` is effective, call `EnterPlanMode`; if
   `--no-plan`, stop here.

`/done` closes the session this skill opens; `/stack` shares its worktree
naming pattern.
