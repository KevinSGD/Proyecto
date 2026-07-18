'use client'

import { useEffect, useState } from 'react'
import Button from '@/components/ui/Button'

export interface AvailabilitySlot {
  dayOfWeek: number
  period: number
  isAvailable: boolean
}

const DAY_LABELS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
const PERIODS = Array.from({ length: 12 }, (_, i) => i + 1)

function keyOf(day: number, period: number) {
  return `${day}-${period}`
}

export default function AvailabilityGrid({
  initialSlots,
  onSave,
  saving = false,
}: {
  initialSlots: AvailabilitySlot[]
  onSave: (slots: AvailabilitySlot[]) => void
  saving?: boolean
}) {
  const [active, setActive] = useState<Set<string>>(
    () => new Set(initialSlots.filter(s => s.isAvailable).map(s => keyOf(s.dayOfWeek, s.period))),
  )

  useEffect(() => {
    setActive(new Set(initialSlots.filter(s => s.isAvailable).map(s => keyOf(s.dayOfWeek, s.period))))
  }, [initialSlots])

  const toggle = (day: number, period: number) => {
    const key = keyOf(day, period)
    setActive((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  const selectAll = () => setActive(new Set(DAY_LABELS.flatMap((_, d) => PERIODS.map(p => keyOf(d, p)))))
  const clearAll = () => setActive(new Set())

  const handleSave = () => {
    const slots: AvailabilitySlot[] = []
    for (let d = 0; d < DAY_LABELS.length; d++) {
      for (const p of PERIODS) {
        slots.push({ dayOfWeek: d, period: p, isAvailable: active.has(keyOf(d, p)) })
      }
    }
    onSave(slots)
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs text-muted-foreground">Haz clic en los bloques para marcar disponibilidad (Lunes a Viernes, periodos 1–12).</p>
        <div className="flex gap-3 shrink-0">
          <button type="button" onClick={selectAll} className="text-xs font-medium text-primary hover:underline">Seleccionar todo</button>
          <button type="button" onClick={clearAll} className="text-xs font-medium text-muted-foreground hover:underline">Limpiar</button>
        </div>
      </div>
      <div className="overflow-x-auto rounded-lg border border-border">
        <table className="w-full text-xs border-collapse">
          <thead>
            <tr className="bg-muted/50">
              <th className="p-1.5 text-left text-muted-foreground font-medium w-20">Día</th>
              {PERIODS.map(p => <th key={p} className="p-1.5 text-center text-muted-foreground font-medium">{p}</th>)}
            </tr>
          </thead>
          <tbody>
            {DAY_LABELS.map((label, d) => (
              <tr key={d} className="border-t border-border">
                <td className="p-1.5 font-medium text-foreground">{label}</td>
                {PERIODS.map((p) => {
                  const isActive = active.has(keyOf(d, p))
                  return (
                    <td key={p} className="p-0.5 text-center">
                      <button
                        type="button"
                        onClick={() => toggle(d, p)}
                        className={`size-6 rounded transition-colors ${isActive ? 'bg-primary' : 'bg-muted hover:bg-border'}`}
                        aria-label={`${label} periodo ${p} — ${isActive ? 'disponible' : 'no disponible'}`}
                        aria-pressed={isActive}
                      />
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex justify-end pt-1">
        <Button onClick={handleSave} loading={saving}>Guardar disponibilidad</Button>
      </div>
    </div>
  )
}
