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

## Acceptance Tests

| ID | Type | Condition | Expected |
|----|------|-----------|----------|
| BP-T1 | Block | `git push --force origin main` | Blocked with explanation |
| BP-T2 | Block | `git reset --hard HEAD~3` on main branch | Blocked with explanation |
| BP-T3 | Block | `git branch -D main` | Blocked with explanation |
| BP-T4 | Allow | `git push --force origin feature/my-branch` | Allowed |
| BP-T5 | Allow | `git reset --hard HEAD~1` on feature branch | Allowed |
| BP-T6 | Allow | `git push origin main` (no --force) | Allowed |
