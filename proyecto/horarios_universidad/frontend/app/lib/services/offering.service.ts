import { api } from '@/lib/api/client'
import type { ApiResponse } from '@/lib/types/common'
import type { Offering, OfferingLine, Group } from '@/lib/types/scheduling'

const BASE = '/api/v1'

export const offeringService = {
  list(institutionId: string, periodId: string) {
    return api.get<ApiResponse<Offering[]>>(
      `${BASE}/institutions/${institutionId}/periods/${periodId}/offerings`,
    )
  },

  getById(id: string) {
    return api.get<ApiResponse<Offering>>(`${BASE}/offerings/${id}`)
  },

  create(data: Partial<Offering>) {
    return api.post<ApiResponse<Offering>>(`${BASE}/offerings`, data)
  },

  update(id: string, data: Partial<Offering>) {
    return api.put<ApiResponse<Offering>>(`${BASE}/offerings/${id}`, data)
  },

  delete(id: string) {
    return api.delete(`${BASE}/offerings/${id}`)
  },

  listLines(offeringId: string) {
    return api.get<ApiResponse<OfferingLine[]>>(`${BASE}/offerings/${offeringId}/lines`)
  },

  addLine(offeringId: string, data: Partial<OfferingLine>) {
    return api.post<ApiResponse<OfferingLine>>(`${BASE}/offerings/${offeringId}/lines`, data)
  },

  updateLine(lineId: string, data: Partial<OfferingLine>) {
    return api.put<ApiResponse<OfferingLine>>(`${BASE}/offering-lines/${lineId}`, data)
  },

  generateGroups(offeringId: string) {
    return api.post<ApiResponse<Group[]>>(`${BASE}/offerings/${offeringId}/generate-groups`, {})
  },

  listGroups(institutionId: string, periodId: string) {
    return api.get<ApiResponse<Group[]>>(
      `${BASE}/institutions/${institutionId}/periods/${periodId}/groups`,
    )
  },

  getGroup(groupId: string) {
    return api.get<ApiResponse<Group>>(`${BASE}/groups/${groupId}`)
  },

  updateGroup(groupId: string, data: { expectedEnrollment?: number; modality?: string; priority?: number }) {
    return api.put<ApiResponse<Group>>(`${BASE}/groups/${groupId}`, data)
  },

  deleteGroup(groupId: string) {
    return api.delete(`${BASE}/groups/${groupId}`)
  },

  listSubjectGroups(subjectId: string, periodId: string) {
    return api.get<ApiResponse<Group[]>>(`${BASE}/subjects/${subjectId}/groups`, { period_id: periodId })
  },

  createSubjectGroup(subjectId: string, data: { periodId: string; expectedEnrollment: number; modality?: string }) {
    return api.post<ApiResponse<Group>>(`${BASE}/subjects/${subjectId}/groups`, data)
  },

  removeLine(lineId: string) {
    return api.delete(`${BASE}/offering-lines/${lineId}`)
  },

  submit(offeringId: string) {
    return api.post<ApiResponse<Offering>>(`${BASE}/offerings/${offeringId}/submit`, {})
  },

  approve(offeringId: string) {
    return api.post<ApiResponse<Offering>>(`${BASE}/offerings/${offeringId}/approve`, {})
  },

  reject(offeringId: string, observations: string) {
    return api.post<ApiResponse<Offering>>(`${BASE}/offerings/${offeringId}/reject`, { observations })
  },

  resubmit(offeringId: string) {
    return api.post<ApiResponse<Offering>>(`${BASE}/offerings/${offeringId}/resubmit`, {})
  },

  // Schedule types (institution-wide time-block configuration)
  listScheduleTypes(institutionId: string) {
    return api.get<ApiResponse<ScheduleTypeDto[]>>(`${BASE}/institutions/${institutionId}/schedule-types`)
  },

  createScheduleType(data: Partial<ScheduleTypeDto> & { institutionId: string }) {
    return api.post<ApiResponse<ScheduleTypeDto>>(`${BASE}/schedule-types`, data)
  },

  updateScheduleType(id: string, data: Partial<ScheduleTypeDto>) {
    return api.put<ApiResponse<ScheduleTypeDto>>(`${BASE}/schedule-types/${id}`, data)
  },
}

export interface ScheduleTypeDto {
  id: string
  institutionId: string
  name: string
  scheduleType: string
  activeDays: number[]
  startPeriod: number
  endPeriod: number
  slotDurationMinutes: number
  startHour: number
}
