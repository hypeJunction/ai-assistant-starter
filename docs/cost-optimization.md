# Claude Code Cost Optimization

A reference setup for reducing token/dollar spend in Claude Code without giving up
capability. Distilled from a working configuration; adapt the specifics (tool
names, paths, model choices) to your own environment.

This is reference material, not an installable skill — copy the pieces that
apply, adjust the rest.

## Fork mode and `CLAUDE_CODE_FORK_SUBAGENT`

A claim has circulated that a Claude Code update made subagents "fork" by
default — silently inheriting the full parent conversation instead of
starting with isolated context. The env var it names,
`CLAUDE_CODE_FORK_SUBAGENT`, **is real** (Claude Code ≥2.1.232) — but the
framing overstates what it controls.

`CLAUDE_CODE_FORK_SUBAGENT` governs **fork mode**: whether Claude can spawn
the `fork` subagent type at all, and the background-execution behavior of
whatever subagents it does spawn (fork mode on runs both forks and non-forks
in the background by default, apart from cases that must stay foreground).
It is on by default in interactive sessions (≥2.1.232) and off by default in
non-interactive mode (`-p`) and the Agent SDK. Set it to `1` to force fork
mode on everywhere (including non-interactive/SDK), or `0` to force it off
everywhere.

What it does **not** do: change whether a *non-fork* subagent (`general-purpose`,
`Explore`, a definition-based agent) inherits context. Those still start
fresh and isolated — system prompt, task message, CLAUDE.md, git status,
preloaded skills — regardless of fork mode. A fork inheriting the parent's
full context is the explicit, unchanged purpose of that subagent type; fork
mode just gates whether Claude is allowed to request it and how it's
scheduled. See
[code.claude.com/docs/en/sub-agents](https://code.claude.com/docs/en/sub-agents)
for the authoritative description.

If you specifically want to guarantee no fork-type subagents ever spawn
(e.g. to bound cost from context-inheriting subagents), two real options:

- **`CLAUDE_CODE_FORK_SUBAGENT=0`** — turns off fork mode everywhere; Claude
  can't spawn forks and background-runs only the documented exceptions.
- **`permissions.deny: ["Agent(fork)"]`** — a more surgical rule that blocks
  the `fork` subagent type specifically, leaving fork mode's background
  scheduling behavior for other subagents untouched.

## The levers

### 0. Cost-saving env vars (near-zero setup cost)

A handful of genuinely documented env vars
([code.claude.com/docs/en/env-vars](https://code.claude.com/docs/en/env-vars))
cut cost with no behavior tradeoff, plus a couple that trade a small behavior
change for a hard ceiling on runaway command/fork cost:

| Var | Effect | Tradeoff |
|---|---|---|
| `DISABLE_TELEMETRY` | Turns off telemetry collection | None |
| `DISABLE_ERROR_REPORTING` | Turns off error reporting | None |
| `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` | Disables non-essential network calls | None |
| `CLAUDE_CODE_FORK_SUBAGENT` | `0` disables fork-mode subagents entirely; `1` forces it on everywhere | `0` means Claude can no longer use forks for cheap cache-sharing background research |
| `BASH_DEFAULT_TIMEOUT_MS` | Default timeout for Bash commands | Commands can now time out that previously ran unbounded |
| `BASH_MAX_TIMEOUT_MS` | Hard cap on a requested timeout | Same |
| `BASH_MAX_OUTPUT_LENGTH` | Truncates large Bash output before it reaches the model | Long legitimate output can get cut |

These are offered as an explicit opt-in step (`/apply-template`'s Step 5.7) —
none are installed by default, and `CLAUDE_CODE_FORK_SUBAGENT`/`BASH_*` are
called out separately from the telemetry-only ones since they change runtime
behavior.

`DISABLE_TELEMETRY` only turns off Anthropic's own internal usage telemetry —
it's independent of OpenTelemetry export configuration, so it does not affect
a Langfuse-based tracing setup (what `cost-audit`/`cost-guardrail` read from).

### 1. Command-level filtering (biggest win on repetitive shell output)

A `PreToolUse` hook on `Bash` calls can rewrite expensive commands (verbose
`git status`, full `git log`, dependency listing commands, etc.) into
token-filtered equivalents before the output ever reaches the model — the
model never sees the tokens it didn't need.

**Option A — dedicated CLI proxy tool.** [`rtk`](https://github.com/rtk-ai/rtk)
("Rust Token Killer") is a purpose-built proxy for this: it ships a rewrite
registry for common dev commands (`git`, `find`, package-manager output,
etc.), reports realized savings (`rtk gain`), and can mine your Claude Code
history for missed rewrite opportunities (`rtk discover`). If you'd rather
not add a new binary dependency, use Option B.

```bash
#!/usr/bin/env bash
# ~/.claude/hooks/rtk-rewrite.sh — PreToolUse hook, matcher: "Bash"
# Requires: rtk >= 0.23.0 (cargo install rtk), jq
command -v jq >/dev/null 2>&1 || exit 0
command -v rtk >/dev/null 2>&1 || exit 0

INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
[ -z "$CMD" ] && exit 0

# rtk rewrite exits 1 when there's no rewrite for this command.
REWRITTEN=$(rtk rewrite "$CMD" 2>/dev/null) || exit 0
[ "$CMD" = "$REWRITTEN" ] && exit 0

ORIGINAL_INPUT=$(echo "$INPUT" | jq -c '.tool_input')
UPDATED_INPUT=$(echo "$ORIGINAL_INPUT" | jq --arg cmd "$REWRITTEN" '.command = $cmd')
jq -n --argjson updated "$UPDATED_INPUT" \
  '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "allow",
    permissionDecisionReason: "RTK auto-rewrite", updatedInput: $updated}}'
```

**Option B — dependency-free hook with a small built-in rewrite table.** No
external binary; extend the `case` statement as you find more noisy commands.

```bash
#!/usr/bin/env bash
# ~/.claude/hooks/filter-rewrite.sh — PreToolUse hook, matcher: "Bash"
# Requires: jq. No other dependencies.
command -v jq >/dev/null 2>&1 || exit 0

INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
[ -z "$CMD" ] && exit 0

REWRITTEN="$CMD"
case "$CMD" in
  "git status")            REWRITTEN="git status --short --branch" ;;
  "git log")                REWRITTEN="git log --oneline -20" ;;
  git\ log\ -p*)            REWRITTEN="${CMD/-p/--stat}" ;;
  "git diff")               REWRITTEN="git diff --stat" ;;
  "ls -la"|"ls -al")        REWRITTEN="ls -la | head -50" ;;
  find\ .\ -iname* )        REWRITTEN="$CMD | head -100" ;;
  npm\ ls*|pnpm\ ls*)       REWRITTEN="$CMD --depth=0" ;;
esac

[ "$CMD" = "$REWRITTEN" ] && exit 0

ORIGINAL_INPUT=$(echo "$INPUT" | jq -c '.tool_input')
UPDATED_INPUT=$(echo "$ORIGINAL_INPUT" | jq --arg cmd "$REWRITTEN" '.command = $cmd')
jq -n --argjson updated "$UPDATED_INPUT" \
  '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "allow",
    permissionDecisionReason: "token-filtered rewrite", updatedInput: $updated}}'
```

Register whichever one you pick in `settings.json`:

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
- **Fails open**: if `jq` (or `rtk`, for Option A) is missing, the hook exits
  0 and the original command runs unmodified — no silent breakage.
- **Transparent**: it rewrites the command, not the result — you still see
  real command output, just pre-filtered to the relevant subset.
- **Don't trust filtered output blindly.** A filtering layer can mask real
  failures (e.g. a linter's exit code buried under trimmed output). For
  anything you're about to act on as pass/fail, spot-check by invoking the
  underlying tool directly (e.g. `node_modules/.bin/eslint` instead of the
  filtered wrapper) rather than trusting the compressed summary.
- If your tool tracks savings (`rtk gain`, or your own counter for Option B),
  check it periodically so the hook's value is measured, not assumed.

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

Three ways to apply this, roughly in order of setup cost:

**A — a `dispatch` subagent you invoke explicitly.** Cheapest to set up:
one Markdown agent definition, no hooks. Create
`.claude/agents/dispatch.md`:

```markdown
---
name: dispatch
description: Cost-aware task router. Runs a well-scoped, self-contained task
  (lookups, mechanical edits, boilerplate, isolated fixes with clear
  acceptance criteria) on the cheapest capable model, escalating only if the
  worker signals it's out of depth. Not for ambiguous, architectural, or
  context-heavy work.
tools: Read, Grep, Glob, Bash, Edit
model: haiku
---

You are a cost-optimized task executor. You were given a fully self-contained
task description — treat it as complete context, you have no prior
conversation to draw on.

1. Attempt the task as specified.
2. If you hit a decision the prompt didn't resolve, or the task requires
   judgment beyond mechanical execution (design tradeoffs, ambiguous intent,
   deep multi-file reasoning), stop and clearly say so instead of guessing —
   the caller will re-run this on a stronger model.
3. Report exactly what you changed/found, not what you attempted.
```

Then delegate to it with the Agent/Task tool for well-scoped work instead of
reaching for your default (likely pricier) model.

**B — a static routing table you enforce by convention.** No tooling; add a
table like the one above to your `CLAUDE.md` and an explicit rule: "when
spawning subagents, pass the model tier matching the task class — never
default all subagents to the most expensive model." This is free but relies
on you (or the assistant) actually consulting it every time.

**C — automatic classification via a real router plugin.** Highest setup
cost, fully automatic, and enforced rather than advisory-only.
[`claude-model-router-hook`](https://github.com/tzachbon/claude-model-router-hook)
(MIT, by tzachbon) is a concrete example worth installing rather than
reimplementing — it wires three hooks:

- **`SessionStart`** (`session_init.py`) — emits the resolved routing table as
  `additionalContext`, so the current session (and you) can see what it will
  do before it does anything.
- **`UserPromptSubmit`** (`user_prompt_submit.py`) — classifies your own
  prompt and either *warns* (prints a `/model … && /effort …` suggestion and
  blocks for resend) or *autoswitches* (writes the suggested model as the
  default for new sessions), depending on config.
- **`PreToolUse`** matched on `Agent|Task` (`pre_tool_use.py`) — classifies
  the subagent's prompt and rewrites the spawn's `model` (and, when a
  matching `routed-*` agent variant is installed, its `subagent_type`) before
  the subagent starts. An explicit `model` the caller already set is never
  overridden.

The classifier itself (`hooks/router/taxonomy.py`) is a scored heuristic, not
a keyword blocklist: each class gets points from keyword/regex hits (capped
per class so no single signal can force a tier), plus structural signals
(prompt length, code fences, traceback text, question density). A class only
"wins" past a confidence margin; below that margin, an optional CLI tiebreak
can run before it abstains and leaves the model unchanged. Every decision
degrades gracefully — missing config, an uninstalled agent variant, or an
env var pinning a model all fail open to "leave it alone" rather than
blocking the tool call.

If you want the effect but not the dependency, the honest fallback is Option
B — the classifier's sophistication is exactly what a static table can't
replicate, so treat B as a stopgap, not an equivalent.

Don't stack B and C — pick one source of truth for routing rules so they
don't drift out of sync.

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

### 4. Runtime circuit breaker (catches multiplication as it happens)

The three levers above reduce token cost per call or per session; none of
them watch for a single turn silently multiplying its own cost — fanning out
many subagents at once, or repeating the same expensive call in a loop.
`ai-assistant-starter`'s `context-circuit-breaker` skill wires a `PreToolUse`
hook, matched on every tool (`"*"`), that tracks a short rolling window of
recent calls per session and warns — via the same
`hookSpecificOutput`/`permissionDecision: "allow"` shape used above, never a
block — once it sees 5+ `Agent`/`Task` spawns or 4+ near-identical/oversized
calls to the same tool within a 5-minute window. It's installed via
`/apply-template`'s Step 5.5 as an explicit opt-in, and is complementary to
this doc's other levers: it catches the pattern live, in-session, where
`cost-audit`/`session-retro` only see it after the fact in trace or
transcript data.

### 5. Historical cost baselines (gates disproportionate spawns)

The circuit breaker above watches call *shape* (fan-out, repeats) — it has
no notion of dollars. `ai-assistant-starter`'s `cost-guardrail` skill closes
that gap: it wires a `PreToolUse` hook, matched on `Agent` and `Bash`, that
compares a requested subagent model tier against historical cost baselines
`cost-audit` mines from Langfuse trace data (`.claude/cost-audit/cost_baselines.json`,
refreshed by `build_cost_baselines.py`), and warns (default) or blocks when
the requested tier's historical median cost is a large multiple of the
cheapest tracked tier's. It fails open whenever that baseline is missing,
stale, or doesn't cover the requested tier, so installing it is harmless
before a baseline exists. Like the circuit breaker, it's installed via
`/apply-template`'s opt-in Step 5.6, uses the same `hookSpecificOutput`
protocol, and the baseline file itself is refreshed only manually (a
scheduled job may remind, never run the refresh unattended — see
`cost-audit`'s "Continuous Baseline Refresh" section).

## Suggested `settings.json` skeleton

```json
{
  "model": "sonnet",
  "effortLevel": "medium",
  "env": {
    "DISABLE_TELEMETRY": "1",
    "DISABLE_ERROR_REPORTING": "1"
  },
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

1. Ask which levers they want (env vars, filtering hook, model routing,
   process rules, or a subset) rather than installing everything at once.
2. For the filtering hook: default to Option B (dependency-free) unless they
   specifically want `rtk` — it needs no external binary and is easy to
   extend with their own noisy commands.
3. For model routing: check what subagent/model-selection mechanism their
   Claude Code setup already has (a plugin, an existing agents/ dir, rules
   in CLAUDE.md) before adding a new one — don't stack two routing
   mechanisms (A/B/C above). Option A (a `dispatch` agent) is the lowest-cost
   starting point if they have nothing yet.
4. For process rules: add them to the user's own `CLAUDE.md` (global or
   project), not this repo's — they're personal working conventions, and
   should evolve from the user's own corrections/confirmations over time
   rather than being copied verbatim.
5. Don't copy someone else's `permissions.allow` list wholesale — it encodes
   their specific toolchain. Rebuild it for the new project/user instead.
