export type ContractType = 'full-time' | 'part-time' | 'adjunct'
export type InstructorStatus = 'active' | 'inactive'

export interface Instructor {
  id: string
  institutionId: string
  employeeCode: string
  firstName: string
  lastName: string
  email: string
  phone?: string
  isActive: boolean
  // Enriched fields (from detail endpoint or joined)
  contractType?: ContractType | string
  maxWeeklyHours?: number
  assignedHours?: number
}

export interface Contract {
  id: string
  instructorId: string
  contractType: string
  startDate?: string | null
  endDate?: string | null
  maxDailyPeriods: number
  maxWeeklyPeriods: number
  minWeeklyPeriods: number
  maxDays?: number | null
  isActive: boolean
}

export interface InstructorDetail extends Instructor {
  contracts: Contract[]
  specialties: Specialty[]
  qualifications: Qualification[]
}

export interface Qualification {
  id: string
  instructorId: string
  qualificationType: string
  title: string
  institutionName: string
  yearObtained?: number | null
}

export interface Availability {
  id: string
  instructorId: string
  periodId?: string | null
  dayOfWeek: number
  period: number
  isAvailable: boolean
}

export interface Specialty {
  id: string
  instructorId: string
  subjectId: string
  proficiencyLevel: number
}

export interface InstructorPreference {
  id: string
  instructorId: string
  periodId?: string | null
  groupId?: string | null
  subjectId?: string | null
  score: number
}
