'use client'

import { useMemo, useRef } from 'react'
import EventBlock from './EventBlock'
import { DAY_LABELS, WEEKDAYS } from './types'
import type { EnrichedAssignment, ViewMode, ScheduleEntity } from './types'

interface ScheduleGridProps {
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
        id = 'global'; label = 'Todos los horarios'; break
    }
    if (!map.has(id)) map.set(id, { id, label, assignments: [] })
    map.get(id)!.assignments.push(a)
  }
  return [...map.values()].sort((a, b) => a.label.localeCompare(b.label))
}

function parseHour(time: string): number {
  return parseInt(time.split(':')[0], 10)
}

function parseMinutes(time: string): number {
  const [h, m] = time.split(':').map(Number)
  return h * 60 + (m || 0)
}

export default function ScheduleGrid({ assignments, viewMode, zoom = 1, startHour = 7, endHour = 21 }: ScheduleGridProps) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const entities = useMemo(() => groupByEntity(assignments, viewMode), [assignments, viewMode])
  const hours = useMemo(() => Array.from({ length: endHour - startHour }, (_, i) => i + startHour), [startHour, endHour])

  const cellHeight = Math.round(56 * zoom)
  const hourColWidth = Math.round(72 * zoom)
  const showTeacher = viewMode !== 'docente'
  const showClassroom = viewMode !== 'salon'
  const showSubject = viewMode === 'docente' || viewMode === 'salon' || viewMode === 'global'

  return (
    <div className="space-y-6">
      {entities.map(entity => (
        <div key={entity.id} className="rounded-xl border border-border bg-card shadow-[0_1px_2px_rgba(45,45,45,0.04)] overflow-hidden">
          {viewMode !== 'global' && (
            <div className="border-b border-border px-5 py-3">
              <h3 className="font-heading text-sm font-semibold text-foreground">{entity.label}</h3>
              <p className="text-xs text-muted-foreground mt-0.5">{entity.assignments.length} asignación(es)</p>
            </div>
          )}
          <div ref={scrollRef} className="overflow-auto">
            <div
              className="grid"
              style={{
                gridTemplateColumns: `${hourColWidth}px repeat(6, minmax(${Math.round(130 * zoom)}px, 1fr))`,
                minWidth: Math.round(hourColWidth + 130 * zoom * 6),
              }}
            >
              {/* Header row - sticky */}
              <div
                className="sticky top-0 z-20 border-b border-r border-border bg-muted p-2 text-xs font-semibold text-muted-foreground"
                style={{ height: Math.round(36 * zoom) }}
              >
                Hora
              </div>
              {WEEKDAYS.map(day => (
                <div
                  key={day}
                  className="sticky top-0 z-20 border-b border-r border-border bg-muted p-2 text-center text-xs font-semibold text-muted-foreground last:border-r-0"
                  style={{ height: Math.round(36 * zoom) }}
                >
                  {DAY_LABELS[day]}
                </div>
              ))}

              {/* Hour rows */}
              {hours.map(h => (
                <div key={h} className="contents">
                  {/* Time label - sticky left */}
                  <div
                    className="sticky left-0 z-10 border-b border-r border-border bg-card p-2 text-xs text-muted-foreground font-medium"
                    style={{ minHeight: cellHeight }}
                  >
                    {`${h}:00`}
                  </div>

                  {/* Day cells */}
                  {WEEKDAYS.map(day => {
                    const cellAssignments = entity.assignments.filter(
                      a => a.dayOfWeek === day && parseHour(a.startTime) === h,
                    )
                    return (
                      <div
                        key={day}
                        className="border-b border-r border-border p-1 last:border-r-0 transition-colors hover:bg-muted/30"
                        style={{ minHeight: cellHeight }}
                      >
                        {cellAssignments.map(a => (
                          <EventBlock
                            key={a.id}
                            assignment={a}
                            showTeacher={showTeacher}
                            showClassroom={showClassroom}
                            showSubject={showSubject}
                            compact={zoom < 1}
                          />
                        ))}
                      </div>
                    )
                  })}
                </div>
              ))}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
