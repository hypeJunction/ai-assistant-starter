# Guard

Single `PreToolUse` runtime enforcement process for Claude Code. Reads the
hook JSON from stdin once and dispatches to a fixed list of pluggable
modules instead of spawning one node process per check. Wired into every
tool call via `plugins/ai-assistant-starter/hooks/hooks.json` — not a
Claude-invoked skill.

## Trigger

Runs on every `PreToolUse` call (`matcher: "*"`). Each module below is gated
internally by tool name — a module that only applies to `Bash` calls is
skipped entirely for other tools, and never runs its detection logic
against them.

## Modules, in order

| Order | Module | Applies to | Decision strength | Source |
|---|---|---|---|---|
| 1 | `destructive-command` | `Bash` | `deny` | `hooks/destructive-command-protection/hook.js` |
| 2 | `branch-protection` | `Bash` | `deny` / `ask` | `hooks/branch-protection/hook.js` |
| 3 | `secret-scan` | `Bash` (`git commit`) | `ask` only | `hooks/guard/modules/secret-scan.js` |
| 4 | `main-shell-run` | `Bash` | `allow` only (advisory) | `hooks/guard/modules/main-shell-run.js` |
| 5 | `cost-guardrail` | `Bash`, `Agent` | `deny` (enforce mode) / `ask` (warn-only mode) | `hooks/cost-guardrail/hook.js` |
| 6 | `circuit-breaker` | every tool | `allow` only (advisory) | `hooks/context-circuit-breaker/hook.js` |

Each existing hook directory keeps its own detection logic, thresholds, and
standalone CLI behavior unchanged — `hook.js` in each of those directories
still reads stdin and prints a hook response when run directly. `guard`
only adds an `evaluate(input)` entrypoint to each one and calls that instead
of shelling out to a second process.

## Combination rule

The most restrictive decision wins: `deny` > `ask` > `allow`. Evaluation
stops at the first module that returns `deny` — nothing downstream of it
runs. `main-shell-run` and `circuit-breaker` are advisory-only: they never
return anything but `allow`, so they can never raise the decision past
whatever the other modules already produced; their reason text is appended
to the final `permissionDecisionReason` instead. If no module returns a
decision or advisory text, `guard` prints nothing (silent allow), matching
each individual hook's current behavior.

## Why `main-shell-run` is advisory-only, not `ask`

The PreToolUse hook input has no field this repo's other hooks rely on, or
that's been found to reliably distinguish "this Bash call came from the
main agent" from "this Bash call came from inside a subagent" (e.g. the
`verifier` subagent that's supposed to run exactly these commands). Making
this module `ask` or `deny` would risk stalling that subagent's own
legitimate test/lint/build runs with no way to tell the two contexts apart.
Staying `allow`-only means it can flag the pattern without ever blocking
automation that depends on running it.

## Fail-open guarantee

Every module call is wrapped in its own try/catch inside `hook.js` — a
module that throws is treated exactly like one that returned no result, and
never stops the remaining modules or `guard` itself from running. Each
module also preserves its own existing fail-open paths:

- `destructive-command` / `branch-protection`: unparsable stdin, or (for
  branch-protection) a `git branch --show-current` failure, resolve to no
  match rather than an error.
- `secret-scan`: any `git diff --cached` failure (not a repo, git missing,
  nothing staged) is a silent allow.
- `cost-guardrail`: `cost_baselines.json` missing, unparsable, stale beyond
  `COST_GUARDRAIL_MAX_STALENESS_DAYS`, or short on samples is a silent
  allow — see `hooks/cost-guardrail/README.md`.
- `circuit-breaker` / `main-shell-run`: never deny or ask, by design.

## Configuration

Reused verbatim from the wrapped modules — see each one's own README:

- `PROTECTED_BRANCHES` (branch-protection)
- `COST_GUARDRAIL_MODE`, `COST_GUARDRAIL_FACTOR`, `COST_GUARDRAIL_BASELINE_PATH`,
  `COST_GUARDRAIL_MAX_STALENESS_DAYS` (cost-guardrail)

`secret-scan` and `main-shell-run` have no separate configuration — their
pattern lists live as constants at the top of their own files.

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
            "command": "node .claude/hooks/guard/hook.js"
          }
        ]
      }
    ]
  }
}
```

## Acceptance tests

| ID | Condition | Expected |
|----|-----------|----------|
| G-T1 | `git status` | Silent allow |
| G-T2 | `rm -rf /` | `deny`, reason prefixed `destructive-command:` |
| G-T3 | `git push --force origin main` on `main` | `deny`, reason prefixed `branch-protection:` |
| G-T4 | `git commit` with a planted secret in the staged diff | `ask`, reason prefixed `secret-scan:`, names file/line |
| G-T5 | `npm test` | `allow`, advisory `[main-shell-run]` reason naming the `verifier` subagent |
| G-T6 | `cost_baselines.json` absent, `Agent` spawn requesting an expensive tier | Silent allow (fail open) |
| G-T7 | 6 rapid `Agent` spawns in one session | `allow` on the 6th call, with `[circuit-breaker]` fan-out advisory appended |
