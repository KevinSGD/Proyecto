export type ViewMode = 'docente' | 'salon' | 'materia' | 'grupo' | 'area' | 'global'
export type GridType = 'weekly' | 'gantt'

export interface EnrichedAssignment {
  id: string
  instructorId: string
  classroomId: string
  groupId: string
  subjectId: string
  dayOfWeek: number
  startTime: string
  endTime: string
  subjectName: string
  subjectCode: string
  teacherName: string
  classroomName: string
  groupLabel: string
  colorIndex: number
}

export interface ScheduleEntity {
  id: string
  label: string
  assignments: EnrichedAssignment[]
}

export const VIEW_MODE_LABELS: Record<ViewMode, string> = {
  docente: 'Por docente',
  salon: 'Por salón',
  materia: 'Por materia',
  grupo: 'Por grupo',
  area: 'Por área',
  global: 'Vista global',
}

export const DAY_LABELS = ['', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
export const WEEKDAYS = [1, 2, 3, 4, 5, 6] as const
