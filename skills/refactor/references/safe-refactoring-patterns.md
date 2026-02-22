# Safe Refactoring Patterns

Common refactoring patterns with before/after examples, risk levels, verification approach, and batch safety guidance.

## Extract Function

**Risk:** Low
**Batch safe:** No — each extraction requires understanding the specific code context

Pull a block of code into a named function. Use when code does something that deserves a name, or when the same logic appears in multiple places.

```typescript
// Before
function processOrder(order: Order) {
  // ... other logic ...
  const subtotal = order.items.reduce((sum, item) => sum + item.price * item.quantity, 0);
  const tax = subtotal * 0.08;
  const shipping = subtotal > 100 ? 0 : 9.99;
  const total = subtotal + tax + shipping;
  // ... use total ...
}

// After
function calculateOrderTotal(items: OrderItem[]): number {
  const subtotal = items.reduce((sum, item) => sum + item.price * item.quantity, 0);
  const tax = subtotal * 0.08;
  const shipping = subtotal > 100 ? 0 : 9.99;
  return subtotal + tax + shipping;
}

function processOrder(order: Order) {
  // ... other logic ...
  const total = calculateOrderTotal(order.items);
  // ... use total ...
}
```

**Verification:** Run tests for the containing module. The extracted function should have identical behavior.

**When NOT to use:**
- The code block is only used once and is already readable
- Extraction would require passing 5+ parameters (indicates the surrounding function needs restructuring first)

## Inline Function

**Risk:** Low
**Batch safe:** Yes — mechanical replacement

Replace a function call with the function body. Use when the function name adds no clarity over the code itself, or when a function is called only once and adds unnecessary indirection.

```typescript
// Before
function isEligible(user: User): boolean {
  return user.age >= 18;
}

if (isEligible(user)) { /* ... */ }

// After
if (user.age >= 18) { /* ... */ }
```

**Verification:** Run tests. Behavior should be identical.

**When NOT to use:**
- The function is called from multiple places
- The function name provides important documentation
- The function body is complex (>3 lines)

## Rename Symbol

**Risk:** Low (with IDE support), Medium (manual)
**Batch safe:** Yes — mechanical find-and-replace within verified scope

Change the name of a variable, function, class, type, or file.

```typescript
// Before
function getData(id: string) { /* ... */ }
const d = getData('123');

// After
function fetchUserById(id: string) { /* ... */ }
const user = fetchUserById('123');
```

**Verification:**
1. Type check must pass (catches missed renames in typed code)
2. Run affected tests
3. Search for string references (logs, error messages, serialized data) that won't be caught by type check

**Batch approach:**
1. Find all occurrences with grep/search
2. Replace in batches of 5 files
3. Type check after each batch
4. Watch for: dynamic access (`obj[variableName]`), string references in tests, serialized names

## Move to Module

**Risk:** Medium
**Batch safe:** No — each move requires updating all import sites

Move a function, class, or type from one file to another. Use when code is in the wrong module or when splitting a large file.

```typescript
// Before: src/utils.ts (too large, mixed concerns)
export function validateEmail(email: string): boolean { /* ... */ }
export function formatCurrency(amount: number): string { /* ... */ }

// After: src/validation.ts (focused module)
export function validateEmail(email: string): boolean { /* ... */ }

// After: src/formatting.ts (focused module)
export function formatCurrency(amount: number): string { /* ... */ }
```

**Steps:**
1. Create the target file
2. Move the code (cut from source, paste to target)
3. Add export in target file
4. Update all import sites to use new path
5. Optionally: re-export from original location temporarily for backwards compatibility

**Verification:**
1. Type check (catches broken imports)
2. Run full test suite (import changes can have surprising effects)
3. Check for dynamic imports: `import('./utils')` won't be caught by type check

**Common pitfalls:**
- Circular dependencies: moving code can create A→B→A import cycles
- Barrel exports: if the original file is re-exported from an index.ts, update that too
- Relative paths: moving a file changes its relative import paths to other modules

