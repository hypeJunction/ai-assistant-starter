#!/usr/bin/env node

/**
 * Branch Protection Hook for Claude Code
 *
 * Intercepts Bash tool calls and blocks (or asks confirmation for) git
 * operations that would rewrite history or destroy work on a protected
 * branch (default: main, master).
 *
 * Hook protocol: reads tool input from stdin as JSON, outputs
 * `hookSpecificOutput.permissionDecision` JSON to stdout (allow/ask/deny).
 * Hard-destructive operations (force-push, hard-reset, branch delete) on a
 * protected branch return `deny`. Softer operations (checkout/restore/clean
 * that discard uncommitted or untracked work) return `ask` rather than a
 * silent block, since they're sometimes exactly what's wanted.
 *
 * Fails open on any error reading stdin or resolving the current branch —
 * this hook should never be the reason a command is blocked when there's
 * no real signal behind it.
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

function protectedBranches() {
  const raw = process.env.PROTECTED_BRANCHES || 'main,master';
  return raw.split(',').map((b) => b.trim()).filter(Boolean);
}

function getCurrentBranch(cwd) {
  try {
    return execSync('git branch --show-current', { cwd, encoding: 'utf8' }).trim() || null;
  } catch {
    return null;
  }
}

function tokenize(cmd) {
  return cmd.split(/\s+/).filter(Boolean);
}

function detectForcePush(cmd, currentBranch, protected_) {
  if (!/\bgit\s+push\b/.test(cmd)) return null;
  if (!/(--force\b|(^|\s)-f\b)/.test(cmd)) return null;

  const tokens = tokenize(cmd);
  const pushIdx = tokens.findIndex((t) => t === 'push');
  const args = tokens.slice(pushIdx + 1).filter((t) => !t.startsWith('-'));
  // args[0] is typically the remote, args[1] the refspec/branch.
  let target = args[1] || null;
  if (target) {
    target = target.split(':').pop(); // handle "HEAD:main" style refspecs
  }
  const effectiveTarget = target || currentBranch;
  if (effectiveTarget && protected_.includes(effectiveTarget)) {
    return {
      decision: 'deny',
      reason: `Branch protection: force-push to protected branch "${effectiveTarget}" is blocked. Force-pushing rewrites shared history — use a non-protected branch or ask the user to run this themselves.`,
    };
  }
  return null;
}

function detectHardReset(cmd, currentBranch, protected_) {
  if (!/\bgit\s+reset\s+--hard\b/.test(cmd)) return null;
  if (currentBranch && protected_.includes(currentBranch)) {
    return {
      decision: 'deny',
      reason: `Branch protection: "git reset --hard" on protected branch "${currentBranch}" is blocked — it destroys uncommitted work. Stash or commit first, or run this on a feature branch.`,
    };
  }
  return null;
}

function detectBranchDelete(cmd, protected_) {
  const match = cmd.match(/\bgit\s+branch\s+(?:-D|--delete\s+--force|-d\s+-f|-f\s+-d)\s+(\S+)/);
  if (!match) return null;
  const branch = match[1];
  if (protected_.includes(branch)) {
    return {
      decision: 'deny',
      reason: `Branch protection: deleting protected branch "${branch}" is blocked.`,
    };
  }
  return null;
}

function detectCheckoutRestoreDot(cmd, currentBranch, protected_) {
  if (!/\bgit\s+(checkout|restore)\s+\.\s*$/.test(cmd.trim())) return null;
  if (currentBranch && protected_.includes(currentBranch)) {
    return {
      decision: 'ask',
      reason: `Branch protection: "git ${cmd.includes('restore') ? 'restore' : 'checkout'} ." on protected branch "${currentBranch}" discards all uncommitted changes. Confirm this is intended before proceeding.`,
    };
  }
  return null;
}

function detectClean(cmd) {
  const match = cmd.match(/\bgit\s+clean\s+([^\s]+(?:\s+-{1,2}\S+)*)/);
  if (!match) return null;
  const flagPart = cmd.slice(match.index);
  const flagTokens = tokenize(flagPart).filter((t) => t.startsWith('-'));
  const shortFlags = flagTokens
    .filter((t) => t.startsWith('-') && !t.startsWith('--'))
    .map((t) => t.slice(1))
    .join('');
  const hasLongForce = flagTokens.includes('--force');
  const hasLongDirs = flagTokens.includes('-d') || flagTokens.includes('--directories') || shortFlags.includes('d');
  const hasForce = shortFlags.includes('f') || hasLongForce;
  const isDryRun = shortFlags.includes('n') || flagTokens.includes('--dry-run');
  if (isDryRun) return null;
  if (hasForce && hasLongDirs) {
    return {
      decision: 'ask',
      reason: 'Branch protection: "git clean" with -f and -d removes untracked files and directories permanently. Confirm this is intended before proceeding.',
    };
  }
  return null;
}

async function main() {
  const input = await getInput();
  const cmd = extractCommand(input);
  if (!cmd || !/\bgit\b/.test(cmd)) {
    process.exit(0);
  }

  const cwd = (input && input.cwd) || process.cwd();
  const protected_ = protectedBranches();
  const currentBranch = getCurrentBranch(cwd);

  const result =
    detectForcePush(cmd, currentBranch, protected_) ||
    detectHardReset(cmd, currentBranch, protected_) ||
    detectBranchDelete(cmd, protected_) ||
    detectCheckoutRestoreDot(cmd, currentBranch, protected_) ||
    detectClean(cmd);

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

module.exports = {
  detectForcePush,
  detectHardReset,
  detectBranchDelete,
  detectCheckoutRestoreDot,
  detectClean,
  protectedBranches,
};
