# WCAG 2.1 AA Checklist

Reference checklist organized by WCAG principle. For each criterion: what to check, common violations, and fix pattern.

## 1. Perceivable

Information and UI components must be presentable in ways users can perceive.

### 1.1.1 Non-text Content (Level A)

- **What to check:** All `<img>`, `<svg>`, `<canvas>`, `<video>`, `<audio>` elements and CSS background images that convey information
- **Common violations:**
  - `<img>` without `alt` attribute
  - `<img alt="image">` or `<img alt="photo.jpg">` (non-descriptive)
  - Icon buttons without accessible names
  - SVG without `<title>` or `aria-label`
  - Form inputs without labels
- **Fix pattern:**
  ```tsx
  // Informational image
  <img src="chart.png" alt="Sales increased 40% in Q3 2024" />

  // Decorative image
  <img src="divider.png" alt="" role="presentation" />

  // Icon button
  <button aria-label="Close dialog"><XIcon aria-hidden="true" /></button>

  // SVG
  <svg role="img" aria-label="Company logo">...</svg>
  ```

### 1.2.1 Audio-only and Video-only (Level A)

- **What to check:** Pre-recorded audio or video content
- **Common violations:** Audio without transcript, video without text alternative
- **Fix pattern:** Provide transcript for audio, text description or audio track for video

### 1.2.2 Captions (Prerecorded) (Level A)

- **What to check:** Video elements with audio content
- **Common violations:** `<video>` without `<track kind="captions">`
- **Fix pattern:**
  ```html
  <video controls>
    <source src="video.mp4" type="video/mp4" />
    <track kind="captions" src="captions.vtt" srclang="en" label="English" />
  </video>
  ```

### 1.2.3 Audio Description or Media Alternative (Level A)

- **What to check:** Video where visual content is not described in the audio
- **Common violations:** No audio description track, no text transcript
- **Fix pattern:** Add `<track kind="descriptions">` or provide a text transcript

### 1.2.4 Captions (Live) (Level AA)

- **What to check:** Live video with audio
- **Common violations:** Live streams without real-time captions
- **Fix pattern:** Integrate live captioning service

### 1.2.5 Audio Description (Prerecorded) (Level AA)

- **What to check:** Pre-recorded video content
- **Common violations:** Important visual info not described in audio
- **Fix pattern:** Provide audio description track

### 1.3.1 Info and Relationships (Level A)

- **What to check:** Semantic HTML usage, heading structure, form grouping, data tables
- **Common violations:**
  - Using `<div>` or `<span>` instead of semantic elements
  - Headings used for styling instead of structure
  - Tables without `<th>` headers
  - Form groups without `<fieldset>` and `<legend>`
  - Lists not using `<ul>`/`<ol>`/`<li>`
- **Fix pattern:**
  ```tsx
  // Use semantic elements
  <nav aria-label="Main navigation">...</nav>
  <main>...</main>
  <aside aria-label="Related articles">...</aside>

  // Data tables
  <table>
    <caption>Monthly sales data</caption>
    <thead><tr><th scope="col">Month</th>...</tr></thead>
    <tbody>...</tbody>
  </table>

  // Form groups
  <fieldset>
    <legend>Shipping Address</legend>
    <label for="street">Street</label>
    <input id="street" name="street" />
  </fieldset>
  ```

### 1.3.2 Meaningful Sequence (Level A)

- **What to check:** DOM order matches visual reading order
- **Common violations:**
  - CSS `order` property changing visual sequence without DOM change
  - `flex-direction: row-reverse` on navigation
  - `tabindex` values greater than 0 forcing unnatural tab order
- **Fix pattern:** Ensure DOM order reflects reading order; avoid `tabindex` > 0

### 1.3.3 Sensory Characteristics (Level A)

- **What to check:** Instructions that rely on shape, size, visual location, orientation, or sound
- **Common violations:**
  - "Click the round button" or "See the sidebar on the right"
  - "Required fields are marked in red" (without additional indicator)
- **Fix pattern:** Supplement sensory cues with text labels

### 1.3.4 Orientation (Level AA)

