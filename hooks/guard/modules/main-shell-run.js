#!/usr/bin/env node

/**
 * Main-Shell Run Module (part of hooks/guard)
 *
 * Advisory-only: flags Bash calls that look like a test/lint/typecheck/build
 * run or a dev-server start/stop/kill, and suggests routing them through the
 * `verifier` subagent instead of running them in the main shell.
 *
 * This module always returns `allow` — never `ask` or `deny` — because there
 * is no reliable field in the PreToolUse hook input to distinguish a call
 * made by the main agent from one made inside a subagent (see hooks/guard/README.md).
 * Blocking or asking here would risk stalling verifier/dispatch subagents
 * that are supposed to run these exact commands; staying advisory-only means
 * this module can never break subagent automation.
 */

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

const RUN_PATTERNS = [
  /\b(npm|pnpm|yarn|bun)\s+run\s+(test|lint|typecheck|build)\b/,
  /\b(npm|pnpm|yarn|bun)\s+test\b/,
  /\bnpx\s+(vitest|jest|playwright|eslint|tsc)\b/,
  /\b(vitest|jest|playwright|eslint|tsc)\b/,
  /\bpytest\b/,
  /\bgo\s+test\b/,
  /\bcargo\s+test\b/,
];

// Kept conservative on purpose: only explicit job-control/dev-server-named kill forms match,
// so an unrelated `kill <pid>` doesn't trip this.
const DEV_SERVER_PATTERNS = [
  /\b(npm|pnpm|yarn|bun)\s+run\s+dev\b/,
  /\bnext\s+dev\b/,
  /\bvite\b(?!st)/,
  /\bpkill\s+-f\b/,
  /\bkill\s+%\d+\b/,
];

function matches(cmd) {
  return RUN_PATTERNS.some((re) => re.test(cmd)) || DEV_SERVER_PATTERNS.some((re) => re.test(cmd));
}

// Importable entrypoint for hooks/guard/hook.js — always `allow`; advisory text only.
function evaluate(input) {
  const cmd = extractCommand(input);
  if (!cmd || !matches(cmd)) return null;

  return {
    decision: 'allow',
    reason: `This looks like a test/lint/build/dev-server command ("${cmd}") — consider routing it through the verifier subagent instead of running it in the main shell, so its raw output gets read before reporting a result.`,
  };
}

async function main() {
  const input = await getInput();
  const result = evaluate(input);

  if (result) {
    console.log(JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        permissionDecision: result.decision,
        permissionDecisionReason: result.reason,
      },
    }));
  }
  process.exit(0);
}

if (require.main === module) {
  main();
}

module.exports = { evaluate, matches, RUN_PATTERNS, DEV_SERVER_PATTERNS };
