#!/usr/bin/env node
// merge-settings-hook.js — idempotently add the context-circuit-breaker
// PreToolUse hook entry into a target project's .claude/settings.json.
//
// Security properties (verify by reading this file — it is the whole script):
//   - No network access, no `eval`, no shelling out.
//   - Only ever reads/writes the single target path given as argv[2].
//   - Touches only the hooks.PreToolUse array; every other key in the file
//     (permissions, model, etc.) is preserved byte-for-byte in structure.
//   - Idempotent: checks whether an entry already references
//     "context-circuit-breaker/references/hook.js" by command string before
//     appending, so re-running never duplicates the entry.
//   - Dry-run by default: prints the resulting JSON and a summary, writes
//     nothing unless --apply is passed.
//
// Usage:
//   node merge-settings-hook.js <target-settings.json> [--apply]
'use strict';

const fs = require('fs');
const path = require('path');

const HOOK_COMMAND = 'node .claude/skills/context-circuit-breaker/references/hook.js';

function usageError() {
  console.error('usage: merge-settings-hook.sh <target-settings.json> [--apply]');
  process.exit(1);
}

const target = process.argv[2];
const apply = process.argv.includes('--apply');
if (!target) usageError();

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

const alreadyPresent = settings.hooks.PreToolUse.some((entry) =>
  Array.isArray(entry.hooks) &&
  entry.hooks.some((h) => h && typeof h.command === 'string' && h.command.includes('context-circuit-breaker/references/hook.js'))
);

if (alreadyPresent) {
  console.log(`Already installed: ${target} already has a context-circuit-breaker PreToolUse hook. No changes needed.`);
  process.exit(0);
}

settings.hooks.PreToolUse.push({
  matcher: '*',
  hooks: [{ type: 'command', command: HOOK_COMMAND }],
});

const output = JSON.stringify(settings, null, 2) + '\n';

if (!apply) {
  console.log(`--- dry run: ${target} ${existed ? '(existing file)' : '(would be created)'} ---`);
  console.log(output);
  console.log('--- end dry run: re-run with --apply to write ---');
  process.exit(0);
}

fs.mkdirSync(path.dirname(target), { recursive: true });
fs.writeFileSync(target, output);
console.log(`${existed ? 'Updated' : 'Created'} ${target} with the context-circuit-breaker PreToolUse hook.`);
