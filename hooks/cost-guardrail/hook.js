#!/usr/bin/env node

/**
 * Cost Guardrail Hook for Claude Code
 *
 * Intercepts Agent (subagent spawn) and Bash tool calls, compares the
 * requested model tier (or tool) against historical cost baselines produced
 * by `cost-audit`'s `build_cost_baselines.py`, and warns or blocks when the
 * requested tier's historical median cost is disproportionate relative to
 * the cheapest tracked tier.
 *
 * Hook protocol: reads tool input from stdin as JSON, outputs
 * `hookSpecificOutput.permissionDecision` JSON to stdout (allow/ask/deny).
 *
 * A PreToolUse hook fires before the call runs, so there is no per-call
 * actual cost to compare against — only priors. The signal here is
 * comparative: is the requested model tier's own historical median cost a
 * large multiple of the cheapest tier we have data for? That's the closest
 * proxy available to "this spawn is disproportionately expensive" before it
 * happens.
 *
 * Fails open (allows silently) whenever baseline data is missing, malformed,
 * stale, or doesn't cover the requested model/tool — this hook should never
 * be the reason a call is blocked when there's no real signal behind it.
 */

const fs = require('fs');

const DEFAULT_BASELINE_PATH = '.claude/cost-audit/cost_baselines.json';
const DEFAULT_FACTOR = 3.0;
const DEFAULT_MAX_STALENESS_DAYS = 45;
const MIN_SAMPLE = 5;

// Small alias table so a subagent's shorthand model name ("sonnet", "opus")
// matches whichever full model id the baseline data recorded it under.
const MODEL_ALIASES = {
  haiku: 'claude-haiku-4-5',
  sonnet: 'claude-sonnet-5',
  opus: 'claude-opus-5',
  fable: 'claude-fable-5-1',
};

function getInput() {
  return new Promise((resolve) => {
    let data = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (chunk) => { data += chunk; });
    process.stdin.on('end', () => {
      try {
        resolve(JSON.parse(data));
      } catch {
        resolve(null);
      }
    });
  });
}

function extractCommand(input) {
  if (!input) return '';
  return (input.tool_input?.command || input.input?.command || '').trim();
}

function extractAgentRequest(input) {
  const ti = (input && (input.tool_input || input.input)) || {};
  return {
    model: ti.model || null,
    subagentType: ti.subagent_type || null,
  };
}

function normalizeModelName(model, byModel) {
  if (!model) return null;
  if (byModel && byModel[model]) return model;
  const lower = model.toLowerCase();
  if (byModel && byModel[lower]) return lower;
  for (const [alias, full] of Object.entries(MODEL_ALIASES)) {
    if (lower.includes(alias)) {
      if (byModel && byModel[full]) return full;
      // Fall back to any tracked key that itself contains the alias.
      const match = byModel && Object.keys(byModel).find((k) => k.toLowerCase().includes(alias));
      if (match) return match;
    }
  }
  return model;
}

function loadBaselines(filePath, maxStalenessDays) {
  let raw;
  try {
    raw = fs.readFileSync(filePath, 'utf8');
  } catch {
    return null;
  }
  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return null;
  }
  if (!parsed || typeof parsed !== 'object' || !parsed.by_model || !parsed.generated_at) {
    return null;
  }
  const generatedAt = new Date(parsed.generated_at);
  if (Number.isNaN(generatedAt.getTime())) return null;
  const ageDays = (Date.now() - generatedAt.getTime()) / (1000 * 60 * 60 * 24);
  if (ageDays > maxStalenessDays) return null;
  return parsed;
}

function cheapestTier(byModel) {
  const eligible = Object.entries(byModel || {}).filter(([, s]) => s && s.count >= MIN_SAMPLE && s.median_cost > 0);
  if (!eligible.length) return null;
  return eligible.reduce((min, cur) => (cur[1].median_cost < min[1].median_cost ? cur : min));
}

