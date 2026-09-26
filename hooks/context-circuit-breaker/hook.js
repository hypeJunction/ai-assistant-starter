#!/usr/bin/env node

/**
 * Context-Multiplication Circuit Breaker for Claude Code
 *
 * Intercepts every PreToolUse call, tracks a short rolling window of recent
 * tool calls per session, and warns (never blocks) when it sees:
 *   - subagent fan-out: many Agent/Task spawns in a short window
 *   - a repeat/loop: the same tool called with large and/or near-identical
 *     input several times in a short window
 *
 * Hook protocol: reads tool input from stdin as JSON, outputs JSON to
 * stdout. This hook only ever allows — a warning is surfaced via
 * permissionDecisionReason on an "allow" decision, never a block.
 */

const fs = require('fs');
const os = require('os');
const path = require('path');
const crypto = require('crypto');

// Rolling window: how far back to look when counting recent calls.
const WINDOW_MS = 5 * 60 * 1000;
// Fan-out check: warn once this many Agent/Task spawns land inside the window.
const FANOUT_THRESHOLD = 5;
// Repeat check: warn once the same tool+input signature repeats this many times inside the window.
const REPEAT_THRESHOLD = 4;
// Repeat check: an input this large (stringified length) counts as "expensive" for the repeat check.
const LARGE_INPUT_CHARS = 20000;
// How many trailing characters of stringified input to hash for the repeat signature.
const SIGNATURE_SAMPLE_CHARS = 500;

const SUBAGENT_TOOL_NAMES = new Set(['Agent', 'Task']);

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

function statePath(sessionId) {
  const safeId = (sessionId || 'unknown').replace(/[^a-zA-Z0-9_-]/g, '_');
  return path.join(os.tmpdir(), `claude-circuit-breaker-${safeId}.json`);
}

function loadState(filePath) {
  try {
    const raw = fs.readFileSync(filePath, 'utf8');
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed.calls) ? parsed : { calls: [] };
  } catch {
    return { calls: [] };
  }
}

function saveState(filePath, state) {
  try {
    fs.writeFileSync(filePath, JSON.stringify(state));
  } catch {
    // Best-effort only — a failed write just means the next call starts a fresh window.
  }
}

function signatureFor(toolName, toolInputStr) {
  const sample = toolInputStr.slice(0, SIGNATURE_SAMPLE_CHARS);
  const hash = crypto.createHash('sha1').update(sample).digest('hex');
  return `${toolName}:${hash}`;
}

function pruneToWindow(calls, now) {
  return calls.filter((c) => now - c.t <= WINDOW_MS);
}

function checkFanOut(calls, toolName) {
  if (!SUBAGENT_TOOL_NAMES.has(toolName)) return null;
  const spawns = calls.filter((c) => SUBAGENT_TOOL_NAMES.has(c.tool));
  // +1 for the call currently being evaluated, which isn't in `calls` yet.
  const count = spawns.length + 1;
  if (count >= FANOUT_THRESHOLD) {
    return `Context-multiplication warning: ${count} subagent spawns (Agent/Task) within the last ${Math.round(WINDOW_MS / 60000)} minutes. Each spawn re-pays context/cache cost — consider batching remaining work into fewer, larger-scoped agents instead of one more spawn.`;
  }
  return null;
}

function checkRepeat(calls, toolName, sig, inputLen) {
  const matches = calls.filter((c) => c.sig === sig);
  const repeatCount = matches.length + 1;
  if (repeatCount >= REPEAT_THRESHOLD) {
    return `Expensive-loop warning: this ${toolName} call has now run with near-identical input ${repeatCount} times within the last ${Math.round(WINDOW_MS / 60000)} minutes. If this is a retry loop, stop and diagnose the root cause instead of repeating the same call.`;
  }
  if (inputLen >= LARGE_INPUT_CHARS) {
    const sameToolCount = calls.filter((c) => c.tool === toolName && c.large).length + 1;
    if (sameToolCount >= REPEAT_THRESHOLD) {
      return `Expensive-loop warning: ${sameToolCount} large ${toolName} calls (>${LARGE_INPUT_CHARS} chars of input) within the last ${Math.round(WINDOW_MS / 60000)} minutes. Consider narrowing scope or delegating remaining work to a subagent instead of repeating large-context calls inline.`;
    }
  }
  return null;
}

async function main() {
  const input = await getInput();
  if (!input) {
    process.exit(0);
  }

  const toolName = input.tool_name || '';
  const toolInput = input.tool_input || input.input || {};
  const sessionId = input.session_id || 'unknown';

  if (!toolName) {
    process.exit(0);
  }

  const toolInputStr = JSON.stringify(toolInput);
  const inputLen = toolInputStr.length;
  const sig = signatureFor(toolName, toolInputStr);

  const filePath = statePath(sessionId);
  const now = Date.now();
  const state = loadState(filePath);
  state.calls = pruneToWindow(state.calls, now);

  const fanOutWarning = checkFanOut(state.calls, toolName);
  const repeatWarning = checkRepeat(state.calls, toolName, sig, inputLen);

  state.calls.push({
    t: now,
    tool: toolName,
    sig,
    large: inputLen >= LARGE_INPUT_CHARS,
  });
  saveState(filePath, state);

  const reason = [fanOutWarning, repeatWarning].filter(Boolean).join(' ');
  if (reason) {
    console.log(JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        permissionDecision: 'allow',
        permissionDecisionReason: reason,
      },
    }));
  }

  process.exit(0);
}

if (require.main === module) {
  main();
}

module.exports = { checkFanOut, checkRepeat, signatureFor, pruneToWindow, statePath };
