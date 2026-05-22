/**
 * Shared event color palette — single source of truth for CalendarioPage and WeeklyCalendar.
 *
 * All colors verified WCAG AA (≥4.5:1) for dark text (#0b1326) on these backgrounds,
 * and chosen to be visually distinct on dark navy surfaces (#0f1829–#171f33).
 *
 * Tailwind class palette (for CalendarioPage / reactive components):
 * Raw hex palette (for WeeklyCalendar table cells):
 */

// Tailwind-class palette — dark mode (low opacity on dark navy surfaces)
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

// Light-mode palette — higher opacity/contrast for readability on light backgrounds
export const EVENT_COLORS_LIGHT = [
  { bg: 'bg-primary/30',              border: 'border-primary/70',              text: 'text-primary' },
  { bg: 'bg-secondary/25',            border: 'border-secondary/70',            text: 'text-secondary' },
  { bg: 'bg-tertiary/25',             border: 'border-tertiary/70',             text: 'text-tertiary' },
  { bg: 'bg-primary-container/60',    border: 'border-primary/60',              text: 'text-on-primary-container' },
  { bg: 'bg-secondary-container/60',  border: 'border-secondary/60',            text: 'text-on-secondary-container' },
  { bg: 'bg-tertiary-container/60',   border: 'border-tertiary/60',             text: 'text-on-tertiary-container' },
  { bg: 'bg-error/20',                border: 'border-error/60',                text: 'text-error' },
  { bg: 'bg-primary-fixed/40',        border: 'border-primary-fixed/70',        text: 'text-on-primary-fixed' },
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
 * @param {string} tema  'dark' | 'light' — selects the appropriate palette
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