## Replace Conditional with Polymorphism

**Risk:** Medium-High
**Batch safe:** No — structural change requiring careful design

Replace switch/if-else chains with polymorphic dispatch. Use when conditionals based on type repeat across multiple functions.

```typescript
// Before: repeated type switches
function calculateArea(shape: Shape): number {
  switch (shape.type) {
    case 'circle': return Math.PI * shape.radius ** 2;
    case 'rectangle': return shape.width * shape.height;
    case 'triangle': return 0.5 * shape.base * shape.height;
  }
}

function calculatePerimeter(shape: Shape): number {
  switch (shape.type) {
    case 'circle': return 2 * Math.PI * shape.radius;
    case 'rectangle': return 2 * (shape.width + shape.height);
    case 'triangle': return shape.a + shape.b + shape.c;
  }
}

// After: polymorphic classes
interface Shape {
  area(): number;
  perimeter(): number;
}

class Circle implements Shape {
  constructor(private radius: number) {}
  area() { return Math.PI * this.radius ** 2; }
  perimeter() { return 2 * Math.PI * this.radius; }
}
```

**Verification:** This changes structure significantly. Existing tests must all pass. Consider writing characterization tests first if coverage is low.

**When NOT to use:**
- Only one switch statement (not enough duplication to justify the abstraction)
- The conditional logic is simple and unlikely to grow
- You're adding a new case, not refactoring existing ones

## Extract Interface / Type

**Risk:** Low
**Batch safe:** Yes — additive change

Create a shared interface when multiple types have the same shape, or when you want to depend on abstractions rather than implementations.

```typescript
// Before: function coupled to specific class
function sendNotification(service: EmailService, message: string) {
  service.send(message);
}

// After: function depends on interface
interface NotificationService {
  send(message: string): Promise<void>;
}

function sendNotification(service: NotificationService, message: string) {
  return service.send(message);
}
```

**Verification:** Type check. This is additive — existing code should work without modification.

## Simplify Conditional

**Risk:** Low
**Batch safe:** No — logic must be verified per instance

Reduce nested conditionals or combine related conditions.

```typescript
// Before: nested guards
function getDiscount(user: User): number {
  if (user.isPremium) {
    if (user.yearsActive > 5) {
      return 0.2;
    } else {
      return 0.1;
    }
  } else {
    return 0;
  }
}

// After: early returns
function getDiscount(user: User): number {
  if (!user.isPremium) return 0;
  if (user.yearsActive > 5) return 0.2;
  return 0.1;
}
```

**Verification:** Run tests. Pay special attention to edge cases — simplified conditions can accidentally change boundary behavior.

## Batch Safety Guide

| Pattern | Batch Safe | Why |
|---------|-----------|-----|
| Rename symbol | Yes | Mechanical find-replace |
| Inline function | Yes | Mechanical expansion |
| Extract interface | Yes | Additive, no behavior change |
| Extract function | No | Context-dependent decisions |
| Move to module | No | Import chain effects |
| Replace conditional | No | Structural redesign |
| Simplify conditional | No | Logic verification needed |

**Batch-safe patterns** can be applied to 5+ files per batch with type check verification between batches.

**Non-batch patterns** should be applied one file at a time with test verification after each change.

## Import/Export Chaining During Moves

When moving code between modules, handle re-exports carefully:

```typescript
// Step 1: Move function to new file
// src/validation.ts (new home)
export function validateEmail(email: string): boolean { /* ... */ }

// Step 2: Re-export from old location (temporary backward compatibility)
// src/utils.ts (old home)
export { validateEmail } from './validation';

// Step 3: Update all import sites (do in batches)
// Change: import { validateEmail } from './utils'
// To:     import { validateEmail } from './validation'

// Step 4: Remove re-export from old location
// Only after all imports are updated and tests pass
```

This approach prevents broken imports during the transition. Never skip steps 2-4 — removing the re-export before updating all import sites will break the build.
