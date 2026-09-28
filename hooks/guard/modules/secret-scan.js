#!/usr/bin/env node

/**
 * Secret Scan Module (part of hooks/guard)
 *
 * Fires on `git commit` Bash calls and scans the staged diff for likely
 * secrets, using the union of patterns documented in commands/commit.md's
 * and commands/validate.md's "Secrets detection" sections. Never blocks —
 * a match returns `ask` so the model confirms before the commit proceeds.
 *
 * Fails open: if `git diff --cached` errors for any reason (not a repo,
 * git missing, nothing staged), this module allows silently.
 */

const { execSync } = require('child_process');

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

function isCommitCommand(cmd) {
  return /\bgit\s+commit\b/.test(cmd);
}

// Union of commands/commit.md's three secrets-detection patterns (generic assignment,
// high-confidence specific tokens, and password/token string literals).
const SECRET_PATTERNS = [
  /(api[_-]?key|secret|password|token|credential|private[_-]?key)\s*[:=]/i,
  /(AKIA[0-9A-Z]{16}|-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----|ghp_[a-zA-Z0-9]{36}|sk-[a-zA-Z0-9]{48}|Bearer [a-zA-Z0-9_.-]{20,})/,
  /(password|passwd|pwd|token|secret)\s*[:=]\s*["'][^"']{8,}/i,
];

// Scans a unified diff's added lines only, tracking file/line position from the hunk headers.
function scanDiff(diff) {
  let file = null;
  let lineNo = null;
  for (const line of diff.split('\n')) {
    const fileMatch = line.match(/^\+\+\+ b\/(.+)$/);
    if (fileMatch) {
      file = fileMatch[1];
      continue;
    }
    const hunkMatch = line.match(/^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@/);
    if (hunkMatch) {
      lineNo = parseInt(hunkMatch[1], 10);
      continue;
    }
    if (line.startsWith('+++') || line.startsWith('---')) continue;
    if (line.startsWith('+')) {
      const content = line.slice(1);
      for (const pattern of SECRET_PATTERNS) {
        if (pattern.test(content)) {
          return { file: file || 'unknown', line: lineNo, text: content.trim().slice(0, 200) };
        }
      }
      if (lineNo !== null) lineNo += 1;
    } else if (!line.startsWith('-')) {
      if (lineNo !== null) lineNo += 1;
    }
  }
  return null;
}

// Importable entrypoint for hooks/guard/hook.js.
function evaluate(input) {
  const cmd = extractCommand(input);
  if (!cmd || !isCommitCommand(cmd)) return null;

  const cwd = (input && input.cwd) || process.cwd();
  let diff;
  try {
    diff = execSync('git diff --cached', { cwd, encoding: 'utf8', maxBuffer: 10 * 1024 * 1024 });
  } catch {
    return null;
  }
  if (!diff) return null;

  const match = scanDiff(diff);
  if (!match) return null;

  return {
    decision: 'ask',
    reason: `Secret scan: possible secret in staged changes at ${match.file}:${match.line} — "${match.text}". Confirm this isn't a real credential before committing.`,
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

module.exports = { evaluate, scanDiff, isCommitCommand, SECRET_PATTERNS };
