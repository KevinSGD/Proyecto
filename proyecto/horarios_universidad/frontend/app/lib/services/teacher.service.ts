import { api } from '@/lib/api/client'
import type { ApiResponse } from '@/lib/types/common'
import type { Instructor, InstructorDetail, Contract, Availability, Specialty } from '@/lib/types/personnel'

const BASE = '/api/v1'

export const teacherService = {
  list(institutionId: string) {
    return api.get<ApiResponse<Instructor[]>>(`${BASE}/institutions/${institutionId}/teachers`)
  },

  getById(id: string) {
    return api.get<ApiResponse<Instructor>>(`${BASE}/teachers/${id}`)
  },

  getDetail(id: string) {
    return api.get<ApiResponse<InstructorDetail>>(`${BASE}/teachers/${id}/detail`)
  },

  create(data: { institutionId: string; areaId?: string; employeeCode: string; firstName: string; lastName: string; email?: string; phone?: string }) {
    return api.post<ApiResponse<Instructor>>(`${BASE}/teachers`, data)
  },

  update(id: string, data: Partial<{ areaId: string; employeeCode: string; firstName: string; lastName: string; email: string; phone: string; isActive: boolean }>) {
    return api.put<ApiResponse<Instructor>>(`${BASE}/teachers/${id}`, data)
  },

  delete(id: string) {
    return api.delete(`${BASE}/teachers/${id}`)
  },

  // Contracts
  createContract(teacherId: string, data: { contractType: string; maxDailyPeriods: number; maxWeeklyPeriods: number; minWeeklyPeriods: number; maxDays?: number }) {
    return api.post<ApiResponse<Contract>>(`${BASE}/teachers/${teacherId}/contracts`, data)
  },

  updateContract(contractId: string, data: Partial<{ contractType: string; maxDailyPeriods: number; maxWeeklyPeriods: number; minWeeklyPeriods: number; maxDays: number; isActive: boolean }>) {
    return api.put<ApiResponse<Contract>>(`${BASE}/contracts/${contractId}`, data)
  },

  // Availability
  listAvailabilities(teacherId: string, periodId?: string) {
    return api.get<ApiResponse<Availability[]>>(
      `${BASE}/teachers/${teacherId}/availability`,
      periodId ? { period_id: periodId } : undefined,
    )
  },

  setAvailability(teacherId: string, data: { slots: { dayOfWeek: number; period: number; isAvailable: boolean }[]; periodId?: string }) {
    return api.put<ApiResponse<number>>(`${BASE}/teachers/${teacherId}/availability`, data)
  },

  // Specialties
  listSpecialties(teacherId: string) {
    return api.get<ApiResponse<Specialty[]>>(`${BASE}/teachers/${teacherId}/specialties`)
  },

  assignSpecialty(teacherId: string, data: { subjectId: string; proficiencyLevel?: number }) {
    return api.post<ApiResponse<Specialty>>(`${BASE}/teachers/${teacherId}/specialties`, data)
  },

  removeSpecialty(specialtyId: string) {
    return api.delete(`${BASE}/specialties/${specialtyId}`)
  },
}