- **What to check:** Content works in both portrait and landscape
- **Common violations:** CSS or JS that locks orientation
- **Fix pattern:** Remove orientation locks unless essential (e.g., piano app)

### 1.3.5 Identify Input Purpose (Level AA)

- **What to check:** Form fields for personal data
- **Common violations:** Missing `autocomplete` attributes on name, email, phone, address fields
- **Fix pattern:**
  ```html
  <input type="email" name="email" autocomplete="email" />
  <input type="tel" name="phone" autocomplete="tel" />
  <input type="text" name="name" autocomplete="name" />
  ```

### 1.4.1 Use of Color (Level A)

- **What to check:** Information conveyed only through color
- **Common violations:**
  - Error states shown only with red border (no icon or text)
  - Links distinguished from text only by color
  - Charts with color-only legends
- **Fix pattern:** Add icons, text, underlines, or patterns alongside color

### 1.4.2 Audio Control (Level A)

- **What to check:** Audio that plays automatically for more than 3 seconds
- **Common violations:** Auto-playing background music or video
- **Fix pattern:** Provide pause/stop/mute controls, or limit auto-play to 3 seconds

### 1.4.3 Contrast (Minimum) (Level AA)

- **What to check:** Text and images of text
- **Common violations:**
  - Light gray text on white background
  - Placeholder text with insufficient contrast
  - Text over images without overlay
- **Fix pattern:**
  - Normal text (under 18pt / 14pt bold): minimum 4.5:1 contrast ratio
  - Large text (18pt+ / 14pt+ bold): minimum 3:1 contrast ratio
  - Use tools: WebAIM Contrast Checker, Chrome DevTools contrast picker

### 1.4.4 Resize Text (Level AA)

- **What to check:** Content readability at 200% browser zoom
- **Common violations:** Fixed pixel heights causing text overflow, truncation at zoom
- **Fix pattern:** Use relative units (`rem`, `em`, `%`), avoid fixed heights on text containers

### 1.4.5 Images of Text (Level AA)

- **What to check:** Text rendered as images
- **Common violations:** Logos with text in image, headings as images
- **Fix pattern:** Use actual text with CSS styling; images of text only for logos

### 1.4.10 Reflow (Level AA)

- **What to check:** Content at 320px viewport width (equivalent to 400% zoom)
- **Common violations:** Horizontal scrolling, content cut off, overlapping elements
- **Fix pattern:** Responsive design, no fixed widths wider than 320px for content

### 1.4.11 Non-text Contrast (Level AA)

- **What to check:** UI components (buttons, inputs, icons) and meaningful graphics
- **Common violations:**
  - Input borders with insufficient contrast against background
  - Icon-only buttons where icon color is too light
  - Custom checkboxes/radios with low contrast
- **Fix pattern:** Ensure 3:1 contrast ratio for UI component boundaries and states

### 1.4.12 Text Spacing (Level AA)

- **What to check:** Content with overridden text spacing (line height 1.5x, paragraph spacing 2x, letter spacing 0.12x, word spacing 0.16x)
- **Common violations:** Fixed-height containers that clip text when spacing increases
- **Fix pattern:** Use `min-height` instead of `height`, allow content to grow

### 1.4.13 Content on Hover or Focus (Level AA)

- **What to check:** Tooltips, popovers, dropdowns triggered by hover or focus
- **Common violations:**
  - Tooltip disappears when moving pointer to it
  - No way to dismiss tooltip without moving focus
  - Tooltip covers other content
- **Fix pattern:** Tooltips must be dismissible (Escape), hoverable (pointer can move to them), and persistent (stay visible while hovered/focused)

## 2. Operable

UI components and navigation must be operable by all users.

### 2.1.1 Keyboard (Level A)

- **What to check:** All interactive elements accessible via keyboard
- **Common violations:**
  - `<div onClick>` without `role="button"` and `onKeyDown`
  - Custom dropdowns without keyboard support
  - Drag-and-drop without keyboard alternative
  - `mousedown`/`mouseup` handlers without keyboard equivalents
- **Fix pattern:**
  ```tsx
  // Use semantic elements
  <button onClick={handleClick}>Submit</button>

  // If div must be interactive
  <div role="button" tabIndex={0} onClick={handleClick}
       onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') handleClick(); }}>
    Submit
  </div>
  ```

