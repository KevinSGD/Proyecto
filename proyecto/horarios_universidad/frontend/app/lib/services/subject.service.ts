import { api } from '@/lib/api/client'
import type { ApiResponse } from '@/lib/types/common'
import type { Subject } from '@/lib/types/academic'

const BASE = '/api/v1'

export const subjectService = {
  list(institutionId: string) {
    return api.get<ApiResponse<Subject[]>>(`${BASE}/institutions/${institutionId}/subjects`)
  },

  getById(id: string) {
    return api.get<ApiResponse<Subject>>(`${BASE}/subjects/${id}`)
  },

  create(data: Partial<Subject> & { institutionId: string }) {
    return api.post<ApiResponse<Subject>>(`${BASE}/subjects`, data)
  },

  update(id: string, data: Partial<Subject>) {
    return api.put<ApiResponse<Subject>>(`${BASE}/subjects/${id}`, data)
  },

  delete(id: string) {
    return api.delete(`${BASE}/subjects/${id}`)
  },
}
