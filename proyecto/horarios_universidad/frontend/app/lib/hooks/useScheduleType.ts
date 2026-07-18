'use client'

import { offeringService } from '@/lib/services/offering.service'
import { useAuthStore } from '@/lib/stores/auth.store'
import { useApiQuery } from './useApiQuery'

export interface ScheduleTypeConfig {
  id: string
  startHour: number
  startPeriod: number
  endPeriod: number
  slotDurationMinutes: number
  activeDays: number[]
}

const DEFAULT_CONFIG: ScheduleTypeConfig = {
  id: '',
  startHour: 7,
  startPeriod: 1,
  endPeriod: 12,
  slotDurationMinutes: 60,
  activeDays: [0, 1, 2, 3, 4],
}

/** Reads the institution's active time-block configuration (jornada).
 *
 * Falls back to the historical defaults (7am start, 12 hourly blocks,
 * Lunes-Viernes) if the institution has no schedule type configured yet.
 */
export function useScheduleType() {
  const { user } = useAuthStore()
  const institutionId = user?.institutionId ?? ''

  const { data, loading, refetch } = useApiQuery(
    () => institutionId ? offeringService.listScheduleTypes(institutionId) : Promise.resolve({ data: [] } as any),
    [institutionId],
  )

  const first = (data?.data ?? [])[0]
  const config: ScheduleTypeConfig = first
    ? {
        id: first.id,
        startHour: first.startHour,
        startPeriod: first.startPeriod,
        endPeriod: first.endPeriod,
        slotDurationMinutes: first.slotDurationMinutes,
        activeDays: first.activeDays,
      }
    : DEFAULT_CONFIG

  return { config, loading, refetch }
}
