const { describe, it, after } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');

const {
  decide,
  checkHeavyBashPattern,
  loadBaselines,
  extractAgentRequest,
  normalizeModelName,
} = require('../../skills/cost-guardrail/references/hook.js');

function freshBaselines(overrides) {
  return {
    generated_at: new Date().toISOString(),
    window: { from: '2026-08-01T00:00:00Z', to: '2026-09-01T00:00:00Z' },
    factor_default: 3.0,
    by_model: {
      'claude-haiku-4-5': { count: 100, median_cost: 0.01, p95_cost: 0.05, mean_cost: 0.015 },
      'claude-sonnet-5': { count: 200, median_cost: 0.03, p95_cost: 0.15, mean_cost: 0.05 },
      'claude-opus-5': { count: 50, median_cost: 0.25, p95_cost: 1.0, mean_cost: 0.3 },
    },
    by_tool: {
      Bash: { count: 500, median_cost: 0.001, p95_cost: 0.005, mean_cost: 0.0015 },
    },
    ...overrides,
  };
}

// ── extractAgentRequest ──

describe('extractAgentRequest', () => {
  it('extracts model and subagent_type from tool_input', () => {
    const result = extractAgentRequest({ tool_input: { model: 'claude-opus-5', subagent_type: 'general' } });
    assert.equal(result.model, 'claude-opus-5');
    assert.equal(result.subagentType, 'general');
  });

  it('returns nulls when absent', () => {
    const result = extractAgentRequest({ tool_input: {} });
    assert.equal(result.model, null);
    assert.equal(result.subagentType, null);
  });
});

// ── normalizeModelName ──

describe('normalizeModelName', () => {
  const byModel = freshBaselines().by_model;

  it('returns exact match untouched', () => {
    assert.equal(normalizeModelName('claude-opus-5', byModel), 'claude-opus-5');
  });

  it('maps a shorthand alias to a tracked full name', () => {
    assert.equal(normalizeModelName('opus', byModel), 'claude-opus-5');
  });

  it('returns null for no model', () => {
    assert.equal(normalizeModelName(null, byModel), null);
  });
});

// ── decide (Agent cost check) ──

describe('decide', () => {
  it('allows a proportionate model tier', () => {
    const result = decide({ model: 'claude-sonnet-5' }, freshBaselines(), { mode: 'enforce', factor: 3.0 });
    assert.equal(result, null);
  });

  it('blocks a disproportionate model tier in enforce mode', () => {
    // opus (0.25) / haiku (0.01) = 25x, well over factor 3.0
    const result = decide({ model: 'claude-opus-5' }, freshBaselines(), { mode: 'enforce', factor: 3.0 });
    assert.notEqual(result, null);
    assert.equal(result.hookSpecificOutput.permissionDecision, 'deny');
  });

  it('never blocks in warn-only mode, asks instead', () => {
    const result = decide({ model: 'claude-opus-5' }, freshBaselines(), { mode: 'warn-only', factor: 3.0 });
    assert.notEqual(result, null);
    assert.equal(result.hookSpecificOutput.permissionDecision, 'ask');
  });

  it('fails open when baselines are null', () => {
    const result = decide({ model: 'claude-opus-5' }, null, { mode: 'enforce', factor: 3.0 });
    assert.equal(result, null);
  });

  it('fails open when the requested model is not tracked', () => {
    const result = decide({ model: 'claude-mythos-5-1' }, freshBaselines(), { mode: 'enforce', factor: 3.0 });
    assert.equal(result, null);
  });

  it('fails open when the tracked model has too few samples', () => {
    const baselines = freshBaselines({
      by_model: { 'claude-opus-5': { count: 2, median_cost: 0.25, p95_cost: 1.0, mean_cost: 0.3 } },
    });
    const result = decide({ model: 'claude-opus-5' }, baselines, { mode: 'enforce', factor: 3.0 });
    assert.equal(result, null);
  });
});

// ── checkHeavyBashPattern ──

describe('checkHeavyBashPattern', () => {
  it('allows Bash when proportionate', () => {
    const baselines = freshBaselines({
      by_tool: {
        Bash: { count: 500, median_cost: 0.001, p95_cost: 0.005, mean_cost: 0.0015 },
        Grep: { count: 500, median_cost: 0.0009, p95_cost: 0.004, mean_cost: 0.0012 },
      },
    });
    const result = checkHeavyBashPattern('git status', baselines.by_tool, { mode: 'enforce', factor: 3.0 });
    assert.equal(result, null);
  });

  it('flags Bash when disproportionately expensive vs cheapest tool', () => {
    const baselines = freshBaselines({
      by_tool: {
        Bash: { count: 500, median_cost: 0.01, p95_cost: 0.05, mean_cost: 0.02 },
        Grep: { count: 500, median_cost: 0.0005, p95_cost: 0.002, mean_cost: 0.0008 },
      },
    });
    const result = checkHeavyBashPattern('some command', baselines.by_tool, { mode: 'enforce', factor: 3.0 });
    assert.notEqual(result, null);
    assert.equal(result.hookSpecificOutput.permissionDecision, 'deny');
  });

  it('fails open with no command', () => {
    const result = checkHeavyBashPattern('', freshBaselines().by_tool, { mode: 'enforce', factor: 3.0 });
    assert.equal(result, null);
  });
});

// ── loadBaselines ──

describe('loadBaselines', () => {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'cost-guardrail-test-'));
  after(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it('returns null for a missing file', () => {
    assert.equal(loadBaselines(path.join(tmpDir, 'nope.json'), 45), null);
  });

  it('returns null for malformed JSON', () => {
    const p = path.join(tmpDir, 'malformed.json');
    fs.writeFileSync(p, '{not json');
    assert.equal(loadBaselines(p, 45), null);
  });

  it('returns null when required fields are missing', () => {
    const p = path.join(tmpDir, 'missing-fields.json');
    fs.writeFileSync(p, JSON.stringify({ foo: 'bar' }));
    assert.equal(loadBaselines(p, 45), null);
  });

  it('returns null when the baseline is stale', () => {
    const p = path.join(tmpDir, 'stale.json');
    const stale = freshBaselines();
    stale.generated_at = new Date(Date.now() - 100 * 24 * 60 * 60 * 1000).toISOString();
    fs.writeFileSync(p, JSON.stringify(stale));
    assert.equal(loadBaselines(p, 45), null);
  });

  it('loads a fresh, well-formed baseline file', () => {
    const p = path.join(tmpDir, 'fresh.json');
    fs.writeFileSync(p, JSON.stringify(freshBaselines()));
    const result = loadBaselines(p, 45);
    assert.notEqual(result, null);
    assert.equal(result.by_model['claude-opus-5'].count, 50);
  });
});
