# Socrate AI Design System Documentation

**Last Updated:** October 25, 2025
**Version:** 2.0 - Green Nature Theme

---

## Executive Summary

This document defines the comprehensive design system for the Socrate AI application. The design system has been completely redesigned to match the new logo's vibrant green nature-inspired color palette, replacing the previous cyan/teal theme while maintaining the academic bronze/gold accents.

---

## Color Palette

### Primary Colors (Green Spectrum)

Extracted directly from the Socrate AI logo, these colors represent knowledge, growth, and AI innovation:

- **Vibrant Lime Green** (Primary Brand Color)
  - `--color-primary-lime: #8fef10` - Main brand color
  - `--color-primary-lime-light: #a4ff2e` - Hover states, highlights
  - `--color-primary-lime-dark: #7dd900` - Pressed states, darker variants

- **Emerald Green** (Secondary Brand Color)
  - `--color-primary-green: #3da85f` - Secondary actions
  - `--color-primary-green-light: #52c273` - Light accents
  - `--color-primary-green-dark: #2d8b4a` - Dark accents

**Use Cases:**
- Primary buttons and CTAs
- Interactive elements (links, focus states)
- Accent borders and glows
- Icons and illustrations
- Progress indicators

**Accessibility:** All primary greens meet WCAG AA contrast requirements (4.5:1) when used on dark backgrounds.

---

### Accent Colors (Gold/Bronze)

Retained from the original design to represent wisdom and academic excellence:

- **Bronze/Gold**
  - `--color-accent-bronze: #D4B875` - Main accent
  - `--color-accent-gold: #D4AF37` - Premium accents
  - `--color-accent-bronze-dark: #A08757` - Darker variant

**Use Cases:**
- Secondary buttons
- Gradient combinations with green
- Text highlights for emphasis
- Badge accents
- Premium features

---

### Background Colors (Deep Forest Green Dark Theme)

Dark theme backgrounds inspired by deep forest green:

- `--color-bg-primary: #0a1612` - Main app background (deep forest)
- `--color-bg-secondary: #15241e` - Section backgrounds
- `--color-bg-tertiary: #1f3329` - Card/panel backgrounds
- `--color-bg-card: #1a2920` - Interactive cards
- `--color-bg-hover: #243d32` - Hover state backgrounds

**Philosophy:** The deep green-tinted backgrounds create an immersive, nature-inspired environment that reduces eye strain while maintaining the dark theme aesthetic.

---

### Text Colors

Optimized for readability on dark backgrounds:

- `--color-text-primary: #f8fafc` - Headings, important text (contrast ratio 15:1)
- `--color-text-secondary: #cbd5e1` - Body text (contrast ratio 12:1)
- `--color-text-tertiary: #A3B3C8` - Less important text (WCAG AA compliant)
- `--color-text-muted: #64748b` - Disabled states, placeholders

---

### Border Colors

- `--color-border-primary: rgba(143, 239, 16, 0.25)` - Lime green borders
- `--color-border-secondary: rgba(201, 169, 113, 0.2)` - Bronze borders
- `--color-border-subtle: rgba(255, 255, 255, 0.08)` - Subtle dividers

---

### Status Colors

- `--color-success: #3da85f` - Success messages (emerald green)
- `--color-warning: #f59e0b` - Warnings
- `--color-error: #ef4444` - Errors
- `--color-info: #8fef10` - Info messages (lime green)

---

## Glow Effects (Signature Design Element)

The design system features vibrant neon-style glow effects that enhance the modern, AI-focused aesthetic:

### Lime Green Glow
```css
--glow-lime: 0 0 20px rgba(143, 239, 16, 0.5),
             0 0 40px rgba(143, 239, 16, 0.25);

--glow-lime-strong: 0 0 10px rgba(164, 255, 46, 0.8),
                    0 0 30px rgba(143, 239, 16, 0.6),
                    0 0 60px rgba(125, 217, 0, 0.4);
```

### Emerald Green Glow
```css
--glow-green: 0 0 20px rgba(61, 168, 95, 0.5),
              0 0 40px rgba(61, 168, 95, 0.25);
```

### Bronze Glow
```css
--glow-bronze: 0 0 20px rgba(212, 175, 55, 0.4),
               0 0 40px rgba(201, 169, 113, 0.2);
```

**Application:**
- Hover states on buttons and cards
- Logo ambient effects
- Focus indicators
- Active interactive elements

---

## Typography

### Font Families

