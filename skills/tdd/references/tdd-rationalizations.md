# TDD Rationalizations

Extended reference for recognizing and resisting rationalizations that break the TDD cycle. This supplements the "Common Rationalizations" table in the main SKILL.md with deeper analysis and real-world scenarios.

## The Rationalization Pattern

Rationalizations follow a predictable structure:

```
Pressure (deadline, complexity, frustration)
  → Rationalization ("I don't need a test for this")
    → Violation (write production code first)
      → Consequence (untested code, hidden bugs, lost TDD guarantees)
```

The key insight: **the rationalization always sounds reasonable in the moment**. That's what makes it dangerous. The rebuttal must be memorized, not reasoned through on the spot.

## Rationalizations by Category

### "Too Simple to Test"

**The claim:** "This code is so simple it can't be wrong."

**Why it's wrong:**
- Simple code is called by complex code. The interaction can be wrong.
- "Simple" code gets modified later. Without a test, the modification is unguarded.
- If it's truly simple, the test takes 30 seconds. The cost of testing is negligible.
- The majority of production bugs are in "obvious" code that nobody tested.

**Real scenario:** A one-line utility `formatCurrency(amount)` is "too simple." Later, someone passes a negative number and it returns `$-5.00` instead of `-$5.00`. Without a test, nobody catches it until a user reports it.

**What to do:** Write the test. It takes 30 seconds. Move on.

### "I'll Write the Test After"

**The claim:** "Let me get the implementation working first, then I'll add tests."

**Why it's wrong:**
- Tests written after implementation verify what the code IS, not what it SHOULD BE
- You can't verify the test catches bugs — the code already passes
- "After" rarely comes — there's always the next feature to build
- The test becomes a copy of the implementation instead of a specification

**Real scenario:** You implement a cache with TTL. You write the test after. The test checks that the cache returns cached values. But you never test that expired values are evicted — because the implementation already "works" and you wrote the test to match.

**What to do:** Delete the implementation. Write the test. Watch it fail. Rewrite the implementation.

### "TDD Doesn't Work for This Type of Code"

**The claim:** "This is UI/integration/infrastructure code — TDD doesn't apply."

**Why it's wrong:**
- TDD works for any code with observable behavior
- If the code has no observable behavior, why are you writing it?
- The difficulty of testing is a signal about the design, not a limitation of TDD
- UI has behavior (renders, responds to events). Integration has contracts. Infrastructure has configuration.

**Exceptions that are actually valid:**
- Exploratory prototyping (use `/explore`, then delete and TDD)
- Purely declarative config files with no logic
- Generated code that isn't manually edited

**What to do:** Identify the behavior. Write a test for it. If you can't identify testable behavior, question whether the code is needed.

### "This Requires Seeing the Implementation First"

**The claim:** "I can't write a test without knowing how the code works."

**Why it's wrong:**
- You don't need to know HOW — you need to know WHAT
- The test is the FIRST client of your API — write what you want to call
- "I need to see it first" usually means "I haven't thought through the requirements"
- Starting with the test forces you to design the interface before the implementation

**What to do:** Describe the behavior in plain English. Turn that sentence into a test. The test IS the specification.

```
English: "When a user submits an invalid email, they should see an error message"
Test: expect(validateEmail('not-an-email')).toEqual({ valid: false, error: 'Invalid email format' })
```

### "Mocking is Too Painful"

**The claim:** "I'd have to mock 5 dependencies to test this. It's not worth it."

**Why it's wrong:**
- Painful mocking means painful design — too many dependencies
- The difficulty is the signal, not the problem
- Fix the design: extract an interface, inject dependencies, split the unit
- If you can't test it without mocking everything, users can't use it without everything either

**What to do:** Refactor the code to have fewer dependencies. Extract pure logic from I/O. Use dependency injection. Then the test becomes easy — and the code becomes better.

### "We're Under Deadline Pressure"

**The claim:** "We don't have time for TDD right now."

**Why it's wrong:**
- TDD is faster for any code that will be maintained (which is all code)
- The time "saved" by skipping tests is spent debugging later — at 3-10x the cost
- Deadline pressure is exactly when you need the safety net most
- Bugs found in production cost 10-100x more to fix than bugs caught by tests

**What to do:** TDD. The cycle is fast (2-5 minutes per RED-GREEN-REFACTOR). The debugging sessions you avoid are what save time.

### "The Existing Code Has No Tests"

**The claim:** "There are no tests for this module anyway, so adding one won't help."

**Why it's wrong:**
- Every tested line is one less future debugging session
- You don't need 100% coverage to get value — one test is infinitely better than zero
- New behavior should be tested regardless of legacy coverage
- You're not responsible for the past, but you are responsible for what you write now

**What to do:** Write a test for YOUR new code. Don't worry about the untested legacy code — that's a separate task for `/test-coverage`.

## Red Flags During TDD

These signals mean you've broken the cycle. Stop and correct before continuing.

| Red Flag | What Happened | Correction |
|----------|--------------|-----------|
| Test passes on first run | Test doesn't test new behavior | Rewrite the test or verify it's actually testing the right thing |
| You wrote production code before the test | TDD violation | Delete the code. Write the test. Rewrite the code. |
| You're not sure why the test fails | Don't understand the system | Read the code. Use `/explore`. Come back when you understand. |
| You added "one more thing" during GREEN | Scope creep in GREEN phase | Revert to last green. Write a test for the extra thing. |
| Mocking more than 2 dependencies | Code has too many collaborators | Refactor to reduce dependencies before continuing |
| Test name describes implementation | Testing HOW, not WHAT | Rename: "should call database" → "should return user by email" |
| Multiple tests failing at once | Jumped ahead | Revert to last green. One failing test at a time. |
| Complex setup (>15 lines of arrange) | Code needs a simpler interface | Extract a builder/factory, or redesign the interface |

## When TDD Genuinely Doesn't Apply

Be honest about these — but also honest that they're rare:

- **Exploratory spikes** — Write throwaway code to learn. Then delete it and TDD the real implementation.
- **Pure configuration** — YAML/JSON files with no conditional logic.
- **Generated code** — Code produced by tools (protobuf, OpenAPI) that you don't manually edit.
- **One-off scripts** — Truly disposable automation that runs once and is deleted.

Everything else benefits from TDD.
