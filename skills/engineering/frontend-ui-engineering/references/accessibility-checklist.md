# Accessibility Checklist

Reference file for frontend-ui-engineering, shipping-and-launch, and code-review-and-quality skills.

## WCAG 2.1 AA Quick Reference

All user-facing interfaces must meet WCAG 2.1 Level AA. The core principles: **Perceivable**, **Operable**, **Understandable**, and **Robust**.

### Perceivable

- [ ] All images have alternative text (`alt` attribute)
- [ ] Video has captions (live content has synchronized captions)
- [ ] Audio has transcript or is not auto-playing
- [ ] Color is not the only way information is conveyed
- [ ] Text contrast ratio ≥ 4.5:1 for normal text, ≥ 3:1 for large text
- [ ] Focus order is logical and matches visual order

### Operable

- [ ] All functionality available via keyboard
- [ ] Focus is visible on all interactive elements
- [ ] No keyboard traps (Tab can always escape)
- [ ] Skip links for main content
- [ ] No content that flashes more than 3 times per second
- [ ] Users have control over timing and limits on content

### Understandable

- [ ] Language is programmatically declared (`lang` attribute)
- [ ] Navigation is consistent across pages
- [ ] Labels are associated with inputs
- [ ] Error messages are specific and helpful

### Robust

- [ ] Valid HTML (no severe validation errors)
- [ ] ARIA used correctly (if used at all)
- [ ] Names, roles, values available to assistive tech

## Keyboard Navigation

### Interactive Elements

| Element | Keyboard Access | Notes |
|---------|-----------------|-------|
| `<button>` | Enter / Space | Native support |
| `<a href>` | Enter | Native support |
| `<input>` | Tab | Native support |
| Custom widget | Tab + arrow keys | Requires `role` and keyboard handlers |

### Requirements

- [ ] Every interactive element has visible focus indicator (outline: 2px solid)
- [ ] Focus moves in logical order (matches visual layout)
- [ ] `tabindex` used only on interactive elements
- [ ] Skip link at top of page links to main content
- [ ] Modal dialogs trap focus when open, release when closed

### Focus Styles

```css
/* Good: Clear focus indicator */
button:focus-visible,
a:focus-visible,
input:focus-visible {
  outline: 3px solid #2563eb;
  outline-offset: 2px;
}

/* Bad: Removing focus indicator */
:focus {
  outline: none;
}
```

## Screen Reader Support

### Semantic HTML

| Element | When to Use | What It Provides |
|---------|-------------|-------------------|
| `<button>` | Actions | Role, click handling, keyboard access |
| `<a href>` | Navigation | Role, href, keyboard access |
| `<h1>`–`<h6>` | Headings | Role, level, accessible name |
| `<ul>/<ol>` | Lists | Role, list item count |
| `<nav>` | Navigation | Role, region, label |
| `<main>` | Main content | Role, region |
| `<main>` | Landmark | Nameable, landmark |

### ARIA Guidelines

- [ ] Prefer native HTML over ARIA
- [ ] If ARIA is used, all required attributes are present
- [ ] `aria-label` used only when no visible label exists
- [ ] `aria-live` regions announce changes appropriately
- [ ] Modals have `role="dialog"`, `aria-modal="true"`, and labeled
- [ ] Custom widgets follow ARIA authoring practices

### Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| `div` for buttons | Not keyboard accessible, no role announced | Use `<button>` |
| Missing labels | Screen reader users can't identify inputs | Use `<label for="id">` or `aria-label` |
| Decorative images with `alt=""` | Wastes screen reader time | Use `alt=""` (empty) |
| Links that say "click here" | Unhelpful out of context | Describe the destination |
| Dynamic content without notifications | Users miss updates | Use `aria-live` region |

## Forms

- [ ] All inputs have associated labels:
  ```html
  <label for="email">Email</label>
  <input id="email" type="email" />
  ```
- [ ] Error messages associated with inputs: `aria-describedby="error-id"`
- [ ] Required fields indicated visually AND programmatically (`required` attribute)
- [ ] Field validation errors are announced (aria-live region)
- [ ] Autocomplete attributes on personal data fields

## Color and Contrast

### Requirements

- [ ] Normal text: 4.5:1 contrast ratio minimum
- [ ] Large text (18px+ or 14px bold): 3:1 minimum
- [ ] UI components (buttons, inputs): 3:1 against adjacent color
- [ ] Color is not the only indicator (icons + text, or text alone)

### Tools

- Chrome DevTools > Accessibility pane > Contrast issues
- WebAIM Contrast Checker
-axe DevTools

## Testing Checklist

### Manual Testing

- [ ] Navigate entire interface with keyboard only
- [ ] Test with VoiceOver (macOS) or NVDA (Windows)
- [ ] Zoom to 200% — no content clipped or overlapped
- [ ] Disable styles — content is readable and ordered
- [ ] Network throttling (Fast 3G) — no missing content

### Automated Tools

- [ ] axe DevTools: 0 critical accessibility issues
- [ ] Lighthouse Accessibility score: 100
- [ ] WAVE (WebAIM): 0 errors

### Mobile

- [ ] VoiceOver (iOS) / TalkBack (Android) navigation works
- [ ] Touch targets ≥ 44x44 CSS pixels
- [ ] No pinch-zoom disabled (unless essential)

## Pre-Launch Accessibility Checklist

1. Keyboard-only navigation: complete all user flows
2. Screen reader: test with VoiceOver + Safari
3. axe DevTools: 0 critical/high issues
4. Lighthouse Accessibility: score ≥ 90
5. Color contrast: verified with DevTools
6. Forms: all fields labeled and error messages announced
7. Images: all have alt text (or empty for decorative)
8. Focus: visible on all interactive elements
9. Zoom: 200% usable, no horizontal scroll
10. No auto-playing audio without controls