# Docs Skill Verification

## Scenario

A developer runs `/docs --files=src/services/payment.service.ts` on a TypeScript file containing:

- 3 exported functions:
  - `processPayment()` — no JSDoc at all
  - `refundPayment()` — has stale JSDoc (wrong parameter description; says `@param orderId` but the actual parameter is `transactionId`)
  - `getPaymentStatus()` — no JSDoc, throws `PaymentError` on invalid ID
- 1 exported interface: `PaymentConfig` (no docs)
- 1 private helper: `_calculateFee()` (no docs — should stay undocumented)
- Test file exists at `src/services/__tests__/payment.service.spec.ts`

**User input:**
> /docs --files=src/services/payment.service.ts

## Expected Outcome

The agent reads the source file and its test file, then adds JSDoc to `processPayment()` and `getPaymentStatus()`, updates the stale JSDoc on `refundPayment()`, adds `@throws PaymentError` to `getPaymentStatus()`, documents the `PaymentConfig` interface, does NOT document `_calculateFee()`, runs typecheck to verify no issues, and presents a documentation report listing what was added, updated, and skipped.

## Key Checkpoints

### 1. Agent reads the source file before making changes

**Phase:** Step 1 (Identify Documentation Scope)

The agent reads `src/services/payment.service.ts` to understand the full file contents — exported functions, interfaces, existing JSDoc (or lack thereof), and private helpers.

**Evidence expected:** The agent opens and reads the source file, identifying 3 exported functions, 1 exported interface, and 1 private helper. It notes which items already have JSDoc and which do not.

### 2. Agent reads the test file to understand edge cases and behavior

**Phase:** Step 2 (Analyze Code Purpose)

The agent discovers and reads `src/services/__tests__/payment.service.spec.ts` to understand function behavior, edge cases, error conditions, and expected inputs/outputs. This is critical for writing accurate documentation rather than guessing.

**Evidence expected:** The agent reads the test file and extracts behavioral insights such as: what `processPayment()` returns on success/failure, what triggers `PaymentError` in `getPaymentStatus()`, and what edge cases `refundPayment()` handles.

### 3. `processPayment()` gets complete JSDoc

**Phase:** Step 3 (Add Documentation)

The agent adds a complete JSDoc block to `processPayment()` including `@param`, `@returns`, and `@example` tags. The description explains what the function does in business terms, not just restating the function name.

**Evidence expected:**
```typescript
/**
 * Charges the customer and records the transaction in the payment ledger.
 *
 * @param amount - The payment amount in cents
 * @param currency - ISO 4217 currency code (e.g., "USD")
 * @param customerId - The customer's unique identifier
 * @returns The completed transaction record with status and ID
 *
 * @example
 * ```typescript
 * const tx = await processPayment(5000, "USD", "cust_123");
 * ```
 */
```

### 4. `refundPayment()` stale JSDoc is updated

**Phase:** Step 3 (Add Documentation)

The agent detects that `refundPayment()` has existing JSDoc with an incorrect parameter name (`@param orderId` instead of `@param transactionId`) and updates it to match the actual function signature. The agent does not leave stale documentation in place.

**Evidence expected:** The `@param orderId` tag is replaced with `@param transactionId` and the description is updated to accurately reflect the parameter's purpose.

### 5. `getPaymentStatus()` gets `@throws PaymentError` tag

**Phase:** Step 3 (Add Documentation)

The agent adds JSDoc to `getPaymentStatus()` that includes `@throws {PaymentError}` because the function throws on invalid payment IDs. The agent learned this from reading the test file or the source implementation.

**Evidence expected:**
```typescript
/**
 * Retrieves the current status of a payment transaction.
 *
 * @param paymentId - The unique payment transaction identifier
 * @returns The payment status object with current state and timestamps
 * @throws {PaymentError} If the payment ID does not exist or is malformed
 *
 * @example
 * ```typescript
 * const status = await getPaymentStatus("pay_abc123");
 * ```
 */
```

### 6. `PaymentConfig` interface gets JSDoc documentation

**Phase:** Step 3 (Add Documentation)

The agent documents the `PaymentConfig` interface with a description of its purpose and, where helpful, adds property-level JSDoc comments.

**Evidence expected:**
```typescript
/**
 * Configuration for the payment service, including gateway credentials
 * and retry behavior.
 *
 * @example
 * ```typescript
 * const config: PaymentConfig = { gateway: "stripe", retries: 3 };
 * ```
 */
export interface PaymentConfig {
  /** The payment gateway provider name */
  gateway: string;
  /** Number of retry attempts for failed transactions */
  retries: number;
}
```

### 7. `_calculateFee()` is NOT documented

**Phase:** Step 3 (Add Documentation)

The agent recognizes that `_calculateFee()` is a private, non-exported helper function and deliberately skips it. The documentation scope is limited to the public API surface (exported functions, classes, and interfaces).

**Evidence expected:** The agent does not add JSDoc to `_calculateFee()`. In the final documentation report, it is either not mentioned or explicitly listed under "Skipped" with a reason (e.g., "private helper — not part of public API").

### 8. User approval gate before writing changes

