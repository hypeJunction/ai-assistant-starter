---
name: start
description: Scope a work session to a ticket, worktree, and goal via flags — no mid-run prompts. Runs as a fixed phase queue over session_state.py and inherits the goal from the session-context plugin. Invoke as `/start [<ticket>] [--worktree|--no-worktree] [--goal=<text>] [--plan|--no-plan]`.
category: process
model: sonnet
effort: low
triggers:
  - start session
  - start ticket
  - new work item
  - begin task
  - pick up ticket
---

# Start

Scopes a session to a ticket, worktree, and goal, then hands off to native
plan mode. Every decision resolves at invocation; nothing is asked mid-run
that the machine can determine for itself.

`SS` below means `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/session_state.py --root .`
and `<id>` means this session's id. An unrecognized flag is an error: report
it and stop before planning.

## Flags

| Flag | Default | Effect |
|---|---|---|
| `<ticket>` | — | ticket or issue identifier |
| `--worktree` / `--no-worktree` | `--worktree` when a ticket is given | create an isolated git worktree |
| `--goal=<text>` | — | session goal, recorded verbatim, never paraphrased |
| `--plan` / `--no-plan` | `--plan` | enter native plan mode at handoff |

## The machine

One call lays out the queue, then each phase is claimed and reported:

```bash
SS plan --session <id> --flow start          # add --skip worktree for --no-worktree
SS next --session <id>                       # prints NEXT=<phase>
SS complete --session <id> --phase <phase> --status passed|skipped [--detail "..."]
```

`plan` auto-skips `worktree` when `.claude/worktree.json` already exists —
that is the inherit path, and it needs no separate branch in this document.
`next` refuses to hand out a phase until the previous one is reported, so the
order below is the only order that can happen. Run `next` between every
phase; never assume what it will say.

## Phases

### `scope` — establish the ticket
Use `<ticket>` if given. Otherwise read `SS status --session <id>`: if
`worktree.ticket` or `session_context.ticket` is set, adopt it silently. Only
with no ticket from any source, ask once via `AskUserQuestion`.

Fetch details through the Atlassian MCP — `getJiraIssue` for a key,
`searchJiraIssuesUsingJql` for a name. Delegate the fetch and the summary to
`dispatch`; it is self-contained lookup work and does not belong in this
context. If the fetch fails, ask the user to paste the details rather than
inventing them. Complete with the ticket key as `--detail`.

### `worktree` — branch and isolate
Pre-flight, then ask the machine for the names:

```bash
git rev-parse --show-toplevel && git fetch origin
SS branch-plan --ticket <T> --type "<issue type>" --summary "<ticket summary>"
```

That prints `BASE`, `BASE_CANDIDATES`, `BASE_AMBIGUOUS`, `BRANCH` and
`WORKTREE_PATH`. Take `BASE` as given when `BASE_AMBIGUOUS=0`; otherwise ask
once via `AskUserQuestion`, offering each of `BASE_CANDIDATES` plus an
"other" option, and re-run nothing. `BRANCH` and `WORKTREE_PATH` are the
machine's to decide — do not rename them.

```bash
git worktree add <WORKTREE_PATH> -b <BRANCH> <BASE>
SS --root <WORKTREE_PATH> worktree-init --ticket <T> --summary "<s>" --base <BASE> --branch <BRANCH>
```

Then `cd` into the new worktree. Every later `SS` call uses it as `--root`.

### `goal` — one line, recorded once
`--goal` verbatim when given. Otherwise run `SS goal --session <id>`: the
session-context plugin's intake question usually already recorded one, and
that is the goal — do not re-ask. With neither, derive one line from the
ticket.

The session-context plugin owns the goal. Record it there, not here:

- Invoke the `session-context:session` skill with `goal <text>` when the goal
  is new or has changed.
- `SESSION_CONTEXT=absent` means the plugin is not installed. Skip the call
  and complete the phase with the goal as `--detail`; nothing downstream
  depends on it.

A goal covering more than one concrete outcome is too broad — ask the user to
narrow it before completing this phase. Never start open-ended.

### `handoff` — plan or stop
Report the scope in four lines: ticket, branch, base, goal. Name any sibling
sessions from `SS status` under `siblings`. Then call `EnterPlanMode` under
`--plan`, or stop under `--no-plan`.

## State

- `.claude/worktree.json` — ticket, summary, base, branch. Written once per
  worktree, shared by every session in it.
- `.claude/sessions/<id>.json` — this session's flow and phase statuses.
- Goal and outcome live in the session-context plugin, which is also the only
  thing that posts either to Langfuse. This skill reads them and never writes
  a competing copy.

## Related

`/done` closes what this opens, `/trash` abandons it, and `/stack` shares the
worktree naming pattern.