### 2.1.2 No Keyboard Trap (Level A)

- **What to check:** Focus can always move away from any element
- **Common violations:**
  - Modal without focus trap implementation (focus escapes to background)
  - Modal with focus trap but no Escape key to close
  - Embedded widgets (iframes, rich text editors) trapping focus
- **Fix pattern:** Implement proper focus management — trap focus inside modals, release on close, always support Escape to dismiss

### 2.1.4 Character Key Shortcuts (Level A)

- **What to check:** Single-character keyboard shortcuts
- **Common violations:** Single-key shortcuts (e.g., "s" to save) that interfere with assistive tech
- **Fix pattern:** Allow shortcuts to be remapped, disabled, or require a modifier key

### 2.2.1 Timing Adjustable (Level A)

- **What to check:** Time limits on content or actions
- **Common violations:** Session timeout without warning, auto-advancing carousels without pause
- **Fix pattern:** Warn before timeout, allow extension, provide pause/stop for auto-advancing content

### 2.2.2 Pause, Stop, Hide (Level A)

- **What to check:** Moving, blinking, scrolling, or auto-updating content
- **Common violations:**
  - Carousels without pause button
  - Animated backgrounds without stop control
  - Auto-refreshing content without pause option
- **Fix pattern:** Provide visible pause/stop controls, respect `prefers-reduced-motion`

### 2.3.1 Three Flashes or Below Threshold (Level A)

- **What to check:** Content that flashes
- **Common violations:** Animations with rapid blinking, video with strobing effects
- **Fix pattern:** No content flashes more than 3 times per second

### 2.4.1 Bypass Blocks (Level A)

- **What to check:** Mechanism to skip repeated content blocks (navigation, headers)
- **Common violations:**
  - No skip-to-content link
  - Skip link present but broken (target ID missing)
  - Skip link hidden and not focusable
- **Fix pattern:**
  ```tsx
  // First element in body
  <a href="#main-content" className="skip-link">Skip to main content</a>

  // Target
  <main id="main-content">...</main>

  // CSS: visible on focus
  .skip-link {
    position: absolute;
    left: -9999px;
  }
  .skip-link:focus {
    position: static;
    left: auto;
  }
  ```

### 2.4.2 Page Titled (Level A)

- **What to check:** Descriptive `<title>` on each page
- **Common violations:**
  - Generic title on all pages ("My App")
  - Missing title entirely
  - Title doesn't reflect page content
- **Fix pattern:** Unique, descriptive title: "Dashboard - My App", "Edit Profile - My App"

### 2.4.3 Focus Order (Level A)

- **What to check:** Tab order follows logical reading sequence
- **Common violations:**
  - `tabindex` values > 0 forcing unnatural order
  - Visual layout doesn't match DOM order
  - Modal or sidebar focus order doesn't match visual layout
- **Fix pattern:** Use natural DOM order, `tabindex="0"` for custom interactive elements, `tabindex="-1"` for programmatic focus

### 2.4.4 Link Purpose (In Context) (Level A)

- **What to check:** Link text describes its destination
- **Common violations:**
  - "Click here", "Read more", "Learn more" without context
  - URLs as link text
  - Adjacent duplicate links (image + text going to same place)
- **Fix pattern:**
  ```tsx
  // Bad
  <a href="/pricing">Click here</a>

  // Good
  <a href="/pricing">View pricing plans</a>

  // If visible text must be short
  <a href="/pricing">Learn more <span className="sr-only">about pricing plans</span></a>
  ```

### 2.4.5 Multiple Ways (Level AA)

- **What to check:** Multiple ways to locate pages (nav, search, site map)
- **Common violations:** Only one navigation mechanism available
- **Fix pattern:** Provide at least two: navigation menu, search, site map, breadcrumbs

### 2.4.6 Headings and Labels (Level AA)

- **What to check:** Headings and labels describe topic or purpose
- **Common violations:** Vague headings ("Section 1"), duplicate labels, missing form labels
- **Fix pattern:** Use descriptive, unique headings and labels

### 2.4.7 Focus Visible (Level AA)

