#!/usr/bin/env node
// merge-settings-hook.js — idempotently add a PreToolUse hook entry into a
// target project's .claude/settings.json.
//
// Security properties (verify by reading this file — it is the whole script):
//   - No network access, no `eval`, no shelling out.
//   - Only ever reads/writes the single target path given as argv[2].
//   - Touches only the hooks.PreToolUse array; every other key in the file
//     (permissions, model, etc.) is preserved byte-for-byte in structure.
//   - Idempotent: checks whether a matcher entry already references the
//     given command string before appending, so re-running never
//     duplicates the entry.
//   - Dry-run by default: prints the resulting JSON and a summary, writes
//     nothing unless --apply is passed.
//
// Usage:
//   node merge-settings-hook.js <target-settings.json> [--apply]
//   node merge-settings-hook.js <target-settings.json> --command <cmd> --matcher <matcher> [--apply]
//
// With no --command/--matcher, defaults to the context-circuit-breaker hook
// (matcher "*") for backward compatibility with existing call sites. Pass
// --matcher multiple times to register the same command under several
// matchers in one call (e.g. cost-guardrail needs both "Agent" and "Bash").
'use strict';

const fs = require('fs');
const path = require('path');

const DEFAULT_COMMAND = 'node .claude/skills/context-circuit-breaker/references/hook.js';
const DEFAULT_MATCHERS = ['*'];

function usageError() {
  console.error(
    'usage: merge-settings-hook.js <target-settings.json> [--command <cmd>] [--matcher <matcher> ...] [--apply]'
  );
  process.exit(1);
}

function parseArgs(argv) {
  const target = argv[0];
  if (!target || target.startsWith('--')) usageError();
  let command = null;
  const matchers = [];
  let apply = false;
  for (let i = 1; i < argv.length; i++) {
    if (argv[i] === '--apply') {
      apply = true;
    } else if (argv[i] === '--command') {
      command = argv[++i];
    } else if (argv[i] === '--matcher') {
      matchers.push(argv[++i]);
    } else {
      usageError();
    }
  }
  return {
    target,
    command: command || DEFAULT_COMMAND,
    matchers: matchers.length ? matchers : DEFAULT_MATCHERS,
    apply,
  };
}

const { target, command, matchers, apply } = parseArgs(process.argv.slice(2));

let settings = {};
let existed = false;
if (fs.existsSync(target)) {
  existed = true;
  const raw = fs.readFileSync(target, 'utf8');
  try {
    settings = raw.trim() ? JSON.parse(raw) : {};
  } catch (err) {
    console.error(`Refusing to touch ${target}: not valid JSON (${err.message})`);
    process.exit(1);
  }
}

settings.hooks = settings.hooks || {};
settings.hooks.PreToolUse = Array.isArray(settings.hooks.PreToolUse) ? settings.hooks.PreToolUse : [];

const hasCommandUnderMatcher = (matcher) =>
  settings.hooks.PreToolUse.some(
    (entry) =>
      entry.matcher === matcher &&
      Array.isArray(entry.hooks) &&
      entry.hooks.some((h) => h && typeof h.command === 'string' && h.command === command)
  );

let changed = false;
for (const matcher of matchers) {
  if (hasCommandUnderMatcher(matcher)) continue;
  const existingEntry = settings.hooks.PreToolUse.find((entry) => entry.matcher === matcher);
  if (existingEntry) {
    existingEntry.hooks = Array.isArray(existingEntry.hooks) ? existingEntry.hooks : [];
    existingEntry.hooks.push({ type: 'command', command });
  } else {
    settings.hooks.PreToolUse.push({ matcher, hooks: [{ type: 'command', command }] });
  }
  changed = true;
}

if (!changed) {
  console.log(`Already installed: ${target} already has this PreToolUse hook under matcher(s) ${matchers.join(', ')}. No changes needed.`);
  process.exit(0);
}

const output = JSON.stringify(settings, null, 2) + '\n';

if (!apply) {
  console.log(`--- dry run: ${target} ${existed ? '(existing file)' : '(would be created)'} ---`);
  console.log(output);
  console.log('--- end dry run: re-run with --apply to write ---');
  process.exit(0);
}

fs.mkdirSync(path.dirname(target), { recursive: true });
fs.writeFileSync(target, output);
console.log(`${existed ? 'Updated' : 'Created'} ${target} with the requested PreToolUse hook(s).`);
