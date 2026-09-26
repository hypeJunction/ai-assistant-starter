# Accessibility Review Skill Verification

## Scenario

A developer has built a settings page with the following components:

| Component | Description | Accessibility Issue |
|-----------|-------------|---------------------|
| Custom dropdown | `<div>`-based dropdown for selecting a theme preference, no ARIA roles, no keyboard handling | Missing ARIA roles and keyboard navigation |
| Profile images | Two `<img>` elements with `alt="image"` | Non-descriptive alt text |
| Modal dialog | Settings confirmation modal that opens but does not trap focus, focus escapes to background elements | Missing focus trap |
| Heading hierarchy | `<h1>` for page title, `<h2>` for sections, `<h3>` for subsections | Correct — no issues |

The developer invokes `/accessibility-review --files=src/pages/Settings.tsx,src/components/ThemeDropdown.tsx,src/components/SettingsModal.tsx`.

### File Details

**`src/pages/Settings.tsx`**
```tsx
<main>
  <h1>Settings</h1>
  <section>
    <h2>Profile</h2>
    <img src="/avatar.png" alt="image" />
    <h3>Display Name</h3>
    <input id="name" />
    <label htmlFor="name">Name</label>
  </section>
  <section>
    <h2>Preferences</h2>
    <img src="/theme-preview.png" alt="image" />
    <ThemeDropdown />
  </section>
  <SettingsModal />
</main>
```

**`src/components/ThemeDropdown.tsx`**
```tsx
<div className="dropdown" onClick={toggleOpen}>
  <div className="dropdown-trigger">{selected}</div>
  {isOpen && (
    <div className="dropdown-menu">
      {options.map(opt => (
        <div key={opt} className="dropdown-item" onClick={() => select(opt)}>
          {opt}
        </div>
      ))}
    </div>
  )}
</div>
```

**`src/components/SettingsModal.tsx`**
```tsx
{isOpen && (
  <div className="modal-overlay">
    <div className="modal">
      <h2>Confirm Changes</h2>
      <p>Save your settings?</p>
      <button onClick={onConfirm}>Save</button>
      <button onClick={onClose}>Cancel</button>
    </div>
  </div>
)}
```

## Expected Outcome

The agent identifies all three accessibility violations (custom dropdown missing ARIA, non-descriptive alt text, modal focus trap), acknowledges the correct heading hierarchy as a positive finding, and produces a WCAG-organized report with severity levels and specific remediation code for each issue. The report also includes layout-level observations (focus order across the page, absence or presence of skip links, landmark regions) and recommends automated tooling.

## Key Checkpoints

### Checkpoint 1: Agent identifies the scope (settings page components)

**Phase:** Phase 1 (Scope)

The agent identifies the three files in scope, categorizes them (page, component, modal), and notes the UI framework (React/JSX). The agent checks for existing a11y tooling (eslint-plugin-jsx-a11y, jest-axe, axe-core) and accessible component libraries (Radix, Headless UI, etc.).

**Evidence expected:**
```
Scope:
- src/pages/Settings.tsx — Page (layout with sections, images, form input)
- src/components/ThemeDropdown.tsx — Component (custom interactive widget)
- src/components/SettingsModal.tsx — Component (modal dialog)

UI Framework: React
Existing a11y tooling: [detected or "None detected"]
Accessible component libraries: [detected or "None detected"]
WCAG level: AA (default)
```

### Checkpoint 2: Agent checks at both component level AND layout level

**Phase:** Phase 2 (Automated Scan) / Phase 3 (Manual Review)

The agent reviews not only individual components (dropdown ARIA, image alt, modal focus) but also layout-level concerns: focus order across the settings page, presence of skip-to-content link, landmark regions (`<main>`, `<nav>`), and heading hierarchy spanning the entire page.

**Evidence expected:**

The agent mentions or checks:
- Focus order across the full settings page (not just within individual components)
- Skip-to-content link presence in the layout
- Landmark regions (`<main>` is present, check for `<nav>` or other landmarks)
- Heading hierarchy across the page (h1 > h2 > h3 sequence)
- Modal focus management in context of the page (where focus goes when modal opens/closes)

### Checkpoint 3: Agent detects missing ARIA on custom dropdown (WCAG 4.1.2)

**Phase:** Phase 2 (Automated Scan)

The agent identifies that `ThemeDropdown.tsx` uses `<div>` elements with `onClick` handlers but lacks `role`, `aria-expanded`, `aria-haspopup`, `tabIndex`, and keyboard event handlers. This is flagged as P0 Critical because the dropdown is completely inaccessible to keyboard and screen reader users.

