# Style Guide & Design Tokens

## Institutional Palette

| Token | Value | Usage |
|-------|-------|-------|
| `--primary` | `#A6061B` | Buttons, links, active states, brand accents |
| `--primary-hover` | `#8A0517` | Button hover |
| `--primary-soft` | `#FCEBED` | Light primary backgrounds |
| `--primary-foreground` | `#FFFFFF` | Text on primary backgrounds |
| `--background` | `#F8F9FA` | Page background |
| `--foreground` | `#2D2D2D` | Primary text |
| `--card` | `#FFFFFF` | Card backgrounds |
| `--muted` | `#F1F2F4` | Muted backgrounds, table headers |
| `--muted-foreground` | `#6B6F76` | Secondary text |
| `--border` | `#E6E8EB` | Borders, dividers |

## Semantic Colors

| Token | Value | Usage |
|-------|-------|-------|
| `--success` / `--success-soft` | `#1E8E3E` / `#E7F4EC` | Positive states |
| `--warning` / `--warning-soft` | `#C77700` / `#FBF0DE` | Caution states |
| `--danger` / `--danger-soft` | `#A6061B` / `#FCEBED` | Error/destructive states |

## Brand Scale

```
brand-900: #7A0514  (darkest)
brand-700: #A6061B  (primary)
brand-500: #C7304A
brand-100: #FCEBED
brand-50:  #FBF3F4  (lightest)
```

## Typography

| Role | Font | Weight | Usage |
|------|------|--------|-------|
| Headings | Sora | 600 (semibold) | `h1`–`h6`, card titles, page headers |
| Body | DM Sans | 400/500/600 | All other text |
| Mono | system monospace | 400 | Codes, IDs |

Base font size: **14px**, line-height: **1.5**.

Headings have `letter-spacing: -0.01em`.

## Radius

| Token | Computed | Usage |
|-------|----------|-------|
| `--radius` | `0.75rem` (12px) | Base radius |
| `--radius-sm` | `7.2px` | Small elements |
| `--radius-md` | `9.6px` | Medium elements |
| `--radius-lg` | `12px` | Cards, modals |
| `--radius-xl` | `16.8px` | Large containers |

## Elevation

| Level | Shadow | Usage |
|-------|--------|-------|
| `--shadow-sm` | `0 1px 2px rgba(45,45,45,0.04)` | Cards at rest |
| `--shadow-md` | `0 4px 12px rgba(45,45,45,0.06)` | Interactive cards on hover |

## Component Variants (CVA)

### Button

| Variant | Appearance |
|---------|------------|
| `primary` | Solid primary bg, white text |
| `secondary` | Muted bg, foreground text |
| `outline` | Border only, foreground text |
| `ghost` | Transparent, foreground text |
| `danger` | Solid danger bg, white text |

### Badge

| Variant | Colors |
|---------|--------|
| `neutral` | muted bg, strong text |
| `brand` | primary-soft bg, primary text |
| `success` | success-soft bg, success text |
| `warning` | warning-soft bg, warning text |
| `danger` | danger-soft bg, danger text |
| `info` | blue-50 bg, blue-700 text |

## Schedule Palette

12-color palette for schedule event blocks, each with `bg`, `fg`, `border`:

1. Red (#FCEBED / #A6061B) — institutional
2. Blue (#DBEAFE / #1E40AF)
3. Green (#D1FAE5 / #065F46)
4. Amber (#FEF3C7 / #92400E)
5. Purple (#EDE9FE / #5B21B6)
6. Pink (#FCE7F3 / #9D174D)
7. Cyan (#CFFAFE / #155E75)
8. Indigo (#E0E7FF / #3730A3)
9. Orange (#FFEDD5 / #9A3412)
10. Teal (#CCFBF1 / #134E4A)
11. Red-light (#FEE2E2 / #991B1B)
12. Green-light (#F0FDF4 / #166534)

Colors are assigned deterministically via `hashStringToIndex(subjectId)`.

## Tailwind v4 Setup

```css
@import 'tailwindcss';
@custom-variant dark (&:is(.dark *));
@theme inline { /* all tokens mapped here */ }
```

CSS custom properties defined in `:root`, mapped to Tailwind utilities via `--color-*` in `@theme inline`.

## Scrollbar

Custom WebKit scrollbar: 8px width, transparent track, neutral-200 thumb with neutral-400 hover.

## Animations

| Class | Animation | Duration |
|-------|-----------|----------|
| `fade-in-up` | Fade + translate Y 8px | 300ms ease-out |
| `slide-in-right` | Slide from right 24px | 250ms cubic-bezier |
| `modal-pop` | Scale 0.96 → 1 | 180ms cubic-bezier |
| `animate-spin` | 360deg rotation | 1s linear infinite |
