---
name: code-review-guidelines
description: Code review best practices including review checklist, comment types, severity levels, feedback patterns, and PR size guidelines. Auto-loaded during code review.
user-invocable: false
---

# Code Review Guidelines

## Core Principles

1. **Be constructive** — Focus on improvement, not criticism
2. **Be specific** — Point to exact lines, suggest alternatives
3. **Be thorough** — Check functionality, readability, security
4. **Be collaborative** — Discussion, not gatekeeping

## Review Checklist

### Functionality
- Does the code do what it's supposed to do?
- Are edge cases handled?
- Are error conditions handled gracefully?
- Does it break existing functionality?

### Code Quality
- Is the code readable and self-documenting?
- Are names descriptive?
- Is there unnecessary duplication?
- Does it follow project patterns?

### Security
- Is user input validated?
- Any SQL injection / XSS vulnerabilities?
- Are secrets properly handled?
- Are permissions checked?

### Testing
- Sufficient test coverage?
- Tests cover edge cases?
- Tests are readable and maintainable?

### Performance
- Any obvious performance issues?
- Efficient database queries?
- Memory leaks?

## Comment Labels

| Label | Meaning | Blocks PR? |
|-------|---------|------------|
| `[blocking]` | Must address before merge | Yes |
| `[suggestion]` | Recommended improvement | No |
| `[nit]` | Minor style issue | No |
| `[question]` | Seeking clarification | No |
| `[praise]` | Positive feedback | No |

## Giving Feedback

**Be specific:**
```markdown
**[suggestion]** The variable `d` on line 45 is unclear. Consider
renaming to `dateOfBirth` to indicate what date this represents.
```

**Explain why:**
```markdown
**[blocking]** Using `any` here defeats type safety. This function
receives user input, so we need proper types.
```

**Suggest alternatives:**
```markdown
**[suggestion]** This loop is O(n²). Consider using a Map for O(n).
```

**Give praise:**
```markdown
**[praise]** Great implementation of retry logic with exponential backoff.
```

## PR Size Guidelines

| Lines Changed | Assessment |
|--------------|------------|
| < 100 | Excellent |
| 100-400 | Good |
| 400-800 | Consider splitting |
| > 800 | Should split |

## Anti-Patterns to Avoid

- **Rubber-stamping** — Approving without reading
- **Nitpicking** — Blocking on minor style issues
- **Bikeshedding** — Debating trivial naming choices
- **Personal attacks** — Criticizing the person, not the code