**Evidence expected:**
```
Finding: WCAG 4.1.2 Name, Role, Value — Custom dropdown missing ARIA roles and keyboard support
- Severity: P0 Critical
- Location: src/components/ThemeDropdown.tsx
- Issue: div-based dropdown has no role="listbox"/"combobox", no aria-expanded,
  no tabIndex, no keyboard handlers (Enter/Space to open, Arrow keys to navigate, Escape to close)
- User impact: Keyboard users cannot operate the dropdown. Screen reader users
  do not know it is an interactive control.
- Recommended fix: [specific code with role, aria-expanded, tabIndex, onKeyDown]
```

### Checkpoint 4: Agent detects non-descriptive alt text "image" (WCAG 1.1.1)

**Phase:** Phase 2 (Automated Scan)

The agent identifies both `<img>` elements in `Settings.tsx` with `alt="image"` and flags them as having non-descriptive alt text. The alt text "image" does not convey the content or purpose of the images.

**Evidence expected:**
```
Finding: WCAG 1.1.1 Non-text Content — Non-descriptive alt text
- Severity: P1 High
- Location: src/pages/Settings.tsx (both img elements)
- Issue: alt="image" is generic and does not describe the content or purpose.
  Screen reader users hear "image, image" which provides no useful information.
- Recommended fix: Use descriptive alt text that conveys the image's purpose,
  e.g., alt="User profile avatar" and alt="Preview of selected theme"
```

### Checkpoint 5: Agent detects modal focus trap issue (WCAG 2.4.3)

**Phase:** Phase 2 (Automated Scan) / Phase 3 (Manual Review)

The agent identifies that `SettingsModal.tsx` lacks focus management: no `role="dialog"`, no `aria-modal="true"`, no focus trap implementation, no Escape key handler, and no focus restoration to the trigger element on close.

**Evidence expected:**
```
Finding: WCAG 2.4.3 Focus Order / 2.1.2 No Keyboard Trap — Modal missing focus management
- Severity: P0 Critical
- Location: src/components/SettingsModal.tsx
- Issue: Modal opens without moving focus into it, has no focus trap (Tab escapes
  to background), no role="dialog", no aria-modal="true", no Escape key to close,
  no focus restoration on close.
- User impact: Keyboard users can Tab into background elements while modal is open.
  Screen reader users are not informed a dialog has opened.
- Recommended fix: [specific code with role="dialog", aria-modal, focus trap, Escape handler]
```

### Checkpoint 6: Agent acknowledges correct heading hierarchy (positive finding)

**Phase:** Phase 3 (Manual Review)

The agent notes that the heading hierarchy (h1 > h2 > h3) is correct and does not flag it as an issue. This is mentioned in the report as a positive finding or in the summary as a checked item that passed.

**Evidence expected:**

The report includes a positive note such as:
```
Heading hierarchy: Correct (h1 "Settings" > h2 "Profile"/"Preferences" > h3 "Display Name")
No heading levels skipped.
```

Or in the Pre-Conclusion Audit:
```
| Heading hierarchy | PASS — correct h1 > h2 > h3 sequence |
```

### Checkpoint 7: Agent checks for keyboard navigation on interactive elements

**Phase:** Phase 3 (Manual Review)

The agent explicitly checks keyboard navigation for all interactive elements: the custom dropdown (no keyboard support), the form input (native, should work), the modal buttons (native, should work but focus trap is missing), and notes which elements fail keyboard access.

**Evidence expected:**

The agent mentions keyboard navigation testing and identifies:
- ThemeDropdown: No keyboard support (cannot Tab to it, no Enter/Space/Arrow key handlers)
- Form input: Native element, keyboard accessible
- Modal buttons: Native buttons but unreachable via keyboard if focus is not trapped in modal

### Checkpoint 8: Agent checks if accessible component libraries are being misused

**Phase:** Phase 1 (Scope) / Phase 2 (Automated Scan)

The agent checks whether the project uses accessible component libraries (Radix, Headless UI, Reach UI, Ark UI) and if so, verifies that ARIA attributes and keyboard handlers have not been overridden or removed. In this scenario, no such library is detected, so the agent notes the absence and moves on.

**Evidence expected:**

One of:
```
Accessible component libraries: None detected.
Note: The custom dropdown in ThemeDropdown.tsx would benefit from using an
accessible component library (Radix UI Select, Headless UI Listbox, etc.)
that provides ARIA and keyboard support by default.
```

Or if a library IS detected:
```
Accessible component libraries: Radix UI detected.
Checking for ARIA overrides or removed keyboard handlers...
```

### Checkpoint 9: Agent recommends specific tooling (axe-core, eslint-plugin-jsx-a11y)

**Phase:** Phase 2 (Automated Scan) / Phase 4 (Report)

The agent recommends automated accessibility testing tools appropriate to the project's stack (React). The recommendations include eslint-plugin-jsx-a11y for static analysis, axe-core for runtime testing, and Lighthouse for audit. The agent notes that automated tools catch approximately 30-40% of issues and manual review is still essential.

**Evidence expected:**

