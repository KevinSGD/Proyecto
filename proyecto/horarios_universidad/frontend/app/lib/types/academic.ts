export interface Institution {
  id: string
  name: string
  code: string
  address?: string
  phone?: string
  email?: string
  website?: string
  logoUrl?: string
  isActive: boolean
}

export interface AcademicPeriod {
  id: string
  institutionId: string
  name: string
  code: string
  startDate: string
  endDate: string
  isActive: boolean
}

export interface Coordinator {
  userId: string
  email: string
  name: string
}

export interface AcademicArea {
  id: string
  institutionId: string
  name: string
  code: string
  description: string
  isActive: boolean
  coordinator?: Coordinator | null
}

export interface AreaCreatePayload {
  institutionId: string
  name: string
  code: string
  description?: string
  coordinator: {
    email: string
    name: string
    password: string
  }
}

export interface Subject {
  id: string
  institutionId: string
  areaId?: string | null
  code: string
  name: string
  creditHours: number
  weeklyHours: number
  modalityDefault: string
  isActive: boolean
  // Legacy display fields (not persisted by backend)
  credits?: number
  semester?: number
  type?: 'theoretical' | 'practical' | 'theoretical-practical'
  requirements?: string
  observations?: string
}
