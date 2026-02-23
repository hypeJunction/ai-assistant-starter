# TDD Skill Verification

## Scenario

A developer needs to build a `PriceCalculator` class with methods for: `calculateSubtotal(items)`, `applyDiscount(subtotal, code)`, and `calculateTax(subtotal, region)`. The feature has 5 distinct behaviors to implement. They invoke `/tdd implement PriceCalculator with subtotal, discount, and tax calculation`.

### Project Context

| Aspect | Detail |
|--------|--------|
| Language | TypeScript |
| Test framework | Vitest |
| Package manager | npm |
| Existing patterns | Pure utility classes with static methods in `src/lib/` |
| Test location | Co-located `__tests__/` directories |

### Behaviors to Implement

| # | Behavior | Method |
|---|----------|--------|
| 1 | Calculates subtotal from item prices and quantities | `calculateSubtotal` |
| 2 | Returns zero subtotal for an empty item list | `calculateSubtotal` |
| 3 | Applies a percentage discount code to a subtotal | `applyDiscount` |
| 4 | Rejects invalid discount codes with an error | `applyDiscount` |
| 5 | Calculates tax based on subtotal and region-specific rate | `calculateTax` |

Note: The 3 methods yield 5 behaviors because `calculateSubtotal` has an edge case (empty list) and `applyDiscount` has an error case (invalid code). Decomposition targets behaviors, not methods.

## Expected Outcome

Agent decomposes the feature into 5 testable behaviors (not just 3 methods), creates the initial test file with `it.todo` stubs as a session roadmap, implements each behavior through strict RED-GREEN-REFACTOR cycles, tracks behavior count across cycles ("Behavior 1/5 complete"), commits at appropriate frequency (every 2-3 behaviors), and ends with all 5 behaviors implemented and tested.

## Key Checkpoints

### Checkpoint 1: Agent decomposes the feature into 5+ testable behaviors

**Phase:** Pre-RED (Feature Decomposition)

The agent analyzes the request and decomposes it into testable behaviors, not just methods. Each behavior is a single observable outcome expressed as "When [condition], it should [result]." The agent identifies that 3 methods produce at least 5 behaviors because some methods have edge cases and error cases.

**Evidence expected:**
```markdown
## Feature Decomposition

**Feature:** PriceCalculator
**Behaviors identified:** 5

| # | Behavior | Expected |
|---|----------|----------|
| 1 | When given items with prices and quantities, calculates the subtotal | Sum of (price * quantity) for all items |
| 2 | When given an empty item list, returns zero | 0 |
| 3 | When given a valid discount code, applies the percentage to subtotal | Reduced subtotal |
| 4 | When given an invalid discount code, throws an error | Error with descriptive message |
| 5 | When given a subtotal and region, calculates tax at the region's rate | Tax amount |
```

### Checkpoint 2: Agent creates the initial test file with todo stubs

**Phase:** Pre-RED (Test File Setup)

Before the first RED phase, the agent creates the test file with a `describe` block and `it.todo` entries for all planned behaviors. This provides a roadmap for the session and makes progress visible.

**Evidence expected:**
```typescript
// src/lib/__tests__/price-calculator.spec.ts
import { describe, it } from 'vitest';

describe('PriceCalculator', () => {
  it.todo('calculates subtotal from item prices and quantities');
  it.todo('returns zero subtotal for an empty item list');
  it.todo('applies percentage discount code to subtotal');
  it.todo('rejects invalid discount codes with an error');
  it.todo('calculates tax based on subtotal and region-specific rate');
});
```

The agent runs the test file to confirm it loads without errors (all 5 tests show as "todo/skipped").

### Checkpoint 3: RED -- Agent writes a failing test for the first behavior

**Phase:** Phase 1 (RED) -- Behavior 1/5

The agent replaces the first `it.todo` with a real test. The test references `PriceCalculator` and `calculateSubtotal`, which do not exist yet. The test describes behavior ("calculates subtotal from item prices and quantities"), not implementation.

**Evidence expected:**
```typescript
it('calculates subtotal from item prices and quantities', () => {
  const items = [
    { price: 10.00, quantity: 2 },
    { price: 5.50, quantity: 3 },
  ];
  const result = calculateSubtotal(items);
  expect(result).toBe(36.50);
});
```

The agent reports:
```markdown
## RED Phase -- Behavior 1/5: Subtotal calculation

**Test file:** `src/lib/__tests__/price-calculator.spec.ts`
**Test name:** `calculates subtotal from item prices and quantities`
**Asserts:** Return value equals sum of (price * quantity) for all items

Ready to verify this test fails.
```

### Checkpoint 4: RED -- Agent runs the test and confirms it fails with the right error

**Phase:** Phase 2 (Verify RED) -- Behavior 1/5

The agent runs the test and confirms it fails for a valid reason (function not found, module not exported, or assertion failure). The agent explicitly states the failure reason and confirms it is a valid RED.

