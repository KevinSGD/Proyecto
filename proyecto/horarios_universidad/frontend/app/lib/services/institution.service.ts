import { api } from '@/lib/api/client'
import type { ApiResponse } from '@/lib/types/common'
import type { Institution } from '@/lib/types/academic'

const BASE = '/api/v1/institutions'

export const institutionService = {
  list() {
    return api.get<ApiResponse<Institution[]>>(BASE)
  },

  getById(id: string) {
    return api.get<ApiResponse<Institution>>(`${BASE}/${id}`)
  },

  create(data: Partial<Institution>) {
    return api.post<ApiResponse<Institution>>(BASE, data)
  },

  update(id: string, data: Partial<Institution>) {
    return api.put<ApiResponse<Institution>>(`${BASE}/${id}`, data)
  },

  delete(id: string) {
    return api.delete(`${BASE}/${id}`)
  },

  listCampuses(institutionId: string) {
    return api.get<ApiResponse<{ id: string; name: string; code: string }[]>>(`${BASE}/${institutionId}/campuses`)
  },

  listPeriods(institutionId: string) {
    return api.get<ApiResponse<{ id: string; name: string; code: string; isActive: boolean }[]>>(`${BASE}/${institutionId}/periods`)
  },

  getActivePeriod(institutionId: string) {
    return api.get<ApiResponse<{ id: string; name: string; code: string }>>(`${BASE}/${institutionId}/periods/active`)
  },

  createPeriod(institutionId: string, data: { name: string; year: number; periodNumber: number }) {
    return api.post<ApiResponse<{ id: string; name: string }>>(`${BASE}/${institutionId}/periods`, { institutionId, ...data })
  },
}
