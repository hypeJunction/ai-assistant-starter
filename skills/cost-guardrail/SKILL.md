---
name: cost-guardrail
description: Runtime enforcement hook that estimates the likely cost of an imminent Agent (subagent) spawn or Bash command against cost-audit-derived historical baselines, and blocks or warns when it's disproportionate. Auto-loaded for Agent and Bash tool calls.
category: enforcement
user-invocable: false
---

# Cost Guardrail

Runtime `PreToolUse` hook for Claude Code. Compares the model tier requested
by an `Agent` (subagent) spawn — or, secondarily, `Bash` calls — against
historical cost baselines mined from Langfuse trace data by `cost-audit`'s
`build_cost_baselines.py`, and warns or blocks when the requested tier's
historical cost is disproportionate.

## Estimation semantics

A `PreToolUse` hook fires *before* the call runs, so there is no per-call
actual cost to compare against — only priors. The signal this hook checks is
comparative, not predictive: **is the requested model tier's historical
median cost a large multiple of the cheapest tracked tier's median cost?**
If a project's baseline shows Opus running at 8x Sonnet's median cost, and
this call requests Opus with nothing in the request that justifies it, that
ratio is the disproportion this hook flags — not a prediction of what this
specific call will cost.

This means the hook is only as good as the baseline data behind it, and it
gets *more* useful over time as `cost_baselines.json` accumulates more
observations across more model tiers (see "Refreshing the baseline" below).

## What It Checks

| Trigger | Condition | Signal |
|---------|-----------|--------|
| `Agent` spawn | Requested model's historical `median_cost` ≥ `factor` × the cheapest tracked tier's `median_cost` | The subagent is being spawned on a tier that's historically far pricier than the cheapest viable tier, with nothing in the call justifying it |
| `Bash` call | `Bash`'s historical `median_cost` ≥ `factor` × the cheapest tracked tool's `median_cost` | Secondary check — Bash calls in this project have historically run disproportionately expensive relative to other tools |

Both checks **fail open** (allow silently, no output) when:

- `cost_baselines.json` doesn't exist, doesn't parse, or is missing required fields
- `generated_at` is older than `COST_GUARDRAIL_MAX_STALENESS_DAYS` (default 45 days)
- the requested model/tool isn't tracked in the baseline, or has fewer than 5 samples
- there's no cheapest-tier baseline to compare against

This hook never blocks a call over *missing* data — only over data that
actively shows a disproportion.

## Installation

Add to your Claude Code settings (`~/.claude/settings.json` or project
`.claude/settings.json`):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Agent",
        "hooks": [{ "type": "command", "command": "node .claude/skills/cost-guardrail/references/hook.js" }]
      },
      {
        "matcher": "Bash",
        "hooks": [{ "type": "command", "command": "node .claude/skills/cost-guardrail/references/hook.js" }]
      }
    ]
  }
}
```

Install via `/apply-template`'s opt-in hook-install step, or add this
snippet by hand — see `docs/README-security-scripts.md` for what running
this hook script does and doesn't do.

## Refreshing the baseline

This hook only reads `.claude/cost-audit/cost_baselines.json` — it never
calls Langfuse itself. That file is produced by:

```bash
python3 skills/cost-audit/references/build_cost_baselines.py --out .claude/cost-audit/cost_baselines.json
```

which needs the same Langfuse credentials as the rest of `/cost-audit`. This
is a **manual, credentialed step** — see `/cost-audit`'s "Continuous baseline
refresh" section for the recommended weekly reminder cadence via `/schedule`.
The hook is harmless (fails open) before this file exists; it just won't
have anything to check against yet.

## Configuration

| Env var | Default | Meaning |
|---|---|---|
| `COST_GUARDRAIL_MODE` | `warn-only` | `enforce` allows `deny`; `warn-only` only ever `ask` (or silent allow), never blocks |
| `COST_GUARDRAIL_FACTOR` | `3.0` | multiple of the cheapest tracked tier's median cost treated as disproportionate |
| `COST_GUARDRAIL_BASELINE_PATH` | `.claude/cost-audit/cost_baselines.json` | override for non-standard install layouts |
| `COST_GUARDRAIL_MAX_STALENESS_DAYS` | `45` | baseline older than this is treated as missing (fail open) |

Default to `warn-only` when first installing this hook — switch to
`enforce` only once the baseline has accumulated enough history that its
`ask` warnings are consistently correct calls, not noise.

## What This Does Not Do

- **Not a per-call cost predictor.** It compares historical tier medians, not
  a prediction of this specific call's actual cost — see "Estimation
  semantics" above.
- **Not a model router.** It never rewrites `model`/`subagent_type` — for
  that, see the model-tier-routing options in `docs/cost-optimization.md`.
  This hook only gates, it doesn't redirect.
- **Doesn't hold Langfuse credentials.** Reading the baseline file is the
  only I/O this hook does; refreshing it is a separate, manual step.

## Acceptance Tests

| ID | Condition | Expected |
|----|-----------|----------|
| CG-T1 | `Agent` spawn requesting a tier whose median cost is within `factor`x the cheapest tracked tier | Silent allow |
| CG-T2 | Same as above, but the ratio exceeds `factor`, `COST_GUARDRAIL_MODE=enforce` | `permissionDecision: "deny"` |
| CG-T3 | Same disproportionate ratio, `COST_GUARDRAIL_MODE=warn-only` (default) | `permissionDecision: "ask"`, never `"deny"` |
| CG-T4 | `cost_baselines.json` missing | Silent allow (fail open) |
| CG-T5 | `cost_baselines.json` present but `generated_at` older than `COST_GUARDRAIL_MAX_STALENESS_DAYS` | Silent allow (fail open) |
| CG-T6 | Requested model not present in `by_model`, or under the minimum sample count | Silent allow (fail open) |
