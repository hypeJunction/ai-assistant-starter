#!/usr/bin/env node

/**
 * Guard: single PreToolUse entrypoint for Claude Code
 *
 * Reads the PreToolUse hook JSON from stdin once and dispatches to a fixed
 * list of modules, gated by tool name, instead of spawning a separate node
 * process per module. Modules run in order; the most restrictive decision
 * wins (deny > ask > allow), and evaluation stops at the first `deny`.
 * Advisory-only modules (context-circuit-breaker, main-shell-run) never
 * raise the decision above `allow` — their reason text is appended to
 * whatever the winning decision's reason is.
 *
 * Each module call is wrapped in its own try/catch: a module that throws is
 * treated the same as one that returned no result (fail open), and never
 * prevents the remaining modules — or the guard itself — from running.
 *
 * See hooks/guard/README.md for the module list, ordering, and combination
 * rule in full, and each module's own file/README for its detection logic.
 */

const destructiveCommand = require('../destructive-command-protection/hook.js');
const branchProtection = require('../branch-protection/hook.js');
const costGuardrail = require('../cost-guardrail/hook.js');
const circuitBreaker = require('../context-circuit-breaker/hook.js');
const secretScan = require('./modules/secret-scan.js');
const mainShellRun = require('./modules/main-shell-run.js');

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

const RANK = { allow: 0, ask: 1, deny: 2 };

// Fixed order: destructive-command -> branch-protection -> secret-scan -> main-shell-run -> cost-guardrail -> circuit-breaker.
const MODULES = [
  { name: 'destructive-command', appliesTo: (t) => t === 'Bash', run: (input) => destructiveCommand.evaluate(input) },
  { name: 'branch-protection', appliesTo: (t) => t === 'Bash', run: (input) => branchProtection.evaluate(input) },
  { name: 'secret-scan', appliesTo: (t) => t === 'Bash', run: (input) => secretScan.evaluate(input) },
  { name: 'main-shell-run', appliesTo: (t) => t === 'Bash', run: (input) => mainShellRun.evaluate(input) },
  { name: 'cost-guardrail', appliesTo: (t) => t === 'Bash' || t === 'Agent', run: (input) => costGuardrail.evaluate(input) },
  { name: 'circuit-breaker', appliesTo: () => true, run: (input) => circuitBreaker.evaluate(input) },
];

// Runs every applicable module, tracks the most restrictive decision, and collects advisory-only text separately.
function evaluate(input) {
  const toolName = (input && (input.tool_name || input.tool)) || '';
  let best = { decision: 'allow', reason: null, module: null };
  const advisories = [];

  for (const mod of MODULES) {
    if (!mod.appliesTo(toolName)) continue;

    let result;
    try {
      result = mod.run(input);
    } catch {
      result = null; // a throwing module fails open, same as a null result
    }
    if (!result) continue;

    if (result.decision === 'allow') {
      if (result.reason) advisories.push(`[${mod.name}] ${result.reason}`);
      continue;
    }

    if (RANK[result.decision] > RANK[best.decision]) {
      best = { decision: result.decision, reason: result.reason, module: mod.name };
      if (result.decision === 'deny') break;
    }
  }

  return { best, advisories };
}

// Combines the winning decision's reason with any advisory text into one string, or null if there's nothing to report.
function buildReason(best, advisories) {
  const parts = [];
  if (best.decision !== 'allow') parts.push(`${best.module}: ${best.reason}`);
  parts.push(...advisories);
  return parts.length ? parts.join(' ') : null;
}

async function main() {
  const input = await getInput();
  if (!input) {
    process.exit(0);
  }

  const { best, advisories } = evaluate(input);
  const reason = buildReason(best, advisories);

  if (reason) {
    console.log(JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        permissionDecision: best.decision,
        permissionDecisionReason: reason,
      },
    }));
  }
  process.exit(0);
}

if (require.main === module) {
  main();
}

module.exports = { evaluate, buildReason, MODULES };