**Evidence expected:**
```bash
npm run test -- src/lib/__tests__/price-calculator.spec.ts
# FAIL: Cannot find module '../price-calculator' or 'calculateSubtotal is not a function'
```

```markdown
## RED Verified -- Behavior 1/5

**Test result:** FAIL
**Failure reason:** Module `price-calculator` does not exist yet
**Valid failure:** Yes -- function has not been created
**Action:** Proceed to GREEN
```

### Checkpoint 5: GREEN -- Agent writes minimal code to make ONLY that test pass

**Phase:** Phase 3 (GREEN) -- Behavior 1/5

The agent creates `src/lib/price-calculator.ts` with only the code needed to pass the first test. The agent does NOT add `applyDiscount` or `calculateTax` yet -- those behaviors have no failing tests.

**Evidence expected:**
```typescript
// src/lib/price-calculator.ts
interface Item {
  price: number;
  quantity: number;
}

export function calculateSubtotal(items: Item[]): number {
  return items.reduce((sum, item) => sum + item.price * item.quantity, 0);
}
```

The agent does NOT add:
- `applyDiscount` (no failing test for it)
- `calculateTax` (no failing test for it)
- Error handling beyond what the test requires
- A class wrapper (unless the test specifically required it)

### Checkpoint 6: GREEN -- Agent runs tests and confirms all pass

**Phase:** Phase 4 (Verify GREEN) -- Behavior 1/5

The agent runs the test and confirms the new test passes. The agent also checks that no other tests broke.

**Evidence expected:**
```bash
npm run test -- src/lib/__tests__/price-calculator.spec.ts
# PASS: 1 passed, 4 todo
```

```markdown
## GREEN Verified -- Behavior 1/5

**New test:** PASS
**Related tests:** PASS (1 test, 4 todo)
**Clean output:** Yes

Ready to refactor.
```

### Checkpoint 7: REFACTOR -- Agent evaluates if refactoring is needed

**Phase:** Phase 5 (REFACTOR) -- Behavior 1/5

After the first behavior, the code is likely clean enough to skip refactoring. The agent explicitly evaluates and may skip with justification. The agent runs tests after any refactoring changes, or confirms no refactoring is needed.

**Evidence expected:**
```markdown
## REFACTOR -- Behavior 1/5

**Evaluation:** Code is minimal and clean. Single function with one reducer. No duplication, no unclear naming.
**Decision:** No refactoring needed at this time.

**All tests:** PASS
**Behavior 1/5 complete.**
```

### Checkpoint 8: Agent tracks behavior count after cycle completion

**Phase:** Post-cycle tracking

After completing the REFACTOR phase (or deciding to skip it), the agent reports progress using the format: "Behavior N/M: [description] -- COMPLETE". This prevents losing track in long sessions.

**Evidence expected:**
```markdown
**Progress:**
- [x] Behavior 1/5: Subtotal calculation -- COMPLETE
- [ ] Behavior 2/5: Empty item list edge case
- [ ] Behavior 3/5: Percentage discount application
- [ ] Behavior 4/5: Invalid discount code error
- [ ] Behavior 5/5: Region-based tax calculation
```

### Checkpoint 9: Agent repeats RED-GREEN-REFACTOR for each remaining behavior

**Phase:** Cycles 2-5

The agent continues through behaviors 2-5, each following the same strict RED-GREEN-REFACTOR cycle. Each cycle:
1. Replaces the next `it.todo` with a real failing test
2. Runs the test and confirms it fails for the right reason
3. Writes minimal code to make it pass
4. Runs all tests and confirms they pass
5. Evaluates refactoring opportunities
6. Reports: "Behavior N/5 complete"

**Evidence expected for Behavior 3 (discount application):**

The agent does NOT write `applyDiscount` until Behavior 3's RED phase. When it does:

```typescript
// RED: Test written
it('applies percentage discount code to subtotal', () => {
  const result = applyDiscount(100, 'SAVE20');
  expect(result).toBe(80);
});
```

```bash
# Verify RED: fails because applyDiscount doesn't exist
npm run test -- src/lib/__tests__/price-calculator.spec.ts
# FAIL: applyDiscount is not a function
```

```typescript
// GREEN: minimal implementation
export function applyDiscount(subtotal: number, code: string): number {
  const discounts: Record<string, number> = { SAVE20: 20 };
  const percent = discounts[code];
  return subtotal - (subtotal * percent / 100);
}
```

Note: The implementation may be naive (hardcoded discount map). That is correct -- the test only requires `SAVE20` to work. Error handling for invalid codes comes in Behavior 4.

### Checkpoint 10: Agent commits at natural TDD boundaries

**Phase:** Commit points during cycles

The agent commits at natural boundaries rather than waiting until the end or committing after every single cycle. For this 5-behavior feature:

