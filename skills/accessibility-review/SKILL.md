---
name: accessibility-review
description: Systematic WCAG 2.1 AA accessibility audit with confidence-based reporting. Scans UI components for keyboard, screen reader, and visual accessibility issues. Use for pre-release audits or after major UI changes.
---

# Accessibility Review

> **Purpose:** Systematic accessibility audit against WCAG 2.1 AA
> **Mode:** Read-only by default — fixes require approval
> **Usage:** `/accessibility-review [scope flags] [component or page]`

## Iron Laws

1. **ACCESSIBILITY IS NOT OPTIONAL** — Every interactive element must be keyboard accessible. Every image must have alt text. Every form must have labels. No exceptions, no "we'll add it later."
2. **TEST WITH REAL TOOLS** — Do not guess at accessibility. Run axe-core, test with keyboard navigation, verify screen reader announcements. Assumptions are not evidence.
3. **SEVERITY REFLECTS USER IMPACT** — A missing skip link is not the same as a completely inaccessible form. Prioritize by how many users are blocked and how severely.

## Constraints

- **Confidence-based reporting** — HIGH: report, MEDIUM: flag as needs verification, LOW: do not report
- **Don't invent issues** — If nothing found, say "clean review" (this is a valid outcome)
- **Research the entire codebase** before reporting — check for shared components, theme providers, layout wrappers
- **No framework FUD** — Don't flag things the framework already handles (e.g., Next.js `<Image>` requires alt, React Native accessibility props)
- **Evidence required** — Every finding must include the specific code AND explain which users are affected

> **Note:** Command examples use `npm` as default. Adapt to the project's package manager per `ai-assistant-protocol` — Project Commands.

## When to Use

- UI component review (new or modified)
- Pre-release accessibility audit
- After major UI changes or redesigns
- New page or feature with interactive elements
- WCAG compliance check before launch

## When NOT to Use

- Non-visual code (APIs, CLI tools, backend services)
- Purely design review (colors, spacing) — ask designer
- Performance audit — use `/validate`
- Security review — use `/security-review`

## Scope Flags

| Flag | Description |
|------|-------------|
| `--files=<paths>` | Review specific files or directories |
| `--wcag-level=<A\|AA\|AAA>` | Target conformance level (default: AA) |
| `--component=<name>` | Review a specific component and its variants |
| (none) | Review all UI files (will ask to confirm scope) |

## Confidence Levels

| Level | Criteria | Action |
|-------|----------|--------|
| **HIGH** | Confirmed violation + code evidence + no mitigation found | Report as finding |
| **MEDIUM** | Possible violation but shared component may handle it, or runtime behavior unclear | Report as "needs verification" |
| **LOW** | Theoretical concern, framework-mitigated, or requires unlikely conditions | Do not report |

## Do Not Flag

Skip these — they produce noise, not signal:

- Test files and test fixtures
- Storybook decorator wrappers (review the stories themselves, not decorators)
- Server-only code with no rendered output
- Components that are never rendered directly (abstract base components)
- Framework-provided components with built-in accessibility (e.g., Radix UI, Headless UI)
- Decorative images that already have `alt=""`

## Workflow

### Phase 1: Scope

Identify what to review:

```bash
# Find UI files
find . -type f \( -name "*.tsx" -o -name "*.jsx" -o -name "*.vue" -o -name "*.svelte" \) | head -100

# If --files flag, scope to those paths
# If --component flag, find that component and its usage
```

1. **Categorize UI files** — Pages, layouts, components, modals, forms
2. **Check for existing a11y setup:**
   - Testing: `jest-axe`, `@axe-core/playwright`, `@axe-core/react`
   - Linting: `eslint-plugin-jsx-a11y`, `eslint-plugin-vuejs-accessibility`
   - Component library: Does it have built-in a11y? (Radix, Headless UI, Ark UI)
3. **Note the UI framework** — React, Vue, Svelte, Angular, etc.
4. **Identify WCAG level** — A, AA (default), or AAA

If scope is large (>30 components), present categories and ask user which to focus on.

### Phase 2: Automated Scan

Review code for common violations (see `references/wcag-checklist.md`):

**Critical checks (P0 candidates):**
- Interactive elements not reachable by keyboard (`div` with `onClick` but no `role`/`tabIndex`)
- Form inputs without associated labels (`<label>` or `aria-label`/`aria-labelledby`)
- Images without `alt` attributes
- Missing `lang` attribute on `<html>`

**High-priority checks (P1 candidates):**
- Color contrast issues (if theme tokens or CSS variables are available)
- Missing document/page `<title>`
- Heading hierarchy violations (skipping levels, multiple `<h1>`)
- ARIA roles used incorrectly (e.g., `role="button"` without keyboard handler)
- Missing `aria-live` regions for dynamic content updates

**Medium-priority checks (P2 candidates):**
- Missing skip-to-content link in layouts
- Focus order that doesn't match visual order
- Missing focus styles (`:focus-visible` or `:focus`)
- Modals/dropdowns without Escape key dismissal

**Enhancement checks (P3 candidates):**
- `prefers-reduced-motion` not respected for animations
- Decorative images using descriptive alt instead of `alt=""`
- ARIA attributes that could be simplified with semantic HTML
- Missing `autocomplete` on form fields

If a11y testing tools are configured, suggest running them:

```bash
# If jest-axe is available
npm run test -- --grep "a11y\|accessibility\|axe"

# If Playwright with axe is available
npx playwright test --grep "a11y"

# If eslint-plugin-jsx-a11y is configured
npx eslint --rule '{"jsx-a11y/*": "error"}' src/
```

### Phase 3: Manual Review

#### Keyboard Navigation Checklist