The report includes a recommendation section such as:
```
Recommended tooling:
- eslint-plugin-jsx-a11y — Static analysis for React accessibility (catches missing alt, missing labels, invalid ARIA)
- axe-core / @axe-core/react — Runtime accessibility testing (overlay in development)
- Lighthouse accessibility audit — Chrome DevTools audit for deployed pages

Note: Automated tools catch ~30-40% of accessibility issues.
Manual review and screen reader testing are still essential for full coverage.
```

Installation commands use the project's detected package manager (not hardcoded to npm).

### Checkpoint 10: Agent generates WCAG-organized report with severity and remediation

**Phase:** Phase 4 (Report)

The agent produces a report following the skill's report format: scope summary, HIGH confidence findings organized by WCAG criterion with severity/location/code/impact/fix, MEDIUM confidence items, summary table, and pre-conclusion audit checklist.

**Evidence expected:**

The report follows the template in SKILL.md Phase 4 and includes:
- Scope section (files, WCAG level, framework, existing tooling)
- HIGH Confidence Findings with at least 3 findings (dropdown, alt text, modal)
- Each finding has: Severity, WCAG criterion, Location, Affected code, User impact, Evidence, Recommended fix
- Summary Table with all findings
- Pre-Conclusion Audit checklist
- Conclusion with overall recommendation

## Anti-Patterns

### 1. Only check individual components, skip layout-level concerns

**Wrong:** Agent reviews ThemeDropdown.tsx for ARIA, SettingsModal.tsx for focus, images for alt text, but never checks layout-level concerns like focus order across the page, skip-to-content links, or landmark regions.

Accessibility issues often exist at the layout level (missing skip links, broken focus order between components, missing landmark regions). The review must cover both component-level and layout-level concerns.

### 2. Accept `alt="image"` as valid alt text

**Wrong:** Agent sees `alt="image"` and moves on because the alt attribute is technically present.

The alt attribute being present is not sufficient. The value "image" is non-descriptive and fails WCAG 1.1.1 because it does not convey the content or purpose of the image. Screen reader users hear "image, image" which is meaningless. Generic values like "image", "photo", "icon", or the filename must be flagged.

### 3. Miss custom widget ARIA requirements

**Wrong:** Agent checks for missing alt text and missing form labels but does not flag the div-based dropdown as inaccessible.

Custom interactive widgets built with non-semantic elements (`<div>`, `<span>`) require ARIA roles, states, properties, and keyboard event handlers per WCAG 4.1.2. A div-based dropdown without `role`, `aria-expanded`, `tabIndex`, and keyboard handlers is completely invisible to assistive technology.

### 4. Skip keyboard navigation testing suggestions

**Wrong:** Agent focuses only on ARIA attributes and alt text but never mentions keyboard navigation testing or checks whether interactive elements can be operated via keyboard.

Keyboard accessibility (WCAG 2.1.1) is a Level A requirement. Every interactive element must be operable via keyboard. The review must include keyboard navigation checks and note which elements fail.

### 5. Hardcode `npm` for tooling installation

**Wrong:** Agent recommends `npm install eslint-plugin-jsx-a11y` without considering the project's package manager.

The project may use pnpm, yarn, or bun. The agent should detect the package manager from the lockfile (pnpm-lock.yaml, yarn.lock, bun.lockb, package-lock.json) and use the appropriate install command, or note that the command should be adapted.

## Known Gaps Addressed

| Gap | Description | Resolution |
|-----|-------------|------------|
| No layout-level scope guidance | The skill only guided review at the component level, missing page-wide concerns like focus order, skip links, and landmark regions | Added two-level review guidance: component level (ARIA, labels, contrast) AND layout level (focus order, skip navigation, landmarks, heading hierarchy across the page, modal focus management) |
| No accessible library misuse detection | The skill's "Do Not Flag" section mentioned Radix/Headless UI but never checked if those libraries were being misused (ARIA overrides, removed keyboard handlers) | Added check for accessible library misuse: verify ARIA attributes not overridden, keyboard handlers not replaced. Libraries provide accessibility by default — misuse is worse than not using them |
| No tooling recommendations | The skill referenced axe-core and eslint-plugin-jsx-a11y in commands but never explicitly recommended adding them if absent | Added tooling recommendations section: eslint-plugin-jsx-a11y (React), axe-core (runtime), Lighthouse (audit), with note that automated tools catch ~30-40% of issues |
| Non-descriptive alt text not in inline checks | The wcag-checklist.md reference mentioned `alt="image"` as a violation, but the main SKILL.md inline checks only looked for missing alt attributes, not non-descriptive values | Added non-descriptive alt text to inline checks: "Images have descriptive alt text (not generic like 'image', 'photo', 'icon', or the filename)" |
| Package manager hardcoded as npm | Command examples used `npm` without detecting the project's actual package manager | Replaced hardcoded npm with detection guidance: check lockfile (pnpm-lock.yaml, yarn.lock, bun.lockb, package-lock.json) and use the corresponding package manager |
