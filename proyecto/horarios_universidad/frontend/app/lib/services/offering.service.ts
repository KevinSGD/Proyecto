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

  deleteGroup(groupId: string) {
    return api.delete(`${BASE}/groups/${groupId}`)
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
}
