const PALETTE = [
  { bg: '#FCEBED', fg: '#A6061B', border: '#F5C6CB' },
  { bg: '#DBEAFE', fg: '#1E40AF', border: '#93C5FD' },
  { bg: '#D1FAE5', fg: '#065F46', border: '#6EE7B7' },
  { bg: '#FEF3C7', fg: '#92400E', border: '#FCD34D' },
  { bg: '#EDE9FE', fg: '#5B21B6', border: '#C4B5FD' },
  { bg: '#FCE7F3', fg: '#9D174D', border: '#F9A8D4' },
  { bg: '#CFFAFE', fg: '#155E75', border: '#67E8F9' },
  { bg: '#E0E7FF', fg: '#3730A3', border: '#A5B4FC' },
  { bg: '#FFEDD5', fg: '#9A3412', border: '#FDBA74' },
  { bg: '#CCFBF1', fg: '#134E4A', border: '#5EEAD4' },
  { bg: '#FEE2E2', fg: '#991B1B', border: '#FCA5A5' },
  { bg: '#F0FDF4', fg: '#166534', border: '#86EFAC' },
] as const

export function getBlockColor(index: number) {
  return PALETTE[index % PALETTE.length]
}

export function hashStringToIndex(str: string): number {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash + str.charCodeAt(i)) | 0
  }
  return Math.abs(hash) % PALETTE.length
}

export { PALETTE }
