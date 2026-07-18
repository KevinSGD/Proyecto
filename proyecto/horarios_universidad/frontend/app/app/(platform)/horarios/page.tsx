'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Calendar, Users, Building2, Save, RotateCcw, ShieldCheck, Lock, ClipboardCheck, Download, ArrowRight, ListTree, Trash2 } from 'lucide-react'
import { FilterSelect, SelectField, NumberField } from '@/components/ui/Field'
import Badge from '@/components/ui/Badge'
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

type ValidationIssue = {
  message: string
  entityType: 'instructor' | 'subject' | 'classroom' | null
  entityId: string | null
  entityLabel: string | null
}

const ENTITY_ROUTES: Record<string, string> = {
  instructor: '/docentes',
  subject: '/materias',
  classroom: '/aulas',
}

export default function HorariosPage() {
  const router = useRouter()
  const [selectedRunId, setSelectedRunId] = useState('')
  const [viewMode, setViewMode] = useState<ViewMode>('global')
  const [gridType, setGridType] = useState<GridType>('weekly')
  const [zoom, setZoom] = useState(1)
  const { user } = useAuthStore()
  const institutionId = user?.institutionId ?? ''
  const { toasts, addToast, removeToast } = useToast()

  const [manageRunsOpen, setManageRunsOpen] = useState(false)
  const [deleteRunTarget, setDeleteRunTarget] = useState<ScheduleRun | null>(null)
  const [deletingRun, setDeletingRun] = useState(false)

  const [editModal, setEditModal] = useState<EnrichedAssignment | null>(null)
  const [editDay, setEditDay] = useState(1)
  const [editPeriod, setEditPeriod] = useState(1)
  const [editClassroom, setEditClassroom] = useState('')
  const [editTeacher, setEditTeacher] = useState('')
  const [saving, setSaving] = useState(false)

  const [validationModal, setValidationModal] = useState(false)
  const [validationResult, setValidationResult] = useState<{ isValid: boolean; errors: ValidationIssue[]; warnings: ValidationIssue[] } | null>(null)
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

  const { assignments, loading, error, refetch, teachers, classrooms, legendItems, scheduleConfig } =
    useScheduleData(activeRunId)
  const gridEndHour = scheduleConfig.startHour + Math.ceil((scheduleConfig.endPeriod - scheduleConfig.startPeriod + 1) * scheduleConfig.slotDurationMinutes / 60)

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
      const resp = await scheduleService.validate(institutionId, periodId, activeRunId || undefined)
      const data = (resp as any)?.data
      const extractIssues = (items: unknown[]): ValidationIssue[] =>
        (items ?? []).map((i: any) => typeof i === 'string'
          ? { message: i, entityType: null, entityId: null, entityLabel: null }
          : {
              message: i?.message ?? JSON.stringify(i),
              entityType: i?.entityType ?? null,
              entityId: i?.entityId ?? null,
              entityLabel: i?.entityLabel ?? null,
            })
      setValidationResult({
        isValid: data?.summary?.isValid ?? data?.summary?.is_valid ?? data?.isValid ?? true,
        errors: extractIssues(data?.errors),
        warnings: extractIssues(data?.warnings),
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

  const handleDeleteRun = async () => {
    if (!deleteRunTarget) return
    setDeletingRun(true)
    try {
      await scheduleService.deleteRun(deleteRunTarget.id)
      addToast('success', `Corrida "${deleteRunTarget.name || deleteRunTarget.id.slice(0, 8)}" eliminada`)
      if (selectedRunId === deleteRunTarget.id) setSelectedRunId('')
      setDeleteRunTarget(null)
      runsRefetch()
    } catch {
      addToast('error', 'Error al eliminar la corrida')
    } finally {
      setDeletingRun(false)
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

  const handleGoToIssue = (issue: ValidationIssue) => {
    if (!issue.entityType) return
    const route = ENTITY_ROUTES[issue.entityType]
    if (!route) return
    setValidationModal(false)
    router.push(`${route}?q=${encodeURIComponent(issue.entityLabel ?? '')}`)
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
              <Button variant="ghost" icon={<ListTree className="size-4" />} onClick={() => setManageRunsOpen(true)}>Gestionar corridas</Button>
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
                startHour={scheduleConfig.startHour}
                endHour={gridEndHour}
                onEdit={openEdit}
                onMove={handleMove}
                movable={!isLocked}
              />
            ) : (
              <GanttGrid assignments={assignments} viewMode={viewMode} zoom={zoom} startHour={scheduleConfig.startHour} endHour={gridEndHour} onEdit={openEdit} />
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
                label="Hora de clase (bloque)"
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
                      <li key={i}>
                        {e.entityType ? (
                          <button
                            type="button"
                            onClick={() => handleGoToIssue(e)}
                            className="w-full flex items-center justify-between gap-2 text-left text-xs text-foreground bg-danger-soft hover:brightness-95 rounded px-2 py-1.5 transition"
                          >
                            <span>{e.message}</span>
                            <ArrowRight className="size-3.5 shrink-0 text-danger" />
                          </button>
                        ) : (
                          <p className="text-xs text-foreground bg-danger-soft rounded px-2 py-1">{e.message}</p>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {validationResult.warnings.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-warning mb-2">Advertencias ({validationResult.warnings.length})</p>
                  <ul className="space-y-1">
                    {validationResult.warnings.map((w, i) => (
                      <li key={i}>
                        {w.entityType ? (
                          <button
                            type="button"
                            onClick={() => handleGoToIssue(w)}
                            className="w-full flex items-center justify-between gap-2 text-left text-xs text-foreground bg-warning-soft hover:brightness-95 rounded px-2 py-1.5 transition"
                          >
                            <span>{w.message}</span>
                            <ArrowRight className="size-3.5 shrink-0 text-warning" />
                          </button>
                        ) : (
                          <p className="text-xs text-foreground bg-warning-soft rounded px-2 py-1">{w.message}</p>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </Modal>

        {/* Manage schedule runs modal */}
        <Modal
          open={manageRunsOpen}
          onClose={() => setManageRunsOpen(false)}
          title="Gestionar corridas del solver"
          confirmLabel="Cerrar"
          onConfirm={() => setManageRunsOpen(false)}
        >
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {runs.length === 0 && (
              <p className="text-sm text-muted-foreground">No hay corridas todavía.</p>
            )}
            {[...runs].reverse().map((r) => (
              <div key={r.id} className="flex items-center justify-between gap-2 rounded-lg border border-border px-3 py-2">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-foreground truncate">{r.name || r.id.slice(0, 8)}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <Badge variant={
                      r.status === 'published' ? 'success' :
                      r.status === 'blocked' ? 'info' :
                      r.status === 'infeasible' || r.status === 'error' ? 'danger' :
                      r.status === 'optimal' || r.status === 'feasible' ? 'brand' : 'neutral'
                    }>{r.status}</Badge>
                  </div>
                </div>
                <button
                  onClick={() => setDeleteRunTarget(r)}
                  title="Eliminar corrida"
                  className="shrink-0 rounded-md p-1.5 text-muted-foreground hover:bg-danger-soft hover:text-danger transition-colors"
                >
                  <Trash2 className="size-4" />
                </button>
              </div>
            ))}
          </div>
        </Modal>

        <Modal
          open={!!deleteRunTarget}
          onClose={() => { if (!deletingRun) setDeleteRunTarget(null) }}
          title="Eliminar corrida"
          confirmLabel={deletingRun ? 'Eliminando...' : 'Eliminar'}
          onConfirm={handleDeleteRun}
          destructive
        >
          <p>
            ¿Eliminar la corrida <strong>{deleteRunTarget?.name || deleteRunTarget?.id.slice(0, 8)}</strong>?
            Se borrarán sus asignaciones y bloques de horario. Esta acción no se puede deshacer.
          </p>
        </Modal>

        <ToastContainer toasts={toasts} onRemove={removeToast} />
      </div>
    </RoleGuard>
  )
}