**Evidence expected:**
- Commit after Behavior 2 or 3: `test: add PriceCalculator subtotal calculation` (covers the first method's behaviors)
- Commit after Behavior 4 or 5: `test: add PriceCalculator discount and tax calculation` (covers remaining behaviors)
- OR commit after each behavior if the behaviors are complex

The agent does NOT:
- Wait until all 5 behaviors are done to make a single commit
- Commit with failing tests
- Commit without running the full test suite first

### Checkpoint 11: Agent does NOT write production code without a failing test

**Phase:** All cycles

At no point does the agent write production code that is not justified by a currently-failing test. This means:

- `calculateSubtotal` is not created until Behavior 1's RED phase
- `applyDiscount` is not created until Behavior 3's RED phase
- `calculateTax` is not created until Behavior 5's RED phase
- Error handling for invalid discount codes is not added until Behavior 4's RED phase
- No "I'll add this while I'm here" code

**Evidence expected:**

After Behavior 2 is complete, the production file contains only `calculateSubtotal` (and possibly an `Item` interface). It does NOT contain stubs, empty functions, or forward declarations for `applyDiscount` or `calculateTax`.

## Anti-Patterns

### 1. Agent writes all tests first, then all production code

**Wrong:** Agent creates the test file with all 5 real tests (not todos), then implements all the production code at once.

This violates the fundamental TDD cycle. The RED-GREEN-REFACTOR loop requires alternating between test and production code. Writing all tests first means multiple tests fail simultaneously, there is no incremental verification, and the agent cannot confirm that each test catches the specific behavior it targets. The `it.todo` stubs are a roadmap, not real tests -- real test implementations must alternate with production code.

### 2. Agent writes more production code than needed to pass the current test

**Wrong:** During Behavior 1's GREEN phase, the agent creates `calculateSubtotal`, `applyDiscount`, and `calculateTax` because "we'll need them anyway."

Only the code required by the currently-failing test should be written. Writing ahead means the extra code is untested (no failing test preceded it), may not match the eventual test requirements, and violates the iron law that every line of production code must be justified by a failing test.

### 3. Agent skips the RED phase (does not confirm the test fails)

**Wrong:** Agent writes the test, then immediately writes the production code without running the test to confirm it fails first.

The RED verification step is what proves the test actually tests something. If the test passes without new code, it does not test new behavior. If it fails for the wrong reason (syntax error, wrong import), the subsequent GREEN phase will fix the wrong problem. Skipping RED removes the safety net.

### 4. Agent rationalizes skipping TDD ("this is too simple for TDD")

**Wrong:** Agent decides that `calculateSubtotal` is "just a reduce" and writes both the test and implementation together, or writes the implementation first.

The "too simple to test" rationalization is explicitly addressed in the skill's Common Rationalizations table. Simple code breaks. A one-line function with a typo is still a bug. The test takes 30 seconds to write. The discipline of the cycle is what provides the guarantee.

### 5. Agent forgets to track which behavior cycle it is on

**Wrong:** After completing 3 behaviors, the agent starts the next RED phase without stating which behavior (4/5) it is working on, or loses count and repeats a behavior.

Multi-cycle TDD sessions require explicit progress tracking. Without it, the agent may skip behaviors, repeat behaviors, or lose context about what has been tested. The "Behavior N/M: [description]" format after each cycle keeps the session organized.

### 6. Agent does not create the initial test file with todo stubs

**Wrong:** Agent jumps straight into the first RED phase without creating a roadmap of planned behaviors, then forgets about one of the 5 behaviors.

The initial test file with `it.todo` entries serves as a session plan. It makes progress visible (4 todo, 1 passed), prevents forgotten behaviors, and gives the developer a preview of the decomposition. Without it, the agent may lose track of remaining work.

## Known Gaps

| Gap | Description | Resolution |
|-----|-------------|------------|
| No multi-cycle behavior tracking | The skill had no guidance on tracking progress across multiple RED-GREEN-REFACTOR cycles. In long sessions, the agent could lose track of which behavior it was implementing or how many remained. | Added "Behavior N/M" tracking format to SKILL.md. Agent reports progress after each cycle completion. |
| No initial test file creation guidance | The skill went straight from behavior identification to writing the first failing test, with no step for creating a test file roadmap. Behaviors could be forgotten in long sessions. | Added pre-RED step to create the test file with `it.todo` stubs for all planned behaviors, providing a visible session roadmap. |
| No commit frequency guidance | The skill said "commit" at the end of a cycle but gave no guidance on when to commit during multi-behavior sessions -- after every cycle? After all cycles? Before risky refactors? | Added commit frequency guidance: after every 2-3 behaviors for simple features, after each behavior for complex features, and always before risky refactors. |
| No feature decomposition strategy | The skill said "break the feature into the smallest testable behavior" but gave no strategy for HOW to decompose. Developers often decompose into methods instead of behaviors, missing edge cases and error paths. | Added decomposition strategy: target behaviors not methods, express as "When [condition], it should [result]", and note that methods may have multiple behaviors (happy path, edge cases, error cases). |
