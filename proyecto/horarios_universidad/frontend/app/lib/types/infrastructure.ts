export interface Building {
  id: string
  institutionId: string
  campusId: string
  name: string
  code: string
  floors: number
  isActive: boolean
}

export interface Classroom {
  id: string
  buildingId: string
  name: string
  code: string
  capacity: number
  floor: number
  isActive: boolean
}

export interface Resource {
  id: string
  institutionId?: string
  name: string
  code: string
  description?: string
  isActive: boolean
}

export interface ClassroomAvailability {
  id: string
  classroomId: string
  dayOfWeek: number
  startTime: string
  endTime: string
  isAvailable: boolean
}
