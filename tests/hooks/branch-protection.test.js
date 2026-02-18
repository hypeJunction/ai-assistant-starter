const { describe, it, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert/strict');

// Save and restore env between tests
let originalEnv;

beforeEach(() => {
  originalEnv = process.env.PROTECTED_BRANCHES;
});

afterEach(() => {
  if (originalEnv === undefined) {
    delete process.env.PROTECTED_BRANCHES;
  } else {
    process.env.PROTECTED_BRANCHES = originalEnv;
  }
});

// Re-require with fresh PROTECTED_BRANCHES each time would be complex,
// so we test with the default (main,master) and one custom env test.
const {
  checkBranchProtection,
  extractCommand,
} = require('../../skills/branch-protection/references/hook.js');

// Helper: simulate getCurrentBranch by temporarily replacing it
// Since checkBranchProtection calls getCurrentBranch internally for some rules,
// we need to test with the actual function. For branch-dependent tests,
// we'll note that the test environment's branch affects results.

describe('extractCommand', () => {
  it('extracts from tool_input.command', () => {
    const result = extractCommand({ tool_input: { command: 'git push -f' } });
    assert.equal(result, 'git push -f');
  });

  it('extracts from input.command fallback', () => {
    const result = extractCommand({ input: { command: 'git push -f' } });
    assert.equal(result, 'git push -f');
  });

  it('returns empty string for null input', () => {
    assert.equal(extractCommand(null), '');
  });

  it('returns empty string for empty object', () => {
    assert.equal(extractCommand({}), '');
  });

  it('lowercases the command', () => {
    const result = extractCommand({ tool_input: { command: 'Git Push -F' } });
    assert.equal(result, 'git push -f');
  });
});

describe('checkBranchProtection — force push', () => {
  it('blocks git push --force origin main', () => {
    const result = checkBranchProtection('git push --force origin main');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks git push -f origin master', () => {
    const result = checkBranchProtection('git push -f origin master');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks git push -f upstream main', () => {
    const result = checkBranchProtection('git push -f upstream main');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks bare git push -f (no remote/branch)', () => {
    const result = checkBranchProtection('git push -f');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('allows git push --force origin feature/foo', () => {
    const result = checkBranchProtection('git push --force origin feature/foo');
    assert.equal(result, null);
  });

  it('allows regular git push origin main (no force)', () => {
    const result = checkBranchProtection('git push origin main');
    assert.equal(result, null);
  });
});

describe('checkBranchProtection — branch deletion', () => {
  it('blocks git branch -D main', () => {
    const result = checkBranchProtection('git branch -d main');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks git branch -D master', () => {
    const result = checkBranchProtection('git branch -d master');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('allows git branch -D feature/foo', () => {
    const result = checkBranchProtection('git branch -d feature/foo');
    assert.equal(result, null);
  });
});

describe('checkBranchProtection — git clean', () => {
  it('blocks git clean -fd (any branch)', () => {
    const result = checkBranchProtection('git clean -fd');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks git clean -f', () => {
    const result = checkBranchProtection('git clean -f');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks git clean --force', () => {
    const result = checkBranchProtection('git clean --force');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('allows git clean -n (dry run, no -f)', () => {
    const result = checkBranchProtection('git clean -n');
    assert.equal(result, null);
  });
});

describe('checkBranchProtection — edge cases', () => {
  it('returns null for empty command', () => {
    assert.equal(checkBranchProtection(''), null);
  });

  it('returns null for unrelated commands', () => {
    assert.equal(checkBranchProtection('npm test'), null);
  });

  it('returns null for regular git commands', () => {
    assert.equal(checkBranchProtection('git status'), null);
    assert.equal(checkBranchProtection('git diff'), null);
    assert.equal(checkBranchProtection('git log'), null);
  });
});

describe('checkBranchProtection — custom PROTECTED_BRANCHES', () => {
  // This test verifies that the module reads PROTECTED_BRANCHES at load time.
  // Since we can't easily re-require the module, we verify the default includes main and master.
  it('default protected branches include main and master', () => {
    // Force push to main should block
    assert.notEqual(checkBranchProtection('git push -f origin main'), null);
    // Force push to master should block
    assert.notEqual(checkBranchProtection('git push -f origin master'), null);
    // Force push to develop should not block
    assert.equal(checkBranchProtection('git push -f origin develop'), null);
  });
});
