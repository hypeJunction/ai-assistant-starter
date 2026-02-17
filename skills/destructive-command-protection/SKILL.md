---
name: destructive-command-protection
description: Runtime enforcement hook that blocks destructive system and database commands. Prevents accidental rm -rf, database drops, and other irreversible operations. Auto-loaded for all command execution.
category: enforcement
user-invocable: false
---

# Destructive Command Protection

Runtime enforcement hook for Claude Code's PreToolUse hook system. Intercepts Bash tool calls and blocks commands that could cause irreversible damage.

## Blocked Operations

| Command Pattern | Risk | Action |
|----------------|------|--------|
| `rm -rf /` or `rm -rf ~` or `rm -rf .` | Filesystem destruction | Block |
| `rm -rf` with no path guard | Accidental recursive deletion | Warn |
| `DROP DATABASE` / `DROP SCHEMA` | Database destruction | Block |
| `TRUNCATE TABLE` without WHERE | Mass data deletion | Block |
| `mkfs` / `dd if=` to disk devices | Disk formatting/overwrite | Block |
| `chmod -R 777` | Security degradation | Block |
| `:(){ :|:& };:` (fork bomb) | System crash | Block |
| `> /dev/sda` or writes to block devices | Disk corruption | Block |
| `kill -9 1` / `kill -9 -1` | System process termination | Block |

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
            "command": "node .claude/skills/destructive-command-protection/references/hook.js"
          }
        ]
      }
    ]
  }
}
```

## Acceptance Tests

| ID | Type | Condition | Expected |
|----|------|-----------|----------|
| DC-T1 | Block | `rm -rf /` | Blocked |
| DC-T2 | Block | `rm -rf ~` | Blocked |
| DC-T3 | Block | `DROP DATABASE production` | Blocked |
| DC-T4 | Block | `chmod -R 777 /` | Blocked |
| DC-T5 | Allow | `rm -rf ./node_modules` | Allowed (specific safe path) |
| DC-T6 | Allow | `rm -rf dist/` | Allowed (build artifact) |
| DC-T7 | Allow | `DROP TABLE IF EXISTS temp_migration` | Allowed (specific table, conditional) |
| DC-T8 | Block | `dd if=/dev/zero of=/dev/sda` | Blocked |
