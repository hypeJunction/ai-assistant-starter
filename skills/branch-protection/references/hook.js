#!/usr/bin/env node

/**
 * Branch Protection Hook for Claude Code
 *
 * Intercepts Bash tool calls and blocks dangerous git operations
 * on protected branches (main, master, production).
 *
 * Hook protocol: reads tool input from stdin as JSON,
 * outputs JSON decision to stdout.
 */

const { execSync } = require('child_process');

const PROTECTED_BRANCHES = (process.env.PROTECTED_BRANCHES || 'main,master')
  .split(',')
  .map(b => b.trim())
  .filter(Boolean);

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
  return cmd.toLowerCase().trim();
}

function getCurrentBranch() {
  try {
    return execSync('git rev-parse --abbrev-ref HEAD', {
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe'],
    }).trim();
  } catch {
    return '';
  }
}

function checkBranchProtection(cmd) {
  const branchPattern = PROTECTED_BRANCHES
    .map(b => b.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
    .join('|');

  // Block: git push --force/-f to protected branches
  if (/git\s+push\s+.*(-f|--force)/.test(cmd)) {
    const targetsBranch = new RegExp(
      `(origin|upstream)\\s+(${branchPattern})\\b`
    ).test(cmd);
    const noExplicitBranch =
      !/origin\s+\S+/.test(cmd) && /git\s+push\s+(-f|--force)/.test(cmd);
    if (targetsBranch || noExplicitBranch) {
      return {
        decision: 'block',
        reason:
          'Force-push to protected branch blocked. Use a feature branch or regular push.',
      };
    }
  }

  // Block: git reset --hard on protected branches
  if (/git\s+reset\s+--hard/.test(cmd)) {
    const branch = getCurrentBranch();
    if (PROTECTED_BRANCHES.includes(branch)) {
      return {
        decision: 'block',
        reason: `Hard reset blocked on protected branch (${branch}). Switch to a feature branch first, or ask the user to confirm.`,
      };
    }
  }

  // Block: git branch -D on protected branches
  if (/git\s+branch\s+-(D|d)\s+/.test(cmd)) {
    const deletesProtected = new RegExp(
      `git\\s+branch\\s+-(D|d)\\s+(${branchPattern})\\b`
    ).test(cmd);
    if (deletesProtected) {
      return {
        decision: 'block',
        reason: `Deletion of protected branch blocked. Protected branches: ${PROTECTED_BRANCHES.join(', ')}.`,
      };
    }
  }

  // Warn: git checkout . / git restore . on protected branches
  if (/git\s+(checkout|restore)\s+(--\s+)?\./.test(cmd)) {
    const branch = getCurrentBranch();
    if (PROTECTED_BRANCHES.includes(branch)) {
      return {
        decision: 'block',
        reason: `Discarding all changes on protected branch (${branch}) blocked as a safety measure. Ask the user to confirm before proceeding.`,
      };
    }
  }

  // Warn: git clean with -f (any branch — removes untracked files irreversibly)
  if (/git\s+clean\s+/.test(cmd) && /\s-[a-z]*f|--force/.test(cmd)) {
    return {
      decision: 'block',
      reason:
        'git clean blocked as a safety measure — this removes untracked files irreversibly. Ask the user to confirm before proceeding.',
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

  const result = checkBranchProtection(cmd);
  if (result) {
    console.log(JSON.stringify(result));
    process.exit(0);
  }

  process.exit(0);
}

// Allow testing when required as a module
if (require.main === module) {
  main();
}

module.exports = { checkBranchProtection, extractCommand, getCurrentBranch, PROTECTED_BRANCHES };
