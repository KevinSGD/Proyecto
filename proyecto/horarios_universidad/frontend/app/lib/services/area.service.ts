import { api } from '@/lib/api/client'
import type { ApiResponse } from '@/lib/types/common'
import type { AcademicArea, AreaCreatePayload } from '@/lib/types/academic'

const BASE = '/api/v1'

export const areaService = {
  list(institutionId: string) {
    return api.get<ApiResponse<AcademicArea[]>>(`${BASE}/institutions/${institutionId}/areas`)
  },

  getById(id: string) {
    return api.get<ApiResponse<AcademicArea>>(`${BASE}/areas/${id}`)
  },

  create(data: AreaCreatePayload) {
    return api.post<ApiResponse<AcademicArea>>(`${BASE}/areas`, data)
  },

  update(id: string, data: Partial<{ name: string; code: string; description: string; isActive: boolean }>) {
    return api.put<ApiResponse<AcademicArea>>(`${BASE}/areas/${id}`, data)
  },

  delete(id: string) {
    return api.delete(`${BASE}/areas/${id}`)
  },
}
