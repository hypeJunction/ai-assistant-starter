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

  // Block: git reset --hard (safety measure — user should confirm branch)
  if (/git\s+reset\s+--hard/.test(cmd)) {
    return {
      decision: 'block',
      reason:
        "Hard reset blocked as a safety measure. Verify you're on a feature branch, then retry. If intentional, ask the user to confirm.",
    };
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

main();
