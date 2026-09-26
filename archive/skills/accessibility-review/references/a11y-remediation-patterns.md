# Accessibility Remediation Patterns

Common fix patterns organized by component type. Each pattern shows the inaccessible code, the fix, and which WCAG criterion it addresses.

## Interactive Elements

### Clickable `div` → Semantic Button

**WCAG:** 2.1.1 Keyboard, 4.1.2 Name/Role/Value

```tsx
// Before: inaccessible
<div className="btn" onClick={handleClick}>Submit</div>

// After: semantic HTML (preferred)
<button className="btn" onClick={handleClick}>Submit</button>

// After: ARIA (when semantic HTML isn't possible)
<div
  role="button"
  tabIndex={0}
  className="btn"
  onClick={handleClick}
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClick();
    }
  }}
>
  Submit
</div>
```

### Icon Button Without Label

**WCAG:** 1.1.1 Non-text Content, 4.1.2 Name/Role/Value

```tsx
// Before: screen reader announces "button" with no label
<button onClick={onClose}><XIcon /></button>

// After: visually hidden label
<button onClick={onClose} aria-label="Close dialog">
  <XIcon aria-hidden="true" />
</button>

// Alternative: visible text with icon
<button onClick={onClose}>
  <XIcon aria-hidden="true" />
  <span className="sr-only">Close dialog</span>
</button>
```

### Toggle Button State

**WCAG:** 4.1.2 Name/Role/Value

```tsx
// Before: state not communicated
<button onClick={toggle}>{isOpen ? 'Hide' : 'Show'} Menu</button>

// After: state communicated via ARIA
<button onClick={toggle} aria-expanded={isOpen}>
  Menu
</button>

// For toggle switches
<button
  role="switch"
  aria-checked={isDarkMode}
  onClick={() => setDarkMode(!isDarkMode)}
>
  Dark mode
</button>
```

## Forms

### Input Without Label

**WCAG:** 1.3.1 Info and Relationships, 3.3.2 Labels or Instructions

```tsx
// Before: placeholder is not a label
<input placeholder="Enter email" />

// After: explicit label
<label htmlFor="email">Email</label>
<input id="email" type="email" placeholder="user@example.com" />

// After: visually hidden label (when design requires no visible label)
<label htmlFor="email" className="sr-only">Email</label>
<input id="email" type="email" placeholder="Enter email" />

// After: aria-label (last resort)
<input type="email" aria-label="Email address" placeholder="Enter email" />
```

### Error Messages Not Associated

**WCAG:** 3.3.1 Error Identification, 1.3.1 Info and Relationships

```tsx
// Before: error exists but not linked to input
<input id="email" type="email" />
<span className="error">Please enter a valid email</span>

// After: error linked via aria-describedby
<input
  id="email"
  type="email"
  aria-invalid={hasError}
  aria-describedby={hasError ? 'email-error' : undefined}
/>
{hasError && (
  <span id="email-error" role="alert">
    Please enter a valid email address
  </span>
)}
```

### Required Field Not Announced

**WCAG:** 3.3.2 Labels or Instructions

```tsx
// Before: visual asterisk only
<label>Email *</label>
<input type="email" />

// After: programmatically required
<label htmlFor="email">
  Email <span aria-hidden="true">*</span>
</label>
<input id="email" type="email" required aria-required="true" />
```

### Radio/Checkbox Group Without Grouping

**WCAG:** 1.3.1 Info and Relationships

```tsx
// Before: ungrouped radios
<label><input type="radio" name="plan" value="free" /> Free</label>
<label><input type="radio" name="plan" value="pro" /> Pro</label>

// After: fieldset with legend
<fieldset>
  <legend>Select a plan</legend>
  <label><input type="radio" name="plan" value="free" /> Free</label>
  <label><input type="radio" name="plan" value="pro" /> Pro</label>
</fieldset>

// Alternative: role="radiogroup"
<div role="radiogroup" aria-labelledby="plan-label">
  <span id="plan-label">Select a plan</span>
  <label><input type="radio" name="plan" value="free" /> Free</label>
  <label><input type="radio" name="plan" value="pro" /> Pro</label>
</div>
```

## Navigation

### Missing Skip Link

**WCAG:** 2.4.1 Bypass Blocks

```tsx
// Add as first child of <body> or root layout
<a href="#main-content" className="skip-link">
  Skip to main content
</a>

<nav aria-label="Main navigation">...</nav>

<main id="main-content">
  {/* Page content */}
</main>
```

```css
.skip-link {
  position: absolute;
  left: -9999px;
  top: auto;
  width: 1px;
  height: 1px;
  overflow: hidden;
}

.skip-link:focus {
  position: fixed;
  top: 10px;
  left: 10px;
  width: auto;
  height: auto;
  padding: 8px 16px;
  background: #000;
  color: #fff;
  z-index: 9999;
  text-decoration: none;
}
```

### Navigation Without Landmark

**WCAG:** 1.3.1 Info and Relationships

