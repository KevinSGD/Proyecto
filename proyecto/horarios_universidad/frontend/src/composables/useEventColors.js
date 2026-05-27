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

// Light-mode palette — soft neutral grays, subtle distinction between materias
export const EVENT_COLORS_LIGHT = [
  { bg: 'bg-slate-100',   border: 'border-slate-300',   text: 'text-slate-700' },
  { bg: 'bg-zinc-100',    border: 'border-zinc-300',    text: 'text-zinc-700' },
  { bg: 'bg-stone-100',   border: 'border-stone-300',   text: 'text-stone-700' },
  { bg: 'bg-neutral-100', border: 'border-neutral-300', text: 'text-neutral-700' },
  { bg: 'bg-gray-100',    border: 'border-gray-300',    text: 'text-gray-700' },
  { bg: 'bg-slate-200',   border: 'border-slate-400',   text: 'text-slate-800' },
  { bg: 'bg-zinc-200',    border: 'border-zinc-400',    text: 'text-zinc-800' },
  { bg: 'bg-stone-200',   border: 'border-stone-400',   text: 'text-stone-800' },
]

/**
 * Hex palette for WeeklyCalendar (raw DOM style usage).
 * All colors are toned-down analogous/complementary hues of the
 * institutional periwinkle-blue system. Saturation kept ≤70 % so
 * they read clearly on dark navy (#0f1829) without visual clashing.
 */
export const HEX_PALETTE = [
  '#f5f5f5', // neutral white-gray
  '#eeeeee',
  '#e8e8e8',
  '#e0e0e0',
  '#d9d9d9',
  '#f5f5f5',
  '#eeeeee',
  '#e8e8e8',
  '#e0e0e0',
  '#d9d9d9',
  '#f5f5f5',
  '#eeeeee',
  '#e8e8e8',
  '#e0e0e0',
  '#d9d9d9',
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
