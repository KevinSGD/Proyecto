import { api } from '@/lib/api/client'
import type { ApiResponse } from '@/lib/types/common'
import type { Building, Classroom, Resource } from '@/lib/types/infrastructure'

const BASE = '/api/v1'

export const classroomService = {
  listBuildings(campusId: string) {
    return api.get<ApiResponse<Building[]>>(`${BASE}/campuses/${campusId}/buildings`)
  },

  getBuilding(id: string) {
    return api.get<ApiResponse<Building>>(`${BASE}/buildings/${id}`)
  },

  createBuilding(data: Partial<Building>) {
    return api.post<ApiResponse<Building>>(`${BASE}/buildings`, data)
  },

  updateBuilding(id: string, data: Partial<Building>) {
    return api.put<ApiResponse<Building>>(`${BASE}/buildings/${id}`, data)
  },

  deleteBuilding(id: string) {
    return api.delete(`${BASE}/buildings/${id}`)
  },

  listClassrooms(institutionId: string) {
    return api.get<ApiResponse<Classroom[]>>(`${BASE}/institutions/${institutionId}/classrooms`)
  },

  getClassroom(id: string) {
    return api.get<ApiResponse<Classroom>>(`${BASE}/classrooms/${id}`)
  },

  createClassroom(data: Partial<Classroom> & { institutionId: string }) {
    return api.post<ApiResponse<Classroom>>(`${BASE}/classrooms`, data)
  },

  updateClassroom(id: string, data: Partial<Classroom>) {
    return api.put<ApiResponse<Classroom>>(`${BASE}/classrooms/${id}`, data)
  },

  deleteClassroom(id: string) {
    return api.delete(`${BASE}/classrooms/${id}`)
  },

  listResources(institutionId: string) {
    return api.get<ApiResponse<Resource[]>>(`${BASE}/institutions/${institutionId}/resources`)
  },

  createResource(data: Partial<Resource> & { institutionId: string }) {
    return api.post<ApiResponse<Resource>>(`${BASE}/resources`, data)
  },

  updateResource(id: string, data: Partial<Resource>) {
    return api.put<ApiResponse<Resource>>(`${BASE}/resources/${id}`, data)
  },

  deleteResource(id: string) {
    return api.delete(`${BASE}/resources/${id}`)
  },

  assignResourceToClassroom(classroomId: string, resourceId: string, quantity: number) {
    return api.post<ApiResponse<unknown>>(`${BASE}/classrooms/${classroomId}/resources`, {
      resourceId,
      quantity,
    })
  },

  listClassroomResources(classroomId: string) {
    return api.get<ApiResponse<Resource[]>>(`${BASE}/classrooms/${classroomId}/resources`)
  },

  unassignResourceFromClassroom(classroomId: string, resourceId: string) {
    return api.delete(`${BASE}/classrooms/${classroomId}/resources/${resourceId}`)
  },

  // Availability
  listAvailability(classroomId: string, periodId?: string) {
    return api.get<ApiResponse<{ id: string; classroomId: string; periodId: string | null; dayOfWeek: number; period: number; isAvailable: boolean }[]>>(
      `${BASE}/classrooms/${classroomId}/availability`,
      periodId ? { period_id: periodId } : undefined,
    )
  },

  setAvailability(classroomId: string, data: { slots: { dayOfWeek: number; period: number; isAvailable: boolean }[]; periodId?: string }) {
    return api.put<ApiResponse<{ saved: number }>>(`${BASE}/classrooms/${classroomId}/availability`, data)
  },
}
