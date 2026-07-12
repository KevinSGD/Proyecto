export function generateCsv(headers: string[], rows: string[][]): string {
  const BOM = '﻿'
  const sep = ';'
  const escape = (v: string) => `"${v.replace(/"/g, '""')}"`
  const lines = [headers.map(escape).join(sep)]
  for (const row of rows) {
    lines.push(row.map(escape).join(sep))
  }
  return BOM + lines.join('\r\n')
}

export function downloadCsv(filename: string, csvContent: string) {
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
