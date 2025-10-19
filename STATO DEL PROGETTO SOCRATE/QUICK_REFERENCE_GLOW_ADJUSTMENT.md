# Quick Reference: Owl Logo Glow Adjustment Guide

This guide provides quick copy-paste CSS snippets for common adjustments to the owl logo ambient glow system.

---

## Common Adjustments

### 1. Increase/Decrease Glow Intensity

**Location**: `D:\railway\memvid\static\css\dashboard.css` (Lines 61-105)

**Brighter Glow** (increase all alpha values by 0.1):
```css
/* Layer 1: Deep Background Glow */
.logo-owl-container::before {
  background: radial-gradient(
    circle at center,
    rgba(0, 217, 192, 0.35) 0%,      /* was 0.25 */
    rgba(0, 217, 192, 0.25) 30%,     /* was 0.15 */
    rgba(0, 255, 224, 0.18) 50%,     /* was 0.08 */
    transparent 70%
  );
}

/* Layer 2: Mid-Range Glow */
.logo-owl-container::after {
  background: radial-gradient(
    circle at center,
    rgba(0, 217, 192, 0.4) 0%,       /* was 0.3 */
    rgba(212, 175, 55, 0.22) 40%,    /* was 0.12 */
    rgba(0, 217, 192, 0.28) 60%,     /* was 0.18 */
    transparent 75%
  );
}
```

**Dimmer Glow** (decrease all alpha values by 0.05):
```css
/* Layer 1: Deep Background Glow */
.logo-owl-container::before {
  background: radial-gradient(
    circle at center,
    rgba(0, 217, 192, 0.20) 0%,      /* was 0.25 */
    rgba(0, 217, 192, 0.10) 30%,     /* was 0.15 */
    rgba(0, 255, 224, 0.03) 50%,     /* was 0.08 */
    transparent 70%
  );
}

/* Layer 2: Mid-Range Glow */
.logo-owl-container::after {
  background: radial-gradient(
    circle at center,
    rgba(0, 217, 192, 0.25) 0%,      /* was 0.3 */
    rgba(212, 175, 55, 0.07) 40%,    /* was 0.12 */
    rgba(0, 217, 192, 0.13) 60%,     /* was 0.18 */
    transparent 75%
  );
}
```

---

### 2. Expand/Contract Glow Radius

**Location**: `D:\railway\memvid\static\css\dashboard.css` (Lines 61-105)

**Larger Glow Area** (20% increase):
```css
/* Layer 1: Deep Background Glow */
.logo-owl-container::before {
  width: 336px;                      /* was 280px (280 × 1.2) */
  height: 336px;
  clip-path: circle(168px at center); /* was 140px (140 × 1.2) */
}

/* Layer 2: Mid-Range Glow */
.logo-owl-container::after {
  width: 240px;                      /* was 200px (200 × 1.2) */
  height: 240px;
  clip-path: circle(120px at center); /* was 100px (100 × 1.2) */
}

/* Particle Glow */
.logo-owl-container .particle-glow {
  width: 192px;                      /* was 160px (160 × 1.2) */
  height: 192px;
  clip-path: circle(96px at center); /* was 80px (80 × 1.2) */
}
```

**Smaller Glow Area** (20% decrease):
```css
/* Layer 1: Deep Background Glow */
.logo-owl-container::before {
  width: 224px;                      /* was 280px (280 × 0.8) */
  height: 224px;
  clip-path: circle(112px at center); /* was 140px (140 × 0.8) */
}

/* Layer 2: Mid-Range Glow */
.logo-owl-container::after {
  width: 160px;                      /* was 200px (200 × 0.8) */
  height: 160px;
  clip-path: circle(80px at center); /* was 100px (100 × 0.8) */
}

/* Particle Glow */
.logo-owl-container .particle-glow {
  width: 128px;                      /* was 160px (160 × 0.8) */
  height: 128px;
  clip-path: circle(64px at center); /* was 80px (80 × 0.8) */
}
```

---

### 3. Change Animation Speed

**Location**: `D:\railway\memvid\static\css\dashboard.css` (Lines 61-105)

**Faster Animations** (reduce duration by 50%):
```css
.logo-owl-container::before {
  animation: owlPulseDeep 2s ease-in-out infinite;  /* was 4s */
}

.logo-owl-container::after {
  animation: owlPulseMid 1.5s ease-in-out infinite 0.5s;  /* was 3s */
}

.logo-owl-icon {
  animation: owlIconGlow 1.5s ease-in-out infinite;  /* was 3s */
}

.logo-owl-container .particle-glow {
  animation: particleRotate 4s linear infinite;  /* was 8s */
}
```

