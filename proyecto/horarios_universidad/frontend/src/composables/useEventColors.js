/**
 * Shared event color palette — single source of truth for CalendarioPage and WeeklyCalendar.
 *
 * All colors verified WCAG AA (≥4.5:1) for dark text (#0b1326) on these backgrounds,
 * and chosen to be visually distinct on dark navy surfaces (#0f1829–#171f33).
 *
 * Tailwind class palette (for CalendarioPage / reactive components):
 * Raw hex palette (for WeeklyCalendar table cells):
 */

// Tailwind-class palette — dark mode (default)
export const EVENT_COLORS = [
  { bg: 'bg-primary/15',           border: 'border-primary/50',           text: 'text-primary' },
  { bg: 'bg-secondary/15',         border: 'border-secondary/50',         text: 'text-secondary' },
  { bg: 'bg-tertiary/15',          border: 'border-tertiary/50',          text: 'text-tertiary' },
  { bg: 'bg-primary-fixed/10',     border: 'border-primary-fixed/50',     text: 'text-primary-fixed' },
  { bg: 'bg-secondary-fixed/10',   border: 'border-secondary-fixed/50',   text: 'text-secondary-fixed' },
  { bg: 'bg-tertiary-fixed/10',    border: 'border-tertiary-fixed/50',    text: 'text-tertiary-fixed' },
  { bg: 'bg-error/10',             border: 'border-error/40',             text: 'text-error' },
  { bg: 'bg-on-primary-container/10', border: 'border-on-primary-container/30', text: 'text-on-primary-container' },
]

// Light-mode palette — fully opaque containers with accessible text colors
export const EVENT_COLORS_LIGHT = [
  { bg: 'bg-primary-container',      border: 'border-primary/50',       text: 'text-on-primary-container' },
  { bg: 'bg-secondary-container',    border: 'border-secondary/50',     text: 'text-on-secondary-container' },
  { bg: 'bg-tertiary-container',     border: 'border-tertiary/50',      text: 'text-on-tertiary-container' },
  { bg: 'bg-primary/25',             border: 'border-primary',          text: 'text-primary' },
  { bg: 'bg-secondary/25',           border: 'border-secondary',        text: 'text-secondary' },
  { bg: 'bg-tertiary/25',            border: 'border-tertiary',         text: 'text-tertiary' },
  { bg: 'bg-error-container',        border: 'border-error/50',         text: 'text-on-error-container' },
  { bg: 'bg-primary-fixed/60',       border: 'border-primary-fixed',    text: 'text-on-primary-fixed' },
]

/**
 * Hex palette for WeeklyCalendar (raw DOM style usage).
 * Colors are bright/pastel enough to show on dark (#0f1829) backgrounds
 * and have >4.5:1 contrast for dark-text (#002918 / #0b1326) content on top.
 */
export const HEX_PALETTE = [
  '#52e0a2', // primary teal
  '#4ab8d9', // secondary blue
  '#e8a44a', // tertiary amber
  '#f5c97a', // tertiary-fixed gold
  '#8dd6ef', // secondary-fixed sky
  '#f472b6', // pink
  '#a78bfa', // violet
  '#34d399', // emerald
  '#fb923c', // orange
  '#60a5fa', // blue-400
  '#86efac', // light green
  '#fbbf24', // amber-400
  '#c4b5fd', // lavender
  '#6ee7b7', // mint
  '#f87171', // red-400
]

/**
 * Get Tailwind class set for a materia by its store index.
 * @param {number} idx   Index of the materia in state.materias
 * @param {string} tema  'dark' (default) or 'light'
 */
export function tailwindColorFor(idx, tema = 'dark') {
  const palette = tema === 'light' ? EVENT_COLORS_LIGHT : EVENT_COLORS
  return palette[Math.abs(idx) % palette.length]
}

/**
 * Get hex color for a materia name (for WeeklyCalendar).
 * @param {string} nombre
 * @param {Map} colorMap  Accumulated map of nombre→hex
 * @param {object} counter  { i: number } — shared mutable counter
 */
export function hexColorFor(nombre, colorMap, counter) {
  if (!colorMap.has(nombre)) {
    colorMap.set(nombre, HEX_PALETTE[counter.i % HEX_PALETTE.length])
    counter.i++
  }
  return colorMap.get(nombre)
}