```tsx
// Before: div-based navigation
<div className="nav">
  <a href="/">Home</a>
  <a href="/about">About</a>
</div>

// After: semantic nav with label
<nav aria-label="Main navigation">
  <a href="/">Home</a>
  <a href="/about">About</a>
</nav>

// Multiple navs need distinct labels
<nav aria-label="Main navigation">...</nav>
<nav aria-label="Footer navigation">...</nav>
```

### Current Page Not Indicated

**WCAG:** 2.4.4 Link Purpose

```tsx
// Before: active page only styled
<nav>
  <a href="/" className="active">Home</a>
  <a href="/about">About</a>
</nav>

// After: aria-current for screen readers
<nav aria-label="Main navigation">
  <a href="/" aria-current="page">Home</a>
  <a href="/about">About</a>
</nav>
```

## Modals and Dialogs

### Focus Not Managed

**WCAG:** 2.4.3 Focus Order, 2.1.2 No Keyboard Trap

```tsx
// Complete accessible modal pattern
function Modal({ isOpen, onClose, title, children }) {
  const modalRef = useRef(null);
  const triggerRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      // Save trigger and move focus to modal
      triggerRef.current = document.activeElement;
      modalRef.current?.focus();
    } else {
      // Return focus to trigger
      triggerRef.current?.focus();
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      ref={modalRef}
      tabIndex={-1}
    >
      <h2 id="modal-title">{title}</h2>
      {children}
      <button onClick={onClose}>Close</button>
    </div>
  );
}
```

## Dynamic Content

### Toast Without Live Region

**WCAG:** 4.1.3 Status Messages

```tsx
// Before: toast appears but screen reader ignores it
<div className="toast">{message}</div>

// After: live region announces the message
<div role="status" aria-live="polite" className="toast">
  {message}
</div>

// For urgent errors
<div role="alert" aria-live="assertive" className="toast-error">
  {errorMessage}
</div>
```

**Important:** The `aria-live` container must exist in the DOM BEFORE the content changes. If you create the element with the content already inside, the screen reader may not announce it.

```tsx
// Correct: container always rendered, content changes
<div role="status" aria-live="polite">
  {notification && <span>{notification}</span>}
</div>

// Wrong: container created with content
{notification && (
  <div role="status" aria-live="polite">{notification}</div>
)}
```

### Loading State Not Announced

**WCAG:** 4.1.3 Status Messages

```tsx
// Pattern: loading → content transition
<div role="status" aria-live="polite">
  {isLoading ? (
    <span>Loading results...</span>
  ) : (
    <span>{results.length} results found</span>
  )}
</div>

// For a loading spinner
<div role="status" aria-live="polite">
  {isLoading && <span className="sr-only">Loading...</span>}
  <Spinner aria-hidden="true" />
</div>
```

## Images

### Informational Image Without Alt

**WCAG:** 1.1.1 Non-text Content

```tsx
// Informational: describe the content
<img src="chart.png" alt="Revenue grew 40% from Q1 to Q3 2024" />

// Decorative: empty alt
<img src="divider.png" alt="" />

// Complex image: use long description
<figure>
  <img
    src="architecture.png"
    alt="System architecture diagram"
    aria-describedby="arch-desc"
  />
  <figcaption id="arch-desc">
    The system consists of three layers: a React frontend communicating
    via REST API to a Node.js backend, which connects to a PostgreSQL database.
  </figcaption>
</figure>
```

### SVG Without Accessible Name

**WCAG:** 1.1.1 Non-text Content

```tsx
// Informational SVG
<svg role="img" aria-label="Warning icon">
  <title>Warning icon</title>
  <path d="..." />
</svg>

// Decorative SVG
<svg aria-hidden="true" focusable="false">
  <path d="..." />
</svg>
```

## Color and Contrast

### Color as Only Indicator

**WCAG:** 1.4.1 Use of Color

```tsx
// Before: error shown only with red border
<input className={hasError ? 'border-red' : ''} />

// After: icon + text + color
<div>
  <input
    className={hasError ? 'border-red' : ''}
    aria-invalid={hasError}
    aria-describedby={hasError ? 'name-error' : undefined}
  />
  {hasError && (
    <span id="name-error" className="error">
      <ErrorIcon aria-hidden="true" /> Name is required
    </span>
  )}
</div>
```

## Visually Hidden Text Utility

Used throughout many patterns above:

```css
/* Screen-reader only text */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}
```

## Fix Priority Guide

When multiple issues are found, fix in this order:

| Priority | Issue Type | Impact |
|----------|-----------|--------|
| 1 | Keyboard access blocked | Users cannot complete tasks at all |
| 2 | Missing form labels | Screen reader users cannot fill forms |
| 3 | Missing image alt text | Informational images invisible to screen readers |
| 4 | Focus management (modals) | Disorienting, may trap keyboard users |
| 5 | ARIA roles on custom widgets | Custom components invisible to assistive tech |
| 6 | Live region announcements | Dynamic updates missed by screen readers |
| 7 | Heading hierarchy | Navigation and comprehension impaired |
| 8 | Color contrast | Content difficult to read for low-vision users |
| 9 | Skip links | Repeated content annoying but not blocking |
| 10 | Motion preferences | Comfort issue for vestibular disorders |
