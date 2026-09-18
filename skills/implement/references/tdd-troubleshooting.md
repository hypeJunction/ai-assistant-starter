# TDD Troubleshooting

Decision tables for common difficulties encountered during TDD. When you're stuck, find your situation below and follow the prescribed action.

## "I Don't Know What Test to Write"

| Situation | Action |
|-----------|--------|
| Requirements are unclear | Ask the user. Don't guess requirements — wrong tests are worse than no tests. |
| Feature is too large to test as one unit | Break it into smaller behaviors. Each behavior is one test. |
| You can see the implementation but not the test | Describe the behavior in plain English. Turn that sentence into a test. |
| Multiple behaviors need testing | Pick the simplest one first. Build up incrementally. |
| The function doesn't exist yet | Write what you WISH you could call. The test defines the API. |

### The "Wish" Technique

When stuck, write the test as if the ideal API already exists:

```typescript
// Step 1: Write what you wish existed
it('should calculate shipping for international orders', () => {
  const order = createOrder({ country: 'DE', items: [{ weight: 2.5 }] });
  const shipping = calculateShipping(order);
  expect(shipping).toEqual({ cost: 15.99, method: 'international', estimatedDays: 7 });
});

// Step 2: Now you know the interface — implement calculateShipping to make this pass
```

The test IS the specification. You don't need to know the implementation to write it.

## "The Test is Too Complex"

| Symptom | Cause | Fix |
|---------|-------|-----|
| >15 lines of setup (Arrange) | Too many dependencies | Extract a test factory/builder |
| Multiple assertions testing different concepts | Test does too much | Split into multiple tests, one concept each |
| Deeply nested mock configuration | Code is tightly coupled | Redesign: extract interfaces, inject dependencies |
| Test requires real database/network | Wrong test type for the layer | Use mocks for unit tests; save real I/O for integration tests |

### Simplification Patterns

**Extract test factory:**

```typescript
// BEFORE: Complex setup in every test
it('should apply discount', () => {
  const user = { id: '1', name: 'Alice', tier: 'premium', joinDate: new Date('2020-01-01') };
  const cart = { items: [{ id: 'a', price: 100, qty: 2 }], userId: '1' };
  const discount = calculateDiscount(user, cart);
  expect(discount).toBe(20);
});

// AFTER: Factory handles defaults
function createUser(overrides = {}) {
  return { id: '1', name: 'Alice', tier: 'standard', joinDate: new Date(), ...overrides };
}
function createCart(overrides = {}) {
  return { items: [{ id: 'a', price: 100, qty: 1 }], userId: '1', ...overrides };
}

it('should apply premium discount', () => {
  const discount = calculateDiscount(
    createUser({ tier: 'premium' }),
    createCart({ items: [{ id: 'a', price: 100, qty: 2 }] })
  );
  expect(discount).toBe(20);
});
```

## "I Must Mock Everything"

This is a design problem, not a testing problem.

| Situation | What It Means | Fix |
|-----------|---------------|-----|
| 3+ mocks required | Unit has too many collaborators | Extract pure logic from side effects |
| Mock configuration is complex | Coupling is too tight | Introduce interfaces at boundaries |
| Changing one mock breaks many tests | Tests are coupled to implementation | Mock at higher boundaries, test through public API |

### The "Extract Pure Logic" Pattern

```typescript
// BEFORE: Must mock database, logger, and email service
async function processOrder(orderId: string) {
  const order = await db.orders.findById(orderId);    // mock 1
  const total = calculateTotal(order.items);
  logger.info(`Processing order ${orderId}`);          // mock 2
  await emailService.send(order.userEmail, total);     // mock 3
  return { orderId, total };
}

// AFTER: Extract pure logic — test WITHOUT mocks
function calculateTotal(items: OrderItem[]): number {
  return items.reduce((sum, item) => sum + item.price * item.quantity, 0);
}

// Unit test the pure function — no mocks needed
it('should sum item prices with quantities', () => {
  const items = [{ price: 10, quantity: 2 }, { price: 5, quantity: 3 }];
  expect(calculateTotal(items)).toBe(35);
});

// Integration test the orchestration — at a higher level
```

## "Tests Pass But Behavior Is Wrong"

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Test passes but user reports bug | Test doesn't cover the actual scenario | Write a test for the exact failing scenario |
| Test passes but code clearly wrong | Test asserts the wrong thing | Review assertions — are they checking the right property? |
| All tests green but feature broken | Tests are too isolated | Add an integration test that exercises the full flow |
| Tests match implementation, not spec | Tests were written to match code, not requirements | Delete tests. Rewrite from requirements/spec. |

## "Bug Found During Development"

When a bug is discovered while doing TDD on a feature:

```
Bug found
  ├─ Is the bug in your new feature code?
  │   └─ Yes → You're still in TDD. Write a failing test for the bug. Fix. Continue.
  ├─ Is the bug in existing code you're changing?
  │   └─ Yes → Write a failing test for the bug FIRST. Fix. Then continue feature TDD.
  └─ Is the bug in unrelated code?
      └─ Create a todo. Do NOT fix. Stay focused on current TDD cycle.
```

### Bug Fix TDD Template

```typescript
// 1. RED: Write test that reproduces the bug
it('should handle 100% discount without going negative', () => {
  const result = calculateDiscount(50.00, 100);
  expect(result).toBe(0); // Currently returns -50
});

// 2. Verify RED: Run test, confirm it fails for the right reason
// Expected: 0, Received: -50 ✓ Valid failure

// 3. GREEN: Fix the bug
export function calculateDiscount(price: number, percent: number): number {
  return Math.max(0, price - (price * percent / 100));
}

// 4. Verify GREEN: All tests pass ✓
// 5. REFACTOR: Clean up if needed
// 6. Continue with original TDD work
```

## Common Error Messages and Fixes

| Error | Likely Cause | Fix |
|-------|-------------|-----|
| `TypeError: X is not a function` | Function not exported or doesn't exist yet | Valid RED — proceed to GREEN to create it |
| `Cannot find module` | Import path wrong | Invalid RED — fix the import, re-run |
| `Expected undefined, received undefined` | Test doesn't actually call anything | Invalid RED — fix the test to call real code |
| `Timeout exceeded` | Async test missing `await` or test is actually slow | Fix async handling or mock the slow operation |
| `Cannot spy on property that doesn't exist` | Mock target is wrong | Fix the mock setup, re-run |

## Decision Table: What Phase Am I In?

If you're confused about where you are in the cycle:

| Current State | Phase | Next Action |
|--------------|-------|-------------|
| No test written yet | Pre-RED | Write a failing test |
| Test written, not yet run | RED | Run the test, verify it fails |
| Test fails for valid reason | Verified RED | Write minimal code to pass |
| Test fails for wrong reason (syntax, import) | Invalid RED | Fix the test, re-run |
| Production code written, not yet verified | GREEN | Run the test, verify it passes |
| New test passes, haven't checked others | Partial GREEN | Run all related tests |
| All tests pass, code is messy | REFACTOR | Clean up, run tests after each change |
| All tests pass, code is clean | Cycle complete | Write next test or commit |
