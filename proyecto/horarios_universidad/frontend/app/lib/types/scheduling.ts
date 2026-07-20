export type RunStatus = 'pending' | 'running' | 'optimal' | 'feasible' | 'infeasible' | 'published' | 'error' | 'blocked'

export interface ScheduleRun {
  id: string
  institutionId: string
  periodId: string
  name: string
  status: RunStatus
  startedAt?: string
  completedAt?: string
  totalAssignments: number
  conflictCount: number
  score?: number
}

export interface ExecutionLogEntry {
  id: string
  scheduleRunId: string
  eventType: string
  message: string
  timestamp?: string
  metadata?: Record<string, unknown>
}

export interface AssignmentSession {
  id: string
  assignmentId: string
  blockIndex: number
  dayOfWeek: number
  startPeriod: number
  duration: number
  classroomId: string
}

export interface Assignment {
  id: string
  scheduleRunId: string
  groupId: string
  instructorId: string
  sessions: AssignmentSession[]
}

export interface FlatAssignment {
  id: string
  instructorId: string
  classroomId: string
  dayOfWeek: number
  startPeriod: number
  duration: number
}

export interface Offering {
  id: string
  institutionId: string
  periodId: string
  areaId: string
  status: string
  observations?: string
  createdBy?: string | null
}

export interface OfferingLine {
  id: string
  offeringId: string
  subjectId: string
  numGroups: number
  expectedEnrollmentPerGroup: number
  modality: string
  scheduleTypeId: string | null
}

export interface Group {
  id: string
  offeringLineId: string
  subjectId: string
  groupNumber: number
  expectedEnrollment: number
  modality: string
  scheduleTypeId: string
  priority: number
  assignedInstructorId?: string | null
}
