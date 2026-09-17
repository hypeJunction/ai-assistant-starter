const { describe, it, afterEach } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');

const {
  classifyTaskClass,
  looksLikePivot,
  buildPlanModeGuidance,
  statePath,
} = require('../../skills/prompt-context-router/references/hook.js');

// ── classifyTaskClass ──

describe('classifyTaskClass', () => {
  it('classifies mechanical prompts', () => {
    assert.equal(classifyTaskClass('please rename this variable'), 'mechanical');
  });

  it('classifies implementation prompts', () => {
    assert.equal(classifyTaskClass('implement a new endpoint for user signup'), 'implementation');
  });

  it('classifies debugging prompts', () => {
    assert.equal(classifyTaskClass('this test is flaky and keeps producing a stack trace'), 'debugging');
  });

  it('classifies architecture prompts', () => {
    assert.equal(classifyTaskClass('we need a redesign, what tradeoff should we accept?'), 'architecture');
  });

  it('classifies extreme prompts', () => {
    assert.equal(classifyTaskClass('this is a codebase-wide rewrite the entire service'), 'extreme');
  });

  it('abstains when nothing matches', () => {
    assert.equal(classifyTaskClass('what time is it in tokyo'), 'abstain');
  });

  it('does not classify a negated architecture ask as architecture', () => {
    assert.equal(classifyTaskClass("don't redesign this, just leave it"), 'abstain');
  });

  it('does not classify a negated extreme ask as extreme', () => {
    assert.equal(classifyTaskClass('no need to rewrite the entire module here'), 'abstain');
  });

  it('does not match "fix" inside "prefix"', () => {
    assert.equal(classifyTaskClass("let's talk about the prefix for these config keys"), 'abstain');
  });

  it('does not match "add" inside "additionally"', () => {
    assert.equal(classifyTaskClass('additionally, the docs look fine'), 'abstain');
  });
});

// ── looksLikePivot ──

describe('looksLikePivot', () => {
  it('flags an aside marker as a pivot', () => {
    const prompt = 'quick question, what does this env var do';
    assert.equal(looksLikePivot(prompt, prompt.toLowerCase()), true);
  });

  it('does not flag a continuation pronoun as a pivot', () => {
    const prompt = 'can you also fix that for me';
    assert.equal(looksLikePivot(prompt, prompt.toLowerCase()), false);
  });

  it('does not flag a prompt with a file reference as a pivot', () => {
    const prompt = 'update skills/foo/hook.js to add a new rule';
    assert.equal(looksLikePivot(prompt, prompt.toLowerCase()), false);
  });

  it('flags a short unrelated prompt as a pivot', () => {
    const prompt = 'what is the capital of Peru';
    assert.equal(looksLikePivot(prompt, prompt.toLowerCase()), true);
  });
});

// ── buildPlanModeGuidance ──

describe('buildPlanModeGuidance', () => {
  it('returns null when already in plan mode', () => {
    const result = buildPlanModeGuidance({ taskClass: 'extreme', permissionMode: 'plan', sessionId: 's1' });
    assert.equal(result, null);
  });

  it('points abstain-classified prompts at context-disambiguation', () => {
    const result = buildPlanModeGuidance({ taskClass: 'abstain', permissionMode: null, sessionId: 's2' });
    assert.match(result.additionalContext, /context-disambiguation/);
  });

  it('advises EnterPlanMode for architecture-classified prompts', () => {
    const result = buildPlanModeGuidance({ taskClass: 'architecture', permissionMode: null, sessionId: 's3' });
    assert.match(result.additionalContext, /EnterPlanMode/);
  });

  describe('extreme class', () => {
    const sessionId = 'test-session-extreme';
    const filePath = statePath(sessionId);

    afterEach(() => {
      fs.rmSync(filePath, { force: true });
    });

    it('denies the first extreme prompt in a session when enforce mode is on', () => {
      const result = buildPlanModeGuidance({
        taskClass: 'extreme', permissionMode: null, sessionId, extremeMode: 'enforce',
      });
      assert.equal(result.permissionDecision, 'deny');
    });

    it('only advises on the second extreme prompt in the same session', () => {
      buildPlanModeGuidance({ taskClass: 'extreme', permissionMode: null, sessionId, extremeMode: 'enforce' });
      const result = buildPlanModeGuidance({
        taskClass: 'extreme', permissionMode: null, sessionId, extremeMode: 'enforce',
      });
      assert.equal(result.permissionDecision, undefined);
      assert.match(result.additionalContext, /EnterPlanMode/);
    });

    it('never denies when extremeMode is not enforce', () => {
      const result = buildPlanModeGuidance({
        taskClass: 'extreme', permissionMode: null, sessionId, extremeMode: 'warn-only',
      });
      assert.equal(result.permissionDecision, undefined);
      assert.match(result.additionalContext, /EnterPlanMode/);
    });
  });
});
