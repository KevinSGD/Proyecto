'use client'

import { useEffect, useMemo, useState } from 'react'
import Button from '@/components/ui/Button'

export interface AvailabilitySlot {
  dayOfWeek: number
  period: number
  isAvailable: boolean
}

const ALL_DAY_LABELS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

function keyOf(day: number, period: number) {
  return `${day}-${period}`
}

function formatHour(hour: number) {
  const h = ((hour % 24) + 24) % 24
  return `${String(h).padStart(2, '0')}:00`
}

export default function AvailabilityGrid({
  initialSlots,
  onSave,
  saving = false,
  startPeriod = 1,
  endPeriod = 12,
  startHour = 7,
  slotDurationMinutes = 60,
  activeDays = [0, 1, 2, 3, 4],
}: {
  initialSlots: AvailabilitySlot[]
  onSave: (slots: AvailabilitySlot[]) => void
  saving?: boolean
  startPeriod?: number
  endPeriod?: number
  startHour?: number
  slotDurationMinutes?: number
  activeDays?: number[]
}) {
  const days = useMemo(
    () => [...activeDays].sort((a, b) => a - b).map(d => ({ index: d, label: ALL_DAY_LABELS[d] ?? `Día ${d}` })),
    [activeDays],
  )
  const hours = useMemo(
    () => Array.from({ length: Math.max(endPeriod - startPeriod + 1, 0) }, (_, i) => startPeriod + i),
    [startPeriod, endPeriod],
  )
  const clockLabel = (period: number) => {
    const from = startHour + ((period - startPeriod) * slotDurationMinutes) / 60
    const to = from + slotDurationMinutes / 60
    return `${formatHour(from)}–${formatHour(to)}`
  }

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

  const selectAll = () => setActive(new Set(days.flatMap(({ index: d }) => hours.map(p => keyOf(d, p)))))
  const clearAll = () => setActive(new Set())

  const handleSave = () => {
    const slots: AvailabilitySlot[] = []
    for (const { index: d } of days) {
      for (const p of hours) {
        slots.push({ dayOfWeek: d, period: p, isAvailable: active.has(keyOf(d, p)) })
      }
    }
    onSave(slots)
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs text-muted-foreground">
          Haz clic en los bloques para marcar disponibilidad ({days[0]?.label ?? ''} a {days[days.length - 1]?.label ?? ''}, horas de clase {formatHour(startHour)}–{formatHour(startHour + hours.length * slotDurationMinutes / 60)}).
        </p>
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
              {hours.map(p => (
                <th key={p} className="p-1.5 text-center text-muted-foreground font-medium whitespace-nowrap">
                  <div>Hora {p - startPeriod + 1}</div>
                  <div className="font-normal opacity-70">{clockLabel(p)}</div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {days.map(({ index: d, label }) => (
              <tr key={d} className="border-t border-border">
                <td className="p-1.5 font-medium text-foreground">{label}</td>
                {hours.map((p) => {
                  const isActive = active.has(keyOf(d, p))
                  return (
                    <td key={p} className="p-0.5 text-center">
                      <button
                        type="button"
                        onClick={() => toggle(d, p)}
                        className={`size-6 rounded transition-colors ${isActive ? 'bg-primary' : 'bg-muted hover:bg-border'}`}
                        aria-label={`${label} hora ${p - startPeriod + 1} (${clockLabel(p)}) — ${isActive ? 'disponible' : 'no disponible'}`}
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