- **What to check:** Visible focus indicator on all interactive elements
- **Common violations:**
  - `outline: none` or `outline: 0` without replacement
  - Focus style only on `:focus` not `:focus-visible`
  - Custom components without focus styles
- **Fix pattern:**
  ```css
  /* Provide visible focus indicator */
  :focus-visible {
    outline: 2px solid #005fcc;
    outline-offset: 2px;
  }

  /* Don't remove focus styles globally */
  /* Bad: *:focus { outline: none; } */
  ```

### 2.5.1 Pointer Gestures (Level A)

- **What to check:** Multi-point or path-based gestures (pinch, swipe, drag)
- **Common violations:** Pinch-to-zoom is only way to zoom, swipe is only way to navigate carousel
- **Fix pattern:** Provide single-pointer alternatives (buttons for zoom, arrows for carousel)

### 2.5.2 Pointer Cancellation (Level A)

- **What to check:** Click/tap activation timing
- **Common violations:** Actions triggered on `mousedown`/`touchstart` instead of `mouseup`/`click`
- **Fix pattern:** Use `click` events (which fire on release) or allow cancellation by moving pointer away

### 2.5.3 Label in Name (Level A)

- **What to check:** Visible label text is included in the accessible name
- **Common violations:**
  - Button shows "Submit" but `aria-label="Send form data"`
  - `<label>` text differs from `aria-label`
- **Fix pattern:** Ensure `aria-label` contains the visible label text, or use `aria-labelledby` pointing to visible text

### 2.5.4 Motion Actuation (Level A)

- **What to check:** Functionality triggered by device motion (shake, tilt)
- **Common violations:** Shake-to-undo with no button alternative
- **Fix pattern:** Provide UI control alternative, allow disabling motion activation

## 3. Understandable

Information and operation of the UI must be understandable.

### 3.1.1 Language of Page (Level A)

- **What to check:** `lang` attribute on `<html>` element
- **Common violations:**
  - Missing `lang` attribute entirely
  - Wrong language code
  - `lang` attribute on `<body>` instead of `<html>`
- **Fix pattern:**
  ```html
  <html lang="en">
  ```

### 3.1.2 Language of Parts (Level AA)

- **What to check:** Content in a different language than the page default
- **Common violations:** Foreign-language quotes or phrases without `lang` attribute
- **Fix pattern:**
  ```html
  <p>The French term <span lang="fr">c'est la vie</span> means "that's life."</p>
  ```

### 3.2.1 On Focus (Level A)

- **What to check:** Context changes when an element receives focus
- **Common violations:**
  - Auto-submitting form when field receives focus
  - Opening new window on focus
  - Navigating to new page on focus
- **Fix pattern:** Focus should never trigger a context change; use explicit activation (click, Enter)

### 3.2.2 On Input (Level A)

- **What to check:** Context changes when user changes input value
- **Common violations:**
  - Form submits when selecting a radio button
  - Page navigates when changing a dropdown value
- **Fix pattern:** Warn users before context change, or require explicit submit action

### 3.2.3 Consistent Navigation (Level AA)

- **What to check:** Navigation consistency across pages
- **Common violations:** Navigation order changes between pages, items appear/disappear
- **Fix pattern:** Keep navigation order and structure consistent across all pages

### 3.2.4 Consistent Identification (Level AA)

- **What to check:** Components with the same function use the same labels
- **Common violations:** Search called "Search" on one page and "Find" on another, different icons for same action
- **Fix pattern:** Use consistent labels and icons for the same functionality everywhere

### 3.3.1 Error Identification (Level A)

- **What to check:** Error messages for form validation
- **Common violations:**
  - Errors shown only with red border (no text description)
  - Generic "Form has errors" without identifying which field
  - Error not associated with input (`aria-describedby` or `aria-errormessage`)
- **Fix pattern:**
  ```tsx
  <label htmlFor="email">Email</label>
  <input id="email" aria-describedby="email-error" aria-invalid="true" />
  <span id="email-error" role="alert">Please enter a valid email address</span>
  ```

### 3.3.2 Labels or Instructions (Level A)

- **What to check:** Form fields have visible labels and instructions
- **Common violations:**
  - Placeholder text used as only label
  - Required field indicator without explanation
  - Complex input format without instructions (e.g., date format)
