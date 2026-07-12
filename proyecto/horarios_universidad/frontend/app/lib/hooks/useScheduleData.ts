'use client'

import { useMemo } from 'react'
import { scheduleService } from '@/lib/services/schedule.service'
import { teacherService } from '@/lib/services/teacher.service'
import { classroomService } from '@/lib/services/classroom.service'
import { subjectService } from '@/lib/services/subject.service'
import { offeringService } from '@/lib/services/offering.service'
import { institutionService } from '@/lib/services/institution.service'
import { useAuthStore } from '@/lib/stores/auth.store'
import { useApiQuery } from './useApiQuery'
import { hashStringToIndex } from '@/components/schedule/palette'
import type { Assignment, Group } from '@/lib/types/scheduling'
import type { Instructor } from '@/lib/types/personnel'
import type { Classroom } from '@/lib/types/infrastructure'
import type { Subject } from '@/lib/types/academic'
import type { EnrichedAssignment } from '@/components/schedule/types'

const START_HOUR = 7

function periodToTime(period: number, slotMinutes: number = 60): string {
  const totalMinutes = START_HOUR * 60 + (period - 1) * slotMinutes
  const h = Math.floor(totalMinutes / 60)
  const m = totalMinutes % 60
  return `${h}:${String(m).padStart(2, '0')}`
}

export function useScheduleData(runId: string) {
  const { user } = useAuthStore()
  const institutionId = user?.institutionId ?? ''
  const { data: periodData } = useApiQuery(
    () => institutionId ? institutionService.getActivePeriod(institutionId) : Promise.resolve({ data: null } as any),
    [institutionId],
  )
  const periodId = (periodData?.data as { id: string } | null)?.id ?? ''

  const { data: assData, loading: assLoad, error: assErr, refetch } =
    useApiQuery(
      () => runId ? scheduleService.getAssignments(runId) : Promise.resolve({ data: [] as Assignment[] }),
      [runId],
    )
  const { data: tchData, loading: tchLoad } = useApiQuery(
    () => institutionId ? teacherService.list(institutionId) : Promise.resolve({ data: [] } as any),
    [institutionId],
  )
  const { data: crData, loading: crLoad } = useApiQuery(
    () => institutionId ? classroomService.listClassrooms(institutionId) : Promise.resolve({ data: [] } as any),
    [institutionId],
  )
  const { data: subData, loading: subLoad } = useApiQuery(
    () => institutionId ? subjectService.list(institutionId) : Promise.resolve({ data: [] } as any),
    [institutionId],
  )
  const { data: grpData, loading: grpLoad } = useApiQuery(
    () => (institutionId && periodId) ? offeringService.listGroups(institutionId, periodId) : Promise.resolve({ data: [] } as any),
    [institutionId, periodId],
  )

  const groups: Group[] = grpData?.data ?? []

  const rawAssignments: Assignment[] = (assData as { data?: Assignment[] })?.data ?? []
  const teachers: Instructor[] = tchData?.data ?? []
  const classrooms: Classroom[] = crData?.data ?? []
  const subjects: Subject[] = subData?.data ?? []

  const teacherMap = useMemo(() => new Map(teachers.map(t => [t.id, t])), [teachers])
  const classroomMap = useMemo(() => new Map(classrooms.map(c => [c.id, c])), [classrooms])
  const subjectMap = useMemo(() => new Map(subjects.map(s => [s.id, s])), [subjects])
  const groupMap = useMemo(() => new Map(groups.map(g => [g.id, g])), [groups])

  const enriched: EnrichedAssignment[] = useMemo(() => {
    const rows: EnrichedAssignment[] = []
    for (const a of rawAssignments) {
      const teacher = teacherMap.get(a.instructorId)
      const teacherLabel = teacher ? `${teacher.firstName} ${teacher.lastName}` : a.instructorId.slice(0, 8)

      const group = groupMap.get(a.groupId)
      const sub = group ? subjectMap.get(group.subjectId) : undefined
      const subjectName = sub?.name ?? ''
      const subjectCode = sub?.code ?? a.groupId.slice(0, 6)
      const subjectId = group?.subjectId ?? a.groupId
      const groupLabel = group ? `G${group.groupNumber}` : ''

      for (const s of a.sessions ?? []) {
        const classroom = classroomMap.get(s.classroomId)
        const startTime = periodToTime(s.startPeriod)
        const endTime = periodToTime(s.startPeriod + s.duration)

        rows.push({
          id: s.id,
          instructorId: a.instructorId,
          classroomId: s.classroomId,
          groupId: a.groupId,
          dayOfWeek: s.dayOfWeek + 1,
          startTime,
          endTime,
          subjectName,
          subjectCode,
          teacherName: teacherLabel,
          classroomName: classroom?.name ?? s.classroomId.slice(0, 8),
          groupLabel,
          colorIndex: hashStringToIndex(subjectId),
        })
      }
    }
    return rows
  }, [rawAssignments, teacherMap, classroomMap, subjectMap, groupMap])

  const loading = assLoad || tchLoad || crLoad || subLoad || grpLoad

  const legendItems = useMemo(() => {
    const seen = new Map<string, { label: string; colorIndex: number }>()
    for (const a of enriched) {
      const key = a.subjectCode
      if (!seen.has(key)) {
        seen.set(key, { label: a.subjectName || a.subjectCode, colorIndex: a.colorIndex })
      }
    }
    return [...seen.values()]
  }, [enriched])

  return {
    assignments: enriched,
    loading,
    error: assErr,
    refetch,
    teachers,
    classrooms,
    subjects,
    legendItems,
  }
}