**Slower Animations** (increase duration by 50%):
```css
.logo-owl-container::before {
  animation: owlPulseDeep 6s ease-in-out infinite;  /* was 4s */
}

.logo-owl-container::after {
  animation: owlPulseMid 4.5s ease-in-out infinite 0.5s;  /* was 3s */
}

.logo-owl-icon {
  animation: owlIconGlow 4.5s ease-in-out infinite;  /* was 3s */
}

.logo-owl-container .particle-glow {
  animation: particleRotate 12s linear infinite;  /* was 8s */
}
```

**Disable All Animations**:
```css
.logo-owl-container::before,
.logo-owl-container::after,
.logo-owl-icon,
.logo-owl-container .particle-glow {
  animation: none !important;
}
```

---

### 4. Change Color Scheme

**Location**: `D:\railway\memvid\static\css\dashboard.css` (Lines 61-105)

**Purple/Pink Variant** (replace cyan with purple):
```css
/* Layer 1: Deep Background Glow */
.logo-owl-container::before {
  background: radial-gradient(
    circle at center,
    rgba(168, 85, 247, 0.25) 0%,     /* Purple */
    rgba(168, 85, 247, 0.15) 30%,
    rgba(217, 70, 239, 0.08) 50%,    /* Pink */
    transparent 70%
  );
}

/* Layer 2: Mid-Range Glow */
.logo-owl-container::after {
  background: radial-gradient(
    circle at center,
    rgba(168, 85, 247, 0.3) 0%,
    rgba(212, 175, 55, 0.12) 40%,    /* Keep bronze */
    rgba(168, 85, 247, 0.18) 60%,
    transparent 75%
  );
}

/* Owl Icon */
.logo-owl-icon {
  filter: drop-shadow(0 0 20px rgba(168, 85, 247, 0.8))
          drop-shadow(0 0 35px rgba(168, 85, 247, 0.4))
          drop-shadow(0 0 50px rgba(212, 175, 55, 0.2));
}

/* Particle Glow */
.logo-owl-container .particle-glow {
  background:
    radial-gradient(circle at 70% 30%, rgba(217, 70, 239, 0.15), transparent 40%),
    radial-gradient(circle at 30% 70%, rgba(212, 175, 55, 0.1), transparent 40%),
    radial-gradient(circle at 50% 50%, rgba(168, 85, 247, 0.12), transparent 50%);
}
```

**Green/Emerald Variant** (replace cyan with green):
```css
/* Layer 1: Deep Background Glow */
.logo-owl-container::before {
  background: radial-gradient(
    circle at center,
    rgba(16, 185, 129, 0.25) 0%,     /* Emerald */
    rgba(16, 185, 129, 0.15) 30%,
    rgba(52, 211, 153, 0.08) 50%,    /* Light emerald */
    transparent 70%
  );
}

/* Layer 2: Mid-Range Glow */
.logo-owl-container::after {
  background: radial-gradient(
    circle at center,
    rgba(16, 185, 129, 0.3) 0%,
    rgba(212, 175, 55, 0.12) 40%,    /* Keep bronze */
    rgba(16, 185, 129, 0.18) 60%,
    transparent 75%
  );
}

/* Owl Icon */
.logo-owl-icon {
  filter: drop-shadow(0 0 20px rgba(16, 185, 129, 0.8))
          drop-shadow(0 0 35px rgba(16, 185, 129, 0.4))
          drop-shadow(0 0 50px rgba(212, 175, 55, 0.2));
}

/* Particle Glow */
.logo-owl-container .particle-glow {
  background:
    radial-gradient(circle at 70% 30%, rgba(52, 211, 153, 0.15), transparent 40%),
    radial-gradient(circle at 30% 70%, rgba(212, 175, 55, 0.1), transparent 40%),
    radial-gradient(circle at 50% 50%, rgba(16, 185, 129, 0.12), transparent 50%);
}
```

---

### 5. Adjust Mobile Scaling

**Location**: `D:\railway\memvid\static\css\dashboard.css` (Lines 788-815)

**Larger Mobile Logo** (increase size by 25%):
```css
@media (max-width: 768px) {
  .logo-owl-container {
    width: 100px;                      /* was 80px (80 × 1.25) */
    height: 100px;
  }

  .logo-owl-icon {
    width: 90px;                       /* was 72px (72 × 1.25) */
    height: 90px;
  }

  .logo-owl-container::before {
    width: 225px;                      /* was 180px (180 × 1.25) */
    height: 225px;
    clip-path: circle(112.5px at center); /* was 90px (90 × 1.25) */
  }

  .logo-owl-container::after {
    width: 162.5px;                    /* was 130px (130 × 1.25) */
    height: 162.5px;
    clip-path: circle(81.25px at center); /* was 65px (65 × 1.25) */
  }

  .logo-owl-container .particle-glow {
    width: 137.5px;                    /* was 110px (110 × 1.25) */
    height: 137.5px;
    clip-path: circle(68.75px at center); /* was 55px (55 × 1.25) */
  }
}
```