- **Fix pattern:** Always provide visible `<label>`, add help text for format requirements, explain required field indicators

### 3.3.3 Error Suggestion (Level AA)

- **What to check:** Error messages suggest how to fix the problem
- **Common violations:**
  - "Invalid input" with no suggestion
  - "Error" with no description at all
- **Fix pattern:** "Please enter an email in the format name@example.com" instead of "Invalid email"

### 3.3.4 Error Prevention (Legal, Financial, Data) (Level AA)

- **What to check:** Submissions that are legal, financial, or modify/delete user data
- **Common violations:**
  - One-click delete without confirmation
  - Financial transaction without review step
  - No way to undo or review before submit
- **Fix pattern:** Provide confirmation dialog, review step, or undo capability for destructive/important actions

## 4. Robust

Content must be robust enough for reliable interpretation by assistive technologies.

### 4.1.1 Parsing (Level A)

- **What to check:** Valid HTML markup
- **Common violations:**
  - Duplicate `id` attributes
  - Unclosed tags
  - Improper nesting (e.g., `<a>` inside `<a>`, `<button>` inside `<a>`)
  - Missing required attributes
- **Fix pattern:** Run HTML validator, fix duplicate IDs, ensure proper nesting

### 4.1.2 Name, Role, Value (Level A)

- **What to check:** Custom components expose correct name, role, and value to assistive tech
- **Common violations:**
  - Custom checkbox without `role="checkbox"` and `aria-checked`
  - Custom select without `role="listbox"` and `role="option"`
  - Custom tabs without `role="tablist"`, `role="tab"`, `role="tabpanel"`
  - Toggle button without `aria-pressed` or `aria-expanded`
  - Missing `aria-label` or `aria-labelledby` on landmark regions
- **Fix pattern:**
  ```tsx
  // Custom toggle
  <button aria-pressed={isActive} onClick={toggle}>Dark Mode</button>

  // Custom accordion
  <button aria-expanded={isOpen} aria-controls="panel-1">Section Title</button>
  <div id="panel-1" role="region" aria-labelledby="heading-1" hidden={!isOpen}>
    ...
  </div>

  // Custom tabs
  <div role="tablist" aria-label="Account settings">
    <button role="tab" aria-selected={activeTab === 0} aria-controls="panel-0">Profile</button>
    <button role="tab" aria-selected={activeTab === 1} aria-controls="panel-1">Security</button>
  </div>
  <div role="tabpanel" id="panel-0" aria-labelledby="tab-0">...</div>
  ```

### 4.1.3 Status Messages (Level AA)

- **What to check:** Dynamic content updates that inform users without receiving focus
- **Common violations:**
  - Toast/snackbar notifications without `aria-live`
  - Search result count updates without announcement
  - Form submission success message not announced
  - Loading states not communicated
- **Fix pattern:**
  ```tsx
  // Toast notification
  <div role="status" aria-live="polite">Item saved successfully</div>

  // Error alert
  <div role="alert" aria-live="assertive">Connection lost. Retrying...</div>

  // Search results
  <div aria-live="polite" aria-atomic="true">{count} results found</div>

  // Loading
  <div role="status" aria-live="polite">
    {isLoading ? "Loading content..." : "Content loaded"}
  </div>
  ```

## Testing Tools Reference

| Tool | Purpose | How to Use |
|------|---------|-----------|
| **axe-core** | Automated a11y testing | `npm install @axe-core/react` for dev overlay |
| **jest-axe** | Jest a11y assertions | `expect(await axe(container)).toHaveNoViolations()` |
| **@axe-core/playwright** | Playwright a11y testing | `const results = await new AxeBuilder({ page }).analyze()` |
| **eslint-plugin-jsx-a11y** | Lint for React a11y | Add to ESLint config |
| **pa11y** | CLI a11y testing | `npx pa11y https://localhost:3000` |
| **Lighthouse** | Chrome DevTools audit | DevTools > Lighthouse > Accessibility |
| **WAVE** | Browser extension | Install from web store |
| **WebAIM Contrast Checker** | Color contrast | https://webaim.org/resources/contrastchecker/ |
