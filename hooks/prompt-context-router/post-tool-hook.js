#!/usr/bin/env node

/**
 * Post-Tool companion hook for prompt-context-router.
 *
 * `hook.js` runs on `UserPromptSubmit`, so it has no view into tool calls
 * made between prompts. This hook runs on `PostToolUse` and records exactly
 * one thing into the shared state file `hook.js` already reads
 * (`statePath`/`loadState`/`saveState`, reused via require rather than
 * duplicated): whether a plan approved via `EnterPlanMode`/`ExitPlanMode` has
 * since been acted on.
 *
 * - `ExitPlanMode` (the plan was approved) starts a fresh cycle:
 *   `implementedSincePlan` and `postPlanPivotNudged` both reset to false.
 * - A mutating tool (`Edit`, `Write`, `NotebookEdit`, `Bash`) sets
 *   `implementedSincePlan = true` — heuristic, not exact: not every Bash call
 *   is a mutation, but false positives here only cost one extra Plan Mode
 *   nudge, which is the acceptable direction to err for this check.
 *
 * This hook never advises or blocks — it only records state, and fails open
 * (best-effort, same as `context-circuit-breaker`'s `saveState`) on any read/
 * write error. `hook.js`'s `buildPostPlanPivotGuidance` is what actually acts
 * on the flag it sets here.
 *
 * Hook protocol: reads the PostToolUse event from stdin as JSON
 * (`input.tool_name`, `input.session_id`), no stdout output.
 */

const { statePath, loadState, saveState } = require('./hook.js');

const MUTATING_TOOLS = new Set(['Edit', 'Write', 'NotebookEdit', 'Bash']);

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

async function main() {
  const input = await getInput();
  const toolName = (input && typeof input.tool_name === 'string' && input.tool_name) || null;
  const sessionId = (input && typeof input.session_id === 'string' && input.session_id) || null;
  if (!toolName) {
    process.exit(0);
  }

  const filePath = statePath(sessionId);
  const state = loadState(filePath);

  if (toolName === 'ExitPlanMode') {
    saveState(filePath, { ...state, implementedSincePlan: false, postPlanPivotNudged: false });
  } else if (MUTATING_TOOLS.has(toolName)) {
    saveState(filePath, { ...state, implementedSincePlan: true });
  }

  process.exit(0);
}

if (require.main === module) {
  main();
}

module.exports = { MUTATING_TOOLS };
