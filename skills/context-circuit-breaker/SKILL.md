---
name: context-circuit-breaker
description: Runtime enforcement hook that warns on context-multiplication patterns — subagent fan-out and expensive-call loops — before they run up cost. Warn-only, never blocks. Auto-loaded for all tool calls.
category: enforcement
user-invocable: false
---

# Context Circuit Breaker

Runtime `PreToolUse` hook for Claude Code. Tracks a short rolling window of
recent tool calls per session and surfaces a warning — via
`permissionDecisionReason` on an `allow` decision — when it detects one of
two context-multiplication patterns. It never blocks a call; the point is to
put the signal in front of the model before the cost compounds further, not
to stop it.

## What It Watches

| Pattern | Condition | Signal |
|---------|-----------|--------|
| Subagent fan-out | 5+ `Agent`/`Task` spawns within a 5-minute rolling window | Each spawn re-pays context/cache cost — suggests batching remaining work into fewer, larger-scoped agents |
| Expensive loop (repeat) | The same tool called with near-identical input 4+ times within the window | Likely a retry loop — suggests diagnosing root cause instead of repeating the call |
| Expensive loop (large + repeated) | The same tool called with >20,000 chars of input 4+ times within the window | Suggests narrowing scope or delegating to a subagent instead of repeating large-context calls inline |

State is kept in a small per-session file under the OS temp directory
(`claude-circuit-breaker-<session_id>.json`), pruned to the rolling window on
every call — no external dependencies, no network access.

## Installation

Add to your Claude Code settings (`~/.claude/settings.json` or project
`.claude/settings.json`):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "node .claude/skills/context-circuit-breaker/references/hook.js"
          }
        ]
      }
    ]
  }
}
```

This matcher applies to every tool call, since both fan-out and repeat
detection need visibility across tool types, not just one.

## What This Does Not Do

- **Never blocks.** Every decision is `permissionDecision: "allow"` — this
  hook only ever adds a warning, it cannot fail closed or interrupt a call.
- **Not a cost tracker.** It has no notion of tokens or dollars, only call
  counts and input size as a proxy. For actual post-hoc cost analysis, use
  `cost-audit` or `session-retro`, which read real trace/transcript data.
- **Session-scoped only.** The rolling window resets when the session id
  changes; it does not track patterns across sessions.

## Thresholds

Constants at the top of `references/hook.js` (`WINDOW_MS`,
`FANOUT_THRESHOLD`, `REPEAT_THRESHOLD`, `LARGE_INPUT_CHARS`). Adjust them
directly in the file if a project's normal workload trips the warning too
often or too rarely — there is no separate config file by design, to keep
this a single self-contained script.

## Acceptance Tests

| ID | Condition | Expected |
|----|-----------|----------|
| CB-T1 | 6 `Agent` tool calls within 5 minutes in one session | 5th call onward carries a fan-out warning |
| CB-T2 | 4 `Bash` calls with identical `command` within 5 minutes | 4th call carries a repeat warning |
| CB-T3 | 4 `Read` calls each with >20,000-char input within 5 minutes | 4th call carries a large-repeat warning |
| CB-T4 | A single normal tool call | No output (silent allow) |
| CB-T5 | 6 `Agent` calls spread more than 5 minutes apart | No fan-out warning (outside window) |
