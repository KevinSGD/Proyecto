'use client'

import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { getBlockColor } from './palette'

interface LegendItem {
  label: string
  colorIndex: number
}

interface ScheduleLegendProps {
  items: LegendItem[]
}

export default function ScheduleLegend({ items }: ScheduleLegendProps) {
  const [expanded, setExpanded] = useState(false)

  if (items.length === 0) return null

  const visible = expanded ? items : items.slice(0, 8)
  const hasMore = items.length > 8

  return (
    <div className="rounded-xl border border-border bg-card p-3">
      <button
        type="button"
        className="flex w-full items-center justify-between text-xs font-semibold text-muted-foreground"
        onClick={() => setExpanded(!expanded)}
      >
        <span>Leyenda ({items.length})</span>
        {hasMore && (expanded ? <ChevronUp className="size-3.5" /> : <ChevronDown className="size-3.5" />)}
      </button>
      <div className="mt-2 flex flex-wrap gap-2">
        {visible.map(item => {
          const color = getBlockColor(item.colorIndex)
          return (
            <div key={item.label} className="flex items-center gap-1.5">
              <div className="size-3 rounded-sm" style={{ backgroundColor: color.bg, borderLeft: `2px solid ${color.fg}` }} />
              <span className="text-[11px] text-muted-foreground">{item.label}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
