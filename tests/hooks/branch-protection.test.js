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

const {
  detectForcePush,
  detectHardReset,
  detectBranchDelete,
  detectCheckoutRestoreDot,
  detectClean,
  protectedBranches,
} = require('../../skills/branch-protection/references/hook.js');

const PROTECTED = ['main', 'master'];

describe('detectForcePush', () => {
  it('denies git push --force origin main', () => {
    const result = detectForcePush('git push --force origin main', null, PROTECTED);
    assert.notEqual(result, null);
    assert.equal(result.decision, 'deny');
  });

  it('denies git push -f origin master', () => {
    const result = detectForcePush('git push -f origin master', null, PROTECTED);
    assert.notEqual(result, null);
    assert.equal(result.decision, 'deny');
  });

  it('denies git push -f upstream main', () => {
    const result = detectForcePush('git push -f upstream main', null, PROTECTED);
    assert.notEqual(result, null);
    assert.equal(result.decision, 'deny');
  });

  it('denies bare git push -f when current branch is protected', () => {
    const result = detectForcePush('git push -f', 'main', PROTECTED);
    assert.notEqual(result, null);
    assert.equal(result.decision, 'deny');
  });

  it('allows bare git push -f when current branch is not protected', () => {
    const result = detectForcePush('git push -f', 'feature/foo', PROTECTED);
    assert.equal(result, null);
  });

  it('allows git push --force origin feature/foo', () => {
    const result = detectForcePush('git push --force origin feature/foo', null, PROTECTED);
    assert.equal(result, null);
  });

  it('allows regular git push origin main (no force)', () => {
    const result = detectForcePush('git push origin main', null, PROTECTED);
    assert.equal(result, null);
  });
});

describe('detectHardReset', () => {
  it('denies git reset --hard on a protected current branch', () => {
    const result = detectHardReset('git reset --hard', 'main', PROTECTED);
    assert.notEqual(result, null);
    assert.equal(result.decision, 'deny');
  });

  it('denies git reset --hard HEAD~1 on master', () => {
    const result = detectHardReset('git reset --hard HEAD~1', 'master', PROTECTED);
    assert.notEqual(result, null);
    assert.equal(result.decision, 'deny');
  });

  it('allows git reset --hard on a non-protected branch', () => {
    const result = detectHardReset('git reset --hard', 'feature/foo', PROTECTED);
    assert.equal(result, null);
  });

  it('allows git reset (soft/mixed, no --hard)', () => {
    const result = detectHardReset('git reset HEAD~1', 'main', PROTECTED);
    assert.equal(result, null);
  });
});

describe('detectBranchDelete', () => {
  it('denies git branch -D main', () => {
    const result = detectBranchDelete('git branch -D main', PROTECTED);
    assert.notEqual(result, null);
    assert.equal(result.decision, 'deny');
  });

  it('denies git branch -D master', () => {
    const result = detectBranchDelete('git branch -D master', PROTECTED);
    assert.notEqual(result, null);
    assert.equal(result.decision, 'deny');
  });

  it('denies git branch --delete --force main', () => {
    const result = detectBranchDelete('git branch --delete --force main', PROTECTED);
    assert.notEqual(result, null);
    assert.equal(result.decision, 'deny');
  });

  it('allows git branch -D feature/foo', () => {
    const result = detectBranchDelete('git branch -D feature/foo', PROTECTED);
    assert.equal(result, null);
  });

  it('allows git branch -d main (soft delete, no force — documents current behavior)', () => {
    const result = detectBranchDelete('git branch -d main', PROTECTED);
    assert.equal(result, null);
  });
});

describe('detectCheckoutRestoreDot', () => {
  it('asks for git checkout . on a protected current branch', () => {
    const result = detectCheckoutRestoreDot('git checkout .', 'main', PROTECTED);
    assert.notEqual(result, null);
    assert.equal(result.decision, 'ask');
  });

  it('asks for git restore . on a protected current branch', () => {
    const result = detectCheckoutRestoreDot('git restore .', 'main', PROTECTED);
    assert.notEqual(result, null);
    assert.equal(result.decision, 'ask');
  });

  it('allows git checkout . on a non-protected branch', () => {
    const result = detectCheckoutRestoreDot('git checkout .', 'feature/foo', PROTECTED);
    assert.equal(result, null);
  });

  it('allows git checkout file.txt (not a bare dot)', () => {
    const result = detectCheckoutRestoreDot('git checkout file.txt', 'main', PROTECTED);
    assert.equal(result, null);
  });
});

describe('detectClean', () => {
  it('asks for git clean -fd', () => {
    const result = detectClean('git clean -fd');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'ask');
  });

  it('asks for git clean -f -d', () => {
    const result = detectClean('git clean -f -d');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'ask');
  });

  it('asks for git clean --force --directories', () => {
    const result = detectClean('git clean --force --directories');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'ask');
  });

  it('allows git clean -f without -d (documents current behavior)', () => {
    const result = detectClean('git clean -f');
    assert.equal(result, null);
  });

  it('allows git clean --force without --directories (documents current behavior)', () => {
    const result = detectClean('git clean --force');
    assert.equal(result, null);
  });

  it('allows git clean -n (dry run, no -f)', () => {
    const result = detectClean('git clean -n');
    assert.equal(result, null);
  });

  it('allows git clean -fdn (dry run wins even with -f and -d)', () => {
    const result = detectClean('git clean -fdn');
    assert.equal(result, null);
  });
});

describe('protectedBranches', () => {
  it('defaults to main and master', () => {
    delete process.env.PROTECTED_BRANCHES;
    assert.deepEqual(protectedBranches(), ['main', 'master']);
  });

  it('reads a custom PROTECTED_BRANCHES env var', () => {
    process.env.PROTECTED_BRANCHES = 'develop, release';
    assert.deepEqual(protectedBranches(), ['develop', 'release']);
  });
});

describe('edge cases', () => {
  it('returns null for empty command across all detectors', () => {
    assert.equal(detectForcePush('', null, PROTECTED), null);
    assert.equal(detectHardReset('', null, PROTECTED), null);
    assert.equal(detectBranchDelete('', PROTECTED), null);
    assert.equal(detectCheckoutRestoreDot('', null, PROTECTED), null);
    assert.equal(detectClean(''), null);
  });

  it('returns null for unrelated commands', () => {
    assert.equal(detectForcePush('npm test', null, PROTECTED), null);
    assert.equal(detectHardReset('npm test', 'main', PROTECTED), null);
  });

  it('returns null for regular git commands', () => {
    assert.equal(detectForcePush('git status', null, PROTECTED), null);
    assert.equal(detectHardReset('git diff', 'main', PROTECTED), null);
    assert.equal(detectBranchDelete('git log', PROTECTED), null);
  });
});