- **Display/Headings:** `'Space Grotesk'` - Modern geometric sans-serif for impact
- **Body Text:** `'Manrope'` - Humanist sans-serif for readability
- **Code:** `'JetBrains Mono'` - Monospace for technical content

### Font Scale (Modular Scale 1.25)

- `--text-xs: 0.75rem` (12px)
- `--text-sm: 0.875rem` (14px)
- `--text-base: 1rem` (16px)
- `--text-lg: 1.125rem` (18px)
- `--text-xl: 1.25rem` (20px)
- `--text-2xl: 1.5rem` (24px)
- `--text-3xl: 1.875rem` (30px)
- `--text-4xl: 2.25rem` (36px)
- `--text-5xl: 3rem` (48px)
- `--text-6xl: 3.75rem` (60px)

### Font Weights

- `--font-normal: 400`
- `--font-medium: 500`
- `--font-semibold: 600`
- `--font-bold: 700`
- `--font-extrabold: 800`

---

## Component Styles

### Buttons

#### Primary Button (`.btn-primary`)
- Background: Lime green gradient
- Glow effect on hover
- Use for main CTAs

#### Secondary Button (`.btn-secondary`)
- Background: Bronze gradient
- Subtler glow
- Use for alternative actions

#### Outline Button (`.btn-outline`)
- Transparent background
- Lime green border
- Use for tertiary actions

#### Sizes
- `.btn-sm` - Compact buttons
- Default - Standard size
- `.btn-lg` - Large, prominent buttons

---

### Cards

#### Standard Card (`.card`)
- Glassmorphism background with backdrop blur
- Lime green glow on hover
- Transforms slightly on interaction

#### Variations
- `.card-glow` - Always glowing
- `.card-bronze` - Bronze accent

---

### Forms

All form inputs feature:
- Lime green focus states
- Consistent 3px focus ring (WCAG 2.1 AA compliant)
- Smooth transitions
- Clear disabled states

---

### Badges

- `.badge-lime` - Lime green theme
- `.badge-green` - Emerald green theme
- `.badge-bronze` - Bronze theme
- `.badge-gold` - Gold premium theme
- `.badge-success` - Success state
- `.badge-warning` - Warning state
- `.badge-error` - Error state

---

## Spacing System (Base Unit: 4px)

```
--space-1: 0.25rem  (4px)
--space-2: 0.5rem   (8px)
--space-3: 0.75rem  (12px)
--space-4: 1rem     (16px)
--space-5: 1.25rem  (20px)
--space-6: 1.5rem   (24px)
--space-8: 2rem     (32px)
--space-10: 2.5rem  (40px)
--space-12: 3rem    (48px)
--space-16: 4rem    (64px)
--space-20: 5rem    (80px)
--space-24: 6rem    (96px)
```

---

## Border Radius

- `--radius-sm: 0.25rem` (4px) - Small elements
- `--radius-md: 0.5rem` (8px) - Standard elements
- `--radius-lg: 0.75rem` (12px) - Cards
- `--radius-xl: 1rem` (16px) - Large panels
- `--radius-full: 9999px` - Circular elements

---

## Transitions

- `--transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1)` - Quick interactions
- `--transition-base: 200ms cubic-bezier(0.4, 0, 0.2, 1)` - Standard
- `--transition-slow: 300ms cubic-bezier(0.4, 0, 0.2, 1)` - Deliberate animations

---

## Z-Index Layers

- `--z-base: 0` - Default layer
- `--z-dropdown: 100` - Dropdowns
- `--z-sticky: 200` - Sticky headers
- `--z-modal-backdrop: 900` - Modal backdrop
- `--z-modal: 1000` - Modals
- `--z-toast: 1100` - Toast notifications

---

## Accessibility Features

### WCAG 2.1 AA Compliance

1. **Color Contrast**
   - All text colors meet 4.5:1 contrast ratio minimum
   - Large text (18px+) meets 3:1 minimum
   - Interactive elements have sufficient contrast

2. **Focus Indicators**
   - 3px solid lime green outline
   - 2px offset for visibility
   - Never remove focus indicators

3. **Keyboard Navigation**
   - All interactive elements keyboard accessible
   - Logical tab order
   - Skip links where appropriate

4. **Screen Reader Support**
   - Semantic HTML structure
   - ARIA labels on complex components
   - Alt text on images

---

## Logo Usage Guidelines

### Full Logo Placement

The Socrate AI logo (Socrates with headphones) should ONLY be used in:
- Hero sections (landing page)
- Dashboard header (large, prominent placement)
- Footer (medium size)
- Marketing materials

**Minimum Size:** 120px width to maintain detail visibility

### Text-Only Branding

