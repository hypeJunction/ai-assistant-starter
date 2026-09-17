#!/usr/bin/env node
// merge-settings-hook.js — idempotently add a PreToolUse hook entry and/or
// env vars into a target project's .claude/settings.json.
//
// Security properties (verify by reading this file — it is the whole script):
//   - No network access, no `eval`, no shelling out.
//   - Only ever reads/writes the single target path given as argv[2].
//   - Touches only the hooks.PreToolUse array and the top-level env object;
//     every other key in the file (permissions, model, etc.) is preserved
//     byte-for-byte in structure.
//   - Idempotent: checks whether a matcher entry already references the
//     given command string, and whether an env key already holds the given
//     value, before making any change — re-running never duplicates entries.
//   - Dry-run by default: prints the resulting JSON and a summary, writes
//     nothing unless --apply is passed.
//
// Usage:
//   node merge-settings-hook.js <target-settings.json> [--apply]
//   node merge-settings-hook.js <target-settings.json> --command <cmd> --matcher <matcher> [--event <event>] [--apply]
//   node merge-settings-hook.js <target-settings.json> --env KEY=VALUE [--env KEY2=VALUE2 ...] [--apply]
//
// With no --command/--matcher, defaults to the context-circuit-breaker hook
// (matcher "*") for backward compatibility with existing call sites — this
// default only applies when at least one hook-related flag path is taken;
// pass --env alone to merge only env vars without touching hooks at all.
// Pass --matcher multiple times to register the same command under several
// matchers in one call (e.g. cost-guardrail needs both "Agent" and "Bash").
// Pass --env multiple times to merge several keys in one call.
// --event selects which hooks.<Event> array to merge into (default
// PreToolUse, for backward compatibility); e.g. --event UserPromptSubmit
// for prompt-context-router.
'use strict';

const fs = require('fs');
const path = require('path');

const DEFAULT_COMMAND = 'node .claude/skills/context-circuit-breaker/references/hook.js';
const DEFAULT_MATCHERS = ['*'];
const DEFAULT_EVENT = 'PreToolUse';

function usageError() {
  console.error(
    'usage: merge-settings-hook.js <target-settings.json> [--command <cmd>] [--matcher <matcher> ...] [--event <event>] [--env KEY=VALUE ...] [--apply]'
  );
  process.exit(1);
}

function parseArgs(argv) {
  const target = argv[0];
  if (!target || target.startsWith('--')) usageError();
  let command = null;
  let event = null;
  const matchers = [];
  const envPairs = [];
  let apply = false;
  for (let i = 1; i < argv.length; i++) {
    if (argv[i] === '--apply') {
      apply = true;
    } else if (argv[i] === '--command') {
      command = argv[++i];
    } else if (argv[i] === '--matcher') {
      matchers.push(argv[++i]);
    } else if (argv[i] === '--event') {
      event = argv[++i];
    } else if (argv[i] === '--env') {
      const pair = argv[++i];
      const eq = pair ? pair.indexOf('=') : -1;
      if (eq <= 0) usageError();
      envPairs.push([pair.slice(0, eq), pair.slice(eq + 1)]);
    } else {
      usageError();
    }
  }
  const wantsHookMerge = command !== null || matchers.length > 0 || envPairs.length === 0;
  return {
    target,
    wantsHookMerge,
    command: command || DEFAULT_COMMAND,
    event: event || DEFAULT_EVENT,
    matchers: matchers.length ? matchers : DEFAULT_MATCHERS,
    envPairs,
    apply,
  };
}

const { target, wantsHookMerge, command, event, matchers, envPairs, apply } = parseArgs(process.argv.slice(2));

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

let changed = false;
const notes = [];

if (wantsHookMerge) {
  settings.hooks = settings.hooks || {};
  settings.hooks[event] = Array.isArray(settings.hooks[event]) ? settings.hooks[event] : [];

  const hasCommandUnderMatcher = (matcher) =>
    settings.hooks[event].some(
      (entry) =>
        entry.matcher === matcher &&
        Array.isArray(entry.hooks) &&
        entry.hooks.some((h) => h && typeof h.command === 'string' && h.command === command)
    );

  let hookChanged = false;
  for (const matcher of matchers) {
    if (hasCommandUnderMatcher(matcher)) continue;
    const existingEntry = settings.hooks[event].find((entry) => entry.matcher === matcher);
    if (existingEntry) {
      existingEntry.hooks = Array.isArray(existingEntry.hooks) ? existingEntry.hooks : [];
      existingEntry.hooks.push({ type: 'command', command });
    } else {
      settings.hooks[event].push({ matcher, hooks: [{ type: 'command', command }] });
    }
    hookChanged = true;
  }
  if (hookChanged) {
    changed = true;
    notes.push(`${event} hook for "${command}" under matcher(s) ${matchers.join(', ')}`);
  } else {
    notes.push(`${event} hook already present under matcher(s) ${matchers.join(', ')} (no change)`);
  }
}

if (envPairs.length > 0) {
  settings.env = settings.env && typeof settings.env === 'object' ? settings.env : {};
  const added = [];
  const updated = [];
  for (const [key, value] of envPairs) {
    if (settings.env[key] === value) continue;
    if (Object.prototype.hasOwnProperty.call(settings.env, key)) {
      updated.push(key);
    } else {
      added.push(key);
    }
    settings.env[key] = value;
  }
  if (added.length || updated.length) {
    changed = true;
    if (added.length) notes.push(`env added: ${added.join(', ')}`);
    if (updated.length) notes.push(`env updated: ${updated.join(', ')}`);
  } else {
    notes.push(`env keys already set to requested values: ${envPairs.map(([k]) => k).join(', ')} (no change)`);
  }
}

if (!changed) {
  console.log(`Already installed: ${target} needs no changes. ${notes.join('; ')}.`);
  process.exit(0);
}

const output = JSON.stringify(settings, null, 2) + '\n';

if (!apply) {
  console.log(`--- dry run: ${target} ${existed ? '(existing file)' : '(would be created)'} ---`);
  console.log(output);
  console.log(`--- changes: ${notes.join('; ')} ---`);
  console.log('--- end dry run: re-run with --apply to write ---');
  process.exit(0);
}

fs.mkdirSync(path.dirname(target), { recursive: true });
fs.writeFileSync(target, output);
console.log(`${existed ? 'Updated' : 'Created'} ${target}. Changes: ${notes.join('; ')}.`);
