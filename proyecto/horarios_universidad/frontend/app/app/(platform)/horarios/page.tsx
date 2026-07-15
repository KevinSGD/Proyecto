'use client'

import { useState } from 'react'
import { Calendar, Users, Building2, Save, RotateCcw } from 'lucide-react'
import { FilterSelect, SelectField, NumberField } from '@/components/ui/Field'
import Button from '@/components/ui/Button'
import DataView from '@/components/ui/DataView'
import Modal from '@/components/ui/Modal'
import PageHeader from '@/components/ui/PageHeader'
import StatCard from '@/components/ui/StatCard'
import { SkeletonCard } from '@/components/ui/Skeleton'
import { useToast, ToastContainer } from '@/components/ui/Toast'
import { ScheduleGrid, GanttGrid, ScheduleToolbar, ScheduleLegend } from '@/components/schedule'
import type { ViewMode, GridType, EnrichedAssignment } from '@/components/schedule/types'
import { useApiQuery } from '@/lib/hooks/useApiQuery'
import { useScheduleData } from '@/lib/hooks/useScheduleData'
import { scheduleService } from '@/lib/services/schedule.service'
import { institutionService } from '@/lib/services/institution.service'
import { useAuthStore } from '@/lib/stores/auth.store'
import type { ScheduleRun } from '@/lib/types/scheduling'
import RoleGuard from '@/lib/guards/RoleGuard'

export default function HorariosPage() {
  const [selectedRunId, setSelectedRunId] = useState('')
  const [viewMode, setViewMode] = useState<ViewMode>('global')
  const [gridType, setGridType] = useState<GridType>('weekly')
  const [zoom, setZoom] = useState(1)
  const { user } = useAuthStore()
  const institutionId = user?.institutionId ?? ''
  const { toasts, addToast, removeToast } = useToast()

  const [editModal, setEditModal] = useState<EnrichedAssignment | null>(null)
  const [editDay, setEditDay] = useState(1)
  const [editPeriod, setEditPeriod] = useState(1)
  const [editClassroom, setEditClassroom] = useState('')
  const [editTeacher, setEditTeacher] = useState('')
  const [saving, setSaving] = useState(false)

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

  const { assignments, loading, error, refetch, teachers, classrooms, legendItems } =
    useScheduleData(activeRunId)

  const openEdit = (a: EnrichedAssignment) => {
    setEditModal(a)
    setEditDay(a.dayOfWeek)
    const startHour = parseInt(a.startTime.split(':')[0], 10)
    const startMin = parseInt(a.startTime.split(':')[1], 10)
    const period = Math.floor((startHour * 60 + startMin - 7 * 60) / 60) + 1
    setEditPeriod(period > 0 ? period : 1)
    setEditClassroom(a.classroomId)
    setEditTeacher(a.instructorId)
  }

  const handleSaveEdit = async () => {
    if (!editModal) return
    setSaving(true)
    try {
      await scheduleService.updateSessionBlock(editModal.id, {
        dayOfWeek: editDay - 1,
        startPeriod: editPeriod,
        classroomId: editClassroom || undefined,
        instructorId: editTeacher || undefined,
      })
      addToast('success', 'Asignación actualizada')
      setEditModal(null)
      refetch()
    } catch {
      addToast('error', 'Error al guardar cambios')
    } finally {
      setSaving(false)
    }
  }

  const handleRerun = async () => {
    if (!institutionId || !periodId) return
    try {
      await scheduleService.generate({ institutionId, periodId })
      addToast('success', 'Solver re-ejecutado. Recargando...')
      setTimeout(() => refetch(), 1500)
    } catch {
      addToast('error', 'Error al re-ejecutar el solver')
    }
  }

  return (
    <RoleGuard allowed={['director']} fallback={<p className="text-muted-foreground">Sin acceso.</p>}>
      <div className="space-y-6">
        <PageHeader
          title="Horarios"
          description="Visualización y edición manual de horarios generados"
          action={
            <div className="flex gap-2">
              <Button variant="ghost" icon={<RotateCcw className="size-4" />} onClick={handleRerun}>Re-ejecutar Solver</Button>
              <Button icon={<Save className="size-4" />} onClick={() => addToast('success', 'Horario guardado')}>Guardar</Button>
            </div>
          }
        />

        {(runsLoad || loading) ? (
          <div className="grid gap-4 sm:grid-cols-3">{[1, 2, 3].map(i => <SkeletonCard key={i} />)}</div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-3">
            <StatCard title="Asignaciones" value={assignments.length} icon={Calendar} subtitle="En la ejecución" />
            <StatCard title="Docentes" value={teachers.length} icon={Users} subtitle="Registrados" />
            <StatCard title="Salones" value={classrooms.length} icon={Building2} subtitle="Disponibles" />
          </div>
        )}

        <ScheduleToolbar
          viewMode={viewMode}
          onViewModeChange={setViewMode}
          gridType={gridType}
          onGridTypeChange={setGridType}
          zoom={zoom}
          onZoomChange={setZoom}
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
          emptyTitle="Sin asignaciones"
          emptyDescription="Los horarios aparecerán al ejecutar el solver"
        >
          {() =>
            gridType === 'weekly' ? (
              <ScheduleGrid assignments={assignments} viewMode={viewMode} zoom={zoom} onEdit={openEdit} />
            ) : (
              <GanttGrid assignments={assignments} viewMode={viewMode} zoom={zoom} onEdit={openEdit} />
            )
          }
        </DataView>

        {/* Edit assignment modal */}
        <Modal
          open={!!editModal}
          onClose={() => setEditModal(null)}
          title="Editar Asignación"
          confirmLabel={saving ? 'Guardando...' : 'Guardar'}
          onConfirm={handleSaveEdit}
        >
          {editModal && (
            <div className="space-y-4">
              <div className="rounded-lg border border-border p-3 bg-muted/50">
                <p className="text-sm font-medium">{editModal.subjectName || editModal.subjectCode}</p>
                <p className="text-xs text-muted-foreground mt-0.5">{editModal.groupLabel}</p>
              </div>

              <SelectField
                label="Día"
                value={String(editDay)}
                onChange={v => setEditDay(Number(v))}
                options={['1', '2', '3', '4', '5', '6']}
                labels={{ '1': 'Lunes', '2': 'Martes', '3': 'Miércoles', '4': 'Jueves', '5': 'Viernes', '6': 'Sábado' }}
              />

              <NumberField
                label="Período (bloque horario)"
                value={editPeriod}
                onChange={setEditPeriod}
              />

              <SelectField
                label="Salón"
                value={editClassroom}
                onChange={setEditClassroom}
                options={classrooms.map(c => c.id)}
                labels={Object.fromEntries(classrooms.map(c => [c.id, `${c.code ?? ''} — ${c.name}`]))}
              />

              <SelectField
                label="Docente"
                value={editTeacher}
                onChange={setEditTeacher}
                options={teachers.map(t => t.id)}
                labels={Object.fromEntries(teachers.map(t => [t.id, `${t.firstName} ${t.lastName}`]))}
              />
            </div>
          )}
        </Modal>

        <ToastContainer toasts={toasts} onRemove={removeToast} />
      </div>
    </RoleGuard>
  )
}
