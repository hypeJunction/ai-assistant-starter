---
name: branch-protection
description: Runtime enforcement hook that blocks dangerous git operations on protected branches. Prevents force-push, hard reset, and branch deletion on main/master. Auto-loaded for all git operations.
category: enforcement
user-invocable: false
---

# Branch Protection

Runtime enforcement hook for Claude Code's PreToolUse hook system. Intercepts Bash tool calls and blocks dangerous git operations on protected branches.

## Protected Operations

| Command Pattern | Risk | Action |
|----------------|------|--------|
| `git push --force` / `git push -f` to main/master | Rewrites shared history | Block |
| `git reset --hard` on main/master | Destroys uncommitted work | Block |
| `git branch -D main` / `git branch -D master` | Deletes protected branch | Block |
| `git checkout .` / `git restore .` on main/master | Discards all changes | Warn |
| `git clean -fd` | Removes untracked files | Warn |

## Installation

Add to your Claude Code settings (`~/.claude/settings.json` or project `.claude/settings.json`):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "node .claude/skills/branch-protection/references/hook.js"
          }
        ]
      }
    ]
  }
}
```

## Configuration

The hook reads protected branch names from the environment or defaults to `main` and `master`:

```bash
export PROTECTED_BRANCHES="main,master,production"
```

## Warn vs Block

The hook protocol only supports `block` and passthrough. "Warn"-level operations are implemented as blocks with a softer confirmation-style message — the agent is told to ask the user before retrying.

## Feature-Branch Safety Reminder

`git reset --hard` and `git push --force` are allowed unconditionally on non-protected branches (BP-T4, BP-T5) — the hook does not block them there. That does not make them safe by default: before running either on any branch, the agent must run `git status` first and stash (`git stash -u`) or commit any uncommitted work it finds, so a feature-branch hard reset or force-push never silently discards it.

## Acceptance Tests

| ID | Type | Condition | Expected |
|----|------|-----------|----------|
| BP-T1 | Block | `git push --force origin main` | Blocked with explanation |
| BP-T2 | Block | `git reset --hard HEAD~3` on main branch | Blocked with explanation |
| BP-T3 | Block | `git branch -D main` | Blocked with explanation |
| BP-T4 | Allow | `git push --force origin feature/my-branch` | Allowed |
| BP-T5 | Allow | `git reset --hard HEAD~1` on feature branch | Allowed |
| BP-T6 | Allow | `git push origin main` (no --force) | Allowed |
| BP-T7 | Warn | `git checkout .` on main branch | Blocked with safety warning |
| BP-T8 | Warn | `git restore .` on main branch | Blocked with safety warning |
| BP-T9 | Warn | `git clean -fd` | Blocked with safety warning |
| BP-T10 | Allow | `git checkout .` on feature branch | Allowed |
| BP-T11 | Allow | `git clean -n` (dry run, no -f) | Allowed |
