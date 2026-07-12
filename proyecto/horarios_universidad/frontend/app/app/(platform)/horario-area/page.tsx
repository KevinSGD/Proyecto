'use client'

import { useState } from 'react'
import { Calendar, Users } from 'lucide-react'
import { FilterSelect } from '@/components/ui/Field'
import DataView from '@/components/ui/DataView'
import PageHeader from '@/components/ui/PageHeader'
import StatCard from '@/components/ui/StatCard'
import { SkeletonCard } from '@/components/ui/Skeleton'
import { ScheduleGrid, GanttGrid, ScheduleToolbar, ScheduleLegend } from '@/components/schedule'
import type { ViewMode, GridType } from '@/components/schedule/types'
import { useApiQuery } from '@/lib/hooks/useApiQuery'
import { useScheduleData } from '@/lib/hooks/useScheduleData'
import { scheduleService } from '@/lib/services/schedule.service'
import { institutionService } from '@/lib/services/institution.service'
import { useAuthStore } from '@/lib/stores/auth.store'
import type { ScheduleRun } from '@/lib/types/scheduling'
import RoleGuard from '@/lib/guards/RoleGuard'

export default function HorarioAreaPage() {
  const [selectedRunId, setSelectedRunId] = useState('')
  const [viewMode, setViewMode] = useState<ViewMode>('docente')
  const [gridType, setGridType] = useState<GridType>('weekly')
  const [zoom, setZoom] = useState(1)
  const { user } = useAuthStore()
  const institutionId = user?.institutionId ?? ''

  const { data: periodData } = useApiQuery(
    () => institutionId ? institutionService.getActivePeriod(institutionId) : Promise.resolve({ data: null } as any),
    [institutionId],
  )
  const periodId = (periodData?.data as { id: string } | null)?.id ?? ''

  const { data: runsData, loading: runsLoad } = useApiQuery(
    () => (institutionId && periodId) ? scheduleService.listRuns(institutionId, periodId) : Promise.resolve({ data: [] } as any),
    [institutionId, periodId],
  )
  const runs: ScheduleRun[] = runsData?.data ?? []
  const activeRunId = selectedRunId || runs[0]?.id || ''

  const { assignments, loading, error, refetch, teachers, legendItems } =
    useScheduleData(activeRunId)

  return (
    <RoleGuard allowed={['coordinador']} fallback={<p className="text-muted-foreground">Sin acceso.</p>}>
      <div className="space-y-6">
        <PageHeader title="Horario del Área" description="Visualización del horario de tu área académica" />

        {(runsLoad || loading) ? (
          <div className="grid gap-4 sm:grid-cols-2">{[1, 2].map(i => <SkeletonCard key={i} />)}</div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            <StatCard title="Asignaciones" value={assignments.length} icon={Calendar} subtitle="De tu área" />
            <StatCard title="Docentes" value={teachers.length} icon={Users} subtitle="Del área" />
          </div>
        )}

        <ScheduleToolbar
          viewMode={viewMode}
          onViewModeChange={setViewMode}
          gridType={gridType}
          onGridTypeChange={setGridType}
          zoom={zoom}
          onZoomChange={setZoom}
          availableViewModes={['docente', 'salon', 'materia', 'area']}
          runSelector={
            runs.length > 1 ? (
              <FilterSelect
                value={activeRunId}
                onChange={setSelectedRunId}
                placeholder="Ejecución"
                options={runs.map(r => r.id)}
                labels={Object.fromEntries(runs.map(r => [r.id, r.name]))}
              />
            ) : undefined
          }
        />

        {legendItems.length > 0 && <ScheduleLegend items={legendItems} />}

        <DataView
          data={assignments}
          loading={runsLoad || loading}
          error={error}
          onRetry={refetch}
          emptyIcon={Calendar}
          emptyTitle="Sin asignaciones del área"
          emptyDescription="El horario aparecerá cuando el solver genere las asignaciones"
        >
          {() =>
            gridType === 'weekly' ? (
              <ScheduleGrid assignments={assignments} viewMode={viewMode} zoom={zoom} />
            ) : (
              <GanttGrid assignments={assignments} viewMode={viewMode} zoom={zoom} />
            )
          }
        </DataView>
      </div>
    </RoleGuard>
  )
}
