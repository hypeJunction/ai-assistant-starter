# Screen Reader Testing Guide

Practical guide for verifying screen reader compatibility during accessibility reviews. Covers testing methodology, platform-specific commands, and what to verify for common UI patterns.

## Testing Methodology

### Before You Start

1. **Identify the target screen readers** — Test with at least one:
   - **NVDA** (Windows, free) — most common screen reader
   - **VoiceOver** (macOS/iOS, built-in) — default for Apple devices
   - **JAWS** (Windows, commercial) — enterprise standard
   - **TalkBack** (Android, built-in) — default for Android
2. **Use the project's target browsers** — Screen reader + browser combos matter:
   - NVDA + Firefox (best support)
   - NVDA + Chrome (common)
   - VoiceOver + Safari (required for macOS/iOS)
   - JAWS + Chrome or Edge (enterprise)
3. **Disable your mouse** — Test keyboard-only interaction to simulate the real experience

### Testing Flow

```
1. Load page → Verify page title announced
2. Navigate headings → Verify hierarchy (h1 → h2 → h3)
3. Tab through interactive elements → Verify each announced with name + role
4. Enter forms → Verify labels, required state, error messages
5. Trigger dynamic content → Verify live region announcements
6. Open/close modals → Verify focus management and announcements
7. Navigate data tables → Verify headers associated with cells
```

## VoiceOver (macOS) Quick Reference

### Essential Commands

| Action | Keys | What to Verify |
|--------|------|----------------|
| Turn on/off | `Cmd + F5` | — |
| Next element | `VO + Right Arrow` | Each element announced with name and role |
| Previous element | `VO + Left Arrow` | — |
| Activate (click) | `VO + Space` | Same as mouse click |
| Read headings | `VO + Cmd + H` | All headings, correct hierarchy |
| Next heading | `VO + Cmd + H` | — |
| Read links | `VO + Cmd + L` | Links have descriptive text |
| Open Rotor | `VO + U` | Navigate by headings, links, landmarks |
| Read all | `VO + A` | Content read in logical order |

`VO` = `Control + Option`

### Form Testing

| Action | Keys | What to Verify |
|--------|------|----------------|
| Next form field | `VO + Cmd + J` | Label announced, type announced |
| Enter form mode | `VO + Shift + Down Arrow` | — |
| Exit form mode | `VO + Shift + Up Arrow` | — |

### What VoiceOver Should Announce

For each element type, verify the announcement includes:

| Element | Expected Announcement |
|---------|----------------------|
| Button | "[label], button" |
| Link | "[text], link" |
| Text input | "[label], edit text" |
| Checkbox | "[label], checkbox, [checked/unchecked]" |
| Radio | "[label], radio button, [selected/not selected], [position] of [total]" |
| Heading | "[text], heading level [N]" |
| Image | "[alt text], image" (or nothing for decorative) |
| Landmark | "[label], [type] landmark" (navigation, main, etc.) |

## NVDA (Windows) Quick Reference

### Essential Commands

| Action | Keys | What to Verify |
|--------|------|----------------|
| Turn on | `Ctrl + Alt + N` | — |
| Stop speech | `Ctrl` | — |
| Next element | `Down Arrow` (browse mode) | Each element announced |
| Previous element | `Up Arrow` | — |
| Activate | `Enter` or `Space` | — |
| List headings | `NVDA + F7` | All headings, correct levels |
| Next heading | `H` | — |
| Next heading level N | `1`–`6` | Specific heading levels |
| Next landmark | `D` | All landmark regions announced |
| Next form field | `F` | All form fields accessible |
| Toggle browse/focus mode | `NVDA + Space` | — |
| Read all | `NVDA + Down Arrow` | Content in logical order |

`NVDA` key = `Insert` (default) or `Caps Lock` (laptop layout)

### Quick Navigation (Browse Mode)

| Key | Element Type |
|-----|-------------|
| `H` | Heading |
| `1`–`6` | Heading level 1–6 |
| `K` | Link |
| `F` | Form field |
| `T` | Table |
| `D` | Landmark |
| `B` | Button |
| `I` | List item |
| `G` | Graphic (image) |

Add `Shift` to go to previous (e.g., `Shift + H` = previous heading).

## What to Test for Common Patterns

### Navigation

- [ ] Landmarks announced: `navigation`, `main`, `banner`, `contentinfo`
- [ ] Skip-to-content link works and moves focus
- [ ] Current page indicated in navigation (`aria-current="page"`)
- [ ] Dropdown menus announce expanded/collapsed state

### Forms

- [ ] Every input has a label announced
- [ ] Required fields announce "required"
- [ ] Error messages announced when they appear (via `aria-live` or `role="alert"`)
- [ ] Error messages associated with their inputs (`aria-describedby`)
- [ ] Fieldset/legend groups related inputs
- [ ] Submit button has clear label

### Modals/Dialogs

- [ ] Focus moves to modal when opened
- [ ] Modal role announced ("dialog")
- [ ] Modal title announced (`aria-labelledby`)
- [ ] Focus trapped inside modal (Tab doesn't leave)
- [ ] Escape closes modal
- [ ] Focus returns to trigger element on close

### Tables

- [ ] Table role announced
- [ ] Caption or `aria-label` describes the table
- [ ] Column and row headers (`<th>`) announced when navigating cells
- [ ] Complex tables have `scope` or `headers` attributes

### Dynamic Content

- [ ] Toast/notification announced without focus change (`role="status"` + `aria-live="polite"`)
- [ ] Urgent alerts announced immediately (`role="alert"` + `aria-live="assertive"`)
- [ ] Loading states announced ("Loading...", then "Content loaded")
- [ ] Search results count announced on update

### Tabs

- [ ] Tab list announced with role and count
- [ ] Selected tab indicated (`aria-selected`)
- [ ] Arrow keys navigate between tabs
- [ ] Tab panel content announced on selection

## Common Screen Reader Issues

| Issue | Symptom | Fix |
|-------|---------|-----|
| Missing label | "Button" or "Edit text" with no name | Add `aria-label` or visible `<label>` |
| Wrong role | Interactive `div` not announced as control | Use semantic HTML or add `role` attribute |
| Broken heading hierarchy | Headings jump from h1 to h4 | Fix heading levels to be sequential |
| Live region not working | Dynamic content update is silent | Add `aria-live` BEFORE content changes (element must exist in DOM first) |
| Focus not managed | Modal opens but screen reader stays on background | Move focus to modal on open, return on close |
| Decorative image read | Screen reader says "image" for icons | Add `alt=""` and `aria-hidden="true"` |
| Duplicate announcements | Label read twice | Remove redundant `aria-label` when visible `<label>` exists |
| Table not navigable | Cells don't announce headers | Use `<th>` with `scope="col"` or `scope="row"` |

## Automated vs Manual Testing

| What | Automated (axe-core, jest-axe) | Manual (screen reader) |
|------|-------------------------------|------------------------|
| Missing alt text | Yes | Yes |
| Missing form labels | Yes | Yes |
| Color contrast | Yes (with caveats) | No |
| Heading hierarchy | Yes | Yes |
| ARIA attribute validity | Yes | No |
| Focus order correctness | No | Yes |
| Live region behavior | No | Yes |
| Keyboard trap detection | No | Yes |
| Meaningful announcements | No | Yes |
| Custom widget usability | No | Yes |
| Reading order vs visual order | No | Yes |

**Rule of thumb:** Automated tools catch ~30-40% of accessibility issues. Manual screen reader testing is required for the rest.
