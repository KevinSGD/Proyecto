'use client'

import { useMemo } from 'react'
import { getBlockColor } from './palette'
import { DAY_LABELS, WEEKDAYS } from './types'
import type { EnrichedAssignment, ViewMode, ScheduleEntity } from './types'

interface GanttGridProps {
  assignments: EnrichedAssignment[]
  viewMode: ViewMode
  zoom?: number
  startHour?: number
  endHour?: number
}

function groupByEntity(assignments: EnrichedAssignment[], viewMode: ViewMode): ScheduleEntity[] {
  const map = new Map<string, ScheduleEntity>()
  for (const a of assignments) {
    let id: string
    let label: string
    switch (viewMode) {
      case 'docente':
        id = a.instructorId; label = a.teacherName; break
      case 'salon':
        id = a.classroomId; label = a.classroomName; break
      case 'materia':
        id = a.groupId; label = a.subjectName || a.subjectCode; break
      case 'grupo':
        id = `${a.groupId}-${a.groupLabel}`; label = `${a.subjectCode} – ${a.groupLabel}`; break
      case 'area':
        id = a.groupId; label = a.subjectName || a.subjectCode; break
      case 'global':
      default:
        id = 'global'; label = 'Todos'; break
    }
    if (!map.has(id)) map.set(id, { id, label, assignments: [] })
    map.get(id)!.assignments.push(a)
  }
  return [...map.values()].sort((a, b) => a.label.localeCompare(b.label))
}

function parseMinutes(time: string): number {
  const [h, m] = time.split(':').map(Number)
  return h * 60 + (m || 0)
}

export default function GanttGrid({ assignments, viewMode, zoom = 1, startHour = 7, endHour = 21 }: GanttGridProps) {
  const entities = useMemo(() => groupByEntity(assignments, viewMode), [assignments, viewMode])
  const totalMinutes = (endHour - startHour) * 60
  const hours = useMemo(() => Array.from({ length: endHour - startHour + 1 }, (_, i) => i + startHour), [startHour, endHour])

  const labelWidth = Math.round(160 * zoom)
  const timelineWidth = Math.round(900 * zoom)
  const rowHeight = Math.round(40 * zoom)

  return (
    <div className="space-y-6">
      {WEEKDAYS.map(day => {
        const dayAssignments = assignments.filter(a => a.dayOfWeek === day)
        if (dayAssignments.length === 0 && viewMode !== 'global') return null

        const dayEntities = entities
          .map(e => ({
            ...e,
            assignments: e.assignments.filter(a => a.dayOfWeek === day),
          }))
          .filter(e => e.assignments.length > 0)

        if (dayEntities.length === 0) return null

        return (
          <div key={day} className="rounded-xl border border-border bg-card shadow-[0_1px_2px_rgba(45,45,45,0.04)] overflow-hidden">
            <div className="border-b border-border px-5 py-3 bg-muted">
              <h3 className="font-heading text-sm font-semibold text-foreground">{DAY_LABELS[day]}</h3>
              <p className="text-xs text-muted-foreground mt-0.5">{dayAssignments.length} asignación(es)</p>
            </div>

            <div className="overflow-x-auto">
              <div style={{ minWidth: labelWidth + timelineWidth }}>
                {/* Time header */}
                <div className="flex border-b border-border">
                  <div
                    className="sticky left-0 z-10 shrink-0 border-r border-border bg-muted px-3 py-2 text-xs font-semibold text-muted-foreground"
                    style={{ width: labelWidth }}
                  >
                    {viewMode === 'docente' ? 'Docente' : viewMode === 'salon' ? 'Salón' : 'Entidad'}
                  </div>
                  <div className="relative flex-1" style={{ width: timelineWidth }}>
                    <div className="flex">
                      {hours.slice(0, -1).map(h => (
                        <div
                          key={h}
                          className="border-r border-border px-1 py-2 text-center text-[10px] font-medium text-muted-foreground"
                          style={{ width: timelineWidth / (endHour - startHour) }}
                        >
                          {`${h}:00`}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Entity rows */}
                {dayEntities.map(entity => (
                  <div key={entity.id} className="flex border-b border-border last:border-b-0">
                    <div
                      className="sticky left-0 z-10 shrink-0 border-r border-border bg-card px-3 flex items-center text-xs font-medium text-foreground truncate"
                      style={{ width: labelWidth, height: rowHeight }}
                    >
                      {entity.label}
                    </div>
                    <div className="relative flex-1" style={{ width: timelineWidth, height: rowHeight }}>
                      {/* Gridlines */}
                      {hours.slice(0, -1).map(h => (
                        <div
                          key={h}
                          className="absolute top-0 bottom-0 border-r border-border/40"
                          style={{ left: `${((h - startHour) / (endHour - startHour)) * 100}%` }}
                        />
                      ))}

                      {/* Assignment bars */}
                      {entity.assignments.map(a => {
                        const start = parseMinutes(a.startTime)
                        const end = parseMinutes(a.endTime)
                        const left = ((start - startHour * 60) / totalMinutes) * 100
                        const width = ((end - start) / totalMinutes) * 100
                        const color = getBlockColor(a.colorIndex)

                        return (
                          <div
                            key={a.id}
                            className="absolute top-1 bottom-1 rounded-md flex items-center px-2 text-[10px] font-medium cursor-grab transition-shadow hover:shadow-md overflow-hidden"
                            style={{
                              left: `${left}%`,
                              width: `${width}%`,
                              backgroundColor: color.bg,
                              borderLeft: `3px solid ${color.fg}`,
                              color: color.fg,
                            }}
                            title={`${a.subjectName || a.subjectCode} — ${a.startTime.slice(0, 5)}–${a.endTime.slice(0, 5)} — ${a.teacherName} — ${a.classroomName}`}
                          >
                            <span className="truncate">
                              {a.subjectCode} {a.startTime.slice(0, 5)}–{a.endTime.slice(0, 5)}
                            </span>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
