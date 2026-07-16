'use client'

import { useState } from 'react'
import { Play, CheckCircle, Zap, AlertTriangle, CalendarPlus } from 'lucide-react'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import { Field, NumberField } from '@/components/ui/Field'
import { Table, THead, TH, TBody, TR, TD } from '@/components/ui/Table'
import DataView from '@/components/ui/DataView'
import PageHeader from '@/components/ui/PageHeader'
import StatCard from '@/components/ui/StatCard'
import { SkeletonCard } from '@/components/ui/Skeleton'
import { useToast, ToastContainer } from '@/components/ui/Toast'
import { useApiQuery } from '@/lib/hooks/useApiQuery'
import { scheduleService } from '@/lib/services/schedule.service'
import { institutionService } from '@/lib/services/institution.service'
import { useAuthStore } from '@/lib/stores/auth.store'
import RoleGuard from '@/lib/guards/RoleGuard'
import type { ScheduleRun } from '@/lib/types/scheduling'

const STATUS_MAP: Record<string, { label: string; variant: 'neutral' | 'warning' | 'success' | 'danger' | 'info' }> = {
  pending: { label: 'Pendiente', variant: 'neutral' },
  running: { label: 'Ejecutando', variant: 'warning' },
  optimal: { label: 'Óptimo', variant: 'success' },
  feasible: { label: 'Factible', variant: 'success' },
  published: { label: 'Publicado', variant: 'info' },
  error: { label: 'Error', variant: 'danger' },
  blocked: { label: 'Bloqueado', variant: 'danger' },
}