- [ ] Can every interactive element be reached with Tab?
- [ ] Is focus order logical (matches visual reading order)?
- [ ] Are focus styles visible on all interactive elements?
- [ ] Can modals and dropdowns be dismissed with Escape?
- [ ] Is there a skip-to-content link on pages with navigation?
- [ ] Do custom widgets support expected keyboard patterns? (Arrow keys for tabs, Space/Enter for buttons)
- [ ] Is there no keyboard trap? (Focus can always move away from any element)

#### Screen Reader Checklist

- [ ] Are headings used hierarchically (h1 > h2 > h3, no skipped levels)?
- [ ] Do informational images have descriptive `alt` text?
- [ ] Do decorative images have empty `alt=""` (or `role="presentation"`)?
- [ ] Are ARIA labels meaningful and non-redundant?
- [ ] Do dynamic updates use `aria-live` regions (polite for non-urgent, assertive for urgent)?
- [ ] Are error messages associated with their inputs (`aria-describedby` or `aria-errormessage`)?
- [ ] Do interactive elements have accessible names?
- [ ] Are form groups labeled with `<fieldset>`/`<legend>` or `role="group"` with `aria-labelledby`?

#### Motion and Visual Checklist

- [ ] Is `prefers-reduced-motion` media query respected?
- [ ] Do animations have pause/stop controls (or are under 5 seconds)?
- [ ] Is content readable at 200% zoom without horizontal scrolling?
- [ ] Does the layout reflow at 320px width without horizontal scroll?
- [ ] Is color never the only means of conveying information?
- [ ] Does text contrast meet minimum ratios (4.5:1 normal, 3:1 large text)?
- [ ] Do UI component boundaries meet 3:1 contrast against adjacent colors?

### Phase 4: Report

Use P0-P3 severity levels:

| Severity | Definition | Examples |
|----------|-----------|----------|
| **P0 Critical** | Users cannot complete a task at all | No keyboard access to submit button, form with no labels, interactive `div` with no role |
| **P1 High** | Significant barrier for assistive tech users | Poor color contrast on body text, missing alt on informational images, heading hierarchy broken |
| **P2 Medium** | Usability degradation but workaround exists | Missing skip link, focus order quirks, no `aria-live` on toast notifications |
| **P3 Low** | Enhancement opportunity | Decorative image could use `alt=""`, ARIA could be simplified, autocomplete missing |

#### Report Format

```markdown
## Accessibility Review: [scope description]

### Scope
- **Files reviewed:** [count]
- **WCAG level:** [A / AA / AAA]
- **UI framework:** [React / Vue / Svelte / etc.]
- **Existing a11y tooling:** [jest-axe, eslint-plugin-jsx-a11y, etc. or "None detected"]

### HIGH Confidence Findings

#### Finding 1: [WCAG Criterion] — [Issue Summary]
- **Severity:** P0 Critical / P1 High
- **WCAG:** [criterion number and name]
- **Location:** `file.tsx:line`
- **Affected code:**
  ```tsx
  [the actual code]
  ```
- **User impact:** [Who is affected and how — keyboard users, screen reader users, etc.]
- **Evidence:** [Why no mitigation exists — what was checked]
- **Recommended fix:**
  ```tsx
  [specific code fix]
  ```

_(Repeat for each HIGH finding, or "No HIGH confidence findings.")_

### MEDIUM Confidence — Needs Verification

These may be real issues but require runtime or manual testing to confirm:

1. **[WCAG Criterion]** — `file.tsx:line` — [Why uncertain: "Contrast depends on runtime theme" / "Shared layout may provide skip link"]

_(Or "None.")_

### Summary Table

| # | Severity | WCAG | Issue | Location | Confidence |
|---|----------|------|-------|----------|------------|
| 1 | P0 | 2.1.1 | No keyboard access on dropdown | `Menu.tsx:42` | HIGH |
| 2 | P1 | 1.1.1 | Missing alt text | `Hero.tsx:15` | HIGH |

### Pre-Conclusion Audit

| Item | Status |
|------|--------|
| Files in scope reviewed | X / Y |
| Keyboard navigation checked | Yes / No |
| Screen reader semantics checked | Yes / No |
| Color and contrast checked | Yes / No |
| WCAG criteria covered | X / [total for level] |
| Shared components checked for mitigations | Yes / No |

### Conclusion

[Overall accessibility posture assessment]

---
**Recommendation:** [Compliant / Needs P0-P1 fixes before release / Needs deeper audit with assistive technology]
```

#### Clean Review Template

When no issues are found:

```markdown
## Accessibility Review: [scope]

**Files reviewed:** [count]
**WCAG level:** AA
**Criteria checked:** [count]
**Findings:** None

No accessibility violations found at HIGH or MEDIUM confidence.
This does not guarantee full WCAG compliance — it means static code analysis
did not identify issues in the reviewed scope. Manual testing with assistive
technology is recommended for full conformance verification.
```

### Phase 5: Fix (Optional, With Approval)

After presenting the report:

1. **Offer to fix P0/P1 issues** — "I found [N] critical/high issues. Want me to fix them?"
2. **GATE: User must approve before any changes** — Do not modify files without explicit approval
3. **Fix in priority order** — P0 first, then P1
4. **Add a11y tests for fixed issues** — If jest-axe or similar is available, add regression tests
5. **Run verification** — Confirm fixes don't break existing tests

## Quick Reference

| Task | Command |
|------|---------|
| Review specific files | `/accessibility-review --files=src/components/Modal.tsx` |
| Review a component | `/accessibility-review --component=LoginForm` |
| AAA conformance check | `/accessibility-review --wcag-level=AAA` |
| Full project audit | `/accessibility-review` |