function decide(request, baselines, opts) {
  const { mode = 'warn-only', factor = DEFAULT_FACTOR } = opts || {};
  if (!baselines) return null; // fail open: no data

  const modelKey = normalizeModelName(request.model, baselines.by_model);
  if (!modelKey) return null; // fail open: no model requested/tracked

  const stats = baselines.by_model[modelKey];
  if (!stats || stats.count < MIN_SAMPLE) return null; // fail open: insufficient data

  const cheapest = cheapestTier(baselines.by_model);
  if (!cheapest) return null; // fail open: no cheapest tier to compare against

  const [cheapestModel, cheapestStats] = cheapest;
  if (cheapestStats.median_cost <= 0) return null;

  const ratio = stats.median_cost / cheapestStats.median_cost;
  if (ratio <= factor) return null; // proportionate, allow silently

  const reason =
    `Cost guardrail: requested model tier "${modelKey}" has a historical median cost ` +
    `${ratio.toFixed(1)}x the cheapest tracked tier "${cheapestModel}" ` +
    `(median $${stats.median_cost} vs $${cheapestStats.median_cost}, n=${stats.count}). ` +
    `Consider whether this task needs this tier.`;

  const permissionDecision = mode === 'enforce' ? 'deny' : 'ask';
  return {
    hookSpecificOutput: {
      hookEventName: 'PreToolUse',
      permissionDecision,
      permissionDecisionReason: reason,
    },
  };
}

function checkHeavyBashPattern(cmd, byTool, opts) {
  const { mode = 'warn-only', factor = DEFAULT_FACTOR } = opts || {};
  if (!cmd || !byTool) return null;

  const stats = byTool['Bash'] || byTool['Tool: Bash'];
  if (!stats || stats.count < MIN_SAMPLE) return null;

  const cheapest = cheapestTier(byTool);
  if (!cheapest) return null;
  const [cheapestTool, cheapestStats] = cheapest;
  if (cheapestStats.median_cost <= 0) return null;

  const ratio = stats.median_cost / cheapestStats.median_cost;
  if (ratio <= factor) return null;

  const reason =
    `Cost guardrail: Bash calls have a historical median cost ${ratio.toFixed(1)}x the ` +
    `cheapest tracked tool "${cheapestTool}" (median $${stats.median_cost} vs $${cheapestStats.median_cost}, n=${stats.count}).`;

  const permissionDecision = mode === 'enforce' ? 'deny' : 'ask';
  return {
    hookSpecificOutput: {
      hookEventName: 'PreToolUse',
      permissionDecision,
      permissionDecisionReason: reason,
    },
  };
}

async function main() {
  const input = await getInput();
  const toolName = (input && (input.tool_name || input.tool)) || '';

  const baselinePath = process.env.COST_GUARDRAIL_BASELINE_PATH || DEFAULT_BASELINE_PATH;
  const mode = process.env.COST_GUARDRAIL_MODE || 'warn-only';
  const factor = parseFloat(process.env.COST_GUARDRAIL_FACTOR || String(DEFAULT_FACTOR));
  const maxStalenessDays = parseFloat(
    process.env.COST_GUARDRAIL_MAX_STALENESS_DAYS || String(DEFAULT_MAX_STALENESS_DAYS)
  );

  const baselines = loadBaselines(baselinePath, maxStalenessDays);

  let result = null;
  if (toolName === 'Agent') {
    result = decide(extractAgentRequest(input), baselines, { mode, factor });
  } else if (toolName === 'Bash') {
    result = checkHeavyBashPattern(extractCommand(input), baselines && baselines.by_tool, { mode, factor });
  }

  if (result) {
    console.log(JSON.stringify(result));
  }
  process.exit(0);
}

if (require.main === module) {
  main();
}

module.exports = {
  decide,
  checkHeavyBashPattern,
  loadBaselines,
  extractAgentRequest,
  extractCommand,
  normalizeModelName,
  cheapestTier,
};
