import { api } from '@/lib/api/client'
import type { ApiResponse } from '@/lib/types/common'
import type { ScheduleRun, Assignment, ExecutionLogEntry } from '@/lib/types/scheduling'

const BASE = '/api/v1'

export const scheduleService = {
  listRuns(institutionId: string, periodId: string) {
    return api.get<ApiResponse<ScheduleRun[]>>(
      `${BASE}/institutions/${institutionId}/periods/${periodId}/schedule-runs`,
    )
  },

  getRun(id: string) {
    return api.get<ApiResponse<ScheduleRun>>(`${BASE}/schedule-runs/${id}`)
  },

  getRunDetail(id: string) {
    return api.get<ApiResponse<ScheduleRun>>(`${BASE}/schedule-runs/${id}/detail`)
  },

  getAssignments(runId: string) {
    return api.get<ApiResponse<Assignment[]>>(`${BASE}/schedule-runs/${runId}/assignments`)
  },

  getLogs(runId: string) {
    return api.get<ApiResponse<ExecutionLogEntry[]>>(`${BASE}/schedule-runs/${runId}/logs`)
  },

  generate(data: { institutionId: string; periodId: string }) {
    return api.post<ApiResponse<ScheduleRun>>(`${BASE}/schedule/generate`, data)
  },

  publish(runId: string) {
    return api.post<ApiResponse<ScheduleRun>>(`${BASE}/schedule/publish`, { scheduleRunId: runId })
  },

  block(runId: string) {
    return api.post<ApiResponse<ScheduleRun>>(`${BASE}/schedule/block`, { scheduleRunId: runId })
  },

  validate(institutionId: string, periodId: string) {
    return api.post<ApiResponse<unknown>>(`${BASE}/schedule/validate`, { institutionId, periodId })
  },

  updateSessionBlock(blockId: string, data: {
    dayOfWeek?: number
    startPeriod?: number
    duration?: number
    classroomId?: string
    instructorId?: string
  }) {
    return api.patch<ApiResponse<unknown>>(`${BASE}/session-blocks/${blockId}`, data)
  },

  dashboard(institutionId: string) {
    return api.get<ApiResponse<Record<string, unknown>>>(
      `${BASE}/institutions/${institutionId}/dashboard`,
    )
  },
}
