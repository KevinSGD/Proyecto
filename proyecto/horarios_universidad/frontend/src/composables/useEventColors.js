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
// 8 slots cycle through all MD3 color roles for maximum visual distinction
export const EVENT_COLORS = [
  { bg: 'bg-primary/15',              border: 'border-primary/50',              text: 'text-primary' },
  { bg: 'bg-tertiary/15',             border: 'border-tertiary/50',             text: 'text-tertiary' },
  { bg: 'bg-secondary/15',            border: 'border-secondary/50',            text: 'text-secondary' },
  { bg: 'bg-tertiary-fixed/10',       border: 'border-tertiary-fixed/50',       text: 'text-tertiary-fixed' },
  { bg: 'bg-primary-fixed/10',        border: 'border-primary-fixed/50',        text: 'text-primary-fixed' },
  { bg: 'bg-secondary-fixed/10',      border: 'border-secondary-fixed/50',      text: 'text-secondary-fixed' },
  { bg: 'bg-error/10',                border: 'border-error/40',                text: 'text-error' },
  { bg: 'bg-on-primary-container/10', border: 'border-on-primary-container/30', text: 'text-on-primary-container' },
]

// Light-mode palette — higher opacity/contrast for readability on light backgrounds
export const EVENT_COLORS_LIGHT = [
  { bg: 'bg-primary/25',             border: 'border-primary/60',              text: 'text-primary' },
  { bg: 'bg-tertiary/25',            border: 'border-tertiary/60',             text: 'text-tertiary' },
  { bg: 'bg-secondary/25',           border: 'border-secondary/60',            text: 'text-secondary' },
  { bg: 'bg-tertiary-container/55',  border: 'border-tertiary/55',             text: 'text-on-tertiary-container' },
  { bg: 'bg-primary-container/55',   border: 'border-primary/55',              text: 'text-on-primary-container' },
  { bg: 'bg-secondary-container/55', border: 'border-secondary/55',            text: 'text-on-secondary-container' },
  { bg: 'bg-error/20',               border: 'border-error/55',                text: 'text-error' },
  { bg: 'bg-primary-fixed/35',       border: 'border-primary-fixed/60',        text: 'text-on-primary-fixed' },
]

/**
 * Hex palette for WeeklyCalendar (raw DOM style usage).
 * All colors are toned-down analogous/complementary hues of the
 * institutional periwinkle-blue system. Saturation kept ≤70 % so
 * they read clearly on dark navy (#0f1829) without visual clashing.
 */
export const HEX_PALETTE = [
  '#6382e6', // periwinkle (primary)
  '#8f7cf5', // soft violet
  '#58a9c5', // cornflower sky
  '#c99848', // warm amber
  '#5aac96', // muted teal
  '#d47a8b', // dusty rose
  '#78ab6e', // sage green
  '#c77856', // terracotta
  '#7497d8', // medium blue
  '#b08ae6', // medium lavender
  '#6ab4b4', // steel cyan
  '#c4a042', // muted gold
  '#8ab87a', // light sage
  '#d07f5e', // warm coral
  '#6882c8', // steel blue
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
