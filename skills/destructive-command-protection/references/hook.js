#!/usr/bin/env node

/**
 * Destructive Command Protection Hook for Claude Code
 *
 * Intercepts Bash tool calls and blocks commands that could cause
 * irreversible system or data damage.
 *
 * Hook protocol: reads tool input from stdin as JSON,
 * outputs JSON decision to stdout.
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
  const cmd = input.tool_input?.command || input.input?.command || '';
  return cmd.trim();
}

const DANGEROUS_RM_TARGETS = [
  /^\/$/,
  /^\/\s/,
  /^~\/?$/,
  /^\$HOME\/?$/,
  /^\/home\/?$/,
  /^\/etc\/?$/,
  /^\/usr\/?$/,
  /^\/var\/?$/,
  /^\/boot\/?$/,
  /^\.\.\/\.\.\//,
  /^\.\/?$/,
];

const SAFE_RM_TARGETS = [
  /node_modules/,
  /dist\/?$/,
  /build\/?$/,
  /\.next\/?$/,
  /\.cache\/?$/,
  /coverage\/?$/,
  /\.turbo\/?$/,
  /tmp\/?$/,
  /\.tmp\/?$/,
  /out\/?$/,
];

function checkDestructiveCommand(cmd) {
  const lower = cmd.toLowerCase();

  // Block: rm -rf with dangerous targets
  const rmMatch = lower.match(
    /rm\s+(-[a-z]*r[a-z]*f[a-z]*|-[a-z]*f[a-z]*r[a-z]*)\s+(.*)/
  );
  if (rmMatch) {
    const target = rmMatch[2].trim().split(/\s/)[0];
    const isSafe = SAFE_RM_TARGETS.some((p) => p.test(target));
    if (isSafe) return null;
    const isDangerous = DANGEROUS_RM_TARGETS.some((p) => p.test(target));
    if (isDangerous) {
      return {
        decision: 'block',
        reason: `Destructive command blocked: 'rm -rf ${target}' targets a critical path. Specify a safe, scoped path instead.`,
      };
    }
  }

  // Block: database destruction
  if (/drop\s+(database|schema)\s+/i.test(cmd)) {
    return {
      decision: 'block',
      reason:
        'DROP DATABASE/SCHEMA blocked. This is an irreversible operation. Ask the user to confirm and run manually.',
    };
  }

  // Block: mass truncate
  if (/truncate\s+table\s+/i.test(cmd) && !/where\s+/i.test(cmd)) {
    if (/if\s+exists/i.test(cmd)) return null;
    return {
      decision: 'block',
      reason:
        'TRUNCATE TABLE blocked as a safety measure. Ask the user to confirm this data deletion.',
    };
  }

  // Block: disk operations
  if (/mkfs[\s.]/.test(lower) || /dd\s+if=.*of=\/dev\//.test(lower)) {
    return {
      decision: 'block',
      reason:
        'Disk format/overwrite operation blocked. This is an irreversible operation.',
    };
  }

  // Block: writes to block devices
  if (/>\s*\/dev\/[sh]d[a-z]/.test(lower)) {
    return {
      decision: 'block',
      reason: 'Write to block device blocked. This would corrupt the disk.',
    };
  }

  // Block: dangerous chmod
  if (/chmod\s+(-R\s+)?777\s+\//.test(cmd)) {
    return {
      decision: 'block',
      reason:
        'chmod -R 777 on system paths blocked. This is a security risk. Use specific permissions instead.',
    };
  }

  // Block: fork bomb patterns
  if (/:\(\)\s*\{.*\|.*&\s*\}\s*;?\s*:/.test(cmd)) {
    return {
      decision: 'block',
      reason: 'Fork bomb pattern detected and blocked.',
    };
  }

  // Block: kill system processes
  if (/kill\s+(-9\s+)?(-1|1)\b/.test(lower)) {
    return {
      decision: 'block',
      reason:
        'Killing init/all processes blocked. Specify a specific process ID.',
    };
  }

  return null;
}

async function main() {
  const input = await getInput();
  const cmd = extractCommand(input);

  if (!cmd) {
    process.exit(0);
  }

  const result = checkDestructiveCommand(cmd);
  if (result) {
    console.log(JSON.stringify(result));
    process.exit(0);
  }

  process.exit(0);
}

main();