**Phase:** Step 4.5 (Confirm Documentation Changes)

Before writing any documentation changes to disk, the agent presents a summary table of planned changes and waits for user approval.

**Evidence expected:**
```markdown
## Planned Documentation Changes

| File | Change |
|------|--------|
| `src/services/payment.service.ts` | Add JSDoc to `processPayment()`, `getPaymentStatus()` |
| `src/services/payment.service.ts` | Update stale JSDoc on `refundPayment()` |
| `src/services/payment.service.ts` | Add interface docs for `PaymentConfig` |

**Apply these changes?** (yes / edit / cancel)
```

The agent does NOT write changes until the user responds with explicit approval.

### 9. Typecheck passes after JSDoc additions

**Phase:** Step 5 (Verify Documentation)

After applying the documentation changes, the agent runs the project's typecheck command to verify that the JSDoc additions do not introduce type errors (e.g., `@param` types conflicting with TypeScript signatures).

**Evidence expected:**
```bash
npm run typecheck
# Exit code 0 — no errors
```

### 10. Documentation report presented listing what was added/updated

**Phase:** Step 6 (Present Documentation Report)

The agent presents the documentation report using the Output Format defined in the skill, listing every change made: new JSDoc added, stale JSDoc updated, and items deliberately skipped.

**Evidence expected:**
```markdown
## Documentation Report

### Files Updated
- `src/services/payment.service.ts` — Added JSDoc to 2 functions, updated 1, documented 1 interface

### Documentation Added
- `processPayment()` — Function description, @param (3), @returns, @example
- `getPaymentStatus()` — Function description, @param, @returns, @throws PaymentError, @example
- `PaymentConfig` — Interface description, property docs, @example

### Documentation Updated
- `refundPayment()` — Fixed stale @param (orderId → transactionId), updated description

### Skipped
- `_calculateFee()` — Private helper, not part of public API
```

## Anti-Patterns

### 1. Documenting every function including private helpers

**Wrong:** Agent adds JSDoc to `_calculateFee()` along with all exported functions.

Private helpers are internal implementation details. Documenting them adds noise, creates maintenance burden, and violates the skill's scope rule of targeting exported functions, classes, and interfaces. The underscore prefix and lack of `export` keyword are clear signals to skip.

### 2. Adding JSDoc that just restates the function name

**Wrong:** Agent writes `/** Processes a payment. */` for `processPayment()` or `/** Gets the payment status. */` for `getPaymentStatus()`.

This adds no value — the function name already says that. JSDoc should explain the business purpose, side effects, error conditions, and non-obvious behavior that a caller needs to know.

### 3. Skipping the test file and guessing behavior

**Wrong:** Agent reads only the source file and writes JSDoc based on function signatures alone, guessing at edge cases and error conditions.

The test file contains concrete evidence of expected behavior: what inputs produce what outputs, what triggers errors, and what edge cases exist. Skipping it leads to inaccurate or incomplete documentation, especially for `@throws` tags and `@returns` descriptions.

### 4. Not updating stale documentation

**Wrong:** Agent sees that `refundPayment()` already has JSDoc and skips it, even though the `@param orderId` tag does not match the actual parameter name `transactionId`.

Stale documentation is worse than no documentation — it actively misleads developers. The skill explicitly requires updating stale docs when found.

### 5. Not including `@throws` for functions that throw errors

**Wrong:** Agent documents `getPaymentStatus()` with `@param` and `@returns` but omits `@throws {PaymentError}`, even though the function throws on invalid IDs.

The `@throws` tag is essential for callers to know they need error handling. Omitting it means callers may not catch the error, leading to unhandled exceptions in production.

## Known Gaps Addressed

| Gap | Description | Resolution |
|-----|-------------|------------|
| No `@throws` in function template | The JSDoc template for functions included `@param`, `@returns`, and `@example` but not `@throws`, making it easy to forget error documentation | Added `@throws {ErrorType}` to the function JSDoc template in Step 3 |
| No interface/type documentation template | Step 3 had templates for functions, classes, inline comments, and READMEs, but nothing for TypeScript interfaces or type aliases | Added "For Interfaces and Type Aliases" template in Step 3 with description, property-level docs, and `@example` |
| No approval gate | The workflow went straight from writing documentation to verifying it, with no user review step | Added Step 4.5 requiring the agent to present planned changes and wait for explicit user approval |
| No early exit for already-documented code | If all exports already had complete JSDoc, the agent would still go through the full workflow with nothing to do | Added early exit after Step 1: if all exported items have complete, accurate JSDoc, report "Documentation is complete" and exit |
| No test file discovery guidance | Step 2 said "read existing tests" but gave no guidance on where to find them | Added test file discovery patterns: `__tests__/` directory, `.spec.ts`/`.test.ts` suffixes, project root `tests/` directory |
| Output format disconnected from workflow | The Output Format section defined a documentation report template, but no workflow step instructed the agent to use it | Added Step 6 explicitly wiring the Output Format to the end of the workflow |
| Incomplete acceptance tests | The acceptance tests table was missing cases for stale doc updates, interface documentation, private helper skipping, and `--files` flag usage | Added missing acceptance test cases to cover these scenarios |