In constrained spaces, use "Socrate AI" text with gradient:
- Navbar links
- Small footers
- Modal headers
- Email signatures

**Brand Text Gradient:**
```css
background: linear-gradient(135deg, #8fef10, #D4AF37);
-webkit-background-clip: text;
-webkit-text-fill-color: transparent;
```

---

## Gradient Combinations

### Primary Gradient (Green to Gold)
```css
background: linear-gradient(135deg, var(--color-primary-lime), var(--color-accent-gold));
```
Use for: Hero titles, stat values, CTA backgrounds

### Green Spectrum Gradient
```css
background: linear-gradient(135deg, var(--color-primary-lime-light), var(--color-primary-green));
```
Use for: Subtle backgrounds, progress bars

### Radial Ambient Glows
```css
background: radial-gradient(circle at center,
  rgba(143, 239, 16, 0.25) 0%,
  rgba(143, 239, 16, 0.15) 30%,
  transparent 70%
);
```
Use for: Logo ambient effects, decorative elements

---

## Animation Principles

1. **Purposeful Motion** - Every animation serves a functional purpose
2. **Natural Easing** - Use cubic-bezier for organic feel
3. **Performance** - Transform and opacity only for 60fps
4. **Respect Motion Preferences** - Honor `prefers-reduced-motion`

### Signature Animations

- **Float Animation** - Gentle vertical oscillation for logos (6s duration)
- **Glow Pulse** - Breathing glow effect (3-4s duration)
- **Grid Movement** - Infinite background grid animation (20s)

---

## Glassmorphism Effects

Cards use modern glassmorphism:
```css
background: rgba(30, 34, 48, 0.7);
backdrop-filter: blur(16px) saturate(180%);
border: 1px solid rgba(255, 255, 255, 0.18);
```

**Browser Support:**
- Modern browsers (95%+ coverage)
- Graceful degradation on older browsers

---

## Mobile Responsiveness

### Breakpoints
- Mobile: `max-width: 768px`
- Tablet: `769px - 1024px`
- Desktop: `1025px+`

### Mobile Adaptations
- Reduced font sizes for headings
- Full-width buttons
- Simplified glow effects (performance)
- Touch-friendly tap targets (minimum 44x44px)

---

## File Structure

```
static/css/
├── styles.css       # Base design system & components
├── landing.css      # Landing page specific styles
└── dashboard.css    # Dashboard specific styles
```

---

## Implementation Notes

### CSS Custom Properties

All design tokens are defined in `:root` in `styles.css`. To use in any file:

```css
.my-element {
  color: var(--color-primary-lime);
  background: var(--color-bg-card);
  padding: var(--space-4);
  border-radius: var(--radius-md);
}
```

### Utility Classes

Common utilities available:
- `.text-lime`, `.text-green`, `.text-bronze` - Text colors
- `.glow-lime`, `.glow-green`, `.glow-bronze` - Glow effects
- `.btn-primary`, `.btn-secondary`, `.btn-outline` - Buttons
- `.badge-lime`, `.badge-green`, `.badge-bronze` - Badges

---

## Design Philosophy

The Socrate AI design system embodies:

1. **Nature-Inspired Intelligence** - Green palette represents growth, knowledge, and natural learning
2. **Academic Excellence** - Gold/bronze accents evoke classical wisdom and philosophy
3. **Modern AI Innovation** - Vibrant neon glows and glassmorphism represent cutting-edge technology
4. **Accessibility First** - Every design decision considers users of all abilities
5. **Performance** - Optimized for smooth 60fps interactions

---

## Future Enhancements

Planned additions to the design system:

- [ ] Light theme variant (nature-inspired with pale greens)
- [ ] Additional badge styles for specific states
- [ ] Loading skeleton components
- [ ] Toast notification system
- [ ] Tooltip system with lime green accents
- [ ] Data visualization color scales
- [ ] Icon library with brand-specific designs

---

## Version History

**Version 2.0** (October 25, 2025)
- Complete redesign with green nature theme
- New logo-based color palette
- Updated all components to use lime/emerald green
- Enhanced accessibility features
- Improved glassmorphism effects

**Version 1.0** (Previous)
- Original cyan/teal theme
- Bronze accents
- Initial component library

---

## Contact & Support

For design system questions or contributions:
- Review this documentation first
- Check `CLAUDE.md` for technical implementation details
- Ensure all changes maintain WCAG AA accessibility standards

---

**Remember:** Consistency is key. Always use design tokens rather than hard-coded values to maintain the unified brand experience across the entire Socrate AI application.
