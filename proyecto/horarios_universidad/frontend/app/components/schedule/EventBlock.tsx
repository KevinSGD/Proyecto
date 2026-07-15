'use client'

import { useState } from 'react'
import { getBlockColor } from './palette'
import type { EnrichedAssignment } from './types'

interface EventBlockProps {
  assignment: EnrichedAssignment
  showTeacher?: boolean
  showClassroom?: boolean
  showSubject?: boolean
  compact?: boolean
  onEdit?: (assignment: EnrichedAssignment) => void
}

export default function EventBlock({ assignment, showTeacher = true, showClassroom = true, showSubject = true, compact, onEdit }: EventBlockProps) {
  const [hovered, setHovered] = useState(false)
  const color = getBlockColor(assignment.colorIndex)

  return (
    <div
      className="relative rounded-md px-2 py-1.5 text-xs mb-1 last:mb-0 cursor-pointer select-none transition-shadow"
      onClick={() => onEdit?.(assignment)}
      style={{
        backgroundColor: color.bg,
        borderLeft: `3px solid ${color.fg}`,
        boxShadow: hovered ? `0 4px 12px ${color.border}80` : 'none',
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <div className="flex items-center gap-1">
        <span className="font-semibold" style={{ color: color.fg }}>
          {assignment.startTime.slice(0, 5)}–{assignment.endTime.slice(0, 5)}
        </span>
      </div>
      {showSubject && (
        <div className="mt-0.5 font-medium truncate" style={{ color: color.fg }}>
          {compact ? assignment.subjectCode : assignment.subjectName || assignment.subjectCode}
        </div>
      )}
      {showTeacher && !compact && (
        <div className="truncate text-[10px]" style={{ color: color.fg, opacity: 0.75 }}>
          {assignment.teacherName}
        </div>
      )}
      {showClassroom && !compact && (
        <div className="truncate text-[10px]" style={{ color: color.fg, opacity: 0.75 }}>
          {assignment.classroomName}
        </div>
      )}
      {assignment.groupLabel && !compact && (
        <div className="truncate text-[10px]" style={{ color: color.fg, opacity: 0.6 }}>
          {assignment.groupLabel}
        </div>
      )}

      {hovered && (
        <div className="absolute z-50 left-full ml-2 top-0 w-56 rounded-lg bg-foreground text-card p-3 shadow-lg text-xs pointer-events-none"
          style={{ minWidth: 200 }}>
          <p className="font-semibold mb-1">{assignment.subjectName || assignment.subjectCode}</p>
          <p>{assignment.startTime.slice(0, 5)} – {assignment.endTime.slice(0, 5)}</p>
          <p className="mt-1 opacity-80">Docente: {assignment.teacherName}</p>
          <p className="opacity-80">Salón: {assignment.classroomName}</p>
          {assignment.groupLabel && <p className="opacity-80">Grupo: {assignment.groupLabel}</p>}
        </div>
      )}
    </div>
  )
}
