'use client'

import { useState } from 'react'
import { Calendar, Users, Building2, Save, RotateCcw, ShieldCheck, Lock, ClipboardCheck, Download } from 'lucide-react'
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

  const [validationModal, setValidationModal] = useState(false)
  const [validationResult, setValidationResult] = useState<{ isValid: boolean; errors: string[]; warnings: string[] } | null>(null)
  const [validating, setValidating] = useState(false)
  const [blocking, setBlocking] = useState(false)
  const [exporting, setExporting] = useState(false)

  const { data: periodData } = useApiQuery(
    () => institutionId ? institutionService.getActivePeriod(institutionId) : Promise.resolve({ data: null } as any),
    [institutionId],
  )
  const periodId = (periodData?.data as { id: string } | null)?.id ?? ''

  const { data: runsData, loading: runsLoad, refetch: runsRefetch } = useApiQuery(
    () => (institutionId && periodId) ? scheduleService.listRuns(institutionId, periodId) : Promise.resolve({ data: [] } as any),
    [institutionId, periodId],
  )
  const runs: ScheduleRun[] = runsData?.data ?? []
  const activeRunId = selectedRunId || runs[0]?.id || ''
  const activeRun = runs.find(r => r.id === activeRunId)
  const isLocked = activeRun?.status === 'blocked' || activeRun?.status === 'published'

  const { assignments, loading, error, refetch, teachers, classrooms, legendItems } =
    useScheduleData(activeRunId)

  const openEdit = (a: EnrichedAssignment) => {
    if (isLocked) {
      addToast('warning', 'El horario está confirmado. No se permite edición.')
      return
    }
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

  const handleSave = async () => {
    refetch()
    addToast('success', 'Los cambios están guardados automáticamente')
  }

  const handleMove = async (blockId: string, dayOfWeek: number, startPeriod: number) => {
    if (isLocked) return
    try {
      await scheduleService.updateSessionBlock(blockId, { dayOfWeek: dayOfWeek - 1, startPeriod })
      addToast('success', 'Clase movida. Usa "Verificar Integridad" para confirmar que no genera interferencias.')
      refetch()
    } catch {
      addToast('error', 'Error al mover la clase')
    }
  }

  const handleValidate = async () => {
    if (!institutionId || !periodId) return
    setValidating(true)
    try {
      const resp = await scheduleService.validate(institutionId, periodId)
      const data = (resp as any)?.data
      const extractMessages = (items: unknown[]): string[] =>
        (items ?? []).map((i: any) => typeof i === 'string' ? i : i?.message ?? JSON.stringify(i))
      setValidationResult({
        isValid: data?.summary?.isValid ?? data?.summary?.is_valid ?? data?.isValid ?? true,
        errors: extractMessages(data?.errors),
        warnings: extractMessages(data?.warnings),
      })
      setValidationModal(true)
    } catch {
      addToast('error', 'Error al verificar integridad')
    } finally {
      setValidating(false)
    }
  }

  const handleBlock = async () => {
    if (!activeRunId) return
    setBlocking(true)
    try {
      await scheduleService.block(activeRunId)
      addToast('success', 'Horario confirmado. La edición ha sido bloqueada.')
      runsRefetch()
    } catch {
      addToast('error', 'Error al confirmar horario')
    } finally {
      setBlocking(false)
    }
  }

  const handleExportExcel = async () => {
    if (!activeRunId) return
    setExporting(true)
    try {
      const { blob, filename } = await scheduleService.exportExcel(activeRunId)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename ?? 'horario.xlsx'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      addToast('success', 'Excel descargado')
    } catch {
      addToast('error', 'Error al exportar el horario a Excel')
    } finally {
      setExporting(false)
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
          actions={
            <div className="flex gap-2">
              <Button variant="ghost" icon={<RotateCcw className="size-4" />} onClick={handleRerun} disabled={isLocked}>Re-ejecutar Solver</Button>
              <Button variant="outline" icon={<ShieldCheck className="size-4" />} onClick={handleValidate} loading={validating}>Verificar Integridad</Button>
              <Button variant="outline" icon={<Download className="size-4" />} onClick={handleExportExcel} loading={exporting} disabled={!activeRunId}>Exportar Excel</Button>
              {!isLocked && (
                <Button variant="outline" icon={<Lock className="size-4" />} onClick={handleBlock} loading={blocking} disabled={!activeRunId}>Confirmar Horario</Button>
              )}
              <Button icon={<Save className="size-4" />} onClick={handleSave} disabled={isLocked}>Guardar</Button>
            </div>
          }
        />

        {isLocked && (
          <div className="rounded-lg border border-info bg-info-soft px-4 py-3 flex items-center gap-2">
            <ClipboardCheck className="size-4 text-info" />
            <p className="text-sm text-foreground">
              Este horario está <strong>{activeRun?.status === 'published' ? 'publicado' : 'confirmado'}</strong>. La edición está bloqueada.
            </p>
          </div>
        )}

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

        {!isLocked && gridType === 'weekly' && assignments.length > 0 && (
          <p className="text-xs text-muted-foreground">
            Arrastra una clase a otro día/hora para moverla, luego usa "Verificar Integridad" para confirmar que no genera interferencias.
          </p>
        )}

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
              <ScheduleGrid
                assignments={assignments}
                viewMode={viewMode}
                zoom={zoom}
                onEdit={openEdit}
                onMove={handleMove}
                movable={!isLocked}
              />
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

        {/* Validation result modal */}
        <Modal
          open={validationModal}
          onClose={() => setValidationModal(false)}
          title="Verificación de Integridad"
          confirmLabel="Cerrar"
          onConfirm={() => setValidationModal(false)}
        >
          {validationResult && (
            <div className="space-y-4">
              <div className={`rounded-lg px-4 py-3 ${validationResult.isValid ? 'bg-success-soft border border-success' : 'bg-danger-soft border border-danger'}`}>
                <p className={`text-sm font-medium ${validationResult.isValid ? 'text-success' : 'text-danger'}`}>
                  {validationResult.isValid ? 'Sin errores de integridad' : 'Se encontraron problemas'}
                </p>
              </div>

              {validationResult.errors.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-danger mb-2">Errores ({validationResult.errors.length})</p>
                  <ul className="space-y-1">
                    {validationResult.errors.map((e, i) => (
                      <li key={i} className="text-xs text-foreground bg-danger-soft rounded px-2 py-1">{String(e)}</li>
                    ))}
                  </ul>
                </div>
              )}

              {validationResult.warnings.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-warning mb-2">Advertencias ({validationResult.warnings.length})</p>
                  <ul className="space-y-1">
                    {validationResult.warnings.map((w, i) => (
                      <li key={i} className="text-xs text-foreground bg-warning-soft rounded px-2 py-1">{String(w)}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </Modal>

        <ToastContainer toasts={toasts} onRemove={removeToast} />
      </div>
    </RoleGuard>
  )
}