export default function GenerarHorariosPage() {
  const { toasts, addToast, removeToast } = useToast()
  const { user } = useAuthStore()
  const institutionId = user?.institutionId ?? ''
  const [generating, setGenerating] = useState(false)
  const [creatingPeriod, setCreatingPeriod] = useState(false)
  const currentYear = new Date().getFullYear()
  const [periodName, setPeriodName] = useState(`${currentYear}-1`)
  const [periodYear, setPeriodYear] = useState(currentYear)
  const [periodNumber, setPeriodNumber] = useState(1)

  const { data: periodData, loading: periodLoading, refetch: periodRefetch } = useApiQuery(
    () => institutionId ? institutionService.getActivePeriod(institutionId) : Promise.resolve({ data: null } as any),
    [institutionId],
  )
  const periodId = (periodData?.data as { id: string } | null)?.id ?? ''

  const handleCreatePeriod = async () => {
    if (!institutionId || !periodName.trim()) return
    setCreatingPeriod(true)
    try {
      await institutionService.createPeriod(institutionId, { name: periodName, year: periodYear, periodNumber })
      addToast('success', 'Periodo académico creado y activado')
      periodRefetch()
    } catch {
      addToast('error', 'Error al crear el periodo académico')
    } finally {
      setCreatingPeriod(false)
    }
  }

  const { data: runData, loading: runLoad, error: runErr, refetch: runRefetch } =
    useApiQuery(
      () => (institutionId && periodId) ? scheduleService.listRuns(institutionId, periodId) : Promise.resolve({ data: [] } as any),
      [institutionId, periodId],
    )

  const runs: ScheduleRun[] = runData?.data ?? []
  const completedRuns = runs.filter(r => r.status === 'optimal' || r.status === 'feasible')
  const publishedRuns = runs.filter(r => r.status === 'published')

  const handleGenerate = async () => {
    if (!institutionId || !periodId) return
    setGenerating(true)
    try {
      await scheduleService.generate({ institutionId, periodId })
      addToast('success', 'Horario generado exitosamente')
      runRefetch()
    } catch {
      addToast('error', 'Error al generar el horario. Verifica que exista oferta académica con grupos.')
    } finally {
      setGenerating(false)
    }
  }

  const handlePublish = async (run: ScheduleRun) => {
    try {
      await scheduleService.publish(run.id)
      addToast('success', 'Horario publicado exitosamente')
      runRefetch()
    } catch { addToast('error', 'Error al publicar') }
  }

  return (
    <RoleGuard allowed={['director']} fallback={<p className="text-muted-foreground">Sin acceso.</p>}>
      <div className="space-y-6">
        <PageHeader
          title="Generar Horarios"
          description="Ejecuta el solver de optimización para crear horarios académicos"
          actions={
            <Button icon={<Zap className="size-4" />} loading={generating} disabled={!periodId} onClick={handleGenerate}>
              Generar horario
            </Button>
          }
        />

        {!periodLoading && !periodId && (
          <Card>
            <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
              <div className="flex items-start gap-3 sm:flex-1">
                <AlertTriangle className="size-5 shrink-0 text-warning" />
                <div>
                  <p className="text-sm font-medium text-foreground">No hay un periodo académico activo</p>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Para poder generar horarios primero necesitas un periodo académico activo. Crea uno abajo para habilitar la ejecución del solver.
                  </p>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-2 sm:w-auto sm:min-w-[360px]">
                <div className="col-span-3 sm:col-span-1">
                  <Field label="Nombre" value={periodName} onChange={setPeriodName} placeholder="2026-1" />
                </div>
                <NumberField label="Año" value={periodYear} onChange={setPeriodYear} />
                <NumberField label="Número" value={periodNumber} onChange={setPeriodNumber} />
              </div>
              <Button icon={<CalendarPlus className="size-4" />} loading={creatingPeriod} onClick={handleCreatePeriod}>
                Crear y activar periodo
              </Button>
            </div>
          </Card>
        )}

        {runLoad ? (
          <div className="grid gap-4 sm:grid-cols-4">{[1, 2, 3, 4].map(i => <SkeletonCard key={i} />)}</div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-4">
            <StatCard title="Ejecuciones" value={runs.length} icon={Play} subtitle="Totales" />
            <StatCard title="Completadas" value={completedRuns.length} icon={CheckCircle} subtitle="Listas para publicar" />
            <StatCard title="Publicadas" value={publishedRuns.length} icon={CheckCircle} subtitle="Horarios activos" />
            <StatCard title="Fallidas" value={runs.filter(r => r.status === 'error').length} icon={AlertTriangle} subtitle="Con errores" />
          </div>
        )}

        <Card bodyClassName="p-0">
          <div className="border-b border-border px-4 py-3">
            <p className="text-sm font-medium text-foreground">Historial de ejecuciones</p>
            <p className="text-xs text-muted-foreground mt-0.5">Cada ejecución genera un horario optimizado usando el solver OR-Tools</p>
          </div>
          <DataView data={runs} loading={runLoad} error={runErr} onRetry={runRefetch}
            emptyIcon={Play} emptyTitle="Sin ejecuciones"
            emptyDescription="Presiona 'Generar horario' para ejecutar el solver de optimización">
            {() => (
              <Table>
                <THead>
                  <TH>Nombre</TH>
                  <TH>Estado</TH>
                  <TH align="center">Asignaciones</TH>
                  <TH align="center">Conflictos</TH>
                  <TH align="center">Score</TH>
                  <TH align="right">Acciones</TH>
                </THead>
                <TBody>
                  {runs.map(r => {
                    const st = STATUS_MAP[r.status]
                    return (
                      <TR key={r.id}>
                        <TD><span className="font-medium">{r.name}</span></TD>
                        <TD><Badge variant={st?.variant ?? 'neutral'}>{st?.label ?? r.status}</Badge></TD>
                        <TD align="center">{r.totalAssignments}</TD>
                        <TD align="center">
                          {r.conflictCount > 0
                            ? <span className="text-danger font-semibold">{r.conflictCount}</span>
                            : <span className="text-success">0</span>}
                        </TD>
                        <TD align="center">{r.score != null ? `${Math.round(r.score)}%` : '—'}</TD>
                        <TD align="right">
                          {(r.status === 'optimal' || r.status === 'feasible') && (
                            <Button size="sm" variant="outline" onClick={() => handlePublish(r)}>Publicar</Button>
                          )}
                          {r.status === 'published' && (
                            <Badge variant="info">Publicado</Badge>
                          )}
                        </TD>
                      </TR>
                    )
                  })}
                </TBody>
              </Table>
            )}
          </DataView>
        </Card>

        <ToastContainer toasts={toasts} onRemove={removeToast} />
      </div>
    </RoleGuard>
  )
}