**Smaller Mobile Logo** (decrease size by 25%):
```css
@media (max-width: 768px) {
  .logo-owl-container {
    width: 60px;                       /* was 80px (80 × 0.75) */
    height: 60px;
  }

  .logo-owl-icon {
    width: 54px;                       /* was 72px (72 × 0.75) */
    height: 54px;
  }

  .logo-owl-container::before {
    width: 135px;                      /* was 180px (180 × 0.75) */
    height: 135px;
    clip-path: circle(67.5px at center); /* was 90px (90 × 0.75) */
  }

  .logo-owl-container::after {
    width: 97.5px;                     /* was 130px (130 × 0.75) */
    height: 97.5px;
    clip-path: circle(48.75px at center); /* was 65px (65 × 0.75) */
  }

  .logo-owl-container .particle-glow {
    width: 82.5px;                     /* was 110px (110 × 0.75) */
    height: 82.5px;
    clip-path: circle(41.25px at center); /* was 55px (55 × 0.75) */
  }
}
```

---

### 6. Disable Particle Rotation

**Location**: `D:\railway\memvid\static\css\dashboard.css` (Line 140)

**Static Particles** (no rotation):
```css
.logo-owl-container .particle-glow {
  /* Comment out or remove the animation line */
  /* animation: particleRotate 8s linear infinite; */
  animation: none;
}
```

---

### 7. Adjust Hover Effect Intensity

**Location**: `D:\railway\memvid\static\css\dashboard.css` (Lines 120-124)

**Stronger Hover Effect**:
```css
.logo-owl-icon:hover {
  filter: drop-shadow(0 0 30px rgba(0, 217, 192, 1))      /* Increased from 25px */
          drop-shadow(0 0 55px rgba(0, 217, 192, 0.7))    /* Increased from 45px and 0.6 */
          drop-shadow(0 0 80px rgba(212, 175, 55, 0.4));  /* Increased from 65px and 0.3 */
}
```

**Subtle Hover Effect**:
```css
.logo-owl-icon:hover {
  filter: drop-shadow(0 0 22px rgba(0, 217, 192, 0.9))    /* Decreased from 25px and 1.0 */
          drop-shadow(0 0 38px rgba(0, 217, 192, 0.5))    /* Decreased from 45px and 0.6 */
          drop-shadow(0 0 55px rgba(212, 175, 55, 0.25)); /* Decreased from 65px and 0.3 */
}
```

**Disable Hover Effect**:
```css
.logo-owl-icon:hover {
  /* Keep same as default state */
  filter: drop-shadow(0 0 20px rgba(0, 217, 192, 0.8))
          drop-shadow(0 0 35px rgba(0, 217, 192, 0.4))
          drop-shadow(0 0 50px rgba(212, 175, 55, 0.2));
}
```

---

## Troubleshooting

### Issue: Glow is too faint
**Solution**: Increase alpha values in gradients (see Section 1: Brighter Glow)

### Issue: Glow extends too far
**Solution**: Reduce clip-path radius values (see Section 2: Smaller Glow Area)

### Issue: Animations are distracting
**Solution**: Slow down animations or disable entirely (see Section 3)

### Issue: Mobile logo is too large/small
**Solution**: Adjust mobile breakpoint values (see Section 5)

### Issue: Glow clips neighboring elements
**Solution**: Reduce Layer 1 width from 280px to 240px

### Issue: Performance lag on mobile
**Solution**: Disable particle rotation and reduce animation complexity:
```css
@media (max-width: 768px) {
  .logo-owl-container .particle-glow {
    display: none; /* Hide particles on mobile */
  }

  .logo-owl-container::before,
  .logo-owl-container::after {
    animation: none; /* Disable animations on mobile */
  }
}
```

---

## File Paths Reference

**CSS File**:
```
D:\railway\memvid\static\css\dashboard.css
```

**HTML File**:
```
D:\railway\memvid\templates\dashboard.html
```

**Logo Image**:
```
D:\railway\memvid\static\images\owl-logo.png
```

---

## Testing Checklist

After making adjustments:

- [ ] Test in Chrome/Edge (desktop)
- [ ] Test in Firefox (desktop)
- [ ] Test in Safari (if available)
- [ ] Test on mobile viewport (DevTools or physical device)
- [ ] Verify glow doesn't overlap neighboring elements
- [ ] Check hover state still works
- [ ] Verify animations are smooth (no jank)
- [ ] Test with `prefers-reduced-motion: reduce` (accessibility)
- [ ] Clear browser cache if changes don't appear

---

**Last Updated**: 2025-10-19
**Related Document**: OWL_LOGO_INTEGRATION_GUIDE.md
