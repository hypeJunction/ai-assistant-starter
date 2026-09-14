# Claude Code Cost Optimization

A reference setup for reducing token/dollar spend in Claude Code without giving up
capability. Distilled from a working configuration; adapt the specifics (tool
names, paths, model choices) to your own environment.

This is reference material, not an installable skill — copy the pieces that
apply, adjust the rest.

## The three levers

### 1. Command-level filtering (biggest win on repetitive shell output)

A `PreToolUse` hook on `Bash` calls can rewrite expensive commands (verbose
`git status`, full `git log`, dependency listing commands, etc.) into
token-filtered equivalents before the output ever reaches the model — the
model never sees the tokens it didn't need. This works with any external
filtering tool exposed as a CLI; the shape is what matters:

```bash
#!/usr/bin/env bash
# ~/.claude/hooks/filter-rewrite.sh — PreToolUse hook, matcher: "Bash"
INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
[ -z "$CMD" ] && exit 0

# Delegate to whatever filtering tool/binary you use; it should exit 1
# (not 0) when there's no rewrite for this command, so the hook can
# pass the original command through untouched.
REWRITTEN=$(your-filter-tool rewrite "$CMD" 2>/dev/null) || exit 0
[ "$CMD" = "$REWRITTEN" ] && exit 0

ORIGINAL_INPUT=$(echo "$INPUT" | jq -c '.tool_input')
UPDATED_INPUT=$(echo "$ORIGINAL_INPUT" | jq --arg cmd "$REWRITTEN" '.command = $cmd')
jq -n --argjson updated "$UPDATED_INPUT" \
  '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "allow",
    permissionDecisionReason: "filtered rewrite", updatedInput: $updated}}'
```

Register it in `settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash", "hooks": [{ "type": "command", "command": "/home/you/.claude/hooks/filter-rewrite.sh" }] }
    ]
  }
}
```

Key properties that make this safe to leave always-on:
- **Fails open**: if the filtering tool or `jq` is missing, the hook exits 0
  and the original command runs unmodified — no silent breakage.
- **Transparent**: it rewrites the command, not the result — you still see
  real command output, just pre-filtered to the relevant subset.
- Track realized savings if your tool supports it (e.g. a `gain`/`stats`
  subcommand) so the hook's value is measurable, not assumed.

### 2. Model-tier routing (biggest win on agentic/subagent work)

Not every task needs your most capable — and most expensive — model. Route by
task class:

| Class | Model | Effort | Examples |
|---|---|---|---|
| mechanical | cheapest/fastest | none/low | git ops, renames, formatting, lookups, version bumps |
| implementation | mid-tier | medium | writing/editing code, standard feature work, tests |
| debugging | mid-tier | high | diagnosing failures, races, regressions, bisecting |
| architecture | top-tier | high | redesigns, tradeoff analysis, multi-file reasoning |
| extreme | top-tier, long-horizon | high | codebase-wide rewrites, multi-system migrations, RFCs |

Two ways to apply this:

- **Session-level default**: set a moderate default model/effort in
  `settings.json` (`"model"`, `"effortLevel"`) rather than maxing out effort
  on every turn by default.
- **Subagent-level enforcement**: when spawning subagents (Task/Agent tool),
  explicitly pass the model tier matching the task class — never default all
  subagents to your most expensive model. This can be automated with a
  `SessionStart` hook that injects the routing table as context, or a
  dedicated router hook/plugin that classifies prompts and sets the model
  parameter for you.

A general-purpose `dispatch`-style subagent — one that tries the cheapest
capable model first and escalates only when the worker signals it's out of
depth — is a good default for well-scoped, self-contained tasks (lookups,
mechanical edits, boilerplate, isolated fixes with clear acceptance
criteria). Keep ambiguous, architectural, or context-heavy work in the main
loop instead of delegating it down.

### 3. Context and process hygiene (compounds over a session/project)

These don't require any tooling, just discipline — and they compound, since
wasted context gets re-paid on every subsequent cache read in a session:

- **Clear stale sessions.** When resuming work after a long gap (new
  calendar day, or wall-clock time much greater than active work time),
  checkpoint progress into a short handoff note and start a fresh session
  rather than continuing in an old session's accumulated context — this
  holds even when it's a direct continuation of the same task. A session
  whose transcript already spans a prior calendar day is itself the trigger;
  don't wait for a second signal.
- **Delegate long sequential traces.** If a single turn/trace is running
  long — dozens of sequential exploration or verification calls against the
  same project — stop and delegate the remaining work to a subagent instead
  of continuing inline. Each additional turn in an already-large session
  re-pays cache-read on the full accumulated context.
- **Avoid redundant verification calls.** Before re-fetching state you
  already have (re-navigating a browser tab, re-reading a file you just
  wrote, re-running a check you just ran), check whether you already know
  the answer from earlier in the session.
- **Avoid blind bulk edits on structured files.** Regex/sed edits on config
  or source files that go wrong trigger expensive retry loops (broken
  build → diagnose → fix → rebuild). Use targeted, verified edits instead —
  slower per-edit, cheaper in aggregate.
- **Curate the permission allowlist.** A `defaultMode` that avoids
  interactive prompts for known-safe, already-approved commands (tests,
  lint, typecheck, read-only git) removes prompt round-trips from the loop.
  Pair this with an explicit `deny` list for destructive operations
  (`rm -rf`, force-push, hard reset, credential file reads) so the
  convenience doesn't become a safety tradeoff.
- **Audit periodically, don't guess.** If trace/observability data is
  available (e.g. via a tracing plugin), periodically audit real sessions
  for waste patterns — duplicate tool calls, retry loops, unusually
  expensive ("whale") sessions — and turn confirmed patterns into rules
  here, rather than optimizing on intuition alone.

## Suggested `settings.json` skeleton

```json
{
  "model": "sonnet",
  "effortLevel": "medium",
  "permissions": {
    "allow": [
      "Bash(git status:*)",
      "Bash(git diff:*)",
      "Bash(git log:*)",
      "Bash(npm run typecheck:*)",
      "Bash(npm run lint:*)",
      "Bash(npm run test:*)"
    ],
    "deny": [
      "Bash(rm -rf *)",
      "Bash(sudo *)",
      "Bash(git push --force*)",
      "Bash(git reset --hard*)",
      "Read(~/.ssh/**)",
      "Read(~/.aws/**)",
      "Read(./.env)"
    ],
    "defaultMode": "acceptEdits"
  },
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash", "hooks": [{ "type": "command", "command": "/home/you/.claude/hooks/filter-rewrite.sh" }] }
    ]
  }
}
```

Adjust the allowlist to your own package manager and toolchain — the point
is curating it deliberately, not the specific entries above.

## Getting started (for an assistant helping someone adopt this)

If you're an AI assistant walking a user through adopting this setup:

1. Ask which levers they want (filtering hook, model routing, process rules,
   or all three) rather than installing everything at once.
2. For the filtering hook: confirm they have (or want) a CLI filtering tool
   before wiring the hook — it fails open, so it's safe to add even if the
   tool isn't installed yet, but it's dead weight until then.
3. For model routing: check what subagent/model-selection mechanism their
   Claude Code setup already has before adding a new one — don't stack two
   routing mechanisms.
4. For process rules: add them to the user's own `CLAUDE.md` (global or
   project), not this repo's — they're personal working conventions, and
   should evolve from the user's own corrections/confirmations over time
   rather than being copied verbatim.
5. Don't copy someone else's `permissions.allow` list wholesale — it encodes
   their specific toolchain. Rebuild it for the new project/user instead.
